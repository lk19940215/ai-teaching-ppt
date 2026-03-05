"""
认知负荷优化提示词模块

基于 Mayer 多媒体学习理论的提示词优化
实现 5 大核心原则：聚焦要义、空间邻近、时间邻近、切块呈现、冗余控制
"""

from typing import Dict, Any, List, Optional
from .base import CognitiveLoadMixin, SubjectPromptStrategy, BloomTaxonomyMixin


class CognitivePromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    认知负荷优化提示词策略

    基于 Mayer 多媒体学习理论，提供通用的认知负荷优化约束：
    1. 聚焦要义原则：根据年级设定每页最大要点数
    2. 空间邻近原则：提示词要求图示与文字说明必须在同一页
    3. 切块呈现原则：复杂概念自动分 2-3 页逐步展开
    4. 冗余控制原则：提示词要求避免文字重复图示已表达的信息
    5. 时间邻近原则：讲解与画面同步呈现
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
        构建认知负荷优化的提示词

        Args:
            content: 教学内容
            grade: 年级
            subject: 学科
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）

        Returns:
            认知负荷优化后的提示词
        """
        grade_desc = self.get_grade_description(grade)
        subject_desc = self.get_subject_description(subject)
        max_points = self.get_max_points_for_grade(grade)
        chunk_size = self.get_chunk_size_for_grade(grade)

        # 基础提示词
        prompt = f"""你是一位精通认知心理学的教学设计师，请根据以下教学内容，设计一份符合学生认知规律的 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：{subject} - {subject_desc}
- 幻灯片数量：{slide_count} 页

【认知负荷优化原则 - 基于 Mayer 多媒体学习理论】

1. **聚焦要义原则**：每页内容不超过{max_points}个要点，去除冗余信息
2. **空间邻近原则**：相关的文字和图示应在同一页呈现，避免学生来回翻看
3. **切块呈现原则**：复杂内容分步展示，每个复杂概念拆分为{chunk_size}页逐步展开
4. **冗余控制原则**：避免用文字重复图示已表达的信息
5. **时间邻近原则**：讲解语音与对应画面应同步呈现

【布局建议】
- 公式推导页：上一步骤 + 下一步骤分两栏展示，箭头连接表示推导关系
- 语法树页：左侧原句 + 右侧树状图对照
- 实验步骤页：顶部步骤说明 + 底部操作图示
- 时间轴页：水平时间轴贯穿页面，事件标注在轴上下方
- 对比分析页：左右分栏对比，中间用虚线分隔
- 概念引入页：顶部生活实例图 + 底部抽象概念定义

【PPT 页面结构建议】
1. **封面页**：课题名称 + 年级学科
2. **目录页**：学习脉络概览
3. **情境导入页**：创设情境、激发兴趣
4. **新知讲解页**：概念讲解、原理探究（注意分块呈现）
5. **互动问答页**：提问、讨论
6. **课堂练习页**：基础题、提升题、拓展题
7. **总结回顾页**：知识框架 + 重点回顾

请生成符合认知负荷优化原则的教学 PPT 内容，确保学生能够有效吸收和理解知识。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用注意力节奏约束
        prompt += self.get_attention_rhythm_constraints(grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建认知负荷优化的输出结构

        包含认知负荷相关的字段：
        - cognitive_load_level: 认知负荷等级（low/medium/high）
        - layout_suggestion: 布局建议
        - chunk_info: 分块信息（如属于某个复杂概念的第几步）
        """
        return {
            "title": "PPT 标题",
            "cognitive_load_config": {
                "max_points_per_slide": "每页最大要点数",
                "chunk_size": "复杂概念分块大小",
                "layout_strategy": "布局策略"
            },
            "slides": [
                {
                    "page_type": "页面类型",
                    "title": "页面标题",
                    "content": ["页面内容要点（不超过 5 个）"],
                    "visual_suggestion": "图示建议（如适用）",
                    "layout": "布局方式（如：左图右文/上图下文/对照式）",
                    "chunk_info": {
                        "is_part_of_complex": "是否属于复杂概念的一部分",
                        "part_number": "第几步（如适用）",
                        "total_parts": "总共几步（如适用）",
                        "concept_name": "所属复杂概念名称（如适用）"
                    },
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
            "概念引入页",        # 认知负荷优化：直观→抽象
            "公式推导页",        # 认知负荷优化：分步展示
            "对比分析页",        # 认知负荷优化：对照布局
            "实验步骤页",        # 认知负荷优化：分块呈现
            "时间轴页",          # 认知负荷优化：时序清晰
        ]
