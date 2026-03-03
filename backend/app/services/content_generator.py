from typing import Dict, Any, List, Optional
from .llm import LLMService, LLMProvider, get_llm_service
import logging

logger = logging.getLogger(__name__)

class PPTContentGenerator:
    """PPT 内容生成器"""

    # 年级对应的深度描述
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
    }

    # 学科特色描述
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

    def _build_generation_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None
    ) -> str:
        """
        构建 PPT 内容生成提示词
        """
        grade_desc = self.GRADE_DESCRIPTIONS.get(grade, "")
        subject_desc = self.SUBJECT_DESCRIPTIONS.get(subject, "")

        prompt = f"""请根据以下教学内容，生成一份教学 PPT 的内容大纲。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：{subject} - {subject_desc}
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【要求】
1. 根据年级调整内容深度和表达方式
2. 提炼核心知识点和重点难点
3. 设计互动环节（课堂提问、小组讨论题、趣味问答）
4. 生成课堂练习题
5. 添加记忆口诀或助记方法
6. 按照以下结构生成页面内容

【PPT 结构】
- 封面页：章节名称
- 目录页：列出主要知识点
- 知识点讲解页：3-5 页，详细讲解每个知识点
- 互动问答页：2-3 页，课堂提问和讨论
- 课堂练习页：2-3 页，练习题
- 总结回顾页：1 页，总结重点

请生成内容，确保条理清晰、层次分明。"""

        return prompt

    def _build_output_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/知识点讲解页/互动问答页/课堂练习页/总结回顾页",
                    "title": "页面标题",
                    "content": ["页面内容要点1", "页面内容要点2"],
                    "interaction": "互动环节描述（如适用）",
                    "exercise": "练习题描述（如适用）",
                    "mnemonic": "记忆口诀或助记方法（如适用）"
                }
                for _ in range(slide_count)
            ],
            "summary": "整体内容总结",
            "key_points": ["重点1", "重点2", "重点3"]
        }

    def generate(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None,
        **llm_kwargs
    ) -> Dict[str, Any]:
        """
        生成 PPT 内容
        Args:
            content: 教学内容
            grade: 年级
            subject: 学科
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）
            **llm_kwargs: LLM 调用参数
        Returns:
            结构化的 PPT 内容
        """
        prompt = self._build_generation_prompt(
            content, grade, subject, slide_count, chapter
        )
        schema = self._build_output_schema(slide_count)

        try:
            result = self.llm_service.generate_structured_content(
                prompt, schema, **llm_kwargs
            )
            logger.info(f"PPT 内容生成成功: {result.get('title', '未知')}")
            return result
        except Exception as e:
            logger.error(f"PPT 内容生成失败: {e}")
            raise RuntimeError(f"PPT 内容生成失败: {e}") from e

    def generate_for_english(
        self,
        content: str,
        grade: str,
        slide_count: int,
        chapter: Optional[str] = None,
        **llm_kwargs
    ) -> Dict[str, Any]:
        """
        生成英语学科专属 PPT 内容
        Args:
            content: 教学内容
            grade: 年级
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）
            **llm_kwargs: LLM 调用参数
        Returns:
            结构化的 PPT 内容
        """
        grade_desc = self.GRADE_DESCRIPTIONS.get(grade, "")

        prompt = f"""请根据以下英语教学内容，生成一份英语教学 PPT 的内容大纲。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：英语
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【英语学科特色要求】
1. 单词卡片页：单词 + 音标 + 中文释义 + 英文例句
2. 语法结构图解页：用表格或图示展示语法规则
3. 情景对话页：生成贴合课文主题的对话示例
4. 课文要点分析页：段落大意、关键句型、常用表达
5. 课堂互动页：填空、选择、连线等练习形式

【PPT 结构】
- 封面页：章节名称
- 单词学习页：3-4 页，单词 + 音标 + 释义 + 例句
- 语法讲解页：2-3 页，语法规则和例句
- 情景对话页：2-3 页，对话练习
- 课文分析页：2-3 页，要点提炼
- 课堂练习页：2-3 页，练习题
- 总结回顾页：1 页

请生成内容，确保英语学习效果。"""

        schema = {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/单词学习页/语法讲解页/情景对话页/课文分析页/课堂练习页/总结回顾页",
                    "title": "页面标题",
                    "content": ["页面内容要点1", "页面内容要点2"],
                    "vocabulary": [{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}],
                    "grammar": "语法规则说明（如适用）",
                    "dialogue": "对话内容（如适用）",
                    "exercise": "练习题描述（如适用）"
                }
                for _ in range(slide_count)
            ],
            "vocabulary_list": [{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}],
            "grammar_points": ["语法点1", "语法点2"],
            "summary": "整体内容总结"
        }

        try:
            result = self.llm_service.generate_structured_content(
                prompt, schema, **llm_kwargs
            )
            logger.info(f"英语 PPT 内容生成成功: {result.get('title', '未知')}")
            return result
        except Exception as e:
            logger.error(f"英语 PPT 内容生成失败: {e}")
            raise RuntimeError(f"英语 PPT 内容生成失败: {e}") from e


# 全局内容生成器实例
_content_generator_instance: Optional[PPTContentGenerator] = None

def get_content_generator(llm_service: Optional[LLMService] = None) -> PPTContentGenerator:
    """获取内容生成器单例"""
    global _content_generator_instance
    if _content_generator_instance is None:
        _content_generator_instance = PPTContentGenerator(llm_service)
    return _content_generator_instance