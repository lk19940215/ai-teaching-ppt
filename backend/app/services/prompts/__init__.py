"""
提示词引擎模块

提供可插拔的学科提示词策略系统，根据学科自动选择对应的策略
"""

from typing import Dict, Any, Optional, Type
from .base import SubjectPromptStrategy, CognitiveLoadMixin
from .general import GeneralPromptStrategy
from .english import EnglishPromptStrategy
from .chinese import ChinesePromptStrategy
from .math import MathPromptStrategy
from .science import PhysicsPromptStrategy, ChemistryPromptStrategy, BiologyPromptStrategy
from .cognitive import CognitivePromptStrategy


class PromptEngine:
    """
    提示词引擎工厂类

    根据学科自动选择对应的提示词策略，提供统一的调用接口
    """

    # 学科到策略类的映射
    STRATEGY_REGISTRY: Dict[str, Type[SubjectPromptStrategy]] = {
        "english": EnglishPromptStrategy,
        "chinese": ChinesePromptStrategy,
        "math": MathPromptStrategy,
        "physics": PhysicsPromptStrategy,
        "chemistry": ChemistryPromptStrategy,
        "biology": BiologyPromptStrategy,
        "general": GeneralPromptStrategy,
    }

    # 默认策略
    DEFAULT_STRATEGY = GeneralPromptStrategy

    def __init__(self, subject: str = "general"):
        """
        初始化提示词引擎

        Args:
            subject: 学科名称，支持 "english", "general" 等
        """
        self.subject = subject.lower()
        self.strategy = self._get_strategy(self.subject)

    def _get_strategy(self, subject: str) -> SubjectPromptStrategy:
        """
        根据学科获取对应的策略实例

        Args:
            subject: 学科名称

        Returns:
            策略实例
        """
        strategy_class = self.STRATEGY_REGISTRY.get(subject, self.DEFAULT_STRATEGY)
        return strategy_class()

    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: Optional[str] = None,
        slide_count: int = 10,
        chapter: Optional[str] = None
    ) -> str:
        """
        构建 PPT 内容生成提示词

        Args:
            content: 教学内容
            grade: 年级
            subject: 学科（可选，优先于构造函数的 subject）
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）

        Returns:
            构建好的提示词
        """
        # 如果调用时指定了 subject，使用对应的策略
        if subject and subject.lower() != self.subject:
            strategy = self._get_strategy(subject.lower())
        else:
            strategy = self.strategy

        return strategy.build_prompt(content, grade, subject or self.subject, slide_count, chapter)

    def build_schema(self, slide_count: int, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        构建输出结构定义

        Args:
            slide_count: 幻灯片数量
            subject: 学科（可选）

        Returns:
            JSON Schema 结构定义
        """
        if subject and subject.lower() != self.subject:
            strategy = self._get_strategy(subject.lower())
        else:
            strategy = self.strategy

        return strategy.build_schema(slide_count)

    def get_page_types(self, subject: Optional[str] = None) -> list:
        """
        获取学科支持的页面类型列表

        Args:
            subject: 学科（可选）

        Returns:
            页面类型字符串列表
        """
        if subject and subject.lower() != self.subject:
            strategy = self._get_strategy(subject.lower())
        else:
            strategy = self.strategy

        return strategy.get_page_types()

    @classmethod
    def register_strategy(cls, subject: str, strategy_class: Type[SubjectPromptStrategy]):
        """
        注册新的学科策略

        Args:
            subject: 学科名称
            strategy_class: 策略类
        """
        cls.STRATEGY_REGISTRY[subject.lower()] = strategy_class

    @classmethod
    def get_available_subjects(cls) -> list:
        """
        获取所有可用的学科列表

        Returns:
            学科名称列表
        """
        return list(cls.STRATEGY_REGISTRY.keys())


# 便捷函数
def get_prompt_engine(subject: str = "general") -> PromptEngine:
    """
    获取提示词引擎实例

    Args:
        subject: 学科名称

    Returns:
        PromptEngine 实例
    """
    return PromptEngine(subject)


def build_prompt(
    content: str,
    grade: str,
    subject: str = "general",
    slide_count: int = 10,
    chapter: Optional[str] = None
) -> str:
    """
    便捷函数：直接构建提示词

    Args:
        content: 教学内容
        grade: 年级
        subject: 学科
        slide_count: 幻灯片数量
        chapter: 章节名称（可选）

    Returns:
        构建好的提示词
    """
    engine = PromptEngine(subject)
    return engine.build_prompt(content, grade, subject, slide_count, chapter)


def build_schema(
    slide_count: int,
    subject: str = "general"
) -> Dict[str, Any]:
    """
    便捷函数：直接构建输出结构

    Args:
        slide_count: 幻灯片数量
        subject: 学科

    Returns:
        JSON Schema 结构定义
    """
    engine = PromptEngine(subject)
    return engine.build_schema(slide_count, subject)
