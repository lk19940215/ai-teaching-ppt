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
import shutil
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
from ..core.models import PPTSession, PPTVersion, SlideSelector
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
_writer = PPTXWriter()


def _get_session(session_id: str) -> PPTSession:
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(404, f"会话不存在: {session_id}")
    return session


def _session_dir(session_id: str) -> Path:
    return Path(settings.UPLOAD_DIR) / session_id


def _generate_previews(session_id: str, pptx_path: Path) -> list[dict]:
    """生成预览图（如果 LibreOffice 可用）"""
    try:
        from ..services.ppt_to_image import PptToImageConverter, Resolution
        preview_dir = Path(settings.PUBLIC_DIR) / "previews" / session_id
        preview_dir.mkdir(parents=True, exist_ok=True)
        converter = PptToImageConverter(preview_dir, Resolution.MEDIUM)
        result = converter.convert(pptx_path)
        if result.success:
            return [
                {"slide_index": img["page"], "url": img["url"]}
                for img in result.images
            ]
    except Exception as e:
        logger.warning(f"预览图生成失败 (可忽略): {e}")
    return []


@router.post("/upload", response_model=UploadResponse)
async def upload_pptx(
    file_a: UploadFile = File(..., alias="file_a"),
    file_b: Optional[UploadFile] = File(None, alias="file_b"),
):
    """上传 1-2 个 PPTX 文件，解析并创建会话"""
    session_id = uuid.uuid4().hex[:12]
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

        parsed = _reader.parse(file_path)
        parsed_data[key] = parsed.model_dump()

        previews = _generate_previews(session_id, file_path)
        for p in previews:
            p["source"] = key
        all_previews.extend(previews)

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

    logger.info(
        f"会话创建: {session_id}, "
        f"文件: {list(original_files.keys())}"
    )

    return UploadResponse(
        session_id=session_id,
        parsed=combined_parsed,
        preview_images=all_previews,
    )


@router.post("/process", response_model=ProcessResponse)
async def process_slides(req: ProcessRequest):
    """AI 处理选定页面 → 立即写回生成新版本"""
    session = _get_session(req.session_id)

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
        raise HTTPException(400, str(e))

    processor = AIProcessor(llm)

    source_key = "ppt_a"
    base_version_path = None

    if session.versions:
        last = session.versions[-1]
        base_version_path = Path(last.output_path)
        if not base_version_path.exists():
            base_version_path = None

    if base_version_path is None:
        base_version_path = Path(session.original_files.get(source_key, ""))
        if not base_version_path.exists():
            raise HTTPException(400, "找不到源文件")

    parsed = _reader.parse(base_version_path)

    contents = []
    for idx in req.slide_indices:
        if idx >= len(parsed.slides):
            raise HTTPException(400, f"页码超出范围: {idx} (共 {parsed.slide_count} 页)")
        content = _extractor.extract_slide(parsed.slides[idx])
        contents.append(content)

    result = processor.process_slides(contents, req.action, req.custom_prompt)

    if not result.success:
        return ProcessResponse(success=False, error=result.error)

    sdir = _session_dir(req.session_id)
    output_path = _writer.apply(base_version_path, result.modifications, sdir)

    version_number = len(session.versions) + 1
    version_id = uuid.uuid4().hex[:8]

    preview_images = _generate_previews(req.session_id, output_path)

    version = PPTVersion(
        version_id=version_id,
        version_number=version_number,
        created_at=datetime.now().isoformat(),
        action=req.action,
        description=result.modifications[0].ai_summary if result.modifications else "",
        output_path=str(output_path),
        slide_selection=[
            SlideSelector(source=source_key, slide_index=i) for i in req.slide_indices
        ],
        modifications=result.modifications,
        preview_images=[p.get("url", "") for p in preview_images],
        source_version_id=session.current_version_id,
    )

    session.versions.append(version)
    session.current_version_id = version_id

    logger.info(
        f"版本 v{version_number} 创建: {version_id}, "
        f"action={req.action}, changes={result.total_changes}"
    )

    return ProcessResponse(
        success=True,
        version=version,
        result=result,
    )


@router.post("/compose", response_model=ComposeResponse)
async def compose_slides(req: ComposeRequest):
    """从多个 PPT 选择页面组合新 PPT"""
    session = _get_session(req.session_id)

    source_files = {}
    for key, path_str in session.original_files.items():
        source_files[key] = Path(path_str)

    if session.versions:
        last = session.versions[-1]
        last_path = Path(last.output_path)
        if last_path.exists():
            source_files["latest"] = last_path

    try:
        sdir = _session_dir(req.session_id)
        output_path = _writer.compose(source_files, req.selections, sdir)
    except Exception as e:
        logger.error(f"页面组合失败: {e}")
        return ComposeResponse(success=False, error=str(e))

    version_number = len(session.versions) + 1
    version_id = uuid.uuid4().hex[:8]

    preview_images = _generate_previews(req.session_id, output_path)

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

    version = next((v for v in session.versions if v.version_id == version_id), None)
    if not version:
        raise HTTPException(404, f"版本不存在: {version_id}")

    path = Path(version.output_path)
    if not path.exists():
        raise HTTPException(404, f"文件不存在: {path}")

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
