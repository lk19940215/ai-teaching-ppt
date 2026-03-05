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
    包含情境创设自动生成支持（feat-039）
    """

    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None,
        difficulty_level: str = "unified"
    ) -> str:
        """
        构建通用学科的 PPT 内容生成提示词

        Args:
            difficulty_level: 教学层次（unified/basic/intermediate/advanced）
        """
        grade_desc = self.get_grade_description(grade)
        subject_desc = self.get_subject_description(subject)
        max_points = self.get_max_points_for_grade(grade)

        # 难度分层策略（feat-040）
        difficulty_strategy = {
            "unified": "统一模式：生成包含基础（1 星）、提高（2 星）、拓展（3 星）三个难度的混合练习，每道题标注难度星级",
            "basic": "基础版：只生成基础难度（1 星）练习，侧重基本概念回忆和简单应用",
            "intermediate": "提高版：只生成中等难度（2 星）练习，侧重知识理解和综合应用",
            "advanced": "拓展版：只生成高难度（3 星）练习，侧重分析评价和创造迁移"
        }

        # 年级差异化的情境创设策略
        if grade in ["1", "2", "3", "4"]:
            scenario_strategy = "低年级情境创设：使用童话故事、动画人物、趣味游戏等贴近儿童生活的场景，语言生动有趣，多用拟人化表达"
        elif grade in ["5", "6", "7", "8"]:
            scenario_strategy = "中年级情境创设：使用校园生活、社会实践、科普探索等场景，联系学生实际经验，激发探究兴趣"
        else:
            scenario_strategy = "高年级情境创设：使用科研探索、职业体验、社会热点等场景，注重知识迁移和实际应用，培养学科素养"

        # 学科差异化的情境创设策略
        scenario_templates = {
            "math": "数学情境：购物消费（计算折扣）、体育运动（数据统计）、建筑设计（几何图形）、旅行规划（路程时间）",
            "english": "英语情境：旅行游记（问路点餐）、校园生活（交友对话）、文化交流（节日习俗）、职场体验（面试工作）",
            "chinese": "语文情境：生活实例（亲情友情）、故事典故（历史人物）、自然景观（四季变化）、文化传承（传统节日）",
            "physics": "物理情境：游乐场（力学现象）、交通工具（运动规律）、家用电器（电学原理）、自然现象（光声热电）",
            "chemistry": "化学情境：厨房化学（食物变化）、日用品（清洁剂成分）、环境保护（污染处理）、工业生产（化学反应）",
            "biology": "生物情境：校园植物（分类观察）、健康生活（营养搭配）、生态系统（食物链）、生命科学（细胞遗传）",
            "history": "历史情境：历史现场（穿越体验）、人物访谈（对话古人）、史料探究（文物解读）、时空对比（古今变化）",
            "politics": "政治情境：社会热点（时事分析）、道德两难（价值判断）、政策解读（民生措施）、法律案例（权利义务）",
            "geography": "地理情境：虚拟旅行（各地风光）、环境考察（地貌气候）、资源调查（矿产能源）、区域规划（城市发展）",
        }
        scenario_hint = scenario_templates.get(subject.lower(), "通用情境：联系学生已有经验，创设真实或模拟的学习场景")

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

【差异化教学要求（feat-040）】
当前模式：{difficulty_level} - {difficulty_strategy.get(difficulty_level, "")}

**难度标注规范**：
- 基础题（1 星★）：直接回忆概念、模仿例题、单一知识点应用
- 提高题（2 星★★）：理解原理、知识综合、变式应用
- 拓展题（3 星★★★）：分析评价、创造迁移、跨知识综合

**输出要求**：
- 在"课堂练习页"和"巩固练习页"中，每道题必须包含 `difficulty` 字段（basic/intermediate/advanced）
- 统一模式下：3 种难度都要有，比例约 50%/30%/20%
- 分层模式下：只生成指定难度的题目

【学科特色要求】
- 语文：注重朗读指导、字词积累、情感体验、文化熏陶
- 数学：注重概念理解、公式推导、变式训练、实际应用
- 英语：注重情境创设、听说领先、读写跟进、文化意识
- 科学/物理/化学/生物：注重实验探究、观察记录、数据分析、结论归纳
- 历史/政治/地理：注重时空观念、因果关系、材料分析、价值引领

【情境创设自动生成要求（feat-039）】

**核心目标**：根据知识点自动生成贴近学生生活的情境导入，激发学习兴趣和动机

**年级差异化策略**：
- {scenario_strategy}

**学科差异化模板**：
- {scenario_hint}

**情境导入页设计要求**：
1. **情境描述（scenario_description）**：用 2-3 句话创设具体场景，让学生有代入感
2. **引导问题（guiding_question）**：提出 1 个核心问题，引发学生思考和探究欲望
3. **视觉建议（visual_suggestion）**：描述适合的画面或图示，帮助教师准备素材
4. **情境类型（scenario_type）**：从以下选择——生活实例、童话故事、动画人物、校园场景、社会实践、科研探索、职业体验、购物消费、体育运动、旅行游记、游乐场、交通工具

**输出格式要求**：
在第一个内容页（情境导入页）中，必须包含 `scenario` 字段：
```json
{{
    "page_type": "情境导入页",
    "title": "吸引人的标题",
    "scenario": {{
        "scenario_description": "具体的情境描述（2-3 句话）",
        "guiding_question": "引导性问题",
        "visual_suggestion": "视觉素材建议",
        "scenario_type": "情境类型"
    }}
}}
```

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
            "scenario": {{"scenario_description": "情境描述", "guiding_question": "引导问题", "visual_suggestion": "视觉建议", "scenario_type": "情境类型"}},
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
3. **情境导入页**（1 页）：创设情境、激发兴趣、引出课题（必须包含 scenario 字段）
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
- 情境导入有趣味性和真实性，能调动学生积极性
- 互动设计有启发性，引导学生主动思考
- 练习题有梯度，兼顾不同层次学生
- 记忆口诀朗朗上口，便于学生记忆

请生成符合以上要求的教学 PPT 内容，确保教学逻辑清晰、情境导入生动、互动设计丰富、学习效果显著。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建通用学科的输出结构定义

        Args:
            slide_count: 幻灯片数量
            difficulty_level: 教学层次（unified/basic/intermediate/advanced）
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/情境导入页/知识点讲解页/互动问答页/课堂练习页/总结回顾页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 情境导入页字段（feat-039）
                    "scenario": {
                        "scenario_description": "情境描述（2-3 句话，贴近学生生活）",
                        "guiding_question": "引导性问题（引发思考）",
                        "visual_suggestion": "视觉素材建议",
                        "scenario_type": "情境类型（生活实例/童话故事/动画人物/校园场景/社会实践/科研探索/职业体验/购物消费/体育运动/旅行游记/游乐场/交通工具）"
                    },
                    "interaction": "互动环节描述（如适用）",
                    "exercise": {
                        "question": "练习题目",
                        "difficulty": "难度（basic/intermediate/advanced，feat-040 差异化教学）",
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
            "情境导入页",        # 情境创设自动生成（feat-039）
            "知识点讲解页",
            "互动问答页",
            "课堂练习页",
            "总结回顾页",
            "图示页",
            "表格页",
            "对比分析页",
        ]
