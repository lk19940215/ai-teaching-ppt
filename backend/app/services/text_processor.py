import re
import logging
from typing import List, Tuple, Dict, Optional
from pathlib import Path

# 可选导入 jieba，如果未安装则使用简单分词
try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

logger = logging.getLogger(__name__)

class TextProcessor:
    """文本内容清洗和合并服务"""

    def __init__(self):
        # 初始化中文分词器
        if HAS_JIEBA:
            try:
                jieba.initialize()
            except Exception:
                pass  # 如果已初始化则忽略

    def clean_text(self, text: str, language: str = "zh") -> str:
        """
        清洗文本内容
        Args:
            language: 'zh' 中文, 'en' 英文, 'mixed' 中英文混合
        """
        if not text:
            return ""

        # 移除特殊字符和多余空白
        text = self._remove_special_chars(text)
        text = self._normalize_whitespace(text)

        # 语言特定处理
        if language == "zh":
            text = self._clean_chinese_text(text)
        elif language == "en":
            text = self._clean_english_text(text)
        else:  # mixed
            text = self._clean_mixed_text(text)

        return text.strip()

    def segment_sentences(self, text: str, language: str = "zh") -> List[str]:
        """将文本分割成句子"""
        if not text:
            return []

        if language == "zh":
            # 中文句子分割：根据标点符号
            sentences = re.split(r'[。！？!?]+', text)
        elif language == "en":
            # 英文句子分割
            sentences = re.split(r'[.!?]+', text)
        else:
            # 混合语言：使用通用标点
            sentences = re.split(r'[。！？.!?]+', text)

        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def extract_keywords(self, text: str, top_k: int = 10, language: str = "zh") -> List[str]:
        """提取关键词（基于简单频率统计）"""
        if not text:
            return []

        # 分词
        if language == "zh":
            words = jieba.lcut(text)
            # 过滤停用词和单字
            words = [w for w in words if len(w) > 1 and not self._is_stopword(w, language)]
        elif language == "en":
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            words = [w for w in words if not self._is_stopword(w, language)]
        else:
            # 混合：分别处理中英文
            chinese_words = jieba.lcut(text)
            chinese_words = [w for w in chinese_words if len(w) > 1 and not self._is_stopword(w, "zh")]
            english_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
            english_words = [w for w in english_words if not self._is_stopword(w, "en")]
            words = chinese_words + english_words

        # 统计词频
        from collections import Counter
        word_freq = Counter(words)

        # 返回最高频的关键词
        keywords = [word for word, _ in word_freq.most_common(top_k)]
        return keywords

    def merge_texts(self, texts: List[str], separator: str = "\n\n") -> str:
        """合并多个文本，去重相似内容"""
        if not texts:
            return ""

        # 简单去重：去除完全相同的文本
        unique_texts = []
        seen = set()
        for text in texts:
            if text not in seen:
                seen.add(text)
                unique_texts.append(text)

        # 合并
        merged = separator.join(unique_texts)
        return merged

    def calculate_text_metrics(self, text: str) -> Dict[str, int]:
        """计算文本指标"""
        if not text:
            return {"characters": 0, "words": 0, "sentences": 0, "paragraphs": 0}

        # 字符数（包括空格）
        char_count = len(text)

        # 单词数（中文字符按字计数，英文按单词）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        word_count = chinese_chars + english_words

        # 句子数
        sentence_count = len(self.segment_sentences(text, "mixed"))

        # 段落数（按空行分割）
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)

        return {
            "characters": char_count,
            "words": word_count,
            "sentences": sentence_count,
            "paragraphs": paragraph_count
        }

    def _remove_special_chars(self, text: str) -> str:
        """移除特殊字符，保留中英文、数字、常见标点"""
        # 保留字符：中文、英文、数字、常见标点、空格
        pattern = r'[^\u4e00-\u9fffa-zA-Z0-9\s。，；：！？、."\'()（）【】《》〈〉「」『』\-—–+*=<>/\\|@#$%&~`]'
        return re.sub(pattern, '', text)

    def _normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        # 替换所有空白字符为单个空格
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白
        return text.strip()

    def _clean_chinese_text(self, text: str) -> str:
        """中文文本清洗"""
        # 规范化中文标点
        text = re.sub(r'[，,]+', '，', text)
        text = re.sub(r'[。.]+', '。', text)
        text = re.sub(r'[！!]+', '！', text)
        text = re.sub(r'[？?]+', '？', text)
        return text

    def _clean_english_text(self, text: str) -> str:
        """英文文本清洗"""
        # 确保单词间有空格
        text = re.sub(r'([a-zA-Z])([^a-zA-Z\s])', r'\1 \2', text)
        text = re.sub(r'([^a-zA-Z\s])([a-zA-Z])', r'\1 \2', text)
        return text

    def _clean_mixed_text(self, text: str) -> str:
        """中英文混合文本清洗"""
        text = self._clean_chinese_text(text)
        text = self._clean_english_text(text)
        return text

    def _is_stopword(self, word: str, language: str) -> bool:
        """判断是否为停用词（简化版）"""
        # 简单停用词列表
        chinese_stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        english_stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "as", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "shall", "should", "may", "might", "must", "can", "could"}

        if language == "zh":
            return word in chinese_stopwords
        elif language == "en":
            return word.lower() in english_stopwords
        return False

# 全局文本处理器实例
_text_processor_instance = None

def get_text_processor() -> TextProcessor:
    """获取文本处理器单例"""
    global _text_processor_instance
    if _text_processor_instance is None:
        _text_processor_instance = TextProcessor()
    return _text_processor_instance