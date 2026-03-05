"""
提示词引擎基类定义
提供可插拔的学科提示词策略系统接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class SubjectPromptStrategy(ABC):
    """
    学科提示词策略基类

    每个学科策略需要实现三个核心方法：
    1. build_prompt: 构建该学科的提示词
    2. build_schema: 构建该学科的输出结构
    3. get_page_types: 获取该学科支持的页面类型
    """

    # 年级对应的深度描述（所有学科共享）
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
        "10": "高中一年级（需要用系统化的语言、注重知识深度和广度、培养抽象思维）",
        "11": "高中二年级（需要用学术化的语言、强调知识迁移和综合运用、高考导向）",
        "12": "高中三年级（需要用精炼专业的语言、强化考点突破和应试技巧、冲刺高考）",
    }

    # 学科特色描述（所有学科共享）
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

    @abstractmethod
    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None
    ) -> str:
        """
        构建该学科的 PPT 内容生成提示词

        Args:
            content: 教学内容
            grade: 年级
            subject: 学科
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）

        Returns:
            构建好的提示词
        """
        pass

    @abstractmethod
    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建该学科的输出结构定义

        Args:
            slide_count: 幻灯片数量

        Returns:
            JSON Schema 结构定义
        """
        pass

    @abstractmethod
    def get_page_types(self) -> List[str]:
        """
        获取该学科支持的页面类型列表

        Returns:
            页面类型字符串列表
        """
        pass

    def get_grade_description(self, grade: str) -> str:
        """获取年级描述"""
        return self.GRADE_DESCRIPTIONS.get(grade, f"未知年级 {grade}")

    def get_subject_description(self, subject: str) -> str:
        """获取学科描述"""
        return self.SUBJECT_DESCRIPTIONS.get(subject, self.SUBJECT_DESCRIPTIONS["general"])


class CognitiveLoadMixin:
    """
    认知负荷优化混入类

    基于 Mayer 多媒体学习理论，控制每页信息量和呈现方式
    包含 5 大核心原则：聚焦要义、空间邻近、时间邻近、切块呈现、冗余控制
    """

    # 年级对应的最大要点数（聚焦要义原则）
    MAX_POINTS_PER_SLIDE = {
        "1": 2,
        "2": 2,
        "3": 3,
        "4": 3,
        "5": 4,
        "6": 4,
        "7": 4,
        "8": 5,
        "9": 5,
        "10": 5,
        "11": 6,
        "12": 6,
    }

    # 复杂概念分块规则（切块呈现原则）
    # 定义哪些内容类型需要分块展示
    COMPLEX_CONCEPT_TYPES = [
        "公式推导",
        "语法树分析",
        "时态对比",
        "实验步骤",
        "化学反应过程",
        "生命活动过程",
        "历史因果链",
        "地理过程",
        "政治原理推导",
    ]

    def get_max_points_for_grade(self, grade: str) -> int:
        """
        获取指定年级每页最大要点数（聚焦要义原则）

        Args:
            grade: 年级（1-12）

        Returns:
            每页最大要点数
        """
        return self.MAX_POINTS_PER_SLIDE.get(grade, 4)

    def get_chunk_size_for_grade(self, grade: str) -> int:
        """
        获取指定年级的分块大小（切块呈现原则）

        复杂概念需要拆分的页数
        """
        chunk_mapping = {
            "1": 3,  # 低年级拆分为更多页
            "2": 3,
            "3": 3,
            "4": 2,
            "5": 2,
            "6": 2,
            "7": 2,
            "8": 2,
            "9": 2,
            "10": 2,
            "11": 2,
            "12": 2,
        }
        return chunk_mapping.get(grade, 2)

    def apply_cognitive_load_constraints(self, prompt: str, grade: str) -> str:
        """
        应用认知负荷约束到提示词

        基于 Mayer 多媒体学习理论的 5 大原则：
        1. 聚焦要义原则（Coherence Principle）：每页内容不超过指定要点数
        2. 空间邻近原则（Spatial Contiguity Principle）：图示与文字在同一页
        3. 时间邻近原则（Temporal Contiguity Principle）：相关内容同时呈现
        4. 切块呈现原则（Segmenting Principle）：复杂内容分步展示
        5. 冗余控制原则（Redundancy Principle）：避免重复信息

        Args:
            prompt: 原始提示词
            grade: 年级

        Returns:
            增强后的提示词
        """
        max_points = self.get_max_points_for_grade(grade)
        chunk_size = self.get_chunk_size_for_grade(grade)

        constraints = f"""

【认知负荷优化要求 - 基于 Mayer 多媒体学习理论】

1. **聚焦要义原则**：每页内容不超过{max_points}个要点，去除冗余信息，保持内容精炼
2. **空间邻近原则**：相关的文字说明和图示必须在同一页呈现，避免学生来回翻看
3. **切块呈现原则**：复杂概念（如公式推导、语法分析、实验过程等）拆分为{chunk_size}页逐步展开，每页聚焦一个子步骤
4. **冗余控制原则**：避免用文字重复图示/表格已清晰表达的信息，图文并茂但不重复
5. **时间邻近原则**：讲解语音与对应画面应同步呈现，避免先讲后看或先看后讲"""

        return prompt + constraints

    def needs_chunking(self, concept_type: str) -> bool:
        """
        判断某概念类型是否需要分块展示

        Args:
            concept_type: 概念类型

        Returns:
            是否需要分块
        """
        return concept_type in self.COMPLEX_CONCEPT_TYPES

    def get_suggested_layout(self, page_type: str) -> str:
        """
        根据页面类型建议布局方式

        Args:
            page_type: 页面类型

        Returns:
            布局建议
        """
        layout_suggestions = {
            "公式推导页": "上一步骤 + 下一步骤分两栏展示，箭头连接表示推导关系",
            "语法树页": "左侧原句 + 右侧树状图对照",
            "实验步骤页": "顶部步骤说明 + 底部操作图示",
            "时间轴页": "水平时间轴贯穿页面，事件标注在轴上下方",
            "对比分析页": "左右分栏对比，中间用虚线分隔",
            "概念引入页": "顶部生活实例图 + 底部抽象概念定义",
        }
        return layout_suggestions.get(page_type, "标准布局：标题 + 要点列表 + 底部图示")

    def get_attention_rhythm_constraints(self, grade: str) -> str:
        """
        获取注意力节奏编排约束

        基于注意力周期理论，设计注意捕捉→保持→转移的内容编排

        Args:
            grade: 年级（1-12）

        Returns:
            注意力节奏编排指令
        """
        # 年级到注意力水平的映射
        if grade in ["1", "2", "3", "4"]:
            cycle_min, cycle_max = 2, 3
            max_same = 2
            hook_freq = 2
            level_desc = "低年级（注意力周期短，需要频繁切换）"
        elif grade in ["5", "6", "7", "8"]:
            cycle_min, cycle_max = 3, 4
            max_same = 2
            hook_freq = 3
            level_desc = "中年级（注意力周期中等，平衡讲解与互动）"
        else:  # 9-12
            cycle_min, cycle_max = 4, 5
            max_same = 3
            hook_freq = 4
            level_desc = "高年级（注意力周期较长，可深入讲解但仍需变化）"

        return f"""

【注意力节奏编排要求 - 基于注意力周期理论】

适用对象：{level_desc}

1. **注意力周期控制**：
   - 每{cycle_min}-{cycle_max}页为一个注意力周期
   - 每个周期内必须包含至少 1 个互动或视觉元素
   - 避免连续超过{max_same}页相同类型的页面（如连续讲解）

2. **页面类型交替规则**：
   - 确保"讲解→互动→练习"的交替节奏
   - 讲解类（概念、公式、原理）后应接互动类（问答、讨论）或视觉类（图示、表格）
   - 每{hook_freq}页插入一个吸引点（趣味事实/你知道吗/挑战时刻/生活应用）

3. **Engagement Hooks（注意力吸引点）设计**：
   - **注意捕捉**：课程开始用情境导入、实际问题或趣味现象引入
   - **注意保持**：在连续讲解 2 页后，插入"你知道吗"、"趣味事实"或快速测验
   - **注意转移**：用"挑战时刻"、"思考问题"引导学生主动思考
   - **生活联系**：展示知识在实际生活中的应用，增强学习动机

4. **推荐的页面序列模式**：
   ```
   开场：情境导入（钩子）→ 学习目标 → 目录
   新知：概念引入（视觉）→ 讲解（1-2 页）→ 互动问答 → 讲解（1-2 页）→ 图示/表格
   巩固：示例演示 → 课堂练习 → 易错警示（互动对比）
   结尾：总结回顾 → 拓展思考/挑战时刻（钩子）
   ```

5. **年级差异化策略**：
   - 低年级（1-4）：每 2 页切换类型，大量使用图示、游戏、竞赛，语言生动有趣
   - 中年级（5-8）：每 3 页切换，平衡知识深度与互动频率，增加讨论和探究
   - 高年级（9-12）：每 4 页切换，注重知识体系和思维深度，但仍需保持变化防止疲劳"""


class BloomTaxonomyMixin:
    """
    布鲁姆目标分类法混入类

    为问题和练习标注认知层级，确保思维训练的递进性
    包含 6 个认知过程维度：记忆、理解、应用、分析、评价、创造
    """

    # 布鲁姆认知层级定义（从低阶到高阶）
    BLOOM_LEVELS = [
        {"level": "remember", "chinese": "记忆", "order": 1},
        {"level": "understand", "chinese": "理解", "order": 2},
        {"level": "apply", "chinese": "应用", "order": 3},
        {"level": "analyze", "chinese": "分析", "order": 4},
        {"level": "evaluate", "chinese": "评价", "order": 5},
        {"level": "create", "chinese": "创造", "order": 6},
    ]

    # 各层级典型行为动词
    BLOOM_VERBS = {
        "remember": ["回忆", "复述", "背诵", "列举", "定义", "命名", "识别", "描述", "指出", "匹配", "选择", "记住"],
        "understand": ["解释", "说明", "概括", "归纳", "总结", "举例", "分类", "比较", "对比", "推断", "预测", "改写", "翻译", "转化", "阐述", "演示"],
        "apply": ["应用", "运用", "使用", "执行", "实施", "计算", "操作", "演示", "展示", "解决", "构建", "制作"],
        "analyze": ["分析", "区分", "分解", "组织", "归因", "找出", "识别关系", "比较结构", "剖析", "解析", "鉴别", "图示", "推断因果", "辨别"],
        "evaluate": ["评价", "评估", "判断", "批判", "论证", "辩护", "比较优劣", "选择最佳", "评定", "检验", "证明", "评论", "鉴定", "权衡"],
        "create": ["创造", "设计", "构思", "规划", "发明", "建构", "产生", "开发", "组织", "整合", "改编", "创作", "提出方案", "制定计划", "重组"],
    }

    # 各层级适用题型
    BLOOM_EXERCISE_TYPES = {
        "remember": {"type": "知识回忆题", "formats": ["填空题", "选择题", "判断题", "匹配题", "复述题"]},
        "understand": {"type": "理解说明题", "formats": ["解释题", "举例题", "改写的", "图表题", "归纳题"]},
        "apply": {"type": "应用操作题", "formats": ["计算题", "应用题", "操作题", "演示题"]},
        "analyze": {"type": "分析探究题", "formats": ["分析题", "比较题", "关系题", "归因题"]},
        "evaluate": {"type": "评价判断题", "formats": ["评价题", "论证题", "选择题（含理由）", "批判题"]},
        "create": {"type": "创造设计题", "formats": ["设计题", "创作题", "规划题", "方案题"]},
    }

    # 年级到认知层级重点的映射
    GRADE_BLOOM_FOCUS = {
        "1": {"focus": ["remember", "understand"], "ratio": [60, 30, 10, 0, 0, 0]},
        "2": {"focus": ["remember", "understand"], "ratio": [55, 30, 15, 0, 0, 0]},
        "3": {"focus": ["remember", "understand", "apply"], "ratio": [45, 30, 20, 5, 0, 0]},
        "4": {"focus": ["remember", "understand", "apply"], "ratio": [40, 30, 25, 5, 0, 0]},
        "5": {"focus": ["understand", "apply", "analyze"], "ratio": [30, 30, 25, 10, 5, 0]},
        "6": {"focus": ["understand", "apply", "analyze"], "ratio": [25, 30, 30, 10, 5, 0]},
        "7": {"focus": ["apply", "analyze", "evaluate"], "ratio": [20, 30, 30, 15, 5, 0]},
        "8": {"focus": ["apply", "analyze", "evaluate"], "ratio": [15, 25, 30, 20, 10, 0]},
        "9": {"focus": ["analyze", "evaluate", "create"], "ratio": [15, 25, 30, 20, 10, 0]},
        "10": {"focus": ["analyze", "evaluate", "create"], "ratio": [10, 20, 30, 25, 10, 5]},
        "11": {"focus": ["analyze", "evaluate", "create"], "ratio": [10, 15, 25, 30, 15, 5]},
        "12": {"focus": ["analyze", "evaluate", "create"], "ratio": [10, 15, 20, 30, 15, 10]},
    }

    def get_bloom_level_description(self, level: str) -> str:
        """
        获取布鲁姆认知层级的描述

        Args:
            level: 层级名称（英文）

        Returns:
            层级描述
        """
        descriptions = {
            "remember": "从长时记忆中提取相关信息，如回忆事实、概念、定义、公式等",
            "understand": "从教学信息中建构意义，如解释、说明、归纳、类比等",
            "apply": "在给定的新情境中执行或使用程序，如运用公式解题、应用规则等",
            "analyze": "将材料分解为组成部分，确定部分之间的关系和组织方式",
            "evaluate": "基于标准和规范作出判断，如评估方案优劣、论证观点等",
            "create": "将要素整合为一个新的整体或原创产品，如设计方案、创作作品等",
        }
        return descriptions.get(level, "")

    def get_bloom_level_order(self, level: str) -> int:
        """
        获取认知层级的顺序（1-6）

        Args:
            level: 层级名称

        Returns:
            层级顺序（1=最低，6=最高）
        """
        for item in self.BLOOM_LEVELS:
            if item["level"] == level:
                return item["order"]
        return 0

    def get_grade_bloom_ratio(self, grade: str) -> List[int]:
        """
        获取指定年级的认知层级建议比例

        Args:
            grade: 年级（1-12）

        Returns:
            6 个层级的建议比例 [记忆，理解，应用，分析，评价，创造]
        """
        config = self.GRADE_BLOOM_FOCUS.get(grade, self.GRADE_BLOOM_FOCUS["5"])
        return config["ratio"]

    def get_bloom_prompt_section(self, grade: str, subject: str) -> str:
        """
        构建布鲁姆分类法的提示词段落

        Args:
            grade: 年级
            subject: 学科

        Returns:
            提示词段落
        """
        ratio = self.get_grade_bloom_ratio(grade)
        level_names = [f"{self.BLOOM_LEVELS[i]['chinese']}({ratio[i]}%)" for i in range(6)]

        return f"""
【布鲁姆目标分类法 - 认知层级递进要求】

为确保思维训练的递进性，请按照布鲁姆认知目标分类法设计问题和练习：

**6 个认知层级（从低到高）**：

1. **记忆 (Remember)** - 回忆事实、概念、定义
   - 典型动词：回忆、复述、列举、定义、命名、识别
   - 适用题型：填空题、选择题、判断题、复述题
   - 示例："什么是...？"、"请列举..."、"请定义..."

2. **理解 (Understand)** - 解释、说明、归纳
   - 典型动词：解释、说明、概括、举例、分类、比较
   - 适用题型：解释题、举例题、图表题、归纳题
   - 示例："请解释...的含义"、"请概括..."、"...和...有什么区别？"

3. **应用 (Apply)** - 在新情境中使用知识
   - 典型动词：应用、运用、使用、计算、操作、解决
   - 适用题型：计算题、应用题、操作题、演示题
   - 示例："请运用...解决问题"、"如何使用..."

4. **分析 (Analyze)** - 区分、组织、找出关系
   - 典型动词：分析、区分、分解、归因、比较结构、推断因果
   - 适用题型：分析题、比较题、关系题、归因题
   - 示例："请分析...的原因"、"比较...的异同"、"找出...之间的关系"

5. **评价 (Evaluate)** - 基于标准作出判断
   - 典型动词：评价、评估、判断、论证、辩护、检验
   - 适用题型：评价题、论证题、批判题、选择题（含理由）
   - 示例："你认为...是否合理？为什么？"、"请评价...的优缺点"

6. **创造 (Create)** - 整合要素形成新的整体
   - 典型动词：创造、设计、构思、规划、发明、整合
   - 适用题型：设计题、创作题、规划题、方案题
   - 示例："请设计一个...方案"、"如果让你来...你会怎么做？"

【递进性设计原则】：

1. **梯度递进**：练习设计应从低阶思维向高阶思维递进
2. **建议比例（{grade}年级）**：{", ".join(level_names)}
3. **避免跳跃**：认知层级之间不应跨越超过 2 级，确保学生思维有过渡
4. **标注要求**：在"课堂练习页"和"互动问答页"中，明确标注每道题的认知层级（如【记忆】【理解】【应用】）
5. **{subject}学科适配**：结合{subject}学科特点，设计符合学科思维方式的认知层级练习题
"""

    def validate_bloom_progression(self, levels: List[str]) -> Dict[str, Any]:
        """
        验证认知层级序列的递进性是否合理

        Args:
            levels: 认知层级名称列表

        Returns:
            验证结果：{"valid": bool, "issues": List[str], "suggestions": List[str]}
        """
        issues = []
        suggestions = []

        if len(levels) < 2:
            return {"valid": True, "issues": [], "suggestions": []}

        # 检查层级跳跃
        for i in range(len(levels) - 1):
            current_order = self.get_bloom_level_order(levels[i])
            next_order = self.get_bloom_level_order(levels[i + 1])

            if next_order - current_order > 2:
                current_cn = next((item["chinese"] for item in self.BLOOM_LEVELS if item["level"] == levels[i]), levels[i])
                next_cn = next((item["chinese"] for item in self.BLOOM_LEVELS if item["level"] == levels[i + 1]), levels[i + 1])
                issues.append(f"从{current_cn}到{next_cn}跳跃过大，建议增加中间层级过渡")
                suggestions.append(f"在{current_cn}和{next_cn}之间插入 1-2 个过渡层级")

        # 检查是否缺少基础层级
        if "remember" not in levels and "understand" in levels:
            issues.append("缺少记忆层级直接跳到理解层级")
            suggestions.append("建议先设计基础知识点回忆题，再进行理解性练习")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
        }

    def get_exercise_schema_for_level(self, level: str) -> Dict[str, Any]:
        """
        获取指定认知层级的练习题 schema 结构

        Args:
            level: 认知层级名称

        Returns:
            练习题 schema 结构
        """
        exercise_info = self.BLOOM_EXERCISE_TYPES.get(level, {})

        return {
            "bloom_level": level,
            "chinese_name": next((item["chinese"] for item in self.BLOOM_LEVELS if item["level"] == level), level),
            "exercise_type": exercise_info.get("type", "综合题"),
            "formats": exercise_info.get("formats", []),
            "question": "题目内容",
            "answer": "参考答案",
            "analysis": "解析说明",
            "difficulty": "难度星级（1-3 星）",
        }
