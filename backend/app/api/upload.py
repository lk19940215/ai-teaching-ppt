from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
import aiofiles
import os
from pathlib import Path
from typing import List, Optional
import uuid
from ..config import settings
from ..services.ocr import get_ocr_service
from ..services.pdf_parser import get_pdf_parser

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
async def upload_text(text: str = Body(..., embed=True)):
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

@router.post("/process/ocr")
async def process_ocr(file_path: str = Body(..., embed=True)):
    """对已上传的图片进行 OCR 识别"""
    try:
        # 构建完整路径
        full_path = settings.UPLOAD_DIR / file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 调用 OCR 服务
        ocr_service = get_ocr_service()
        text = ocr_service.extract_text(full_path)

        return JSONResponse(content={
            "message": "OCR 识别成功",
            "text": text,
            "char_count": len(text)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {str(e)}")

@router.post("/process/pdf")
async def process_pdf(file_path: str = Body(..., embed=True)):
    """对已上传的 PDF 进行文本提取"""
    try:
        # 构建完整路径
        full_path = settings.UPLOAD_DIR / file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 调用 PDF 解析服务
        pdf_parser = get_pdf_parser()
        full_text, pages_text = pdf_parser.extract_text(full_path)
        page_count = pdf_parser.get_page_count(full_path)

        return JSONResponse(content={
            "message": "PDF 解析成功",
            "full_text": full_text,
            "page_count": page_count,
            "char_count": len(full_text),
            "pages": [{"page": p, "text": t} for p, t in pages_text]
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 解析失败: {str(e)}")

@router.post("/process/extract")
async def extract_content(
    file_path: str = Body(..., embed=True),
    file_type: Optional[str] = Body(None, embed=True)
):
    """统一内容提取接口（自动判断文件类型）"""
    try:
        # 支持相对路径和绝对路径
        if os.path.isabs(file_path):
            full_path = Path(file_path)
        else:
            full_path = settings.UPLOAD_DIR / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {full_path}")

        # 根据文件扩展名判断类型
        ext = full_path.suffix.lower()
        if ext == ".pdf":
            pdf_parser = get_pdf_parser()
            full_text, pages_text = pdf_parser.extract_text(full_path)
            return JSONResponse(content={
                "message": "PDF 内容提取成功",
                "file_type": "pdf",
                "text": full_text,
                "page_count": len(pages_text)
            })
        elif ext in [".jpg", ".jpeg", ".png"]:
            ocr_service = get_ocr_service()
            text = ocr_service.extract_text(full_path)
            return JSONResponse(content={
                "message": "图片 OCR 识别成功",
                "file_type": "image",
                "text": text
            })
        elif ext == ".txt":
            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                text = await f.read()
            return JSONResponse(content={
                "message": "文本读取成功",
                "file_type": "text",
                "text": text
            })
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容提取失败: {str(e)}")