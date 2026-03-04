"""
认知负荷优化提示词模块（Phase 3 占位）

基于 Mayer 多媒体学习理论的提示词优化
目前为占位实现，后续将填充完整的认知负荷约束逻辑
"""

from typing import Dict, Any, List, Optional
from .base import CognitiveLoadMixin, SubjectPromptStrategy


class CognitivePromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin):
    """
    认知负荷优化提示词策略（占位）

    Phase 3 将实现：
    1. 聚焦要义原则：根据年级设定每页最大要点数
    2. 空间邻近原则：提示词要求图示与文字说明必须在同一页
    3. 切块呈现原则：复杂概念自动分 2-3 页逐步展开
    4. 冗余控制原则：提示词要求避免文字重复图示已表达的信息
    """

    def __init__(self):
        """初始化认知负荷策略"""
        pass

    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None
    ) -> str:
        """
        构建认知负荷优化的提示词（占位实现）

        TODO: Phase 3 实现完整的认知负荷约束
        """
        grade_desc = self.get_grade_description(grade)
        subject_desc = self.get_subject_description(subject)
        max_points = self.get_max_points_for_grade(grade)

        # 基础提示词（占位）
        prompt = f"""你是一位精通认知心理学的教学设计师，请根据以下教学内容，设计一份符合学生认知规律的 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：{subject} - {subject_desc}
- 幻灯片数量：{slide_count} 页

【认知负荷优化原则】（Phase 3 实现）
1. **聚焦要义原则**：每页内容不超过{max_points}个要点，去除冗余信息
2. **空间邻近原则**：相关的文字和图示应在同一页呈现
3. **时间邻近原则**：相关的声音和画面应同时呈现
4. **切块呈现原则**：复杂内容分步展示，避免一次性呈现过多信息
5. **冗余控制原则**：避免用文字重复图示已表达的信息

【PPT 页面结构建议】
- 封面页：课题名称 + 年级学科
- 目录页：学习脉络概览
- 情境导入页：创设情境、激发兴趣
- 新知讲解页：概念讲解、原理探究
- 互动问答页：提问、讨论
- 课堂练习页：基础题、提升题、拓展题
- 总结回顾页：知识框架 + 重点回顾

请生成符合认知负荷优化原则的教学 PPT 内容。"""

        # 应用认知负荷约束（占位调用）
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        return prompt

    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建认知负荷优化的输出结构（占位实现）
        """
        return {
            "title": "PPT 标题",
            "slides": [
                {
                    "page_type": "页面类型",
                    "title": "页面标题",
                    "content": ["页面内容要点（不超过 5 个）"],
                    "visual_suggestion": "图示建议（如适用）",
                    "interaction": "互动设计（如适用）"
                }
                for _ in range(slide_count)
            ],
            "summary": "整体内容总结",
            "key_points": ["重点 1", "重点 2", "重点 3"]
        }

    def get_page_types(self) -> List[str]:
        """
        获取认知负荷优化策略支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "知识点讲解页",
            "图示页",
            "互动问答页",
            "课堂练习页",
            "总结回顾页",
        ]
