import os
from pathlib import Path
import fitz  # PyMuPDF
import logging
from typing import List, Tuple, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)

class PDFParser:
    """PDF 解析服务，提取文本和图片"""

    def __init__(self):
        pass

    def extract_text(self, pdf_path: Path) -> Tuple[str, List[Tuple[int, str]]]:
        """
        提取 PDF 中的文本内容
        Returns:
            (full_text, pages_text) - 完整文本和按页分离的文本列表
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        full_text = ""
        pages_text = []

        try:
            doc = fitz.open(str(pdf_path))
            logger.info(f"PDF 打开成功: {pdf_path.name}, 页数: {doc.page_count}")

            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")  # 提取文本

                # 清理文本
                cleaned_text = self._clean_text(page_text)
                pages_text.append((page_num + 1, cleaned_text))
                full_text += cleaned_text + "\n\n"

            doc.close()
            logger.info(f"PDF 文本提取完成: {pdf_path.name}, 总字符数: {len(full_text)}")
            return full_text.strip(), pages_text

        except Exception as e:
            logger.error(f"PDF 文本提取失败 {pdf_path}: {e}")
            raise RuntimeError(f"PDF 解析失败: {e}")

    def extract_images(self, pdf_path: Path, output_dir: Path, dpi: int = 150) -> List[Path]:
        """
        提取 PDF 中的图片
        Args:
            output_dir: 图片保存目录
            dpi: 图片输出分辨率
        Returns:
            保存的图片路径列表
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        saved_images = []

        try:
            doc = fitz.open(str(pdf_path))

            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)

                    if base_image:
                        # 获取图片数据
                        image_data = base_image["image"]
                        image_ext = base_image["ext"]

                        # 生成文件名
                        image_name = f"page{page_num+1}_img{img_index+1}.{image_ext}"
                        image_path = output_dir / image_name

                        # 保存图片
                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        saved_images.append(image_path)
                        logger.debug(f"提取图片: {image_path.name}")

            doc.close()
            logger.info(f"PDF 图片提取完成: {pdf_path.name}, 提取图片数: {len(saved_images)}")
            return saved_images

        except Exception as e:
            logger.error(f"PDF 图片提取失败 {pdf_path}: {e}")
            raise RuntimeError(f"PDF 图片提取失败: {e}")

    def get_page_count(self, pdf_path: Path) -> int:
        """获取 PDF 页数"""
        try:
            doc = fitz.open(str(pdf_path))
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            logger.error(f"获取 PDF 页数失败 {pdf_path}: {e}")
            return 0

    def _clean_text(self, text: str) -> str:
        """清理文本：移除多余空白、控制字符"""
        if not text:
            return ""

        # 替换各种空白字符为单个空格
        import re
        text = re.sub(r'\s+', ' ', text)

        # 移除控制字符（保留常见标点）
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

        return text.strip()

    def extract_text_with_positions(self, pdf_path: Path) -> List[Tuple[int, List[Tuple[float, float, float, float, str]]]]:
        """
        提取带位置信息的文本（用于高级布局分析）
        Returns:
            List of (page_num, [(x0, y0, x1, y1, text), ...])
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        try:
            doc = fitz.open(str(pdf_path))
            result = []

            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                blocks = page.get_text("dict")["blocks"]

                page_texts = []
                for block in blocks:
                    if block["type"] == 0:  # 文本块
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                bbox = span["bbox"]  # (x0, y0, x1, y1)
                                text = span["text"]
                                if text.strip():
                                    page_texts.append((bbox[0], bbox[1], bbox[2], bbox[3], text))

                result.append((page_num + 1, page_texts))

            doc.close()
            return result

        except Exception as e:
            logger.error(f"PDF 位置文本提取失败 {pdf_path}: {e}")
            return []

# 全局 PDF 解析服务实例
_pdf_parser_instance = None

def get_pdf_parser() -> PDFParser:
    """获取 PDF 解析服务单例"""
    global _pdf_parser_instance
    if _pdf_parser_instance is None:
        _pdf_parser_instance = PDFParser()
    return _pdf_parser_instance