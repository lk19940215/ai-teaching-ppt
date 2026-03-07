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
        self.lang = lang
        self.ocr = None
        self._initialize_ocr()

    def _initialize_ocr(self):
        if self.ocr is None:
            try:
                self.ocr = PaddleOCR(lang=self.lang)
                logger.info(f"PaddleOCR 初始化完成，语言：{self.lang}")
            except Exception as e:
                logger.error(f"PaddleOCR 初始化失败：{e}")
                raise RuntimeError(f"OCR 引擎初始化失败：{e}")

    def recognize_image(self, image_path: Path) -> List[Tuple[np.ndarray, str, float]]:
        self._initialize_ocr()
        try:
            if not image_path.exists():
                raise FileNotFoundError(f"图片文件不存在：{image_path}")

            result = self.ocr.predict(str(image_path))
            ocr_results = []
            for item in result:
                rec_polys = item.get('rec_polys', [])
                rec_texts = item.get('rec_texts', [])
                rec_scores = item.get('rec_scores', [])
                
                for i, text in enumerate(rec_texts):
                    if i < len(rec_polys):
                        bbox = np.array(rec_polys[i])
                        confidence = rec_scores[i] if i < len(rec_scores) else 1.0
                        ocr_results.append((bbox, text, confidence))
                break
            logger.info(f"OCR 识别完成：{image_path.name}, 识别到 {len(ocr_results)} 个文本区域")
            return ocr_results
        except Exception as e:
            logger.error(f"OCR 识别失败 {image_path}: {e}", exc_info=True)
            raise RuntimeError(f"图片文字识别失败：{e}")

    def extract_text(self, image_path: Path, min_confidence: float = 0.5) -> str:
        results = self.recognize_image(image_path)
        # bbox 是 numpy 数组，每个点 [x, y]，取左上角 y 坐标
        sorted_results = sorted(results, key=lambda x: x[0][0][1] if x[0].shape[0] > 0 else 0)
        lines = [text for bbox, text, confidence in sorted_results if confidence >= min_confidence]
        full_text = "\n".join(lines)
        logger.info(f"文本提取完成：{image_path.name}, 字符数：{len(full_text)}")
        return full_text

    def recognize_multiple_images(self, image_paths: List[Path]) -> List[str]:
        texts = []
        for img_path in image_paths:
            try:
                text = self.extract_text(img_path)
                texts.append(text)
            except Exception as e:
                logger.error(f"批量识别失败 {img_path}: {e}")
                texts.append(f"[识别失败：{img_path.name}]")
        return texts

_ocr_service_instance = None

def get_ocr_service(lang: str = "ch") -> OCRService:
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService(lang)
    return _ocr_service_instance
