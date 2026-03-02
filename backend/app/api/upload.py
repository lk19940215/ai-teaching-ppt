from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import aiofiles
import os
from pathlib import Path
from typing import List
import uuid
from ..config import settings

router = APIRouter(prefix=settings.API_V1_STR, tags=["upload"])

# 支持的 MIME 类型
ALLOWED_IMAGE_TYPES = settings.ALLOWED_IMAGE_TYPES
ALLOWED_PDF_TYPE = settings.ALLOWED_PDF_TYPE
MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE

async def save_upload_file(file: UploadFile, subdir: str = "temp") -> Path:
    """保存上传文件到指定子目录，返回保存路径"""
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix if file.filename else ".bin"
    file_name = f"{uuid.uuid4().hex}{file_ext}"
    save_dir = settings.UPLOAD_DIR / subdir
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / file_name

    # 检查文件大小
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="文件大小超过 20MB 限制")

    # 保存文件
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # 重置文件指针以便后续读取
    await file.seek(0)
    return file_path

@router.post("/upload/image")
async def upload_image(files: List[UploadFile] = File(...)):
    """上传图片文件（支持多张）"""
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")

    saved_files = []
    errors = []

    for file in files:
        # 检查文件类型
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            errors.append(f"文件 {file.filename} 类型不支持，仅支持 JPG/PNG")
            continue

        try:
            file_path = await save_upload_file(file, "images")
            saved_files.append({
                "filename": file.filename,
                "saved_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
                "size": file_path.stat().st_size,
                "content_type": file.content_type
            })
        except Exception as e:
            errors.append(f"文件 {file.filename} 上传失败: {str(e)}")

    if errors and not saved_files:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return JSONResponse(content={
        "message": "图片上传成功",
        "saved_files": saved_files,
        "errors": errors if errors else None
    })

@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 文件"""
    if file.content_type != ALLOWED_PDF_TYPE:
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    try:
        file_path = await save_upload_file(file, "pdfs")
        return JSONResponse(content={
            "message": "PDF 上传成功",
            "saved_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
            "size": file_path.stat().st_size,
            "filename": file.filename
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 上传失败: {str(e)}")

@router.post("/upload/text")
async def upload_text(text: str):
    """上传文本内容（直接粘贴）"""
    if not text or len(text.strip()) == 0:
        raise HTTPException(status_code=400, detail="文本内容不能为空")

    # 简单文本清洗：去除多余空白
    cleaned_text = " ".join(text.strip().split())

    # 保存文本到文件（可选）
    file_name = f"{uuid.uuid4().hex}.txt"
    save_dir = settings.UPLOAD_DIR / "texts"
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / file_name

    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
        await f.write(cleaned_text)

    return JSONResponse(content={
        "message": "文本上传成功",
        "saved_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
        "text_length": len(cleaned_text),
        "preview": cleaned_text[:200] + ("..." if len(cleaned_text) > 200 else "")
    })