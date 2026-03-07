"""
理科学科提示词策略（物理/化学/生物）
专为理科实验探究设计的提示词模板
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin


class PhysicsPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    物理学科提示词策略

    专为物理教学设计，包含：
    1. 实验设计：探究目的、器材准备、步骤设计
    2. 现象观察：记录实验现象、描述变化过程
    3. 数据分析：处理实验数据、发现规律
    4. 归纳规律：从实验结论提炼物理规律
    5. 应用迁移：联系实际、解决物理问题
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
        构建物理学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的物理教师，请根据以下物理教学内容，设计一份高质量的物理教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：物理
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【物理教学原则】
1. **实验探究**：通过实验观察→数据分析→归纳规律的探究过程学习物理
2. **从生活走向物理**：从生活现象入手，提炼物理本质
3. **从物理走向社会**：将物理知识应用于解决实际问题
4. **重视科学思维**：培养观察、比较、分析、综合、抽象、概括能力
5. **强调科学方法**：控制变量法、转换法、等效替代法、理想模型法等

【物理专属教学要求】
1. **实验设计页**：
   - 探究目的（研究什么问题）
   - 实验器材（需要哪些器材）
   - 实验步骤（如何操作）
   - 注意事项（安全提醒、操作要点）
   - 数据记录表格设计

2. **现象观察页**：
   - 实验前状态描述
   - 实验过程现象记录
   - 实验后状态变化
   - 关键现象特写/放大

3. **数据分析页**：
   - 原始数据呈现（表格）
   - 数据处理方法（计算/图像）
   - 数据变化规律发现
   - 误差分析

4. **规律归纳页**：
   - 从实验数据提炼规律
   - 用文字表述规律
   - 用公式表达规律
   - 规律的适用条件

5. **应用迁移页**：
   - 生活中的物理现象解释
   - 物理知识的技术应用
   - 相关物理问题求解

【PPT 结构建议】
n【错题分析要求（feat-041 智能错题分析）- 物理学科】

1. **常见错误类型**：
   - 单位换算：单位忘记转换、单位书写错误
   - 公式套用：公式选择错误、适用条件不清楚
   - 实验操作：仪器使用错误、读数方法不对
   - 受力分析：力的方向判断错误、遗漏力
   - 图像理解：坐标轴含义混淆、斜率/面积物理意义理解错误

2. **错题分析页设计要求**：
   - 错误示例：展示学生常见错误解答
   - 错误原因：分析物理概念或方法理解偏差
   - 正确解法：给出规范的解题过程
   - 预防策略：如何建立正确的物理思维

3. **输出格式要求**：
   ```json
   {{
     "page_type": "错题分析页",
     "title": "易错警示",
     "common_mistakes": [
       {{
         "mistake_type": "错误类型",
         "mistake_example": "错误示例",
         "reason": "错误原因分析",
         "correct_method": "正确解法",
         "prevention_strategy": "预防策略"
       }}
     ]
   }}
   ```
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：物理观念、科学思维、科学探究、科学态度
3. **情境导入**（1 页）：生活现象/物理实验视频/趣味问题引入
4. **实验探究**（4-6 页）：
   - 实验设计（1 页）
   - 现象观察（2 页）
   - 数据分析（2 页）
   - 规律归纳（1 页）
5. **知识应用**（2-3 页）：例题讲解、实际应用
6. **课堂小结**（1 页）：知识框架 + 科学方法 + 课后探究

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 图示与数据表格应在同一页呈现
- 复杂实验分步展示：拆分为 2-3 页逐步展开
- 避免冗余：图像已表达的信息不用文字重复

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "experiment_design": {{"purpose": "探究目的", "materials": ["器材 1", "器材 2"], "steps": ["步骤 1", "步骤 2"], "notes": ["注意事项"]}},
            "experiment_observation": {{"before": "实验前状态", "process": ["现象 1", "现象 2"], "after": "实验后状态", "key_points": ["关键现象"]}},
            "data_analysis": {{"raw_data": [["表头 1", "表头 2"], ["数据 1", "数据 2"]], "processing": "数据处理方法", "pattern": "发现的规律", "error_analysis": "误差分析"}},
            "physics_law": {{"name": "规律名称", "statement": "文字表述", "formula": "公式表达", "conditions": "适用条件"}},
            "application": {{"scenario": "应用场景", "problem": "实际问题", "solution": "解决方案"}}
        }}
    ],
    "experiments": ["实验 1", "实验 2"],
    "physics_laws": ["物理规律 1", "物理规律 2"],
    "scientific_methods": ["科学方法 1", "科学方法 2"],
    "summary": "总结"
}}

请生成内容，确保学生经历完整的科学探究过程，培养物理观念和科学思维。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建物理学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/实验设计页/现象观察页/数据分析页/规律归纳页/应用迁移页/图示页/表格页/对比分析页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 实验设计页字段
                    "experiment_design": {
                        "purpose": "探究目的/研究问题",
                        "hypothesis": "猜想与假设",
                        "materials": ["实验器材 1", "实验器材 2", "实验器材 3"],
                        "steps": [
                            {"step_number": 1, "description": "步骤 1 描述", "diagram_suggestion": "配图建议"}
                        ],
                        "notes": ["注意事项 1", "注意事项 2"],
                        "data_table_design": {"headers": ["表头 1", "表头 2"], "rows": 5}
                    },
                    # 现象观察页字段
                    "experiment_observation": {
                        "before": "实验前状态描述",
                        "process": ["现象 1", "现象 2", "现象 3"],
                        "after": "实验后状态描述",
                        "key_points": ["关键现象 1", "关键现象 2"],
                        "visual_suggestion": "视觉呈现建议（放大/特写/对比）"
                    },
                    # 数据分析页字段
                    "data_analysis": {
                        "raw_data": {
                            "headers": ["表头 1", "表头 2", "表头 3"],
                            "values": [["数据 1", "数据 2"], ["数据 3", "数据 4"]]
                        },
                        "processing_method": "数据处理方法（计算平均值/绘制图像/寻找比例关系）",
                        "pattern_discovered": "发现的数据规律",
                        "error_analysis": "误差来源分析"
                    },
                    # 规律归纳页字段
                    "physics_law": {
                        "name": "物理规律名称",
                        "statement": "文字表述",
                        "formula": "公式表达",
                        "symbol_explanation": {"symbol1": "解释 1", "symbol2": "解释 2"},
                        "conditions": "适用条件和范围",
                        "historical_background": "发现历史（可选）"
                    },
                    # 应用迁移页字段
                    "application": {
                        "scenario": "应用场景/生活实例",
                        "problem": "实际问题描述",
                        "solution": "用物理知识解决方案",
                        "extension": "拓展思考"
                    }
                }
                for _ in range(slide_count)
            ],
            "experiments": [
                {
                    "name": "实验名称",
                    "type": "演示实验/分组实验/探究实验",
                    "purpose": "实验目的"
                }
            ],
            "physics_laws": [
                {
                    "name": "规律名称",
                    "formula": "公式",
                    "application": "应用领域"
                }
            ],
            "scientific_methods": [
                "科学方法 1（如：控制变量法、转换法、等效替代法、理想模型法）",
                "科学方法 2"
            ],
            "summary": "整体内容总结（知识 + 方法 + 探究过程）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取物理学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "实验设计页",        # 物理专属：探究目的、器材、步骤
            "现象观察页",        # 物理专属：实验现象记录
            "数据分析页",        # 物理专属：数据处理、规律发现
            "规律归纳页",        # 物理专属：从实验提炼规律
            "应用迁移页",        # 物理专属：联系实际应用
            "图示页",            # 电路图、受力分析图、光路图等
            "表格页",            # 实验数据表、对比表
            "对比分析页",        # 不同条件下的对比
        ]


class ChemistryPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    化学学科提示词策略

    专为化学教学设计，包含：
    1. 实验步骤：仪器准备、操作流程、安全事项
    2. 反应现象：颜色变化、气体生成、沉淀产生
    3. 方程式：化学方程式书写、配平、条件标注
    4. 微观解释：分子/原子/离子层面的解释
    5. 元素周期律：元素性质递变规律
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
        构建化学学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的化学教师，请根据以下化学教学内容，设计一份高质量的化学教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：化学
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【化学教学原则】
1. **宏观辨识与微观探析**：从宏观现象理解微观本质
2. **变化观念与平衡思想**：理解化学变化的本质和规律
3. **证据推理与模型认知**：基于实验证据推理，建立模型
4. **实验探究与创新意识**：通过实验探究培养科学精神
5. **科学精神与社会责任**：认识化学对社会发展的贡献

【化学专属教学要求】
1. **实验步骤页**：
   - 实验目的
   - 仪器和药品
   - 操作步骤（详细、有序）
   - 安全注意事项（腐蚀性、毒性、易燃性）
   - 废弃物处理

2. **反应现象页**：
   - 反应前物质状态（颜色、状态、气味）
   - 反应过程现象（发光、发热、颜色变化、气体生成、沉淀产生）
   - 反应后产物状态
   - 现象描述要点

3. **化学方程式页**：
   - 反应物化学式
   - 生成物化学式
   - 配平过程
   - 反应条件标注
   - 方程式意义

4. **微观解释页**：
   - 分子/原子/离子模型
   - 微粒运动变化示意
   - 化学键的断裂与形成
   - 电子转移/共用

5. **元素周期律页**：
   - 元素在周期表中的位置
   - 原子结构示意图
   - 性质递变规律
   - 相似性和差异性

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：宏观辨识、微观探析、变化观念、实验探究
3. **情境导入**（1 页）：生活实例/化学魔术/趣味实验引入
4. **实验探究**（4-6 页）：
   - 实验设计（1 页）
   - 现象观察（2 页）
   - 方程式书写（1-2 页）
   - 微观解释（1 页）
5. **知识应用**（2-3 页）：性质应用、计算练习
6. **课堂小结**（1 页）：知识框架 + 思想方法

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点
- 微观模型与宏观现象应在同一页对照呈现
n【错题分析要求（feat-041 智能错题分析）- 化学学科】

1. **常见错误类型**：
   - 单位换算：质量/体积/摩尔单位转换错误
   - 公式套用：化学方程式配平错误、计算式选择错误
   - 实验操作：仪器选择错误、操作顺序不对、安全注意事项遗漏
   - 微观理解：分子/原子/离子概念混淆、化学键理解错误
   - 方程式书写：反应物生成物写反、条件遗漏、状态符号缺失

2. **错题分析页设计要求**：
   - 错误示例：展示学生常见错误解答或方程式
   - 错误原因：分析化学概念或实验操作理解偏差
   - 正确解法：给出规范的解题过程或化学方程式
   - 预防策略：如何建立正确的化学思维

3. **输出格式要求**：
   ```json
   {{
     "page_type": "错题分析页",
     "title": "易错警示",
     "common_mistakes": [
       {{
         "mistake_type": "错误类型",
         "mistake_example": "错误示例",
         "reason": "错误原因分析",
         "correct_method": "正确解法",
         "prevention_strategy": "预防策略"
       }}
     ]
   }}
   ```
- 复杂反应分步展示
- 化学方程式配平过程逐步显示

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "experiment_steps": {{"purpose": "实验目的", "instruments": ["仪器 1", "仪器 2"], "reagents": ["药品 1", "药品 2"], "procedures": ["步骤 1", "步骤 2"], "safety": ["安全事项"]}},
            "reaction_phenomena": {{"before": "反应前", "process": ["现象 1", "现象 2"], "after": "反应后"}},
            "chemical_equation": {{"reactants": ["反应物 1", "反应物 2"], "products": ["生成物 1", "生成物 2"], "condition": "反应条件", "balanced": "配平方程式"}},
            "microscopic_explanation": {{"model": "微粒模型描述", "process": "微粒变化过程", "bond_changes": "化学键变化"}},
            "periodic_trend": {{"element": "元素名", "position": "周期表位置", "trend": "性质递变规律"}}
        }}
    ],
    "experiments": ["实验 1", "实验 2"],
    "equations": ["方程式 1", "方程式 2"],
    "summary": "总结"
}}

请生成内容，确保学生理解宏观现象与微观本质的关系，掌握化学方程式书写和实验探究能力。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建化学学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/实验步骤页/反应现象页/化学方程式页/微观解释页/元素周期律页/图示页/表格页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 实验步骤页字段
                    "experiment_steps": {
                        "purpose": "实验目的",
                        "principle": "实验原理",
                        "instruments": ["仪器 1", "仪器 2", "仪器 3"],
                        "reagents": ["药品 1", "药品 2", "药品 3"],
                        "procedures": [
                            {"step_number": 1, "description": "步骤 1 描述", "operation_suggestion": "操作要领"}
                        ],
                        "safety_notes": ["安全事项 1", "安全事项 2"],
                        "waste_disposal": "废弃物处理方法"
                    },
                    # 反应现象页字段
                    "reaction_phenomena": {
                        "before": {
                            "substances": ["物质 1 状态", "物质 2 状态"],
                            "appearance": "反应前外观"
                        },
                        "process": [
                            "现象 1（颜色变化/气体生成/沉淀产生/发光发热）",
                            "现象 2"
                        ],
                        "after": {
                            "products": ["产物 1 状态", "产物 2 状态"],
                            "appearance": "反应后外观"
                        },
                        "key_observations": ["关键观察点 1", "关键观察点 2"]
                    },
                    # 化学方程式页字段
                    "chemical_equation": {
                        "reactants": ["反应物 1 化学式", "反应物 2 化学式"],
                        "products": ["生成物 1 化学式", "生成物 2 化学式"],
                        "condition": "反应条件（加热/催化剂/通电等）",
                        "balanced_equation": "配平后的化学方程式",
                        "balancing_steps": ["配平步骤 1", "配平步骤 2"],
                        "meaning": "方程式的意义（质量关系/粒子数量关系）"
                    },
                    # 微观解释页字段
                    "microscopic_explanation": {
                        "model_description": "微粒模型描述（分子/原子/离子）",
                        "particle_changes": "微粒变化过程",
                        "bond_breaking": "化学键断裂情况",
                        "bond_forming": "化学键形成情况",
                        "electron_transfer": "电子转移/共用情况",
                        "diagram_suggestion": "微观示意图建议"
                    },
                    # 元素周期律页字段
                    "periodic_trend": {
                        "element_name": "元素名称",
                        "symbol": "元素符号",
                        "position": {"period": "周期数", "group": "族"},
                        "atomic_structure": {"protons": "质子数", "electrons": "电子数", "electron_configuration": "电子排布"},
                        "properties_trend": "性质递变规律",
                        "comparison_with_similar_elements": "与相似元素的比较"
                    }
                }
                for _ in range(slide_count)
            ],
            "experiments": [
                {
                    "name": "实验名称",
                    "type": "演示实验/分组实验/探究实验",
                    "purpose": "实验目的",
                    "safety_level": "安全等级（低/中/高）"
                }
            ],
            "equations": [
                {
                    "equation": "化学方程式",
                    "type": "反应类型（化合/分解/置换/复分解）",
                    "application": "应用领域"
                }
            ],
            "summary": "整体内容总结（知识 + 微观本质 + 实验技能）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取化学学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "实验步骤页",        # 化学专属：仪器、药品、操作流程
            "反应现象页",        # 化学专属：颜色变化、气体、沉淀
            "化学方程式页",      # 化学专属：方程式书写、配平
            "微观解释页",        # 化学专属：分子/原子/离子模型
            "元素周期律页",      # 化学专属：周期表位置、性质递变
            "图示页",            # 实验装置图、微观模型图
            "表格页",            # 物质性质对比表、实验数据表
        ]


class BiologyPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    生物学科提示词策略

    专为生物教学设计，包含：
    1. 结构观察：器官/组织/细胞结构观察
    2. 功能分析：结构与功能相适应的观点
    3. 过程描述：生命活动过程、生理过程
    4. 系统思维：生物体整体性、生态系统思维
    5. 实验探究：观察实验、对照实验设计
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
        构建生物学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的生物教师，请根据以下生物教学内容，设计一份高质量的生物教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：生物
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【生物教学原则】
1. **结构与功能观**：生物体的结构与其功能相适应
2. **物质与能量观**：理解生物体内的物质变化和能量流动
3. **信息传递观**：理解生命活动的信息调控
4. **系统整体观**：从细胞→组织→器官→系统→个体的层次理解
5. **生态整体观**：理解生物与环境的关系、生态系统的平衡

【生物专属教学要求】
1. **结构观察页**：
   - 观察对象（细胞/组织/器官）
   - 结构组成部分
   - 各部分特征
   - 结构层次关系
   - 观察方法（显微镜使用、解剖观察）

2. **功能分析页**：
   - 结构对应的功能
   - 功能实现的机制
   - 结构与功能的适应性
   - 功能障碍的影响

3. **过程描述页**：
   - 生命活动的起点
   - 过程的各个阶段
   - 每阶段的特点
   - 调控机制
   - 过程的意义

4. **系统思维页**：
   - 该知识点在生物体中的位置
   - 与其他系统的联系
   - 整体协调机制
   - 稳态维持

5. **实验探究页**：
   - 探究问题
   - 实验设计（对照原则、单一变量原则）
   - 预期结果
   - 结论推导

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：生命观念、科学思维、科学探究、社会责任
3. **情境导入**（1 页）：生命现象/健康问题/生物趣事引入
4. **新知讲解**（4-6 页）：
   - 结构观察（2 页）
   - 功能分析（2 页）
   - 过程描述（2 页）
5. **实验探究**（2-3 页）
6. **课堂小结**（1 页）：知识框架 + 生命观念

n【错题分析要求（feat-041 智能错题分析）- 生物学科】

1. **常见错误类型**：
   - 概念混淆：细胞器功能混淆、生理过程混淆
   - 结构识别：显微镜下结构识别错误、标注位置错误
   - 过程理解：生命活动顺序错误、因果关系颠倒
   - 专业术语：生物学名词书写错误、概念表述不准确
   - 图表分析：坐标图含义理解错误、曲线趋势判断错误

2. **错题分析页设计要求**：
   - 错误示例：展示学生常见错误答案或图示
   - 错误原因：分析生物概念或生命过程理解偏差
   - 正确解法：给出规范的解答或正确的结构图示
   - 预防策略：如何建立正确的生物学思维

3. **输出格式要求**：
   ```json
   {{
     "page_type": "错题分析页",
     "title": "易错警示",
     "common_mistakes": [
       {{
         "mistake_type": "错误类型",
         "mistake_example": "错误示例",
         "reason": "错误原因分析",
         "correct_method": "正确解法",
         "prevention_strategy": "预防策略"
       }}
     ]
   }}
   ```
【认知负荷优化要求】
- 每页内容不超过{max_points}个要点
- 结构图与功能说明应在同一页呈现
- 复杂生命过程分步展示
- 宏观与微观层次清晰区分

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "structure_observation": {{"object": "观察对象", "parts": ["部分 1", "部分 2"], "features": ["特征 1", "特征 2"], "method": "观察方法"}},
            "function_analysis": {{"structure": "结构名称", "function": "功能", "adaptation": "适应性表现"}},
            "process_description": {{"name": "过程名称", "stages": ["阶段 1", "阶段 2"], "regulation": "调控机制"}},
            "system_thinking": {{"level": "结构层次", "connections": ["联系 1", "联系 2"], "homeostasis": "稳态维持"}},
            "experiment_inquiry": {{"question": "探究问题", "design": "实验设计", "result": "预期结果", "conclusion": "结论"}}
        }}
    ],
    "structures": ["结构 1", "结构 2"],
    "processes": ["生命过程 1", "生命过程 2"],
    "summary": "总结"
}}

请生成内容，确保学生形成正确的生命观念，理解结构与功能的关系，掌握科学探究方法。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建生物学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/结构观察页/功能分析页/过程描述页/系统思维页/实验探究页/图示页/表格页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 结构观察页字段
                    "structure_observation": {
                        "object": "观察对象（细胞/组织/器官/系统）",
                        "location": "在生物体中的位置",
                        "parts": [
                            {"name": "部分 1 名称", "description": "描述", "feature": "特征"}
                        ],
                        "hierarchy": "结构层次关系",
                        "observation_method": "观察方法（显微镜倍数/染色方法/解剖技巧）",
                        "diagram_suggestion": "结构示意图建议"
                    },
                    # 功能分析页字段
                    "function_analysis": {
                        "structure_name": "结构名称",
                        "function": "功能描述",
                        "mechanism": "功能实现机制",
                        "adaptation_evidence": "结构与功能相适应的证据",
                        "dysfunction_impact": "功能障碍的影响"
                    },
                    # 过程描述页字段
                    "process_description": {
                        "process_name": "生命过程名称",
                        "significance": "该过程的生物学意义",
                        "stages": [
                            {"stage_number": 1, "name": "阶段 1 名称", "description": "阶段 1 描述", "location": "发生场所", "key_events": ["关键事件 1", "关键事件 2"]}
                        ],
                        "regulation": "调控机制（神经调节/体液调节/自身调节）",
                        "influencing_factors": ["影响因素 1", "影响因素 2"]
                    },
                    # 系统思维页字段
                    "system_thinking": {
                        "level": "结构层次（细胞/组织/器官/系统/个体）",
                        "position": "在上一层次中的位置",
                        "connections": [
                            {"connected_system": "相关系统", "relationship": "关系描述"}
                        ],
                        "coordination": "整体协调机制",
                        "homeostasis": "稳态维持方式"
                    },
                    # 实验探究页字段
                    "experiment_inquiry": {
                        "question": "探究问题",
                        "hypothesis": "假设",
                        "design": {
                            "variables": {"independent": "自变量", "dependent": "因变量", "controlled": "控制变量"},
                            "groups": ["实验组设计", "对照组设计"],
                            "procedure": ["操作步骤 1", "操作步骤 2"]
                        },
                        "expected_result": "预期结果",
                        "conclusion": "结论推导"
                    }
                }
                for _ in range(slide_count)
            ],
            "structures": [
                {
                    "name": "结构名称",
                    "level": "结构层次",
                    "function": "主要功能"
                }
            ],
            "processes": [
                {
                    "name": "生命过程名称",
                    "significance": "生物学意义",
                    "regulation_type": "调节方式"
                }
            ],
            "summary": "整体内容总结（知识 + 生命观念 + 科学思维）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取生物学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "结构观察页",        # 生物专属：细胞/组织/器官结构
            "功能分析页",        # 生物专属：结构与功能适应
            "过程描述页",        # 生物专属：生命活动过程
            "系统思维页",        # 生物专属：层次关系、整体协调
            "实验探究页",        # 生物专属：观察实验、对照实验
            "图示页",            # 结构示意图、过程流程图
            "表格页",            # 结构对比表、过程阶段表
        ]
