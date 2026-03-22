"""
PPT 处理 API 路由

端点:
  POST /ppt/upload          上传 PPTX（支持 1-2 个文件）
  POST /ppt/process         AI 处理选定页面 → 立即生成新版本
  POST /ppt/compose         从多个 PPT 选页组合新 PPT
  GET  /ppt/versions/{id}   获取版本历史
  GET  /ppt/download/{id}/{version_id}  下载指定版本
"""

import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from ..config import settings
from ..core.pptx_reader import PPTXReader
from ..core.content_extractor import ContentExtractor
from ..core.pptx_writer import PPTXWriter
from ..core.style_applicator import StyleApplicator
from ..core.animation_applicator import AnimationApplicator
from ..core.models import PPTSession, PPTVersion, SlideSelector
from ..core.session_logger import get_session_logger
from ..ai.llm_client import LLMClient
from ..ai.processor import AIProcessor
from .schemas import (
    ProcessRequest, ComposeRequest,
    UploadResponse, ProcessResponse, ComposeResponse, VersionListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ppt", tags=["PPT"])

_sessions: dict[str, PPTSession] = {}
_reader = PPTXReader()
_extractor = ContentExtractor()
_writer = PPTXWriter(
    style_applicator=StyleApplicator(),
    animation_applicator=AnimationApplicator(enabled=True),
)


def _get_session(session_id: str) -> PPTSession:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"会话不存在: {session_id}")
    return session


def _session_dir(session_id: str) -> Path:
    return Path(settings.UPLOAD_DIR) / session_id


def _generate_previews(
    session_id: str, pptx_path: Path, pages: list[int] | None = None
) -> list[dict]:
    """生成预览图（如果 LibreOffice 可用）

    Args:
        pages: 只为指定页面生成预览（0-based），None 表示全部。
               返回顺序与 pages 参数一致（新页面可排在前面）。
    """
    try:
        from ..services.ppt_to_image import PptToImageConverter, Resolution
        preview_dir = Path(settings.PUBLIC_DIR) / "previews" / session_id
        preview_dir.mkdir(parents=True, exist_ok=True)
        converter = PptToImageConverter(preview_dir, Resolution.MEDIUM)
        result = converter.convert(pptx_path, pages=pages)
        if result.success:
            images = [
                {"slide_index": img["page"], "url": img["url"]}
                for img in result.images
            ]
            if pages is not None:
                page_to_img = {img["slide_index"]: img for img in images}
                images = [page_to_img[p] for p in pages if p in page_to_img]
            return images
    except Exception as e:
        logger.warning(f"预览图生成失败 (可忽略): {e}")
    return []


@router.post("/upload", response_model=UploadResponse)
async def upload_pptx(
    file_a: UploadFile = File(..., alias="file_a"),
    file_b: Optional[UploadFile] = File(None, alias="file_b"),
):
    """上传 1-2 个 PPTX 文件，解析并创建会话"""
    session_id = f"{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    slog = get_session_logger(session_id)
    slog.section("新会话 - 上传 PPTX")

    sdir = _session_dir(session_id)
    sdir.mkdir(parents=True, exist_ok=True)

    original_files = {}
    parsed_data = {}
    all_previews = []

    for key, upload in [("ppt_a", file_a), ("ppt_b", file_b)]:
        if upload is None:
            continue
        if not upload.filename.lower().endswith(".pptx"):
            raise HTTPException(400, f"{key}: 只支持 .pptx 文件")

        file_path = sdir / f"{key}_{upload.filename}"
        content = await upload.read()
        file_path.write_bytes(content)
        original_files[key] = str(file_path)

        slog.begin("parse", key=key, filename=upload.filename, size_mb=f"{len(content)/1024/1024:.1f}")
        parsed = _reader.parse(file_path)
        parsed_data[key] = parsed.model_dump()
        slog.end("parse", slide_count=parsed.slide_count)

        slog.begin("preview", key=key)
        previews = _generate_previews(session_id, file_path)
        for p in previews:
            p["source"] = key
        all_previews.extend(previews)
        slog.end("preview", count=len(previews))

    session = PPTSession(
        session_id=session_id,
        created_at=datetime.now().isoformat(),
        original_files=original_files,
        parsed=parsed_data,
    )
    _sessions[session_id] = session

    combined_parsed = {}
    for key, data in parsed_data.items():
        combined_parsed[key] = data

    slog.info("会话创建完成", files=str(list(original_files.keys())), total_previews=len(all_previews))

    return UploadResponse(
        session_id=session_id,
        parsed=combined_parsed,
        preview_images=all_previews,
    )


@router.post("/process", response_model=ProcessResponse)
async def process_slides(req: ProcessRequest):
    """AI 处理选定页面 → 立即写回生成新版本"""
    session = _get_session(req.session_id)
    slog = get_session_logger(req.session_id)
    slog.section(f"AI 处理 - {req.action}")
    slog.info("请求参数",
              action=req.action,
              slide_indices=str(req.slide_indices),
              domain=req.domain or "_default",
              provider=req.provider or "default",
              model=req.model or "default")

    try:
        llm = LLMClient(
            provider=req.provider,
            api_key=req.api_key,
            base_url=req.base_url,
            model=req.model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except ValueError as e:
        slog.error(f"LLM 客户端创建失败: {e}")
        raise HTTPException(400, str(e))

    processor = AIProcessor(llm, session_logger=slog)

    # 提取内容：支持单源(slide_indices)和多源(selections)
    slog.begin("extract_content")
    contents = []
    source_key = req.source

    if req.action == "fuse" and req.selections:
        # 多源融合：从不同源文件提取页面
        base_version_path = None
        for sel in req.selections:
            src_path_str = session.original_files.get(sel.source)
            if not src_path_str:
                slog.error(f"源文件 {sel.source} 不存在")
                continue
            src_path = Path(src_path_str)
            if not src_path.exists():
                slog.error(f"源文件不存在: {src_path}")
                continue
            parsed = _reader.parse(src_path)
            if sel.slide_index >= len(parsed.slides):
                slog.error(f"页码超出范围: {sel.source}[{sel.slide_index}]")
                continue
            content = _extractor.extract_slide(parsed.slides[sel.slide_index])
            contents.append(content)
            if base_version_path is None:
                base_version_path = src_path

        if not base_version_path:
            slog.error("没有有效的源文件")
            raise HTTPException(400, "没有有效的源文件")
    else:
        # 单源模式：优先用最新版本，页码不足时回退原始文件
        original_path = Path(session.original_files.get(source_key, ""))
        base_version_path = None

        if session.versions:
            last = session.versions[-1]
            candidate = Path(last.output_path)
            if candidate.exists():
                candidate_parsed = _reader.parse(candidate)
                max_idx = max(req.slide_indices) if req.slide_indices else 0
                if max_idx < len(candidate_parsed.slides):
                    base_version_path = candidate
                    parsed = candidate_parsed

        if base_version_path is None:
            if not original_path.exists():
                slog.error("找不到源文件")
                raise HTTPException(400, "找不到源文件")
            base_version_path = original_path
            parsed = _reader.parse(base_version_path)

        for idx in req.slide_indices:
            if idx >= len(parsed.slides):
                slog.error(f"页码超出范围: {idx}")
                raise HTTPException(400, f"页码超出范围: {idx} (共 {parsed.slide_count} 页)")
            content = _extractor.extract_slide(parsed.slides[idx])
            contents.append(content)

    slog.end("extract_content", slides=len(contents))

    if not contents:
        return ProcessResponse(success=False, error="没有可处理的内容")

    slog.info("基础版本", path=str(base_version_path.name))

    slog.begin("llm_call")
    result = processor.process_slides(contents, req.action, req.domain, req.custom_prompt)
    slog.end("llm_call", success=result.success, total_changes=result.total_changes)

    if not result.success:
        slog.error(f"AI 处理失败: {result.error}")
        return ProcessResponse(success=False, error=result.error)

    if result.modifications:
        slog.info("AI 摘要", summary=result.modifications[0].ai_summary or "")

    slog.begin("write_pptx")
    sdir = _session_dir(req.session_id)
    apply_result = _writer.apply(base_version_path, result.modifications, sdir)
    output_path = apply_result.output_path
    slog.end("write_pptx", output=output_path.name,
             result_pages=len(apply_result.modified_indices))

    version_number = len(session.versions) + 1
    version_id = uuid.uuid4().hex[:8]

    # 干净输出：文件只含 AI 结果页面，直接全量生成预览
    slog.begin("generate_preview")
    preview_images = _generate_previews(req.session_id, output_path)
    slog.end("generate_preview", count=len(preview_images))

    slide_selection = []
    if req.selections:
        slide_selection = req.selections
    else:
        slide_selection = [
            SlideSelector(source=source_key, slide_index=i) for i in req.slide_indices
        ]

    version = PPTVersion(
        version_id=version_id,
        version_number=version_number,
        created_at=datetime.now().isoformat(),
        action=req.action,
        description=(result.modifications[0].ai_summary or "") if result.modifications else "",
        output_path=str(output_path),
        slide_selection=slide_selection,
        modifications=result.modifications,
        preview_images=[p.get("url", "") for p in preview_images],
        source_version_id=session.current_version_id,
    )

    session.versions.append(version)
    session.current_version_id = version_id

    slog.info(f"版本 v{version_number} 创建完成",
              version_id=version_id,
              changes=result.total_changes)

    return ProcessResponse(
        success=True,
        version=version,
        result=result,
    )


@router.post("/compose", response_model=ComposeResponse)
async def compose_slides(req: ComposeRequest):
    """从多个 PPT 选择页面组合新 PPT"""
    session = _get_session(req.session_id)
    slog = get_session_logger(req.session_id)
    slog.section("页面组合 - compose")

    selections_desc = [f"{s.source}[{s.slide_index}]" for s in req.selections]
    slog.info("组合请求", pages=str(selections_desc))

    source_files = {}
    for key, path_str in session.original_files.items():
        source_files[key] = Path(path_str)

    if session.versions:
        last = session.versions[-1]
        last_path = Path(last.output_path)
        if last_path.exists():
            source_files["latest"] = last_path

    try:
        slog.begin("compose_pptx")
        sdir = _session_dir(req.session_id)
        output_path = _writer.compose(source_files, req.selections, sdir)
        slog.end("compose_pptx", output=output_path.name)
    except Exception as e:
        slog.error(f"页面组合失败: {e}")
        return ComposeResponse(success=False, error=str(e))

    version_number = len(session.versions) + 1
    version_id = uuid.uuid4().hex[:8]

    slog.begin("generate_preview")
    preview_images = _generate_previews(req.session_id, output_path)
    slog.end("generate_preview", count=len(preview_images))

    version = PPTVersion(
        version_id=version_id,
        version_number=version_number,
        created_at=datetime.now().isoformat(),
        action="compose",
        description=f"从 {len(req.selections)} 页组合",
        output_path=str(output_path),
        slide_selection=req.selections,
        preview_images=[p.get("url", "") for p in preview_images],
        source_version_id=session.current_version_id,
    )

    session.versions.append(version)
    session.current_version_id = version_id

    slog.info(f"组合完成 v{version_number}", version_id=version_id, pages=len(req.selections))

    return ComposeResponse(success=True, version=version)


@router.get("/versions/{session_id}", response_model=VersionListResponse)
async def get_versions(session_id: str):
    """获取版本历史"""
    session = _get_session(session_id)
    return VersionListResponse(
        session_id=session_id,
        versions=session.versions,
        current_version_id=session.current_version_id,
    )


@router.get("/download/{session_id}/{version_id}")
async def download_version(session_id: str, version_id: str):
    """下载指定版本的 PPTX"""
    session = _get_session(session_id)
    slog = get_session_logger(session_id)

    version = next((v for v in session.versions if v.version_id == version_id), None)
    if not version:
        raise HTTPException(404, f"版本不存在: {version_id}")

    path = Path(version.output_path)
    if not path.exists():
        raise HTTPException(404, f"文件不存在: {path}")

    slog.info("下载版本", version_id=version_id, version=f"v{version.version_number}", file=path.name)

    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"v{version.version_number}_{path.name}",
    )


@router.get("/download/{session_id}")
async def download_latest(session_id: str):
    """下载最新版本"""
    session = _get_session(session_id)

    if not session.versions:
        first_file = list(session.original_files.values())[0] if session.original_files else None
        if not first_file:
            raise HTTPException(404, "没有可下载的文件")
        path = Path(first_file)
        if not path.exists():
            raise HTTPException(404, "原始文件不存在")
        return FileResponse(
            path=str(path),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=path.name,
        )

    latest = session.versions[-1]
    path = Path(latest.output_path)
    if not path.exists():
        raise HTTPException(404, f"文件不存在: {path}")

    return FileResponse(
        path=str(path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"v{latest.version_number}_{path.name}",
    )


@router.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """获取会话信息"""
    session = _get_session(session_id)
    return session.model_dump()
