"""
PPT 合并 API 路由

核心功能：
- /ppt/parse: 解析上传的 PPT 文件
- /ppt/ai-merge-single: 单页 AI 处理（润色/扩展/改写/提取）
- /ppt/ai-merge: 多页 AI 合并
- /ppt/generate-final: 生成最终 PPT
"""

from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from typing import Optional, AsyncGenerator, List, Dict, Any
import logging
import traceback as traceback_module
import uuid
import aiofiles
import asyncio
import json
import tempfile
import hashlib
import time
import psutil
import os

from ..services.ppt_generator import get_ppt_generator, generate_single_slide_pptx
from ..services.ppt_to_image import convert_single_slide_to_image
from ..config import settings

router = APIRouter(prefix=settings.API_V1_STR, tags=["ppt"])

logger = logging.getLogger(__name__)

# ==================== 工具函数 ====================

# PPT 解析缓存
_ppt_parse_cache: Dict[str, Dict[str, Any]] = {}
_PPT_CACHE_MAX_SIZE = 100
_PPT_CACHE_TTL = 1800
_MEMORY_WARNING_THRESHOLD = 0.85
_MEMORY_CRITICAL_THRESHOLD = 0.95


def _get_memory_usage() -> float:
    """获取当前进程内存使用率"""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        system_mem = psutil.virtual_memory().total
        return mem_info.rss / system_mem
    except Exception:
        return 0.0


def _compute_file_hash(content: bytes) -> str:
    """计算文件内容的 SHA256 哈希值"""
    return hashlib.sha256(content).hexdigest()


def safe_join_list(items: List[Any], separator: str = '\n') -> str:
    """
    安全连接列表元素，处理混合类型（str/dict）。

    Args:
        items: 可能包含字符串或字典的列表
        separator: 连接符，默认换行符

    Returns:
        连接后的字符串
    """
    if not items:
        return ''

    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            text = (item.get('text') or
                    item.get('content') or
                    item.get('point') or
                    item.get('title') or
                    item.get('value') or
                    str(item))
            result.append(text)
        else:
            result.append(str(item))

    return separator.join(result)


def test_json_serialization(data: Any, context: str = "data") -> Dict[str, Any]:
    """
    测试 JSON 序列化并返回详细的调试信息。

    Args:
        data: 要测试的数据
        context: 上下文描述（用于日志）

    Returns:
        包含成功状态、错误信息、问题字段等的字典
    """
    start_time = time.time()
    result = {
        "success": False,
        "error": None,
        "problematic_fields": [],
        "json_length": None,
        "duration_ms": 0
    }

    try:
        json_str = json.dumps(data, ensure_ascii=False, default=str)
        result["success"] = True
        result["json_length"] = len(json_str)
        logger.info(f"[JSON序列化] {context}: 成功，长度 {len(json_str)} 字符")
    except TypeError as e:
        result["error"] = str(e)
        logger.error(f"[JSON序列化] {context}: 失败 - {e}")

        if isinstance(data, dict):
            for key, value in data.items():
                try:
                    json.dumps({key: value}, ensure_ascii=False, default=str)
                except TypeError:
                    result["problematic_fields"].append(f"{key}: {type(value).__name__}")
                    logger.error(f"[JSON序列化] {context}: 字段 '{key}' 无法序列化")

    result["duration_ms"] = round((time.time() - start_time) * 1000, 2)
    return result


def _cleanup_cache():
    """清理过期缓存并执行 LRU 淘汰"""
    current_time = time.time()
    keys_to_remove = []
    for file_hash, cache_entry in list(_ppt_parse_cache.items()):
        if current_time - cache_entry["timestamp"] > _PPT_CACHE_TTL:
            keys_to_remove.append(file_hash)
    if len(_ppt_parse_cache) - len(keys_to_remove) > _PPT_CACHE_MAX_SIZE:
        sorted_entries = sorted(
            [(k, v) for k, v in _ppt_parse_cache.items() if k not in keys_to_remove],
            key=lambda x: x[1]["timestamp"]
        )
        keys_to_remove.extend([k for k, _ in sorted_entries[:_PPT_CACHE_MAX_SIZE // 2]])
    for key in keys_to_remove:
        del _ppt_parse_cache[key]


def _get_from_cache(file_hash: str) -> Optional[Dict[str, Any]]:
    """从缓存中获取解析结果"""
    if file_hash not in _ppt_parse_cache:
        return None
    cache_entry = _ppt_parse_cache[file_hash]
    current_time = time.time()
    if current_time - cache_entry["timestamp"] > _PPT_CACHE_TTL:
        del _ppt_parse_cache[file_hash]
        return None
    return cache_entry["data"]


def _add_to_cache(file_hash: str, data: Dict[str, Any]):
    """添加解析结果到缓存"""
    _cleanup_cache()
    _ppt_parse_cache[file_hash] = {"data": data, "timestamp": time.time()}


def _fix_invalid_namespaces(file_path: Path) -> Path:
    """修复 PPTX 文件中无效的 XML 命名空间声明"""
    import zipfile
    import re
    import shutil

    temp_dir = file_path.parent
    fix_dir = temp_dir / f"fixed_{uuid.uuid4().hex}"
    fix_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(file_path, 'r') as z:
            z.extractall(fix_dir)

        ns_pattern = re.compile(r'xmlns:ns(\d+)=([\'"])%s\2')
        placeholder_pattern = re.compile(r'xmlns:([a-zA-Z0-9_]+)=["\']\{([^}]*)\}[^"\']*["\']')

        fixed_count = 0

        for xml_file in fix_dir.rglob("*.xml"):
            try:
                content = xml_file.read_text(encoding='utf-8')
                original_content = content

                def replace_ns(match):
                    ns_num = match.group(1)
                    quote = match.group(2)
                    return f'xmlns:ns{ns_num}={quote}http://schemas.openxmlformats.org/presentationml/2006/placeholder{quote}'

                content = ns_pattern.sub(replace_ns, content)
                content = placeholder_pattern.sub(
                    r'xmlns:\1="http://schemas.openxmlformats.org/presentationml/2006/\2"',
                    content
                )

                if content != original_content:
                    xml_file.write_text(content, encoding='utf-8')
                    fixed_count += 1

            except Exception as e:
                logger.warning(f"修复 XML 文件失败 {xml_file}: {e}")

        fixed_path = temp_dir / f"fixed_{uuid.uuid4().hex}_{file_path.name}"
        with zipfile.ZipFile(fixed_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(fix_dir):
                for f in files:
                    file_on_disk = Path(root) / f
                    arcname = file_on_disk.relative_to(fix_dir)
                    z.write(file_on_disk, arcname)

        logger.info(f"PPTX 命名空间修复：{file_path.name} -> {fixed_path.name} (修复 {fixed_count} 个文件)")
        return fixed_path

    except Exception as e:
        logger.error(f"修复 PPTX 命名空间失败：{e}")
        return file_path
    finally:
        try:
            shutil.rmtree(fix_dir)
        except Exception:
            pass


async def sse_generator(progress_queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """SSE 事件生成器（含心跳机制）"""
    HEARTBEAT_INTERVAL = 3.0
    try:
        while True:
            try:
                event = await asyncio.wait_for(progress_queue.get(), timeout=HEARTBEAT_INTERVAL)
                if event is None:
                    break
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                heartbeat = {"type": "heartbeat", "timestamp": time.time()}
                yield f"data: {json.dumps(heartbeat, ensure_ascii=False)}\n\n"
    except asyncio.CancelledError:
        logger.info("SSE 连接被客户端关闭")
        raise


# ==================== 会话管理端点 ====================

# 内存中的会话存储（简单实现，生产环境应使用数据库）
_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/session/create")
async def create_session(
    ppt_a: UploadFile = File(None, description="PPT A 文件"),
    ppt_b: UploadFile = File(None, description="PPT B 文件"),
):
    """
    创建合并会话

    接收两个 PPT 文件，创建会话 ID，返回会话信息
    """
    if not ppt_a and not ppt_b:
        raise HTTPException(status_code=400, detail="至少需要上传一个文件")

    session_id = uuid.uuid4().hex[:8]
    temp_dir = Path(tempfile.gettempdir()) / "ppt_sessions"
    temp_dir.mkdir(parents=True, exist_ok=True)

    documents = {}

    for ppt_file, key in [(ppt_a, "ppt_a"), (ppt_b, "ppt_b")]:
        if ppt_file:
            content = await ppt_file.read()
            if content:
                temp_path = temp_dir / f"{session_id}_{uuid.uuid4().hex[:8]}_{ppt_file.filename}"
                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(content)

                # 解析 PPT 获取页数
                try:
                    from pptx import Presentation
                    prs = Presentation(temp_path)
                    total_slides = len(prs.slides)
                except Exception:
                    total_slides = 0

                documents[key] = {
                    "source_file": str(temp_path),
                    "total_slides": total_slides,
                    "slides": {}
                }

    # 存储会话
    _sessions[session_id] = {
        "session_id": session_id,
        "documents": documents,
        "created_at": time.time()
    }

    return JSONResponse(content={
        "session_id": session_id,
        "documents": documents
    })


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    获取会话详情
    """
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    return JSONResponse(content=_sessions[session_id])


# ==================== PPT 解析端点 ====================

@router.post("/ppt/parse")
async def parse_ppt(
    file: UploadFile = File(..., description="要解析的 PPTX 文件"),
    extract_enhanced: bool = Form(False, description="是否提取增强元数据"),
    max_image_size: int = Form(512, description="图片最大尺寸"),
    timeout: int = Form(30, description="解析超时时间（秒）"),
    use_cache: bool = Form(True, description="是否启用缓存"),
):
    """
    解析 PPTX 文件，提取每页的内容用于前端预览

    Returns:
        JSON: { pages: [{ index, title, content, shapes, layout }] }
    """
    try:
        start_time = time.time()

        # 内存检查
        memory_usage = _get_memory_usage()
        if memory_usage > _MEMORY_CRITICAL_THRESHOLD:
            raise HTTPException(status_code=503, detail=f"服务器内存紧张 ({memory_usage:.1%})")
        if memory_usage > _MEMORY_WARNING_THRESHOLD:
            extract_enhanced = False

        content_bytes = await file.read()

        if len(content_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")

        file_hash = _compute_file_hash(content_bytes)
        cache_key = f"{file_hash}_{'enhanced' if extract_enhanced else 'basic'}_{max_image_size}"

        if use_cache:
            cached_result = _get_from_cache(cache_key)
            if cached_result:
                return JSONResponse(content={**cached_result, "from_cache": True})

        if not file.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="仅支持 .pptx 格式文件")

        temp_dir = Path(tempfile.gettempdir()) / "ppt_parse"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"{uuid.uuid4().hex}_{file.filename}"

        try:
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(content_bytes)

            temp_path = _fix_invalid_namespaces(temp_path)

            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
            try:
                from pptx.enum.text import MSO_AUTO_SHAPE_TYPE
            except ImportError:
                MSO_AUTO_SHAPE_TYPE = None
            from pptx.dml.color import RGBColor
            import base64
            from io import BytesIO
            from PIL import Image

            prs = Presentation(temp_path)
            pages: List[Dict[str, Any]] = []

            def extract_text_run_style(run):
                """提取文本运行的样式信息"""
                font_info = {}
                if hasattr(run, 'font'):
                    font = run.font
                    if font.name:
                        font_info['name'] = font.name
                    if font.size:
                        font_info['size'] = font.size.pt
                    if font.bold is not None:
                        font_info['bold'] = font.bold
                    if font.italic is not None:
                        font_info['italic'] = font.italic
                    if font.underline is not None:
                        font_info['underline'] = font.underline
                    if font.color and hasattr(font.color, 'rgb') and font.color.rgb:
                        rgb = font.color.rgb
                        font_info['color'] = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                return font_info

            def image_to_base64(image_bytes: bytes, max_size: int = 512) -> str:
                """将图片压缩并转换为 Base64"""
                try:
                    img = Image.open(BytesIO(image_bytes))
                    if img.width > max_size or img.height > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    if img.mode in ('RGBA', 'P', 'LA'):
                        img = img.convert('RGB')
                    output = BytesIO()
                    img.save(output, format='JPEG', quality=75, optimize=True)
                    output.seek(0)
                    return base64.b64encode(output.getvalue()).decode('utf-8')
                except Exception as e:
                    logger.warning(f"图片转 Base64 失败: {e}")
                    return ""

            for slide_idx, slide in enumerate(prs.slides):
                page_data = {
                    "index": slide_idx,
                    "title": "",
                    "content": [],
                    "shapes": [],
                    "has_complex_elements": False,
                    "complex_element_types": []
                }

                enhanced_content = []

                for shape in slide.shapes:
                    shape_info = {"type": "unknown", "name": shape.name}

                    if hasattr(shape, 'shape_type'):
                        try:
                            shape_info["type"] = str(shape.shape_type)
                        except:
                            pass

                    if shape.has_text_frame:
                        for para in shape.text_frame.paragraphs:
                            para_text = ""
                            for run in para.runs:
                                para_text += run.text

                            if para_text.strip():
                                if extract_enhanced:
                                    run_data = {
                                        "type": "text",
                                        "text": para_text,
                                        "font": extract_text_run_style(run) if para.runs else {}
                                    }
                                    enhanced_content.append(run_data)
                                else:
                                    page_data["content"].append(para_text)

                    # 处理图片
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        try:
                            image = shape.image
                            image_bytes = image.blob
                            image_base64 = image_to_base64(image_bytes, max_image_size)
                            if image_base64:
                                page_data["shapes"].append({
                                    "type": "picture",
                                    "base64": f"data:image/jpeg;base64,{image_base64}"
                                })
                                page_data["has_complex_elements"] = True
                                page_data["complex_element_types"].append("picture")
                        except Exception as e:
                            logger.warning(f"提取图片失败: {e}")

                    # 处理表格
                    if shape.has_table:
                        table_data = []
                        for row in shape.table.rows:
                            row_data = []
                            for cell in row.cells:
                                row_data.append(cell.text)
                            table_data.append(row_data)
                        page_data["shapes"].append({
                            "type": "table",
                            "data": table_data
                        })
                        page_data["has_complex_elements"] = True
                        page_data["complex_element_types"].append("table")

                if extract_enhanced and enhanced_content:
                    page_data["content"] = enhanced_content

                # 尝试提取标题
                if slide.shapes.title and slide.shapes.title.text:
                    page_data["title"] = slide.shapes.title.text

                pages.append(page_data)

            result = {"pages": pages, "total_pages": len(pages)}

            if use_cache:
                _add_to_cache(cache_key, result)

            duration = time.time() - start_time
            logger.info(f"PPT 解析完成: {file.filename}, {len(pages)} 页, 耗时 {duration:.2f}s")

            return JSONResponse(content=result)

        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPT 解析失败: {e}")
        logger.error(traceback_module.format_exc())
        raise HTTPException(status_code=500, detail=f"PPT 解析失败: {str(e)}")


# ==================== AI 合并端点 ====================

@router.post('/ppt/ai-merge')
async def ai_merge_ppts(
    file_a: UploadFile = File(..., description='PPT A 文件'),
    file_b: UploadFile = File(..., description='PPT B 文件'),
    merge_type: str = Form('full', description='合并类型'),
    selected_pages_a: str = Form('', description='PPT A 选中页码'),
    selected_pages_b: str = Form('', description='PPT B 选中页码'),
    single_page_action: str = Form('polish', description='单页处理动作'),
    single_page_index: int = Form(0, description='单页处理的页码'),
    source_doc: str = Form('A', description='单页处理的源文档'),
    custom_prompt: str = Form('', description='自定义合并提示语'),
    provider: str = Form('deepseek', description='LLM 服务商'),
    api_key: str = Form(..., description='API Key'),
    temperature: float = Form(0.3, description='温度参数'),
    max_tokens: int = Form(3000, description='最大输出 token'),
):
    """
    AI 合并多个 PPT

    支持三种模式：
    - full: 全量合并
    - single: 单页处理
    - partial: 部分页面合并

    Returns:
        SSE 流式响应，包含处理进度和结果
    """
    progress_queue = asyncio.Queue()

    async def merge_in_background():
        temp_a = None
        temp_b = None
        try:
            logger.info(f'开始 AI 内容融合：type={merge_type}')

            from ..services.ppt_content_parser import parse_pptx_to_structure
            from ..services.content_merger import get_content_merger

            doc_a = {"slides": []}
            doc_b = {"slides": []}

            need_parse_a = merge_type != 'single' or source_doc == 'A'
            need_parse_b = merge_type != 'single' or source_doc == 'B'

            if need_parse_a:
                await progress_queue.put({"stage": "analysis", "progress": 10, "message": "正在解析 PPT A 内容..."})
                content_a = await file_a.read()
                if content_a:
                    temp_dir_a = Path(tempfile.gettempdir()) / 'ppt_ai_merge'
                    temp_dir_a.mkdir(parents=True, exist_ok=True)
                    temp_a = temp_dir_a / f'{uuid.uuid4().hex}_{file_a.filename}'
                    async with aiofiles.open(temp_a, 'wb') as f:
                        await f.write(content_a)
                    doc_a = parse_pptx_to_structure(temp_a)

            if need_parse_b:
                await progress_queue.put({"stage": "analysis", "progress": 25, "message": "正在解析 PPT B 内容..."})
                content_b = await file_b.read()
                if content_b:
                    temp_dir_b = Path(tempfile.gettempdir()) / 'ppt_ai_merge'
                    temp_dir_b.mkdir(parents=True, exist_ok=True)
                    temp_b = temp_dir_b / f'{uuid.uuid4().hex}_{file_b.filename}'
                    async with aiofiles.open(temp_b, 'wb') as f:
                        await f.write(content_b)
                    doc_b = parse_pptx_to_structure(temp_b)

            await progress_queue.put({"stage": "thinking", "progress": 50, "message": "正在调用 AI 生成合并策略..."})

            merger = get_content_merger(provider=provider, api_key=api_key, temperature=temperature, max_tokens=max_tokens)

            if merge_type == 'full':
                plan = merger.merge_full(doc_a, doc_b, custom_prompt)
                result = {
                    'merge_type': 'full',
                    'plan': {
                        'merge_strategy': plan.merge_strategy,
                        'summary': plan.summary,
                        'knowledge_points': plan.knowledge_points,
                        'slide_plan': [{
                            'action': p.action.value,
                            'source': p.source,
                            'slide_index': p.slide_index,
                            'sources': p.sources,
                            'new_content': p.new_content,
                            'instruction': p.instruction,
                            'reason': p.reason
                        } for p in plan.slide_plan]
                    }
                }

            elif merge_type == 'single':
                source_doc_data = doc_a if source_doc == 'A' else doc_b
                slides = source_doc_data.get('slides', [])
                if single_page_index < 0 or single_page_index >= len(slides):
                    raise ValueError(f'页码超出范围：{single_page_index}')

                slide = slides[single_page_index]
                single_result = merger.process_single_page(slide, single_page_action, custom_prompt)

                action_desc = {
                    'polish': '润色',
                    'expand': '扩展',
                    'rewrite': '改写',
                    'extract': '知识点提取'
                }.get(single_page_action, single_page_action)

                result = {
                    'merge_type': 'single',
                    'plan': {
                        'merge_strategy': f'单页{action_desc}操作',
                        'summary': f'对第 {single_page_index + 1} 页执行 {action_desc}操作',
                        'knowledge_points': [],
                        'slide_plan': [{
                            'action': single_result.get('action', single_page_action),
                            'source': source_doc,
                            'slide_index': single_page_index,
                            'sources': None,
                            'new_content': single_result.get('new_content'),
                            'instruction': custom_prompt or f'执行{action_desc}操作',
                            'reason': f'AI{action_desc}处理'
                        }]
                    }
                }

            elif merge_type == 'partial':
                pages_a_idx = [int(p.strip()) for p in selected_pages_a.split(',') if p.strip()] if selected_pages_a else []
                pages_b_idx = [int(p.strip()) for p in selected_pages_b.split(',') if p.strip()] if selected_pages_b else []
                slides_a, slides_b = doc_a.get('slides', []), doc_b.get('slides', [])
                pages_a = [slides_a[i] for i in pages_a_idx if 0 <= i < len(slides_a)]
                pages_b = [slides_b[i] for i in pages_b_idx if 0 <= i < len(slides_b)]
                if not pages_a and not pages_b:
                    raise ValueError('至少需要选择一个页面')
                result = merger.merge_pages(pages_a, pages_b, custom_prompt)
                result['merge_type'] = 'partial'

            else:
                raise ValueError(f'不支持的合并类型：{merge_type}')

            # 验证 JSON 序列化
            serialization_result = test_json_serialization(result, context="ai_merge_result")
            if not serialization_result["success"]:
                raise ValueError(f"JSON 序列化失败: {serialization_result['error']}")

            await progress_queue.put({
                "stage": "complete",
                "progress": 100,
                "message": "AI 内容融合完成！",
                "result": result
            })

        except ValueError as e:
            logger.error(f'参数错误：{e}')
            await progress_queue.put({"stage": "error", "progress": 0, "message": f'参数错误：{str(e)}'})
        except Exception as e:
            logger.error(f'AI 融合失败：{e}')
            logger.error(traceback_module.format_exc())
            await progress_queue.put({"stage": "error", "progress": 0, "message": f'AI 融合失败：{str(e)}'})
        finally:
            for temp_path in [temp_a, temp_b]:
                try:
                    if temp_path and temp_path.exists():
                        temp_path.unlink()
                except:
                    pass
            await progress_queue.put(None)

    task = asyncio.create_task(merge_in_background())
    await asyncio.sleep(0)

    return StreamingResponse(
        sse_generator(progress_queue),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@router.post("/ppt/ai-merge-single")
async def ai_merge_single_page(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PPT 文件"),
    page_index: int = Form(..., description="要处理的页码（0-indexed）"),
    action: str = Form(..., description="操作类型：polish/expand/rewrite/extract"),
    custom_prompt: Optional[str] = Form(None, description="自定义提示语"),
    provider: str = Form("deepseek", description="LLM 服务商"),
    api_key: str = Form(..., description="API Key"),
    temperature: float = Form(0.3, description="温度参数"),
    max_tokens: int = Form(2000, description="最大输出 token"),
):
    """
    单页 AI 处理 + 实时生成 PPT 图片预览

    流程：
    1. 解析原始 PPT 获取页面结构
    2. 调用 LLM 进行 AI 处理
    3. 生成单页 PPTX 文件
    4. 转换为 PNG 预览

    Returns:
        JSON: { success, content, preview_url, image_path, degraded }
    """
    temp_pptx = None
    output_pptx = None

    try:
        logger.info(f"单页处理请求: page={page_index}, action={action}, file={file.filename}")

        # 保存上传文件
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="上传文件为空")

        temp_dir = Path(tempfile.gettempdir()) / 'ppt_ai_merge_single'
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_pptx = temp_dir / f'{uuid.uuid4().hex}_{file.filename}'
        async with aiofiles.open(temp_pptx, 'wb') as f:
            await f.write(content)

        # 解析 PPT
        from ..services.ppt_content_parser import parse_pptx_to_structure

        doc = parse_pptx_to_structure(temp_pptx)
        slides = doc.get("slides", [])

        if page_index < 0 or page_index >= len(slides):
            raise HTTPException(
                status_code=400,
                detail=f"页码超出范围：{page_index}，有效范围 0-{len(slides) - 1}"
            )

        original_slide = slides[page_index]

        # 调用 LLM 处理
        from ..services.content_merger import get_content_merger

        merger = get_content_merger(
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

        result = merger.process_single_page(original_slide, action, custom_prompt)

        # 提取处理后的内容
        new_content = result.get("new_content", {})

        if not new_content:
            new_content = {
                "title": original_slide.get("teaching_content", {}).get("title", ""),
                "main_points": [],
                "additional_content": ""
            }

        # 类型安全处理
        main_points = new_content.get("main_points", [])
        if isinstance(main_points, list):
            safe_points = []
            for p in main_points:
                if isinstance(p, str):
                    safe_points.append(p)
                elif isinstance(p, dict):
                    text = (p.get('text') or p.get('content') or p.get('point') or str(p))
                    safe_points.append(text)
                else:
                    safe_points.append(str(p))
            main_points = safe_points
        else:
            main_points = []

        new_content["main_points"] = main_points

        # 生成单页 PPTX
        output_pptx = temp_dir / f'slide_{page_index}_{action}_{uuid.uuid4().hex}.pptx'
        generate_single_slide_pptx(
            content=new_content,
            output_path=output_pptx,
            slide_index=page_index,
            layout_type="auto"
        )

        # 转换为 PNG
        session_id = uuid.uuid4().hex
        image_output_dir = settings.PUBLIC_DIR / "images" / session_id
        image_output_dir.mkdir(parents=True, exist_ok=True)

        image_result = convert_single_slide_to_image(
            pptx_path=output_pptx,
            output_dir=image_output_dir,
            page_index=0,
            resolution="high"
        )

        # 构建返回结果
        response = {
            "success": True,
            "content": new_content,
            "preview_url": image_result.get("url") if image_result and image_result.get("success") else None,
            "image_path": image_result.get("path") if image_result else None,
            "degraded": image_result.get("degraded", False) if image_result else True,
            "error": image_result.get("error") if image_result and not image_result.get("success") else None
        }

        # 验证 JSON 序列化
        serialization_result = test_json_serialization(response, context="ai_merge_single_response")
        if not serialization_result["success"]:
            raise ValueError(f"JSON 序列化失败: {serialization_result['error']}")

        # 注册后台清理任务
        def cleanup_temp_files():
            import time
            time.sleep(30)
            for temp_path in [temp_pptx, output_pptx]:
                try:
                    if temp_path and temp_path.exists():
                        temp_path.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {temp_path}, error={e}")

        background_tasks.add_task(cleanup_temp_files)

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"单页处理失败: {e}")
        logger.error(traceback_module.format_exc())
        raise HTTPException(status_code=500, detail=f"单页处理失败: {str(e)}")


# ==================== 最终生成端点 ====================

@router.post("/ppt/generate-final")
async def generate_final_ppt(
    session_id: str = Body(..., description="会话 ID"),
    title: str = Body(..., description="最终 PPT 标题"),
    grade: str = Body("6", description="年级"),
    subject: str = Body("general", description="学科"),
    style: str = Body("simple", description="风格"),
    final_selection: Optional[List[str]] = Body(None, description="最终选择的版本ID列表"),
    content_snapshots: Optional[Dict[str, Any]] = Body(None, description="前端附带的内容快照")
):
    """
    基于当前选择的版本生成最终 PPT

    流程：
    1. 获取会话数据
    2. 如果提供了 final_selection，只包含指定的版本
    3. 否则收集所有活跃页面的当前版本
    4. 生成统一样式的最终 PPT

    Returns:
        JSON: { success, download_url, file_name, total_slides }
    """
    from ..services.ppt_generator import generate_ppt_from_versions
    from io import BytesIO
    import re

    logger.info(f"生成最终 PPT: session_id={session_id}, title={title}, final_selection={final_selection}")

    try:
        merged_slides = []

        # 如果有 content_snapshots，直接使用
        if content_snapshots:
            for version_id, snapshot in content_snapshots.items():
                if snapshot:
                    merged_slides.append({
                        "source_pptx": None,
                        "slide_index": 0,
                        "content_snapshot": snapshot,
                        "version": "v1"
                    })

        # 如果没有快照，从会话中获取原始文件
        if not merged_slides and session_id in _sessions:
            session_data = _sessions[session_id]
            documents = session_data.get("documents", {})

            from ..services.ppt_content_parser import parse_pptx_to_structure

            # 解析 final_selection 格式: "ppt_a_0_v1" -> (ppt_a, 0)
            for version_id in (final_selection or []):
                match = re.match(r'^(ppt_[ab])_(\d+)_v\d+$', version_id)
                if match:
                    doc_key = match.group(1)  # ppt_a or ppt_b
                    slide_idx = int(match.group(2))

                    doc_data = documents.get(doc_key, {})
                    source_file = doc_data.get("source_file")

                    if source_file and Path(source_file).exists():
                        doc = parse_pptx_to_structure(Path(source_file))
                        slides = doc.get("slides", [])

                        if slide_idx < len(slides):
                            slide = slides[slide_idx]
                            tc = slide.get("teaching_content", {})
                            merged_slides.append({
                                "source_pptx": source_file,
                                "slide_index": slide_idx,
                                "content_snapshot": {
                                    "title": tc.get("title", ""),
                                    "main_points": tc.get("main_points", []),
                                    "additional_content": tc.get("additional_content", ""),
                                    "elements": []
                                },
                                "version": "v1"
                            })

        if not merged_slides:
            raise HTTPException(status_code=400, detail="没有可生成的页面，请确保已上传文件并选择了幻灯片")

        logger.info(f"收集到 {len(merged_slides)} 个页面用于生成最终 PPT")

        # 生成最终 PPT
        output_path = generate_ppt_from_versions(
            merged_slides,
            title=title,
            grade=grade,
            subject=subject,
            style=style
        )

        file_name = output_path.name

        logger.info(f"最终 PPT 生成成功：{file_name}")

        response_data = {
            "success": True,
            "download_url": f"/uploads/generated/{file_name}",
            "file_name": file_name,
            "total_slides": len(merged_slides)
        }

        return JSONResponse(content=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成最终 PPT 失败：{e}")
        raise HTTPException(status_code=500, detail=f"生成最终 PPT 失败：{str(e)}")