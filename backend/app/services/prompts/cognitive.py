"""
认知负荷优化提示词模块

基于 Mayer 多媒体学习理论的提示词优化
实现 5 大核心原则：聚焦要义、空间邻近、时间邻近、切块呈现、冗余控制
"""

from typing import Dict, Any, List, Optional
from .base import (
    CognitiveLoadMixin,
    SubjectPromptStrategy,
    BloomTaxonomyMixin,
    QuestionChainMixin,
    MetacognitivePromptMixin,
)


class CognitivePromptStrategy(
    SubjectPromptStrategy,
    CognitiveLoadMixin,
    BloomTaxonomyMixin,
    QuestionChainMixin,
    MetacognitivePromptMixin
):
    """
    认知负荷优化提示词策略

    基于 Mayer 多媒体学习理论，提供通用的认知负荷优化约束：
    1. 聚焦要义原则：根据年级设定每页最大要点数
    2. 空间邻近原则：提示词要求图示与文字说明必须在同一页
    3. 切块呈现原则：复杂概念自动分 2-3 页逐步展开
    4. 冗余控制原则：提示词要求避免文字重复图示已表达的信息
    5. 时间邻近原则：讲解与画面同步呈现

    整合问题链教学法与元认知提示系统：
    - 问题链：是什么 → 为什么 → 怎么用 → 如果...会怎样 → 还有其他方法吗
    - 元认知提示：想一想 / 试着解释 / 和之前学的有什么关系
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

【先行组织者策略 - 基于 Ausubel 有意义学习理论】

在每个**新概念**首次出现前，必须用 1 页"概念桥接页"连接学生已有知识：

1. **桥接结构**：你已经知道 X → 今天学习 Y → X 和 Y 的关系是...
2. **桥接方式**（三选一）：
   - **类比桥接**：用学生熟悉的生活实例类比新概念（如：水流类比电流）
   - **回顾桥接**：回顾已学过的相关旧知识（如：复习分数再学小数）
   - **经验桥接**：连接学生的生活经验（如：购物经历引入负数）
3. **输出格式**：在桥接页的 JSON 中包含 `bridge_config` 字段：
   ```json
   {
     "page_type": "概念桥接页",
     "title": "从 X 到 Y",
     "known_concept": "学生已知的概念 X",
     "new_concept": "今天要学的概念 Y",
     "bridge_type": "类比/回顾/经验",
     "bridge_content": "桥接内容的具体描述",
     "connection": "X 和 Y 的关系说明"
   }
   ```

【脚手架渐撤策略 - 基于 Vygotsky 最近发展区理论】

练习设计必须体现"支架渐撤"的递进结构，帮助学生从依赖走向独立：

1. **三阶段递进**：
   - **阶段 1（完整示范）**：提供完整解题步骤和详细提示，学生模仿学习
   - **阶段 2（部分提示）**：只给关键提示，学生补全中间步骤
   - **阶段 3（独立完成）**：只给问题，学生独立完成

2. **输出格式**：在"课堂练习页"的 JSON 中包含 `scaffold_stage` 字段：
   ```json
   {
     "page_type": "课堂练习页",
     "scaffold_stage": 1,  // 1=完整示范，2=部分提示，3=独立完成
     "exercises": [
       {
         "question": "题目",
         "hint": "阶段 1/2 时提供提示，阶段 3 为空",
         "steps": "阶段 1 时提供完整步骤，阶段 2/3 为空",
         "bloom_level": "认知层级"
       }
     ]
   }
   ```

3. **年级适配规则**：
   - 小学低年级（1-3）：以阶段 1 为主（70%），少量阶段 2（30%）
   - 小学高年级（4-6）：阶段 1（40%）、阶段 2（40%）、阶段 3（20%）
   - 初中（7-9）：阶段 1（20%）、阶段 2（50%）、阶段 3（30%）
   - 高中（10-12）：阶段 2（40%）、阶段 3（60%）

请生成符合认知负荷优化原则、包含先行组织者和脚手架策略的教学 PPT 内容，确保学生能够有效吸收和理解知识。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用注意力节奏约束
        prompt += self.get_attention_rhythm_constraints(grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        # 应用问题链教学法约束
        prompt += self.get_question_chain_prompt_section(grade, subject)

        # 应用元认知提示约束
        prompt += self.get_metacognitive_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建认知负荷优化的输出结构

        包含认知负荷相关的字段：
        - cognitive_load_level: 认知负荷等级（low/medium/high）
        - layout_suggestion: 布局建议
        - chunk_info: 分块信息（如属于某个复杂概念的第几步）
        - bridge_config: 先行组织者桥接配置（概念桥接页专用）
        - scaffold_stage: 脚手架阶段（练习页专用）
        - meta_prompt: 元认知提示（问题链与自我反思触发点）
        """
        base_schema = {
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
                    "bridge_config": {
                        "known_concept": "学生已知的概念 X（概念桥接页专用）",
                        "new_concept": "今天要学的概念 Y（概念桥接页专用）",
                        "bridge_type": "类比/回顾/经验（概念桥接页专用）",
                        "bridge_content": "桥接内容的具体描述（概念桥接页专用）",
                        "connection": "X 和 Y 的关系说明（概念桥接页专用）"
                    },
                    "scaffold_stage": "脚手架阶段：1=完整示范，2=部分提示，3=独立完成（练习页专用）",
                    "bloom_level": "认知层级：remember/understand/apply/analyze/evaluate/create",
                    "question_chain": {
                        "level": "问题链层级：what/why/how/what_if/what_else",
                        "question": "递进式问题内容"
                    },
                    "meta_prompt": {
                        "type": "元认知提示类型：reflect/connect/predict/evaluate/extend/monitor",
                        "icon": "图标符号：💭/🔗/🔮/✓/🚀/📊",
                        "content": "提示语内容",
                        "position": "插入位置：before_content/after_content/side_note",
                        "visual_style": "视觉样式：thought_bubble/highlight_box/sidebar"
                    },
                    "interaction": "互动设计（如适用）"
                }
                for _ in range(slide_count)
            ],
            "summary": "整体内容总结",
            "key_points": ["重点 1", "重点 2", "重点 3"]
        }

        return base_schema

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
            "概念桥接页",        # 先行组织者：连接新旧知识
            "公式推导页",        # 认知负荷优化：分步展示
            "对比分析页",        # 认知负荷优化：对照布局
            "实验步骤页",        # 认知负荷优化：分块呈现
            "时间轴页",          # 认知负荷优化：时序清晰
            "思考气泡页",        # 元认知提示：反思/连接/预测/评估/拓展/监控
            "问题链递进页",      # 问题链教学法：是什么→为什么→怎么用→如果→还有
            "反思 checkpoint 页", # 元认知提示：学习 checkpoints，促进自我监控
        ]
