import os
from pathlib import Path
from typing import List, Tuple, Optional
import logging
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class OCRService:
    """PaddleOCR 图片文字识别服务"""

    def __init__(self, lang: str = "ch"):
        """
        初始化 OCR 引擎
        Args:
            lang: 识别语言，'ch' 中文，'en' 英文，'ch_en' 中英文混合
        """
        self.lang = lang
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        """初始化 PaddleOCR 引擎（懒加载）"""
        if self.ocr is None:
            try:
                # PaddleOCR 3.4.0 新 API - 使用最小参数集
                self.ocr = PaddleOCR(lang=self.lang, ocr_version="PP-OCRv4", use_angle_cls=True)
                logger.info(f"PaddleOCR 初始化完成，语言: {self.lang}")
            except Exception as e:
                logger.error(f"PaddleOCR 初始化失败: {e}")
                raise RuntimeError(f"OCR 引擎初始化失败: {e}")

    def recognize_image(self, image_path: Path) -> List[Tuple[List[List[float]], str, float]]:
        """
        识别单张图片中的文字
        Returns:
            List of (bounding_box, text, confidence)
        """
        self._initialize_ocr()
        try:
            # 验证图片文件
            if not image_path.exists():
                raise FileNotFoundError(f"图片文件不存在: {image_path}")

            # 执行 OCR 识别 - PaddleOCR 3.4.0 新 API
            result = self.ocr.ocr(str(image_path))

            # 解析结果 - PaddleOCR 3.4.0 返回字典列表
            ocr_results = []
            if result and len(result) > 0:
                page_result = result[0]
                # 检查是否是字典格式（新 API）
                if isinstance(page_result, dict):
                    rec_texts = page_result.get('rec_texts', [])
                    rec_scores = page_result.get('rec_scores', [])
                    rec_polys = page_result.get('rec_polys', [])

                    for i, text in enumerate(rec_texts):
                        bbox = rec_polys[i].tolist() if i < len(rec_polys) else [[0,0], [0,0], [0,0], [0,0]]
                        confidence = rec_scores[i] if i < len(rec_scores) else 1.0
                        ocr_results.append((bbox, text, confidence))
                # 兼容旧格式
                elif hasattr(page_result, '__iter__') and not isinstance(page_result, str):
                    for line in page_result:
                        if line and len(line) >= 2:
                            bbox = line[0]
                            text = line[1][0] if isinstance(line[1], (tuple, list)) else str(line[1])
                            confidence = line[1][1] if isinstance(line[1], (tuple, list)) else 1.0
                            ocr_results.append((bbox, text, confidence))

            logger.info(f"OCR 识别完成: {image_path.name}, 识别到 {len(ocr_results)} 个文本区域")
            return ocr_results

        except Exception as e:
            logger.error(f"OCR 识别失败 {image_path}: {e}")
            raise RuntimeError(f"图片文字识别失败: {e}")

    def extract_text(self, image_path: Path, min_confidence: float = 0.5) -> str:
        """
        提取图片中的文字，按行合并
        Args:
            min_confidence: 最低置信度阈值，低于此值的文本将被过滤
        Returns:
            合并后的文本字符串
        """
        results = self.recognize_image(image_path)

        # 按 y 坐标排序（从上到下）
        sorted_results = sorted(results, key=lambda x: x[0][0][1])  # 按左上角 y 坐标排序

        lines = []
        for bbox, text, confidence in sorted_results:
            if confidence >= min_confidence:
                lines.append(text)

        full_text = "\n".join(lines)
        logger.info(f"文本提取完成: {image_path.name}, 字符数: {len(full_text)}")
        return full_text

    def recognize_multiple_images(self, image_paths: List[Path]) -> List[str]:
        """批量识别多张图片"""
        texts = []
        for img_path in image_paths:
            try:
                text = self.extract_text(img_path)
                texts.append(text)
            except Exception as e:
                logger.error(f"批量识别失败 {img_path}: {e}")
                texts.append(f"[识别失败: {img_path.name}]")
        return texts

# 全局 OCR 服务实例（单例）
_ocr_service_instance = None

def get_ocr_service(lang: str = "ch") -> OCRService:
    """获取 OCR 服务单例"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService(lang)
    return _ocr_service_instance