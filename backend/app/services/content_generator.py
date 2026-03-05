"""
PPT 内容生成器

使用可插拔的提示词引擎，根据学科自动选择合适的提示词策略
"""

from typing import Dict, Any, List, Optional
from .llm import LLMService, LLMProvider, get_llm_service
from .prompts import PromptEngine
from .attention_optimizer import AttentionRhythmOptimizer, get_attention_optimizer
import logging

logger = logging.getLogger(__name__)


class PPTContentGenerator:
    """PPT 内容生成器"""

    # 年级对应的深度描述（保留向后兼容）
    GRADE_DESCRIPTIONS = {
        "1": "小学一年级（需要用最简单的语言、大量图片、拼音标注）",
        "2": "小学二年级（需要用简单的语言、配合图片）",
        "3": "小学三年级（需要用通俗易懂的语言、配合插图）",
        "4": "小学四年级（需要用清晰的语言、加入互动游戏）",
        "5": "小学五年级（需要用详细的语言、添加思考题）",
        "6": "小学六年级（需要用准确的语言、添加练习题）",
        "7": "初中一年级（需要用正式的语言、建立知识体系）",
        "8": "初中二年级（需要用严谨的语言、深入讲解）",
        "9": "初中三年级（需要用专业的语言、重点突出）",
        "10": "高中一年级（需要用系统化的语言、注重知识深度和广度、培养抽象思维）",
        "11": "高中二年级（需要用学术化的语言、强调知识迁移和综合运用、高考导向）",
        "12": "高中三年级（需要用精炼专业的语言、强化考点突破和应试技巧、冲刺高考）",
    }

    # 学科特色描述（保留向后兼容）
    SUBJECT_DESCRIPTIONS = {
        "chinese": "语文（注重拼音、朗读、感悟、书写）",
        "math": "数学（注重逻辑思维、计算、应用题、图形）",
        "english": "英语（注重单词、发音、句型、情景对话）",
        "science": "科学（注重实验、观察、探究、记录）",
        "physics": "物理（注重公式、实验、原理、应用）",
        "chemistry": "化学（注重反应、实验、结构、性质）",
        "biology": "生物（注重观察、实验、生命过程、生态系统）",
        "history": "历史（注重时间线、事件、人物、因果关系）",
        "politics": "政治（注重概念、原理、联系实际、价值观念）",
        "geography": "地理（注重地图、位置、环境、人文）",
        "general": "通用学科",
    }

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        初始化 PPT 内容生成器
        Args:
            llm_service: LLM 服务实例
        """
        self.llm_service = llm_service or get_llm_service()
        self.prompt_engine = PromptEngine()

    def generate(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None,
        difficulty_level: str = "unified",
        **llm_kwargs
    ) -> Dict[str, Any]:
        """
        生成 PPT 内容（统一入口，根据学科自动选择策略）
        Args:
            content: 教学内容
            grade: 年级
            subject: 学科
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）
            difficulty_level: 教学层次（unified/basic/intermediate/advanced）
            **llm_kwargs: LLM 调用参数
        Returns:
            结构化的 PPT 内容
        """
        # 使用 PromptEngine 根据学科选择对应的策略
        prompt = self.prompt_engine.build_prompt(
            content=content,
            grade=grade,
            subject=subject,
            slide_count=slide_count,
            chapter=chapter,
            difficulty_level=difficulty_level
        )

        schema = self.prompt_engine.build_schema(
            slide_count=slide_count,
            subject=subject,
            difficulty_level=difficulty_level
        )

        try:
            result = self.llm_service.generate_structured_content(
                prompt, schema, **llm_kwargs
            )
            logger.info(f"PPT 内容生成成功：{result.get('title', '未知')}")

            # 应用注意力节奏优化
            optimizer = get_attention_optimizer(grade, subject)
            optimized_result = self._apply_attention_optimization(result, optimizer)

            return optimized_result
        except Exception as e:
            logger.error(f"PPT 内容生成失败：{e}")
            raise RuntimeError(f"PPT 内容生成失败：{e}") from e

    def _apply_attention_optimization(
        self,
        result: Dict[str, Any],
        optimizer: AttentionRhythmOptimizer
    ) -> Dict[str, Any]:
        """
        应用注意力节奏优化到生成的 PPT 内容

        Args:
            result: 原始 PPT 内容
            optimizer: 注意力节奏优化器

        Returns:
            优化后的 PPT 内容
        """
        slides = result.get("slides", [])

        if not slides:
            return result

        # 分析当前节奏
        rhythm_analysis = optimizer.analyze_rhythm(slides)

        # 如果有问题，尝试优化序列
        if not rhythm_analysis["valid"]:
            logger.warning(
                f"注意力节奏检测到问题：{[i['message'] for i in rhythm_analysis['issues']]}"
            )
            optimized_slides = optimizer.optimize_sequence(slides)
            result["slides"] = optimized_slides

            # 重新分析优化后的节奏
            final_analysis = optimizer.analyze_rhythm(optimized_slides)
            result["attention_rhythm_analysis"] = final_analysis
            logger.info(f"注意力节奏优化完成：{final_analysis['stats']}")
        else:
            # 即使没有问题，也记录分析结果
            result["attention_rhythm_analysis"] = rhythm_analysis

        return result

    def generate_for_english(
        self,
        content: str,
        grade: str,
        slide_count: int,
        chapter: Optional[str] = None,
        difficulty_level: str = "unified",
        **llm_kwargs
    ) -> Dict[str, Any]:
        """
        生成英语学科专属 PPT 内容（向后兼容的便捷方法）
        Args:
            content: 教学内容
            grade: 年级
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）
            difficulty_level: 教学层次（unified/basic/intermediate/advanced）
            **llm_kwargs: LLM 调用参数
        Returns:
            结构化的 PPT 内容
        """
        # 内部调用统一的 generate 方法，指定 subject="english"
        return self.generate(
            content=content,
            grade=grade,
            subject="english",
            slide_count=slide_count,
            chapter=chapter,
            difficulty_level=difficulty_level,
            **llm_kwargs
        )


# 全局内容生成器实例
_content_generator_instance: Optional[PPTContentGenerator] = None


def get_content_generator(llm_service: Optional[LLMService] = None) -> PPTContentGenerator:
    """获取内容生成器单例"""
    global _content_generator_instance
    if _content_generator_instance is None:
        _content_generator_instance = PPTContentGenerator(llm_service)
    return _content_generator_instance
