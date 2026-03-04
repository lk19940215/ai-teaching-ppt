"""
英语学科提示词策略
专为英语教学设计的提示词模板
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy


class EnglishPromptStrategy(SubjectPromptStrategy):
    """
    英语学科提示词策略

    将原有的 generate_for_english 逻辑迁移至此，专为英语教学设计的提示词模板
    """

    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None
    ) -> str:
        """
        构建英语学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)

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

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题（单元/主题名称）",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点 1", "页面内容要点 2"],
            "vocabulary": [{{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}}],
            "grammar": "语法规则说明（如适用）",
            "dialogue": "对话内容（如适用）",
            "exercise": "练习题描述（如适用）"
        }}
    ],
    "vocabulary_list": [{{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}}],
    "grammar_points": ["语法点 1", "语法点 2"],
    "summary": "整体内容总结"
}}

请生成内容，确保学生能够在情境中学习、在运用中掌握。"""

        return prompt

    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建英语学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/单词学习页/语法讲解页/情景对话页/课文分析页/课堂练习页/总结回顾页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    "vocabulary": [{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}],
                    "grammar": "语法规则说明（如适用）",
                    "dialogue": "对话内容（如适用）",
                    "exercise": "练习题描述（如适用）"
                }
                for _ in range(slide_count)
            ],
            "vocabulary_list": [{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}],
            "grammar_points": ["语法点 1", "语法点 2"],
            "summary": "整体内容总结"
        }

    def get_page_types(self) -> List[str]:
        """
        获取英语学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "单词学习页",
            "语法讲解页",
            "情景对话页",
            "课文分析页",
            "课堂练习页",
            "总结回顾页",
        ]
