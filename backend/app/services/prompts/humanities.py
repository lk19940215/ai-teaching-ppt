"""
文科学科提示词策略（历史/政治/地理）
专为文科教学设计的提示词模板，强调时间轴、因果分析、材料解读、区域比较
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin


class HistoryPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    历史学科提示词策略

    专为历史教学设计，包含：
    1. 时间轴展示：历史事件的时序关系
    2. 因果链分析：历史事件的因果关系
    3. 史料解读：原始史料的阅读与分析
    4. 多视角评价：从不同角度评价历史事件
    5. 历史启示：以史为鉴、联系现实
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
        构建历史学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的历史教师，请根据以下历史教学内容，设计一份高质量的历史教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：历史
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【历史教学原则】
1. **时序意识**：建立清晰的时间线索，理解历史发展的先后顺序
2. **因果分析**：探究历史事件的背景、原因、经过、结果、影响
3. **史料实证**：运用一手史料和二手史料，培养证据意识
4. **多视角评价**：从政治、经济、文化、社会等多角度评价历史
5. **历史解释**：理解不同历史解释的合理性，培养批判性思维
6. **家国情怀**：从历史中汲取智慧，培养爱国情怀和国际视野

【历史专属教学要求】
1. **时间轴页**：
   - 时间范围（起止年代）
   - 关键时间节点
   - 重大历史事件
   - 发展阶段划分
   - 时代特征概括

2. **背景分析页**：
   - 国际背景
   - 国内背景
   - 政治背景
   - 经济背景
   - 文化背景
   - 社会背景

3. **因果分析页**：
   - 根本原因
   - 直接原因
   - 导火线
   - 必要条件
   - 充分条件

4. **史料解读页**：
   - 史料原文（文言文/外文翻译）
   - 史料出处
   - 史料类型（一手/二手）
   - 史料价值
   - 解读要点

5. **过程叙述页**：
   - 事件起因
   - 发展阶段
   - 关键转折点
   - 最终结果
   - 重要人物作用

6. **影响评价页**：
   - 短期影响
   - 长期影响
   - 积极影响
   - 消极影响
   - 历史地位

7. **多视角评价页**：
   - 政治视角评价
   - 经济视角评价
   - 文化视角评价
   - 社会视角评价
   - 国际视角评价

8. **历史启示页**：
   - 历史经验
   - 历史教训
   - 现实意义
   - 当代启示

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：时空观念、史料实证、历史解释、家国情怀
3. **情境导入**（1 页）：历史故事/影视片段/文物图片引入
4. **时序梳理**（2-3 页）：
   - 时间轴展示（1 页）
   - 发展阶段（1-2 页）
5. **深度探究**（4-6 页）：
   - 背景分析（1 页）
   - 因果分析（1 页）
   - 史料解读（1-2 页）
   - 过程叙述（1-2 页）
6. **评价反思**（2-3 页）：
   - 影响评价（1 页）
   - 多视角评价（1 页）
   - 历史启示（1 页）
7. **课堂小结**（1 页）：知识框架 + 历史智慧

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 时间轴与事件说明应在同一页呈现
- 复杂历史过程分步展示：拆分为 2-3 页逐步展开
- 史料原文与白话译文对照呈现

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "timeline": {{"period": "时间范围", "events": [{{"year": "年份", "event": "事件"}}]}},
            "background_analysis": {{"international": "国际背景", "domestic": "国内背景", "political": "政治背景", "economic": "经济背景"}},
            "cause_analysis": {{"root_cause": "根本原因", "direct_cause": "直接原因", "trigger": "导火线", "conditions": ["条件 1", "条件 2"]}},
            "historical_material": {{"text": "史料原文", "source": "出处", "type": "史料类型", "value": "史料价值", "interpretation": "解读要点"}},
            "process_narrative": {{"cause": "起因", "stages": ["阶段 1", "阶段 2"], "turning_point": "转折点", "result": "结果"}},
            "impact_evaluation": {{"short_term": "短期影响", "long_term": "长期影响", "positive": "积极影响", "negative": "消极影响"}},
            "multi_perspective": {{"political": "政治视角", "economic": "经济视角", "cultural": "文化视角", "social": "社会视角"}}
        }}
    ],
    "timeline": [{{"year": "年份", "event": "事件"}}],
    "key_figures": ["历史人物 1", "历史人物 2"],
    "historical_terms": ["历史概念 1", "历史概念 2"],
    "summary": "总结"
}}

请生成内容，确保学生形成清晰的时空观念，掌握史料实证方法，培养历史解释能力和家国情怀。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建历史学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/时间轴页/背景分析页/因果分析页/史料解读页/过程叙述页/影响评价页/多视角评价页/历史启示页/图示页/表格页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 时间轴页字段
                    "timeline": {
                        "period": "时间范围（如：1840-1919 年）",
                        "era_name": "时代名称（如：近代史）",
                        "events": [
                            {"year": "具体年份", "event": "事件名称", "significance": "历史意义"}
                        ],
                        "stages": ["阶段 1 名称", "阶段 2 名称"],
                        "visual_suggestion": "时间轴呈现方式（水平/垂直/曲线）"
                    },
                    # 背景分析页字段
                    "background_analysis": {
                        "international": "国际背景描述",
                        "domestic": "国内背景描述",
                        "political": "政治背景",
                        "economic": "经济背景",
                        "cultural": "文化背景",
                        "social": "社会背景",
                        "key_contradictions": ["主要矛盾 1", "主要矛盾 2"]
                    },
                    # 因果分析页字段
                    "cause_analysis": {
                        "root_cause": "根本原因（深层、长远的原因）",
                        "direct_cause": "直接原因（触发事件）",
                        "trigger": "导火线（偶然事件）",
                        "necessary_conditions": ["必要条件 1", "必要条件 2"],
                        "contributing_factors": ["促进因素 1", "促进因素 2"],
                        "causal_chain": ["原因→结果 1", "结果 1→结果 2"]
                    },
                    # 史料解读页字段
                    "historical_material": {
                        "text": "史料原文（文言文或翻译）",
                        "source": "出处（书名/篇名/作者）",
                        "time_period": "史料产生的时代",
                        "type": "史料类型（一手史料/二手史料/实物史料/口述史料）",
                        "reliability": "可信度评估",
                        "value": "史料价值（证明了什么）",
                        "interpretation_points": ["解读要点 1", "解读要点 2"],
                        "modern_translation": "白话文翻译（可选）"
                    },
                    # 过程叙述页字段
                    "process_narrative": {
                        "cause": "事件起因",
                        "stages": [
                            {"stage_name": "阶段名称", "time": "时间", "description": "描述", "key_events": ["关键事件 1", "关键事件 2"]}
                        ],
                        "turning_point": "关键转折点",
                        "climax": "高潮部分",
                        "result": "最终结果",
                        "key_figures_role": "重要人物作用"
                    },
                    # 影响评价页字段
                    "impact_evaluation": {
                        "short_term_impact": "短期影响（即时后果）",
                        "long_term_impact": "长期影响（深远影响）",
                        "positive_impacts": ["积极影响 1", "积极影响 2"],
                        "negative_impacts": ["消极影响 1", "消极影响 2"],
                        "historical_status": "历史地位",
                        "significance": "历史意义"
                    },
                    # 多视角评价页字段
                    "multi_perspective": {
                        "political_perspective": "政治视角评价",
                        "economic_perspective": "经济视角评价",
                        "cultural_perspective": "文化视角评价",
                        "social_perspective": "社会视角评价",
                        "international_perspective": "国际视角评价",
                        "different_historical_views": ["不同历史观点 1", "不同历史观点 2"]
                    },
                    # 历史启示页字段
                    "historical_revelation": {
                        "experiences": ["历史经验 1", "历史经验 2"],
                        "lessons": ["历史教训 1", "历史教训 2"],
                        "contemporary_relevance": "现实意义",
                        "enlightenment": "当代启示"
                    }
                }
                for _ in range(slide_count)
            ],
            "timeline": [
                {
                    "year": "年份",
                    "event": "事件名称",
                    "significance": "历史意义"
                }
            ],
            "key_figures": [
                {
                    "name": "人物姓名",
                    "role": "历史角色",
                    "contribution": "主要贡献",
                    "evaluation": "历史评价"
                }
            ],
            "historical_terms": [
                {
                    "term": "历史概念",
                    "definition": "定义",
                    "time_period": "时代",
                    "significance": "历史意义"
                }
            ],
            "summary": "整体内容总结（知识 + 方法 + 价值观）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取历史学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "时间轴页",        # 历史专属：时序关系、发展阶段
            "背景分析页",      # 历史专属：时代背景
            "因果分析页",      # 历史专属：原因探究
            "史料解读页",      # 历史专属：原始史料分析
            "过程叙述页",      # 历史专属：事件经过
            "影响评价页",      # 历史专属：历史影响
            "多视角评价页",    # 历史专属：多元评价
            "历史启示页",      # 历史专属：以史为鉴
            "图示页",          # 历史地图、关系图
            "表格页",          # 对比表、年代表
        ]


class PoliticsPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    政治学科提示词策略

    专为政治教学设计，包含：
    1. 概念界定：明确政治概念的内涵外延
    2. 原理阐述：政治学基本原理
    3. 案例分析：理论联系实际
    4. 价值引领：社会主义核心价值观
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
        构建政治学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的政治教师，请根据以下政治教学内容，设计一份高质量的政治教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：政治
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【政治教学原则】
1. **概念准确**：政治概念表述严谨、科学
2. **原理清晰**：基本原理阐述透彻、逻辑严密
3. **理论联系实际**：用理论分析现实问题，用现实验证理论
4. **价值引领**：渗透社会主义核心价值观，培养家国情怀
5. **辩证思维**：培养全面、发展、联系地看问题

【政治专属教学要求】
1. **概念界定页**：
   - 概念名称
   - 内涵（本质属性）
   - 外延（适用范围）
   - 相关概念辨析
   - 概念形成过程

2. **原理阐述页**：
   - 原理内容
   - 理论依据
   - 逻辑推导
   - 适用条件
   - 理论意义

3. **案例分析页**：
   - 案例背景
   - 案例描述
   - 理论分析
   - 结论启示
   - 类似案例

4. **政策解读页**：
   - 政策名称
   - 出台背景
   - 主要内容
   - 实施意义
   - 社会影响

5. **价值引领页**：
   - 价值观念
   - 理论依据
   - 现实意义
   - 践行路径
   - 榜样示范

6. **辩证分析页**：
   - 问题提出
   - 正面分析
   - 反面分析
   - 全面认识
   - 正确态度

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：政治认同、科学精神、法治意识、公共参与
3. **情境导入**（1 页）：时事热点/社会现象/生活实例引入
4. **新知讲解**（4-6 页）：
   - 概念界定（1 页）
   - 原理阐述（2 页）
   - 案例分析（2 页）
5. **拓展提升**（2-3 页）：
   - 政策解读（1 页）
   - 价值引领（1 页）
6. **课堂小结**（1 页）：知识框架 + 素养提升

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 理论与案例应在同一页对照呈现
- 复杂概念分步展示：拆分为 2-3 页逐步展开
- 避免空洞说教，多用实例说明

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "concept_definition": {{"name": "概念名", "connotation": "内涵", "extension": "外延", "distinction": "相关概念辨析"}},
            "principle_explanation": {{"content": "原理内容", "basis": "理论依据", "logic": "逻辑推导", "significance": "理论意义"}},
            "case_analysis": {{"background": "案例背景", "description": "案例描述", "analysis": "理论分析", "conclusion": "结论启示"}},
            "policy_interpretation": {{"name": "政策名", "background": "出台背景", "content": "主要内容", "significance": "实施意义"}},
            "value_guidance": {{"value": "价值观念", "basis": "理论依据", "relevance": "现实意义", "path": "践行路径"}}
        }}
    ],
    "key_concepts": ["概念 1", "概念 2"],
    "principles": ["原理 1", "原理 2"],
    "cases": ["案例 1", "案例 2"],
    "summary": "总结"
}}

请生成内容，确保学生理解政治概念和原理，培养政治认同和科学精神，树立正确的价值观。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建政治学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/概念界定页/原理阐述页/案例分析页/政策解读页/价值引领页/辩证分析页/图示页/表格页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 概念界定页字段
                    "concept_definition": {
                        "name": "概念名称",
                        "connotation": "内涵（本质属性）",
                        "extension": "外延（适用范围）",
                        "formation_process": "概念形成过程",
                        "related_concepts": ["相关概念 1", "相关概念 2"],
                        "distinction": "与相关概念的区别"
                    },
                    # 原理阐述页字段
                    "principle_explanation": {
                        "content": "原理内容表述",
                        "theoretical_basis": "理论依据",
                        "logical_derivation": "逻辑推导过程",
                        "applicable_conditions": "适用条件",
                        "theoretical_significance": "理论意义",
                        "practical_value": "实践价值"
                    },
                    # 案例分析页字段
                    "case_analysis": {
                        "background": "案例背景",
                        "description": "案例详细描述",
                        "theoretical_analysis": "用理论分析案例",
                        "key_issues": ["关键问题 1", "关键问题 2"],
                        "conclusion": "结论",
                        "enlightenment": "启示",
                        "similar_cases": ["类似案例 1", "类似案例 2"]
                    },
                    # 政策解读页字段
                    "policy_interpretation": {
                        "name": "政策名称",
                        "issuing_body": "发布机关",
                        "background": "出台背景",
                        "main_content": ["主要内容 1", "主要内容 2"],
                        "key_points": ["要点 1", "要点 2"],
                        "implementation_significance": "实施意义",
                        "social_impact": "社会影响"
                    },
                    # 价值引领页字段
                    "value_guidance": {
                        "value_concept": "价值观念",
                        "theoretical_basis": "理论依据",
                        "historical_origin": "历史渊源",
                        "contemporary_relevance": "现实意义",
                        "practice_path": "践行路径",
                        "role_model": "榜样示范"
                    },
                    # 辩证分析页字段
                    "dialectical_analysis": {
                        "issue": "问题提出",
                        "positive_analysis": "正面分析",
                        "negative_analysis": "反面分析",
                        "comprehensive_view": "全面认识",
                        "correct_attitude": "正确态度"
                    }
                }
                for _ in range(slide_count)
            ],
            "key_concepts": [
                {
                    "name": "概念名称",
                    "definition": "定义",
                    "category": "所属范畴"
                }
            ],
            "principles": [
                {
                    "name": "原理名称",
                    "content": "原理内容",
                    "application": "应用领域"
                }
            ],
            "cases": [
                {
                    "name": "案例名称",
                    "type": "案例类型",
                    "relevance": "与理论的关联"
                }
            ],
            "summary": "整体内容总结（知识 + 能力 + 价值观）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取政治学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "概念界定页",      # 政治专属：概念内涵外延
            "原理阐述页",      # 政治专属：理论原理
            "案例分析页",      # 政治专属：理论联系实际
            "政策解读页",      # 政治专属：政策分析
            "价值引领页",      # 政治专属：价值观教育
            "辩证分析页",      # 政治专属：辩证思维
            "图示页",          # 概念关系图、逻辑图
            "表格页",          # 对比表、分类表
        ]


class GeographyPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    地理学科提示词策略

    专为地理教学设计，包含：
    1. 位置定位：空间位置、区域范围
    2. 自然环境：地形、气候、水文、土壤、植被
    3. 人文特征：人口、城市、产业、文化
    4. 区域比较：不同区域的异同
    5. 人地关系：人类活动与地理环境的关系
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
        构建地理学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的地理教师，请根据以下地理教学内容，设计一份高质量的地理教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：地理
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【地理教学原则】
1. **空间观念**：建立地理空间概念，理解地理事物的空间分布
2. **综合思维**：从要素综合、时空综合、地方综合角度分析地理问题
3. **区域认知**：认识区域特征、区域差异、区域联系
4. **人地协调观**：理解人地关系，树立可持续发展观念
5. **地理实践力**：培养地图阅读、地理观察、调查研究能力

【地理专属教学要求】
1. **位置定位页**：
   - 经纬度位置
   - 海陆位置
   - 相对位置
   - 区域范围
   - 地理位置评价

2. **自然环境页**：
   - 地形地貌
   - 气候特征
   - 水文状况
   - 土壤类型
   - 植被分布

3. **人文特征页**：
   - 人口特征
   - 城市分布
   - 产业发展
   - 交通运输
   - 文化特色

4. **区域比较页**：
   - 比较对象
   - 相似点
   - 差异点
   - 差异原因
   - 各自优势

5. **人地关系页**：
   - 环境对人类的影响
   - 人类对环境的影响
   - 人地协调措施
   - 可持续发展路径

6. **地图分析页**：
   - 地图类型
   - 图例解读
   - 信息提取
   - 空间分析
   - 结论归纳

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：区域认知、综合思维、人地协调观、地理实践力
3. **情境导入**（1 页）：地理景观图/地图/地理趣事引入
4. **区域定位**（1-2 页）：
   - 位置描述（1 页）
   - 区域范围（1 页）
5. **地理特征**（4-6 页）：
   - 自然环境（2-3 页）
   - 人文特征（2-3 页）
6. **区域分析**（2-3 页）：
   - 区域比较（1 页）
   - 人地关系（1 页）
7. **课堂小结**（1 页）：知识框架 + 地理素养

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 地图与文字说明应在同一页呈现
- 复杂地理过程分步展示
- 避免冗余：地图已表达的信息不用文字重复

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "location": {{"latitude_longitude": "经纬度", "sea_land": "海陆位置", "relative": "相对位置", "evaluation": "位置评价"}},
            "natural_environment": {{"terrain": "地形", "climate": "气候", "hydrology": "水文", "soil": "土壤", "vegetation": "植被"}},
            "human_features": {{"population": "人口", "city": "城市", "industry": "产业", "transport": "交通", "culture": "文化"}},
            "regional_comparison": {{"objects": ["区域 1", "区域 2"], "similarities": ["相似点 1", "相似点 2"], "differences": ["差异 1", "差异 2"]}},
            "human_land_relationship": {{"environment_impact": "环境影响", "human_impact": "人类影响", "measures": "协调措施"}}
        }}
    ],
    "maps": ["地图 1", "地图 2"],
    "regions": ["区域 1", "区域 2"],
    "summary": "总结"
}}

请生成内容，确保学生形成区域认知能力，理解人地关系，培养综合思维和地理实践力。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建地理学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/位置定位页/自然环境页/人文特征页/区域比较页/人地关系页/地图分析页/图示页/表格页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 位置定位页字段
                    "location": {
                        "latitude_longitude": "经纬度位置",
                        "hemisphere": "半球位置",
                        "sea_land_position": "海陆位置",
                        "relative_position": "相对位置（相邻区域）",
                        "geographical_significance": "地理位置意义",
                        "evaluation": "位置优越性评价"
                    },
                    # 自然环境页字段
                    "natural_environment": {
                        "terrain": {
                            "type": "地形类型",
                            "features": "地形特征",
                            "distribution": "地形分布"
                        },
                        "climate": {
                            "type": "气候类型",
                            "features": "气候特征",
                            "factors": "气候影响因素"
                        },
                        "hydrology": {
                            "rivers": "河流状况",
                            "lakes": "湖泊状况",
                            "water_resources": "水资源状况"
                        },
                        "soil": {
                            "type": "土壤类型",
                            "distribution": "土壤分布",
                            "fertility": "土壤肥力"
                        },
                        "vegetation": {
                            "type": "植被类型",
                            "distribution": "植被分布",
                            "characteristics": "植被特征"
                        }
                    },
                    # 人文特征页字段
                    "human_features": {
                        "population": {
                            "size": "人口数量",
                            "distribution": "人口分布",
                            "structure": "人口结构",
                            "trend": "人口变化趋势"
                        },
                        "city": {
                            "distribution": "城市分布",
                            "hierarchy": "城市等级体系",
                            "urbanization": "城市化水平"
                        },
                        "industry": {
                            "primary": "第一产业",
                            "secondary": "第二产业",
                            "tertiary": "第三产业",
                            "layout": "产业布局特点"
                        },
                        "transport": {
                            "network": "交通网络",
                            "main_lines": "主要线路",
                            "hub": "交通枢纽"
                        },
                        "culture": {
                            "customs": "风俗习惯",
                            "language": "语言",
                            "religion": "宗教",
                            "heritage": "文化遗产"
                        }
                    },
                    # 区域比较页字段
                    "regional_comparison": {
                        "comparison_objects": ["区域 1 名称", "区域 2 名称"],
                        "comparison_dimension": "比较维度（自然/人文/经济）",
                        "similarities": [
                            {"aspect": "方面", "description": "相似点描述"}
                        ],
                        "differences": [
                            {"aspect": "方面", "region_a": "区域 A 特点", "region_b": "区域 B 特点", "reason": "差异原因"}
                        ],
                        "respective_advantages": {
                            "region_a": "区域 A 优势",
                            "region_b": "区域 B 优势"
                        }
                    },
                    # 人地关系页字段
                    "human_land_relationship": {
                        "environment_impact_on_human": "地理环境对人类活动的影响",
                        "human_impact_on_environment": "人类活动对地理环境的影响",
                        "environmental_issues": ["环境问题 1", "环境问题 2"],
                        "coordination_measures": ["协调措施 1", "协调措施 2"],
                        "sustainable_path": "可持续发展路径"
                    },
                    # 地图分析页字段
                    "map_analysis": {
                        "map_type": "地图类型",
                        "scale": "比例尺",
                        "legend": "图例说明",
                        "extracted_info": ["提取信息 1", "提取信息 2"],
                        "spatial_pattern": "空间分布规律",
                        "conclusion": "分析结论"
                    }
                }
                for _ in range(slide_count)
            ],
            "maps": [
                {
                    "name": "地图名称",
                    "type": "地图类型（政区图/地形图/气候图等）",
                    "information": "包含的主要信息"
                }
            ],
            "regions": [
                {
                    "name": "区域名称",
                    "level": "区域等级",
                    "characteristics": "区域特征"
                }
            ],
            "summary": "整体内容总结（知识 + 能力 + 人地观念）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取地理学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "位置定位页",      # 地理专属：经纬度、海陆位置
            "自然环境页",      # 地理专属：地形/气候/水文/土壤/植被
            "人文特征页",      # 地理专属：人口/城市/产业/交通/文化
            "区域比较页",      # 地理专属：区域差异分析
            "人地关系页",      # 地理专属：人地协调
            "地图分析页",      # 地理专属：地图阅读
            "图示页",          # 地理示意图、剖面图
            "表格页",          # 数据表、对比表
        ]
