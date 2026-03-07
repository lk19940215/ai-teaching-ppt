"""
PPT 生成历史记录 API
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import uuid
import logging

from ..models.database import get_db, get_db_session, init_db
from ..models.history_crud import (
    add_generation_record,
    get_history_by_session,
    get_history_record,
    delete_history_record,
    search_history,
    get_history_count,
    regenerate_from_history,
)
from ..services.ppt_generator import get_ppt_generator
from ..services.llm import get_llm_service
from ..services.content_generator import get_content_generator
from ..config import settings

router = APIRouter(prefix=settings.API_V1_STR, tags=["history"])

logger = logging.getLogger(__name__)


# 确保数据库初始化
init_db()


@router.get("/history")
async def list_history(
    session_id: str = Query(..., description="用户 session ID"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db = Depends(get_db),
):
    """获取生成历史记录列表"""
    try:
        records = get_history_by_session(db, session_id, limit, offset)
        total = get_history_count(db, session_id)
        return {
            "success": True,
            "data": [record.to_dict() for record in records],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"获取历史记录失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取历史记录失败：{str(e)}")


@router.get("/history/search")
async def search_history_api(
    session_id: str = Query(..., description="用户 session ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    grade: Optional[str] = Query(None, description="年级筛选"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db = Depends(get_db),
):
    """搜索历史记录"""
    try:
        records = search_history(db, session_id, keyword, grade, subject, limit, offset)
        total = len(records)
        return {
            "success": True,
            "data": [record.to_dict() for record in records],
            "total": total,
        }
    except Exception as e:
        logger.error(f"搜索历史记录失败：{e}")
        raise HTTPException(status_code=500, detail=f"搜索失败：{str(e)}")


@router.get("/history/{record_id}")
async def get_history_detail(
    record_id: int,
    session_id: str = Query(..., description="用户 session ID"),
    db = Depends(get_db),
):
    """获取单条历史记录详情"""
    record = get_history_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 验证是否属于当前用户
    if record.session_id != session_id:
        raise HTTPException(status_code=403, detail="无权访问该记录")

    return {
        "success": True,
        "data": record.to_dict(),
    }


@router.delete("/history/{record_id}")
async def delete_history(
    record_id: int,
    session_id: str = Query(..., description="用户 session ID"),
    db = Depends(get_db),
):
    """删除历史记录"""
    success = delete_history_record(db, record_id, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="记录不存在或无权删除")

    return {
        "success": True,
        "message": "记录已删除",
    }


@router.post("/history/{record_id}/regenerate")
async def regenerate_from_history_api(
    record_id: int,
    session_id: str = Query(..., description="用户 session ID"),
    api_key: str = Body(..., embed=True, description="LLM API Key"),
    provider: str = Body("deepseek", embed=True, description="LLM 服务商"),
    temperature: Optional[float] = Body(None, embed=True, description="温度参数"),
    max_output_tokens: Optional[int] = Body(None, embed=True, description="最大输出 token 数"),
    db = Depends(get_db),
):
    """基于历史记录重新生成 PPT"""
    try:
        # 获取历史记录
        record = get_history_record(db, record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        # 验证是否属于当前用户
        if record.session_id != session_id:
            raise HTTPException(status_code=403, detail="无权访问该记录")

        # 获取原始内容
        if not record.content_text:
            raise HTTPException(status_code=400, detail="历史记录中未找到原始内容")

        content_text = record.content_text.get("text", "") if isinstance(record.content_text, dict) else str(record.content_text)

        # 调用 LLM 重新生成内容
        llm_temperature = temperature if temperature is not None else 0.7
        llm_max_tokens = max_output_tokens if max_output_tokens is not None else 4000

        llm_service = get_llm_service(
            provider=provider,
            api_key=api_key,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )

        content_generator = get_content_generator(llm_service)

        # 根据学科选择生成器
        if record.subject == "english":
            ppt_content = content_generator.generate_for_english(
                content=content_text,
                grade=record.grade,
                slide_count=record.slide_count or 15,
                chapter=record.chapter
            )
        else:
            ppt_content = content_generator.generate(
                content=content_text,
                grade=record.grade,
                subject=record.subject,
                slide_count=record.slide_count or 15,
                chapter=record.chapter
            )

        # 生成新文件
        file_name = f"{ppt_content.get('title', '教学 PPT')}_{uuid.uuid4().hex[:8]}.pptx"
        output_path = settings.UPLOAD_DIR / "generated" / file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        ppt_generator = get_ppt_generator()
        ppt_generator.generate(ppt_content, output_path, record.grade, record.style, record.subject)

        # 创建新历史记录
        new_record = regenerate_from_history(
            db, record_id, session_id,
            file_name, str(output_path), ppt_content
        )

        return {
            "success": True,
            "message": "重新生成成功",
            "data": new_record.to_dict(),
            "download_url": f"/uploads/generated/{file_name}",
        }

    except ValueError as e:
        logger.error(f"参数错误：{e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        logger.error(f"生成超时：{e}")
        raise HTTPException(status_code=408, detail="生成超时，请稍后重试")
    except Exception as e:
        logger.error(f"重新生成失败：{e}")
        raise HTTPException(status_code=500, detail=f"重新生成失败：{str(e)}")


@router.post("/history/save")
async def save_generation_history(
    session_id: str = Body(..., embed=True, description="用户 session ID"),
    title: str = Body(..., embed=True, description="PPT 标题"),
    grade: str = Body(..., embed=True, description="年级"),
    subject: str = Body(..., embed=True, description="学科"),
    style: str = Body(..., embed=True, description="PPT 风格"),
    file_name: str = Body(..., embed=True, description="文件名"),
    file_path: str = Body(..., embed=True, description="文件路径"),
    content_text: Optional[dict] = Body(None, embed=True, description="原始内容文本"),
    slide_count: Optional[int] = Body(None, embed=True, description="幻灯片页数"),
    chapter: Optional[str] = Body(None, embed=True, description="章节名称"),
    ppt_content: Optional[dict] = Body(None, embed=True, description="PPT 内容结构"),
    db = Depends(get_db),
):
    """保存生成历史记录（在 PPT 生成后调用）"""
    try:
        record = add_generation_record(
            db, session_id, title, grade, subject, style,
            file_name, file_path, content_text, slide_count, chapter, ppt_content
        )
        return {
            "success": True,
            "message": "历史记录已保存",
            "data": record.to_dict(),
        }
    except Exception as e:
        logger.error(f"保存历史记录失败：{e}")
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)}")
