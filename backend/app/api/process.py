from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
from ..config import settings
from ..services.ocr import get_ocr_service
from ..services.pdf_parser import get_pdf_parser
from ..services.text_processor import get_text_processor

router = APIRouter(prefix=settings.API_V1_STR, tags=["process"])
logger = logging.getLogger(__name__)

class ProcessRequest(BaseModel):
    """处理请求基类"""
    file_path: str = Field(..., description="上传文件相对路径（相对于 uploads 目录）")
    language: str = Field(default="ch", description="识别语言：ch 中文，en 英文，ch_en 中英文混合")

class OCRRequest(ProcessRequest):
    """OCR 处理请求"""
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="最低置信度阈值")

class PDFParseRequest(ProcessRequest):
    """PDF 解析请求"""
    extract_images: bool = Field(default=False, description="是否提取图片")
    image_dpi: int = Field(default=150, ge=72, le=300, description="图片提取分辨率")

class TextCleanRequest(BaseModel):
    """文本清洗请求"""
    text: str = Field(..., min_length=1, description="待清洗的文本")
    language: str = Field(default="zh", description="文本语言：zh 中文，en 英文，mixed 混合")

class MergeTextsRequest(BaseModel):
    """合并文本请求"""
    texts: List[str] = Field(..., min_items=1, description="待合并的文本列表")
    separator: str = Field(default="\n\n", description="分隔符")

@router.post("/process/ocr")
async def process_ocr(request: OCRRequest):
    """处理图片 OCR 识别"""
    try:
        # 构建完整文件路径
        full_path = settings.UPLOAD_DIR / request.file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        # 检查文件类型（确保是图片）
        allowed_ext = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
        if full_path.suffix.lower() not in allowed_ext:
            raise HTTPException(status_code=400, detail="文件不是支持的图片格式")

        # 执行 OCR
        ocr_service = get_ocr_service(request.language)
        extracted_text = ocr_service.extract_text(full_path, request.min_confidence)

        # 文本清洗
        text_processor = get_text_processor()
        cleaned_text = text_processor.clean_text(extracted_text, request.language)

        # 计算指标
        metrics = text_processor.calculate_text_metrics(cleaned_text)
        keywords = text_processor.extract_keywords(cleaned_text, top_k=10, language=request.language)

        return {
            "success": True,
            "message": "OCR 识别成功",
            "original_text": extracted_text,
            "cleaned_text": cleaned_text,
            "metrics": metrics,
            "keywords": keywords,
            "file_path": request.file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR 处理失败: {str(e)}")

@router.post("/process/pdf")
async def process_pdf(request: PDFParseRequest):
    """处理 PDF 解析"""
    try:
        full_path = settings.UPLOAD_DIR / request.file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="PDF 文件不存在")

        if full_path.suffix.lower() != ".pdf":
            raise HTTPException(status_code=400, detail="文件不是 PDF 格式")

        # 执行 PDF 解析
        pdf_parser = get_pdf_parser()
        full_text, pages_text = pdf_parser.extract_text(full_path)

        # 提取图片（如果需要）
        extracted_images = []
        if request.extract_images:
            image_dir = settings.UPLOAD_DIR / "pdf_images" / full_path.stem
            extracted_images = pdf_parser.extract_images(full_path, image_dir, request.image_dpi)
            extracted_images = [str(img.relative_to(settings.UPLOAD_DIR)) for img in extracted_images]

        # 文本清洗
        text_processor = get_text_processor()
        cleaned_text = text_processor.clean_text(full_text, "mixed")

        # 计算指标
        metrics = text_processor.calculate_text_metrics(cleaned_text)
        keywords = text_processor.extract_keywords(cleaned_text, top_k=10, language="mixed")

        # 页面信息
        page_details = []
        for page_num, page_text in pages_text:
            cleaned_page = text_processor.clean_text(page_text, "mixed")
            page_metrics = text_processor.calculate_text_metrics(cleaned_page)
            page_details.append({
                "page_number": page_num,
                "text": cleaned_page,
                "metrics": page_metrics
            })

        return {
            "success": True,
            "message": "PDF 解析成功",
            "page_count": len(pages_text),
            "full_text": cleaned_text,
            "pages": page_details,
            "extracted_images": extracted_images if extracted_images else None,
            "metrics": metrics,
            "keywords": keywords,
            "file_path": request.file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF 处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF 处理失败: {str(e)}")

@router.post("/process/text")
async def process_text(request: TextCleanRequest):
    """处理文本清洗"""
    try:
        text_processor = get_text_processor()

        # 清洗文本
        cleaned_text = text_processor.clean_text(request.text, request.language)

        # 分割句子
        sentences = text_processor.segment_sentences(cleaned_text, request.language)

        # 提取关键词
        keywords = text_processor.extract_keywords(cleaned_text, top_k=10, language=request.language)

        # 计算指标
        metrics = text_processor.calculate_text_metrics(cleaned_text)

        return {
            "success": True,
            "message": "文本处理成功",
            "original_text": request.text,
            "cleaned_text": cleaned_text,
            "sentences": sentences,
            "keywords": keywords,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"文本处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")

@router.post("/process/merge")
async def merge_texts(request: MergeTextsRequest):
    """合并多个文本"""
    try:
        text_processor = get_text_processor()

        # 合并文本
        merged_text = text_processor.merge_texts(request.texts, request.separator)

        # 清洗合并后的文本
        cleaned_text = text_processor.clean_text(merged_text, "mixed")

        # 计算指标
        metrics = text_processor.calculate_text_metrics(cleaned_text)

        return {
            "success": True,
            "message": "文本合并成功",
            "merged_text": cleaned_text,
            "input_count": len(request.texts),
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"文本合并失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文本合并失败: {str(e)}")

@router.get("/process/status")
async def get_processing_status():
    """获取处理服务状态"""
    try:
        # 检查 OCR 服务
        ocr_service = get_ocr_service()
        ocr_ready = ocr_service.ocr is not None

        # 检查 PDF 解析服务
        pdf_parser = get_pdf_parser()
        pdf_ready = pdf_parser is not None

        # 检查文本处理器
        text_processor = get_text_processor()
        text_ready = text_processor is not None

        return {
            "ocr_service": "ready" if ocr_ready else "not_initialized",
            "pdf_parser": "ready" if pdf_ready else "not_initialized",
            "text_processor": "ready" if text_ready else "not_initialized",
            "upload_dir_exists": settings.UPLOAD_DIR.exists(),
            "upload_dir": str(settings.UPLOAD_DIR)
        }
    except Exception as e:
        logger.error(f"获取服务状态失败: {e}")
        return {
            "ocr_service": "error",
            "pdf_parser": "error",
            "text_processor": "error",
            "error": str(e)
        }