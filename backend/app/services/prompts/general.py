"""
通用学科提示词策略
适用于大多数学科的默认提示词模板
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin


class GeneralPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    通用学科提示词策略

    适用于语文、数学、科学等大多数学科的默认提示词模板
    继承 CognitiveLoadMixin 提供认知负荷优化约束
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
        构建通用学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        subject_desc = self.get_subject_description(subject)
        max_points = self.get_max_points_for_grade(grade)

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

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 图文并茂：图示与文字说明应在同一页呈现
- 复杂内容分步展示：拆分为 2-3 页逐步展开
- 避免冗余：文字不要重复图示已表达的信息

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
- 每页内容精炼，不超过{max_points}个要点
- 语言通俗易懂，符合年级认知水平
- 互动设计有趣味性，能调动学生积极性
- 练习题有梯度，兼顾不同层次学生
- 记忆口诀朗朗上口，便于学生记忆

请生成符合以上要求的教学 PPT 内容，确保教学逻辑清晰、互动设计丰富、学习效果显著。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建通用学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/知识点讲解页/互动问答页/课堂练习页/总结回顾页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    "interaction": "互动环节描述（如适用）",
                    "exercise": {
                        "question": "练习题目",
                        "answer": "参考答案",
                        "analysis": "解析说明",
                        "bloom_level": "认知层级（remember/understand/apply/analyze/evaluate/create）",
                        "difficulty": "难度星级（1-3 星）"
                    },
                    "mnemonic": "记忆口诀或助记方法（如适用）"
                }
                for _ in range(slide_count)
            ],
            "summary": "整体内容总结",
            "key_points": ["重点 1", "重点 2", "重点 3"]
        }

    def get_page_types(self) -> List[str]:
        """
        获取通用学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "知识点讲解页",
            "互动问答页",
            "课堂练习页",
            "总结回顾页",
            "图示页",
            "表格页",
            "对比分析页",
        ]
