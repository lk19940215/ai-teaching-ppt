from fastapi import APIRouter, HTTPException, Body, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pathlib import Path
from typing import Optional, AsyncGenerator, List, Dict, Any
import logging
import uuid
import aiofiles
import asyncio
import json
import io
import tempfile

from ..services.ppt_generator import get_ppt_generator
from ..config import settings

router = APIRouter(prefix=settings.API_V1_STR, tags=["ppt"])

logger = logging.getLogger(__name__)

@router.post("/ppt/generate")
async def generate_ppt(
    content: dict = Body(..., embed=True),
    grade: str = Body("6", embed=True),
    subject: str = Body("general", embed=True),
    style: str = Body("simple", embed=True),
    file_name: Optional[str] = Body(None, embed=True)
):
    """
    生成 PPT 文件
    Args:
        content: PPT 内容数据
        grade: 年级
        subject: 学科
        style: PPT 风格
        file_name: 文件名（可选）
    Returns:
        生成的 PPT 文件下载链接
    """
    try:
        # 生成文件名
        if not file_name:
            file_name = f"{content.get('title', '教学 PPT')}_{uuid.uuid4().hex[:8]}.pptx"

        # 确保 .pptx 扩展名
        if not file_name.endswith(".pptx"):
            file_name += ".pptx"

        # 生成文件路径
        output_path = settings.UPLOAD_DIR / "generated" / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 生成 PPT
        generator = get_ppt_generator()
        generator.generate(content, output_path, grade, style, subject)

        return JSONResponse(content={
            "success": True,
            "message": "PPT 生成成功",
            "download_url": f"/uploads/generated/{file_name}",
            "file_name": file_name
        })

    except Exception as e:
        logger.error(f"PPT 生成失败：{e}")
        raise HTTPException(status_code=500, detail=f"PPT 生成失败：{str(e)}")


@router.get("/ppt/download/{file_name}")
async def download_ppt(file_name: str):
    """
    下载 PPT 文件
    Args:
        file_name: 文件名
    Returns:
        PPT 文件下载
    """
    file_path = settings.UPLOAD_DIR / "generated" / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=file_name
    )


@router.post("/ppt/generate-full")
async def generate_full_ppt(
    text_content: str = Body(..., embed=True),
    grade: str = Body("6", embed=True),
    subject: str = Body("math", embed=True),
    slide_count: int = Body(15, embed=True),
    chapter: Optional[str] = Body(None, embed=True),
    provider: str = Body("deepseek", embed=True),
    api_key: str = Body(..., embed=True),
    style: str = Body("simple", embed=True),
    session_id: Optional[str] = Body(None, embed=True),
    temperature: Optional[float] = Body(None, embed=True),
    max_output_tokens: Optional[int] = Body(None, embed=True),
    difficulty_level: str = Body("unified", embed=True),
):
    """
    完整生成 PPT（内容生成 + 文件生成）
    Args:
        text_content: 教学文本内容
        grade: 年级
        subject: 学科
        slide_count: 幻灯片数量
        chapter: 章节名称
        provider: LLM 服务商
        api_key: API Key
        style: PPT 风格
        temperature: 温度参数（可选，从前端传递）
        max_output_tokens: 最大输出 token 数（可选，从前端传递）
        difficulty_level: 教学层次（unified/basic/intermediate/advanced）
    Returns:
        生成结果和下载链接
    """
    try:
        # 步骤 1: 调用 LLM 生成内容
        from ..services.llm import get_llm_service
        from ..services.content_generator import get_content_generator

        # 使用前端传递的参数，或使用默认值
        llm_temperature = temperature if temperature is not None else 0.7
        llm_max_tokens = max_output_tokens if max_output_tokens is not None else 4000

        llm_service = get_llm_service(
            provider=provider,
            api_key=api_key,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )

        generator = get_content_generator(llm_service)

        # 英语学科使用专门的内容生成器
        if subject == "english":
            ppt_content = generator.generate_for_english(
                content=text_content,
                grade=grade,
                slide_count=slide_count,
                chapter=chapter,
                difficulty_level=difficulty_level
            )
        else:
            ppt_content = generator.generate(
                content=text_content,
                grade=grade,
                subject=subject,
                slide_count=slide_count,
                chapter=chapter,
                difficulty_level=difficulty_level
            )

        # 步骤 2: 生成 PPT 文件
        ppt_generator = get_ppt_generator()
        file_name = f"{ppt_content.get('title', '教学 PPT')}_{uuid.uuid4().hex[:8]}.pptx"
        output_path = settings.UPLOAD_DIR / "generated" / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ppt_generator.generate(ppt_content, output_path, grade, style, subject)

        # 保存历史记录（如果提供了 session_id）
        history_record = None
        if session_id:
            from ..models.database import get_db_session
            from ..models.history_crud import add_generation_record

            db = get_db_session()
            try:
                history_record = add_generation_record(
                    db=db,
                    session_id=session_id,
                    title=ppt_content.get('title', '教学 PPT'),
                    grade=grade,
                    subject=subject,
                    style=style,
                    file_name=file_name,
                    file_path=str(output_path),
                    content_text={"text": text_content},
                    slide_count=slide_count,
                    chapter=chapter,
                    ppt_content=ppt_content,
                )
            finally:
                db.close()

        response_data = {
            "success": True,
            "message": "PPT 生成成功",
            "content": ppt_content,
            "download_url": f"/uploads/generated/{file_name}",
            "file_name": file_name
        }
        if history_record:
            response_data["history_id"] = history_record.id

        return JSONResponse(content=response_data)

    except ValueError as e:
        logger.error(f"参数错误：{e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        logger.error(f"生成超时：{e}")
        raise HTTPException(status_code=408, detail="生成超时，请稍后重试")
    except Exception as e:
        logger.error(f"完整 PPT 生成失败：{e}")
        raise HTTPException(status_code=500, detail=f"PPT 生成失败：{str(e)}")


async def sse_generator(progress_queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """SSE 事件生成器"""
    try:
        while True:
            event = await progress_queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except asyncio.CancelledError:
        logger.info("SSE 连接被客户端关闭")
        raise


@router.post("/ppt/generate-stream")
async def generate_full_ppt_stream(
    text_content: str = Body(..., embed=True),
    grade: str = Body("6", embed=True),
    subject: str = Body("math", embed=True),
    slide_count: int = Body(15, embed=True),
    chapter: Optional[str] = Body(None, embed=True),
    provider: str = Body("deepseek", embed=True),
    api_key: str = Body(..., embed=True),
    style: str = Body("simple", embed=True),
    session_id: Optional[str] = Body(None, embed=True),
    temperature: Optional[float] = Body(None, embed=True),
    max_output_tokens: Optional[int] = Body(None, embed=True),
    difficulty_level: str = Body("unified", embed=True),
):
    """
    完整生成 PPT（SSE 流式响应）
    Args:
        text_content: 教学文本内容
        grade: 年级
        subject: 学科
        slide_count: 幻灯片数量
        chapter: 章节名称
        provider: LLM 服务商
        api_key: API Key
        style: PPT 风格
        temperature: 温度参数（可选，从前端传递）
        max_output_tokens: 最大输出 token 数（可选，从前端传递）
        difficulty_level: 教学层次（unified/basic/intermediate/advanced）
    Returns:
        SSE 流式响应，包含进度事件和最终结果
    """
    progress_queue: asyncio.Queue = asyncio.Queue()

    async def generate_in_background():
        """后台执行生成任务"""
        logger.info("后台生成任务启动")
        try:
            # 阶段 1: 分析内容 (10%)
            logger.info("发送第一个 SSE 事件：analyzing_content 10%")
            await progress_queue.put({
                "stage": "analyzing_content",
                "progress": 10,
                "message": "正在分析教材内容..."
            })

            # 步骤 1: 调用 LLM 生成内容
            from ..services.llm import get_llm_service
            from ..services.content_generator import get_content_generator

            llm_temperature = temperature if temperature is not None else 0.7
            llm_max_tokens = max_output_tokens if max_output_tokens is not None else 4000

            # 注意：base_url 和 model 参数不传递，让 LLMService 根据 provider 使用默认值
            # 各服务商默认值已在 llm.py 中定义：
            # - DeepSeek: https://api.deepseek.com, deepseek-chat
            # - OpenAI: https://api.openai.com/v1, gpt-4
            # - Claude: https://api.anthropic.com/v1, claude-3-opus-20240229
            # - GLM: https://open.bigmodel.cn/api/paas/v4, glm-4
            llm_service = get_llm_service(
                provider=provider,
                api_key=api_key,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens
            )

            generator = get_content_generator(llm_service)

            # 阶段 2: 生成大纲 (30%)
            await progress_queue.put({
                "stage": "generating_outline",
                "progress": 30,
                "message": "正在调用 AI 生成 PPT 大纲..."
            })

            # 英语学科使用专门的内容生成器
            if subject == "english":
                ppt_content = generator.generate_for_english(
                    content=text_content,
                    grade=grade,
                    slide_count=slide_count,
                    chapter=chapter,
                    difficulty_level=difficulty_level
                )
            else:
                ppt_content = generator.generate(
                    content=text_content,
                    grade=grade,
                    subject=subject,
                    slide_count=slide_count,
                    chapter=chapter,
                    difficulty_level=difficulty_level
                )

            # 阶段 3: 构建幻灯片 (60%)
            await progress_queue.put({
                "stage": "building_slides",
                "progress": 60,
                "message": "正在构建幻灯片页面..."
            })

            # 步骤 2: 生成 PPT 文件
            ppt_generator = get_ppt_generator()
            file_name = f"{ppt_content.get('title', '教学 PPT')}_{uuid.uuid4().hex[:8]}.pptx"
            output_path = settings.UPLOAD_DIR / "generated" / file_name
            output_path.parent.mkdir(parents=True, exist_ok=True)

            ppt_generator.generate(ppt_content, output_path, grade, style, subject)

            # 阶段 4: 添加动画效果 (85%)
            await progress_queue.put({
                "stage": "adding_animations",
                "progress": 85,
                "message": "正在添加动画效果..."
            })

            # 保存历史记录（如果提供了 session_id）
            history_record = None
            if session_id:
                from ..models.database import get_db_session
                from ..models.history_crud import add_generation_record

                db = get_db_session()
                try:
                    history_record = add_generation_record(
                        db=db,
                        session_id=session_id,
                        title=ppt_content.get('title', '教学 PPT'),
                        grade=grade,
                        subject=subject,
                        style=style,
                        file_name=file_name,
                        file_path=str(output_path),
                        content_text={"text": text_content},
                        slide_count=slide_count,
                        chapter=chapter,
                        ppt_content=ppt_content,
                    )
                finally:
                    db.close()

            response_data = {
                "success": True,
                "message": "PPT 生成成功",
                "content": ppt_content,
                "download_url": f"/uploads/generated/{file_name}",
                "file_name": file_name
            }
            if history_record:
                response_data["history_id"] = history_record.id

            # 阶段 5: 完成 (100%)
            await progress_queue.put({
                "stage": "complete",
                "progress": 100,
                "message": "生成完成！",
                "result": response_data
            })

        except ValueError as e:
            logger.error(f"参数错误：{e}")
            await progress_queue.put({
                "stage": "error",
                "progress": 0,
                "message": f"参数错误：{str(e)}"
            })
        except TimeoutError as e:
            logger.error(f"生成超时：{e}")
            await progress_queue.put({
                "stage": "error",
                "progress": 0,
                "message": "生成超时，请稍后重试"
            })
        except Exception as e:
            logger.error(f"完整 PPT 生成失败：{e}")
            await progress_queue.put({
                "stage": "error",
                "progress": 0,
                "message": f"PPT 生成失败：{str(e)}"
            })
        finally:
            # 结束 SSE 流
            await progress_queue.put(None)

    # 启动后台任务
    task = asyncio.create_task(generate_in_background())

    # 让出控制权给事件循环，确保后台任务立即开始执行
    # 这样第一个 SSE 事件（analyzing_content 10%）会在返回响应前被放入队列
    await asyncio.sleep(0)

    # 返回 SSE 流
    return StreamingResponse(
        sse_generator(progress_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/ppt/generate-stream")
async def generate_full_ppt_stream_get(
    text_content: str,
    grade: str = "6",
    subject: str = "math",
    slide_count: int = 15,
    chapter: Optional[str] = None,
    provider: str = "deepseek",
    api_key: str = "",
    style: str = "simple",
    session_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None,
    difficulty_level: str = "unified",
):
    """
    完整生成 PPT（SSE 流式响应 - GET 版本，用于 EventSource）
    """
    logger.info(f"收到 SSE 生成请求：text_content={text_content[:50]}..., grade={grade}, subject={subject}")
    progress_queue: asyncio.Queue = asyncio.Queue()

    async def generate_in_background():
        """后台执行生成任务"""
        logger.info("后台生成任务启动")
        try:
            # 阶段 1: 分析内容 (10%)
            logger.info("发送第一个 SSE 事件：analyzing_content 10%")
            await progress_queue.put({
                "stage": "analyzing_content",
                "progress": 10,
                "message": "正在分析教材内容..."
            })

            # 步骤 1: 调用 LLM 生成内容
            from ..services.llm import get_llm_service
            from ..services.content_generator import get_content_generator

            llm_temperature = temperature if temperature is not None else 0.7
            llm_max_tokens = max_output_tokens if max_output_tokens is not None else 4000

            # 注意：base_url 和 model 参数不传递，让 LLMService 根据 provider 使用默认值
            # 各服务商默认值已在 llm.py 中定义：
            # - DeepSeek: https://api.deepseek.com, deepseek-chat
            # - OpenAI: https://api.openai.com/v1, gpt-4
            # - Claude: https://api.anthropic.com/v1, claude-3-opus-20240229
            # - GLM: https://open.bigmodel.cn/api/paas/v4, glm-4
            llm_service = get_llm_service(
                provider=provider,
                api_key=api_key,
                temperature=llm_temperature,
                max_tokens=llm_max_tokens
            )

            generator = get_content_generator(llm_service)

            # 阶段 2: 生成大纲 (30%)
            await progress_queue.put({
                "stage": "generating_outline",
                "progress": 30,
                "message": "正在调用 AI 生成 PPT 大纲..."
            })

            # 英语学科使用专门的内容生成器
            if subject == "english":
                ppt_content = generator.generate_for_english(
                    content=text_content,
                    grade=grade,
                    slide_count=slide_count,
                    chapter=chapter,
                    difficulty_level=difficulty_level
                )
            else:
                ppt_content = generator.generate(
                    content=text_content,
                    grade=grade,
                    subject=subject,
                    slide_count=slide_count,
                    chapter=chapter,
                    difficulty_level=difficulty_level
                )

            # 阶段 3: 构建幻灯片 (60%)
            await progress_queue.put({
                "stage": "building_slides",
                "progress": 60,
                "message": "正在构建幻灯片页面..."
            })

            # 步骤 2: 生成 PPT 文件
            ppt_generator = get_ppt_generator()
            file_name = f"{ppt_content.get('title', '教学 PPT')}_{uuid.uuid4().hex[:8]}.pptx"
            output_path = settings.UPLOAD_DIR / "generated" / file_name
            output_path.parent.mkdir(parents=True, exist_ok=True)

            ppt_generator.generate(ppt_content, output_path, grade, style, subject)

            # 阶段 4: 添加动画效果 (85%)
            await progress_queue.put({
                "stage": "adding_animations",
                "progress": 85,
                "message": "正在添加动画效果..."
            })

            # 保存历史记录（如果提供了 session_id）
            history_record = None
            if session_id:
                from ..models.database import get_db_session
                from ..models.history_crud import add_generation_record

                db = get_db_session()
                try:
                    history_record = add_generation_record(
                        db=db,
                        session_id=session_id,
                        title=ppt_content.get('title', '教学 PPT'),
                        grade=grade,
                        subject=subject,
                        style=style,
                        file_name=file_name,
                        file_path=str(output_path),
                        content_text={"text": text_content},
                        slide_count=slide_count,
                        chapter=chapter,
                        ppt_content=ppt_content,
                    )
                finally:
                    db.close()

            response_data = {
                "success": True,
                "message": "PPT 生成成功",
                "content": ppt_content,
                "download_url": f"/uploads/generated/{file_name}",
                "file_name": file_name
            }
            if history_record:
                response_data["history_id"] = history_record.id

            # 阶段 5: 完成 (100%)
            await progress_queue.put({
                "stage": "complete",
                "progress": 100,
                "message": "生成完成！",
                "result": response_data
            })

        except ValueError as e:
            logger.error(f"参数错误：{e}")
            await progress_queue.put({
                "stage": "error",
                "progress": 0,
                "message": f"参数错误：{str(e)}"
            })
        except TimeoutError as e:
            logger.error(f"生成超时：{e}")
            await progress_queue.put({
                "stage": "error",
                "progress": 0,
                "message": "生成超时，请稍后重试"
            })
        except Exception as e:
            logger.error(f"完整 PPT 生成失败：{e}")
            await progress_queue.put({
                "stage": "error",
                "progress": 0,
                "message": f"PPT 生成失败：{str(e)}"
            })
        finally:
            # 结束 SSE 流
            await progress_queue.put(None)

    # 启动后台任务
    task = asyncio.create_task(generate_in_background())

    # 让出控制权给事件循环，确保后台任务立即开始执行
    # 这样第一个 SSE 事件（analyzing_content 10%）会在返回响应前被放入队列
    await asyncio.sleep(0)

    # 返回 SSE 流
    return StreamingResponse(
        sse_generator(progress_queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/ppt/merge")
async def merge_ppts(
    files: list[UploadFile] = File(..., description="要合并的多个 PPT 文件"),
    title: str = Form("合并课件", description="合并后课件的标题"),
):
    """
    合并多个 PPT 文件为一个新课件
    Args:
        files: 要合并的 PPTX 文件列表（至少 2 个）
        title: 合并后课件的标题
    Returns:
        合并后的 PPT 文件下载链接
    """
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="至少需要上传 2 个 PPT 文件")

        if len(files) > 10:
            raise HTTPException(status_code=400, detail="最多支持合并 10 个 PPT 文件")

        # 验证文件类型并保存临时文件
        from pathlib import Path
        import tempfile

        temp_dir = Path(tempfile.gettempdir()) / "ppt_merge"
        temp_dir.mkdir(parents=True, exist_ok=True)

        ppt_paths = []
        try:
            for file in files:
                if not file.filename.lower().endswith(".pptx"):
                    raise HTTPException(
                        status_code=400,
                        detail=f"不支持的文件格式：{file.filename}，仅支持 .pptx 格式"
                    )

                # 保存临时文件
                temp_path = temp_dir / f"{uuid.uuid4().hex}_{file.filename}"
                async with aiofiles.open(temp_path, "wb") as f:
                    content = await file.read()
                    await f.write(content)
                ppt_paths.append(temp_path)

            # 生成输出文件名
            output_file_name = f"merged_{uuid.uuid4().hex[:8]}.pptx"
            output_path = settings.UPLOAD_DIR / "generated" / output_file_name

            # 调用合并服务
            from ..services.ppt_generator import get_ppt_generator
            generator = get_ppt_generator()
            generator.merge_ppts(ppt_paths, output_path, title)

            return JSONResponse(content={
                "success": True,
                "message": f"成功合并 {len(files)} 个 PPT 文件",
                "download_url": f"/uploads/generated/{output_file_name}",
                "file_name": output_file_name,
                "merged_count": len(files)
            })

        finally:
            # 清理临时文件
            for temp_path in ppt_paths:
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败：{temp_path}, {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPT 合并失败：{e}")
        raise HTTPException(status_code=500, detail=f"PPT 合并失败：{str(e)}")


@router.post("/ppt/parse")
async def parse_ppt(
    file: UploadFile = File(..., description="要解析的 PPTX 文件"),
):
    """
    解析 PPTX 文件，提取每页的内容用于前端预览
    Args:
        file: PPTX 文件
    Returns:
        JSON 格式：{ pages: [{ index, title, content, shapes }] }
    """
    try:
        # 验证文件类型
        if not file.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="仅支持 .pptx 格式文件")

        # 保存到临时文件
        temp_dir = Path(tempfile.gettempdir()) / "ppt_parse"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"{uuid.uuid4().hex}_{file.filename}"

        try:
            async with aiofiles.open(temp_path, "wb") as f:
                content = await file.read()
                await f.write(content)

            # 解析 PPTX
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE

            prs = Presentation(temp_path)
            pages: List[Dict[str, Any]] = []

            for slide_idx, slide in enumerate(prs.slides):
                page_data: Dict[str, Any] = {
                    "index": slide_idx + 1,  # 从 1 开始计数
                    "title": "",
                    "content": [],
                    "shapes": []
                }

                # 提取形状信息
                for shape in slide.shapes:
                    shape_info: Dict[str, Any] = {
                        "type": str(shape.shape_type) if hasattr(shape, "shape_type") else "unknown",
                        "name": shape.name if hasattr(shape, "name") else ""
                    }

                    # 提取文本框内容
                    if hasattr(shape, "has_text_frame") and shape.has_text_frame:
                        text_content = ""
                        for paragraph in shape.text_frame.paragraphs:
                            para_text = paragraph.text.strip()
                            if para_text:
                                text_content += para_text + "\n"

                        if text_content.strip():
                            # 第一个文本框通常作为标题（通过形状名称判断）
                            if not page_data["title"] and ("Title" in shape_info["name"] or shape_info["type"].startswith("PLACEHOLDER")):
                                page_data["title"] = text_content.strip()
                            else:
                                page_data["content"].append(text_content.strip())

                    # 记录形状类型
                    page_data["shapes"].append(shape_info)

                pages.append(page_data)

            return JSONResponse(content={
                "success": True,
                "file_name": file.filename,
                "total_pages": len(pages),
                "pages": pages
            })

        finally:
            # 清理临时文件
            try:
                if temp_path.exists():
                    temp_path.unlink()
            except Exception as e:
                logger.warning(f"清理临时文件失败：{temp_path}, {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PPT 解析失败：{e}")
        raise HTTPException(status_code=500, detail=f"PPT 解析失败：{str(e)}")


@router.post("/ppt/smart-merge")
async def smart_merge_ppt(
    file_a: UploadFile = File(..., description="PPT 文件 A"),
    file_b: UploadFile = File(..., description="PPT 文件 B"),
    page_prompts: str = Form("{}", description="页面级提示语 JSON"),
    global_prompt: str = Form("", description="全局合并提示语"),
    api_key: str = Form(..., description="LLM API Key"),
    provider: str = Form("deepseek", description="LLM 服务商"),
    title: str = Form("智能合并课件", description="合并后课件标题"),
    temperature: Optional[float] = Form(0.3, description="LLM 温度参数"),
    max_tokens: Optional[int] = Form(2000, description="LLM 最大输出 token 数"),
):
    """
    智能合并两个 PPT 文件：根据页面级提示语调用 LLM 生成合并策略

    Args:
        file_a: PPT 文件 A
        file_b: PPT 文件 B
        page_prompts: 页面级提示语 JSON，格式：{"a_pages": {"1": "提示语 1", "2": "提示语 2"}, "b_pages": {"1": "提示语 1"}}
        global_prompt: 全局合并提示语，如"将 A 的概念讲解与 B 的例题结合"
        api_key: LLM API Key
        provider: LLM 服务商（deepseek/openai/claude/glm）
        title: 合并后课件标题
        temperature: LLM 温度参数
        max_tokens: LLM 最大输出 token 数

    Returns:
        合并后的 PPT 文件下载链接
    """
    try:
        # 验证文件类型
        if not file_a.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="文件 A 格式错误，仅支持 .pptx 格式")
        if not file_b.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="文件 B 格式错误，仅支持 .pptx 格式")

        # 解析页面提示语
        try:
            page_prompts_dict = json.loads(page_prompts) if page_prompts else {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="页面提示语 JSON 格式错误")

        # 保存临时文件
        temp_dir = Path(tempfile.gettempdir()) / "ppt_smart_merge"
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_a = temp_dir / f"{uuid.uuid4().hex}_{file_a.filename}"
        temp_b = temp_dir / f"{uuid.uuid4().hex}_{file_b.filename}"

        ppt_paths = []
        try:
            # 保存文件 A
            async with aiofiles.open(temp_a, "wb") as f:
                content = await file_a.read()
                await f.write(content)
            ppt_paths.append(temp_a)

            # 保存文件 B
            async with aiofiles.open(temp_b, "wb") as f:
                content = await file_b.read()
                await f.write(content)
            ppt_paths.append(temp_b)

            # 步骤 1: 解析两个 PPT 的内容
            from pptx import Presentation

            prs_a = Presentation(temp_a)
            prs_b = Presentation(temp_b)

            # 提取 A 的内容摘要
            a_pages_info = []
            for i, slide in enumerate(prs_a.slides):
                page_info = {"index": i + 1, "title": "", "content_summary": ""}
                for shape in slide.shapes:
                    if shape.has_text_frame and shape.text.strip():
                        if not page_info["title"]:
                            page_info["title"] = shape.text.strip()[:50]
                        else:
                            page_info["content_summary"] += shape.text.strip()[:100] + "..."
                            break
                a_pages_info.append(page_info)

            # 提取 B 的内容摘要
            b_pages_info = []
            for i, slide in enumerate(prs_b.slides):
                page_info = {"index": i + 1, "title": "", "content_summary": ""}
                for shape in slide.shapes:
                    if shape.has_text_frame and shape.text.strip():
                        if not page_info["title"]:
                            page_info["title"] = shape.text.strip()[:50]
                        else:
                            page_info["content_summary"] += shape.text.strip()[:100] + "..."
                            break
                b_pages_info.append(page_info)

            # 步骤 2: 构建 LLM 提示词，生成合并策略
            from ..services.llm import get_llm_service, LLMProvider

            # 构建页面提示语字符串
            a_prompts_str = ""
            for page_num, prompt in page_prompts_dict.get("a_pages", {}).items():
                page_data = a_pages_info[int(page_num) - 1] if int(page_num) <= len(a_pages_info) else {}
                a_prompts_str += f"- A 第{page_num}页 [{page_data.get('title', '无标题')}]: {prompt}\n"

            b_prompts_str = ""
            for page_num, prompt in page_prompts_dict.get("b_pages", {}).items():
                page_data = b_pages_info[int(page_num) - 1] if int(page_num) <= len(b_pages_info) else {}
                b_prompts_str += f"- B 第{page_num}页 [{page_data.get('title', '无标题')}]: {prompt}\n"

            # 系统提示词
            system_prompt = """你是一个专业的 PPT 合并助手。请根据用户提供的页面级提示语，生成 PPT 合并策略。

请严格按照以下 JSON 格式输出：
{
  "slides_to_merge": [
    {
      "from_a": [1, 2],      // 从 A 中选取的页码
      "from_b": [3, 4],      // 从 B 中选取的页码
      "action": "combine",   // 合并方式：combine(合并到一页)/append_a(追加 A)/append_b(追加 B)
      "instruction": "保留标题，正文合并"  // 合并指令
    }
  ],
  "slides_to_skip_a": [5, 6],  // 从 A 中跳过的页码
  "slides_to_skip_b": [7, 8],  // 从 B 中跳过的页码
  "global_adjustments": "统一字体和颜色"  // 全局调整说明
}

要求：
1. 所有页码从 1 开始计数
2. 封面页（第 1 页）通常不需要合并，会自动跳过
3. action 只能是 combine/append_a/append_b
4. 未被明确处理的页面默认追加到末尾"""

            # 用户提示词
            user_prompt = f"""PPT A 内容（共{len(a_pages_info)}页）：
{json.dumps(a_pages_info, ensure_ascii=False, indent=2)}

PPT B 内容（共{len(b_pages_info)}页）：
{json.dumps(b_pages_info, ensure_ascii=False, indent=2)}

页面级提示语：
A 页面：
{a_prompts_str if a_prompts_str else "无"}

B 页面：
{b_prompts_str if b_prompts_str else "无"}

全局提示语：
{global_prompt if global_prompt else "无"}

请根据以上信息，生成合并策略 JSON。"""

            # 调用 LLM
            llm_service = get_llm_service(
                provider=provider,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )

            strategy_response = llm_service.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])

            # 解析 LLM 返回的策略
            try:
                merge_strategy = json.loads(strategy_response)
            except json.JSONDecodeError as e:
                logger.error(f"LLM 返回的策略 JSON 解析失败：{strategy_response[:500]}")
                # 尝试修复 JSON
                from ..services.llm import LLMService
                fix_service = LLMService()
                fixed_json = fix_service._fix_json(strategy_response)
                try:
                    merge_strategy = json.loads(fixed_json)
                except:
                    raise HTTPException(status_code=500, detail=f"LLM 生成的策略 JSON 格式错误：{e}")

            logger.info(f"LLM 生成的合并策略：{json.dumps(merge_strategy, ensure_ascii=False)}")

            # 步骤 3: 执行智能合并
            output_file_name = f"smart_merged_{uuid.uuid4().hex[:8]}.pptx"
            output_path = settings.UPLOAD_DIR / "generated" / output_file_name

            from ..services.ppt_generator import get_ppt_generator
            generator = get_ppt_generator()
            generator.smart_merge_ppts(
                ppt_a_path=temp_a,
                ppt_b_path=temp_b,
                output_path=output_path,
                merge_strategy=merge_strategy,
                title=title
            )

            return JSONResponse(content={
                "success": True,
                "message": "智能合并成功",
                "download_url": f"/uploads/generated/{output_file_name}",
                "file_name": output_file_name,
                "strategy": merge_strategy,
                "merged_from": [file_a.filename, file_b.filename]
            })

        finally:
            # 清理临时文件
            for temp_path in ppt_paths:
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except Exception as e:
                    logger.warning(f"清理临时文件失败：{temp_path}, {e}")

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"参数错误：{e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        logger.error(f"LLM 调用超时：{e}")
        raise HTTPException(status_code=408, detail="LLM 调用超时，请稍后重试")
    except Exception as e:
        logger.error(f"智能合并失败：{e}")
        raise HTTPException(status_code=500, detail=f"智能合并失败：{str(e)}")

