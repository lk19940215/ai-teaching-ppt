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
        构建 PPT 内容生成提示词（优化版：增强知识点结构化、教学逻辑、互动设计）
        """
        grade_desc = self.GRADE_DESCRIPTIONS.get(grade, "")
        subject_desc = self.SUBJECT_DESCRIPTIONS.get(subject, "")

        prompt = f"""你是一位经验丰富的教学设计师，请根据以下教学内容，设计一份高质量的教学 PPT 内容大纲。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：{subject} - {subject_desc}
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【教学设计原则】
1. **知识结构化和层次化**：按照"导入→新授→巩固→拓展→总结"的教学逻辑组织内容
2. **由浅入深、循序渐进**：从具体到抽象，从已知到未知，符合学生认知规律
3. **多元互动设计**：每 2-3 页设置一个互动环节（提问/讨论/游戏/竞赛）
4. **多感官参与**：结合视觉（图表）、听觉（朗读）、动觉（操作）多种学习方式
5. **形成性评价**：嵌入即时反馈的练习题，检测学习效果

【学科特色要求】
- 语文：注重朗读指导、字词积累、情感体验、文化熏陶
- 数学：注重概念理解、公式推导、变式训练、实际应用
- 英语：注重情境创设、听说领先、读写跟进、文化意识
- 科学/物理/化学/生物：注重实验探究、观察记录、数据分析、结论归纳
- 历史/政治/地理：注重时空观念、因果关系、材料分析、价值引领

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题（简洁明了，体现主题）",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题（吸引学生注意）",
            "content": ["要点 1（简洁、关键词）", "要点 2（配合图示说明）"],
            "interaction": "互动设计（如适用）",
            "mnemonic": "记忆口诀/助记方法（如适用）"
        }}
    ],
    "summary": "本节课的核心要点总结（1-2 句话）",
    "key_points": ["重点 1", "重点 2", "重点 3"]
}}

【PPT 页面结构建议】
1. **封面页**：课题名称 + 年级学科 + 授课教师
2. **目录页**：清晰展示本节课的学习脉络
3. **情境导入页**（1 页）：创设情境、激发兴趣、引出课题
4. **新知讲解页**（3-5 页）：
   - 概念讲解：定义 + 特征 + 示例
   - 原理探究：推导过程 + 关键步骤 + 注意事项
   - 方法总结：解题思路 + 技巧点拨 + 易错警示
5. **互动问答页**（2-3 页）：
   - 基础提问：回顾刚学的知识点
   - 拓展讨论：联系生活实际
   - 思辨问题：培养批判性思维
6. **课堂练习页**（2-3 页）：
   - 基础题：巩固基础知识
   - 提升题：训练思维能力
   - 拓展题：挑战学有余力的学生
7. **总结回顾页**：知识框架 + 重点回顾 + 课后思考

【质量要求】
- 每页内容精炼，不超过 5 个要点
- 语言通俗易懂，符合年级认知水平
- 互动设计有趣味性，能调动学生积极性
- 练习题有梯度，兼顾不同层次学生
- 记忆口诀朗朗上口，便于学生记忆

请生成符合以上要求的教学 PPT 内容，确保教学逻辑清晰、互动设计丰富、学习效果显著。"""

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

        prompt = f"""你是一位经验丰富的英语教师，请根据以下英语教学内容，设计一份高质量的英语教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：英语
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【英语教学原则】
1. **情境创设**：在真实或模拟的情境中呈现语言，让学生在语境中理解和使用
2. **听说领先**：先听后说，先输入后输出，遵循语言习得规律
3. **词不离句**：单词教学要放在句子和语篇中，避免孤立记忆
4. **循环复现**：设计多种活动让学生反复接触目标语言
5. **文化渗透**：适时介绍英语国家的文化背景，培养跨文化意识

【英语学科特色要求】
1. **单词卡片页**：单词 + 音标 + 中文释义 + 英文例句 + 配图建议
2. **语法结构图解页**：用表格/树状图/流程图展示语法规则
3. **情景对话页**：生成贴合课文主题的对话示例（2-4 轮对话）
4. **课文要点分析页**：段落大意、关键句型、常用表达、写作手法
5. **课堂互动页**：填空、选择、连线、角色扮演等练习形式

【PPT 结构建议】
1. **封面页**：Unit/Topic + Grade + Teacher
2. **Learning Objectives**（1 页）：本节课的学习目标
3. **Warm-up/Lead-in**（1 页）：热身活动/导入
4. **Vocabulary Learning**（3-4 页）：单词呈现、操练、运用
5. **Grammar Focus**（2-3 页）：规则呈现、结构分析、操练活动
6. **Dialogue/Text Study**（2-3 页）：听/读理解、语言点、跟读模仿
7. **Practice/Production**（2-3 页）：控制性练习、半控制练习、自由表达
8. **Summary & Homework**（1 页）：总结 + 作业

请生成内容，确保学生能够在情境中学习、在运用中掌握。"""

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