"""
数学学科提示词策略
专为数学教学设计的提示词模板
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin


class MathPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    数学学科提示词策略

    专为数学教学设计，包含：
    1. 概念引入：从直观到抽象，用生活实例引入数学概念
    2. 公式推导：逐步标注推导过程，注明每步依据
    3. 例题精讲：审题→分析→解题→反思四步法
    4. 变式训练：同一方法不同情境，由浅入深梯度练习
    5. 易错警示：常见错误类型 + 正确方法对比
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
        构建数学学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的数学教师，请根据以下数学教学内容，设计一份高质量的数学教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：数学
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【数学教学原则】
1. **具体到抽象**：从生活实例/直观模型引入，逐步过渡到抽象符号和公式
2. **循序渐进**：由浅入深、由易到难，遵循知识的逻辑顺序和学生认知规律
3. **数形结合**：善于用图形、线段图、数轴等直观工具辅助理解
4. **变式教学**：通过一题多解、一题多变、多题归一，培养学生思维灵活性
5. **反思提升**：解题后引导学生回顾思路、总结方法、提炼数学思想

【数学专属教学要求】
1. **概念引入页**：
   - 生活情境/实际问题导入
   - 直观模型展示（图形、实物、数轴等）
   - 抽象出数学概念/定义
   - 概念的本质特征和关键属性
   - 正反例辨析（什么是/什么不是）

2. **公式推导页**：
   - 推导的起点（已知条件/已有知识）
   - 推导的步骤（每一步清晰标注）
   - 每步的依据（定义/公理/定理）
   - 最终结论（公式/法则）
   - 公式的理解要点和记忆方法

3. **例题精讲页**（四步法）：
   - 【审题】：提取已知条件、明确求解目标、识别题型
   - 【分析】：寻找解题思路、联想相关方法、制定解题策略
   - 【解题】：规范书写过程、关键步骤展示、易错点提醒
   - 【反思】：一题多解、变式拓展、方法总结、数学思想提炼

4. **变式训练页**：
   - 基础变式：改变数字/图形，保持方法不变
   - 情境变式：改变问题背景，本质相同
   - 逆向变式：条件结论互换
   - 综合变式：多个知识点融合

5. **易错警示页**：
   - 常见错误类型展示（计算错误/概念混淆/步骤遗漏/单位遗忘等）
   - 错误原因分析
   - 正确解法对比
   - 预防策略和检查方法

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：知识技能、数学思考、问题解决、情感态度
3. **情境导入**（1 页）：生活实例/实际问题/数学故事引入
4. **探究新知**（4-6 页）：
   - 概念形成（2 页）：直观感知→抽象概括
   - 公式推导（2 页）：逐步推导→理解记忆
   - 例题示范（2 页）：四步法精讲
5. **变式训练**（2-3 页）：梯度练习、巩固提升
6. **易错警示**（1 页）：常见错误 + 正确对比
7. **课堂小结**（1 页）：知识框架 + 思想方法 + 课后思考

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 数形结合：图形与文字说明应在同一页呈现
- 复杂推导分步展示：拆分为 2-3 页逐步展开
- 避免冗余：图形已表达的信息不用文字重复

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "concept": {{"name": "概念名", "definition": "定义", "features": ["特征 1", "特征 2"], "examples": ["正例", "反例"]}},
            "formula_derivation": {{"name": "公式名", "steps": [{{"step": "步骤 1", "reason": "依据"}}], "result": "最终公式", "tips": "理解要点"}},
            "example_problem": {{"title": "例题", "given": "已知条件", "target": "求解目标", "analysis": "思路分析", "solution": ["解题步骤 1", "解题步骤 2"], "reflection": "反思总结", "alternative_methods": ["解法 2"]}},
            "variation_practice": [{{"type": "变式类型", "problem": "题目", "hint": "提示"}}],
            "common_mistakes": [{{"mistake": "错误示例", "reason": "错误原因", "correct": "正确方法"}}]
        }}
    ],
    "formulas": ["公式 1", "公式 2"],
    "key_points": ["重点 1", "重点 2"],
    "mathematical_thinking": ["数学思想 1", "数学思想 2"],
    "summary": "总结"
}}

请生成内容，确保学生在知识技能、数学思维和解决问题能力方面都能得到提升。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建数学学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/概念引入页/公式推导页/例题讲解页/变式训练页/易错警示页/课堂练习页/总结回顾页/图示页/表格页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 概念引入页字段
                    "concept": {
                        "name": "概念名称",
                        "definition": "定义（文字表述）",
                        "symbolic_form": "符号表示（如适用）",
                        "features": ["本质特征 1", "本质特征 2"],
                        "visual_model": "直观模型描述（图形/数轴等）",
                        "positive_examples": ["正例 1", "正例 2"],
                        "negative_examples": ["反例 1", "反例 2"],
                        "common_misconceptions": ["常见误解"]
                    },
                    # 公式推导页字段
                    "formula_derivation": {
                        "name": "公式/定理名称",
                        "prerequisites": ["前置知识 1", "前置知识 2"],
                        "steps": [
                            {
                                "step_number": 1,
                                "content": "步骤 1 的内容",
                                "reason": "依据（定义/公理/定理）",
                                "visual": "配图说明（如适用）"
                            }
                        ],
                        "result": "最终公式/结论",
                        "understanding_tips": "理解要点和记忆方法",
                        "application_scope": "适用范围和条件"
                    },
                    # 例题讲解页字段（四步法）
                    "example_problem": {
                        "title": "例题标题",
                        "given": "已知条件",
                        "target": "求解目标",
                        "analysis": "思路分析（如何想到这个解法）",
                        "solution": ["解题步骤 1", "解题步骤 2", "解题步骤 3"],
                        "key_steps": ["关键步骤说明"],
                        "common_errors": ["易错点提醒"],
                        "reflection": "反思总结（方法提炼、数学思想）",
                        "alternative_methods": ["解法 2 的思路"],
                        "variation": "变式拓展（改变条件/结论后如何解）"
                    },
                    # 变式训练页字段
                    "variation_practice": [
                        {
                            "type": "变式类型（基础变式/情境变式/逆向变式/综合变式）",
                            "problem": "题目内容",
                            "difficulty": "难度星级（1-3 星）",
                            "hint": "解题提示",
                            "connection": "与原题的联系"
                        }
                    ],
                    # 易错警示页字段
                    "common_mistakes": [
                        {
                            "mistake_type": "错误类型（计算错误/概念混淆/步骤遗漏/单位遗忘）",
                            "mistake_example": "错误示例",
                            "reason_analysis": "错误原因分析",
                            "correct_method": "正确解法",
                            "prevention_strategy": "预防策略"
                        }
                    ]
                }
                for _ in range(slide_count)
            ],
            "formulas": [
                {
                    "name": "公式名称",
                    "content": "公式内容",
                    "conditions": "适用条件",
                    "meaning": "含义解释"
                }
            ],
            "key_points": ["重点 1", "重点 2", "重点 3"],
            "mathematical_thinking": [
                "数学思想方法 1（如：数形结合、分类讨论、转化与化归）",
                "数学思想方法 2"
            ],
            "summary": "整体内容总结（知识 + 方法 + 思想）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取数学学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "概念引入页",        # 数学专属：直观→抽象
            "公式推导页",        # 数学专属：逐步标注
            "例题讲解页",        # 数学专属：四步法（审题→分析→解题→反思）
            "变式训练页",        # 数学专属：梯度练习
            "易错警示页",        # 数学专属：错误 vs 正确对比
            "课堂练习页",
            "总结回顾页",
            "图示页",            # 线段图、数轴、几何图形等
            "表格页",            # 数据整理、对比分析
            "对比分析页",        # 概念对比、解法对比
        ]
