"""
布鲁姆目标分类法模块

基于修订版布鲁姆认知目标分类法（Bloom's Taxonomy），为教学问题
和练习标注认知层级，确保思维训练的递进性。

修订版布鲁姆分类法（2001）包含 6 个认知过程维度：
1. 记忆 (Remember) - 从长时记忆中提取相关知识
2. 理解 (Understand) - 从教学信息中建构意义
3. 应用 (Apply) - 在给定情境中执行或使用程序
4. 分析 (Analyze) - 将材料分解为部分，确定关系
5. 评价 (Evaluate) - 基于标准和规范作出判断
6. 创造 (Create) - 将要素整合为新的整体或原创产品
"""

from enum import Enum
from typing import Dict, List, Optional, Any


class BloomLevel(Enum):
    """布鲁姆认知层级枚举"""

    REMEMBER = "remember"        # 记忆
    UNDERSTAND = "understand"    # 理解
    APPLY = "apply"              # 应用
    ANALYZE = "analyze"          # 分析
    EVALUATE = "evaluate"        # 评价
    CREATE = "create"            # 创造

    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        names = {
            "remember": "记忆",
            "understand": "理解",
            "apply": "应用",
            "analyze": "分析",
            "evaluate": "评价",
            "create": "创造",
        }
        return names[self.value]

    @property
    def description(self) -> str:
        """获取层级描述"""
        descriptions = {
            "remember": "从长时记忆中提取相关信息，如回忆事实、概念、定义、公式等",
            "understand": "从教学信息中建构意义，如解释、说明、归纳、类比等",
            "apply": "在给定的新情境中执行或使用程序，如运用公式解题、应用规则等",
            "analyze": "将材料分解为组成部分，确定部分之间的关系和组织方式",
            "evaluate": "基于标准和规范作出判断，如评估方案优劣、论证观点等",
            "create": "将要素整合为一个新的整体或原创产品，如设计方案、创作作品等",
        }
        return descriptions[self.value]

    @property
    def key_verbs(self) -> List[str]:
        """获取该层级常用的行为动词"""
        verbs = {
            "remember": [
                "回忆", "复述", "背诵", "列举", "定义", "命名",
                "识别", "描述", "指出", "匹配", "选择", "记住"
            ],
            "understand": [
                "解释", "说明", "概括", "归纳", "总结", "举例",
                "分类", "比较", "对比", "推断", "预测", "改写",
                "翻译", "转化", "阐述", "演示"
            ],
            "apply": [
                "应用", "运用", "使用", "执行", "实施", "计算",
                "操作", "演示", "展示", "解决", "构建", "制作"
            ],
            "analyze": [
                "分析", "区分", "分解", "组织", "归因", "找出",
                "识别关系", "比较结构", "剖析", "解析", "鉴别",
                "图示", "推断因果", "辨别"
            ],
            "evaluate": [
                "评价", "评估", "判断", "批判", "论证", "辩护",
                "比较优劣", "选择最佳", "评定", "检验", "证明",
                "评论", "鉴定", "权衡"
            ],
            "create": [
                "创造", "设计", "构思", "规划", "发明", "建构",
                "产生", "开发", "组织", "整合", "改编", "创作",
                "提出方案", "制定计划", "重组"
            ],
        }
        return verbs[self.value]

    @property
    def question_templates(self) -> List[str]:
        """获取该层级的问题模板示例"""
        templates = {
            "remember": [
                "什么是...？",
                "请列举...",
                "请定义...",
                "谁/何时/哪里...？",
                "请描述...",
                "请复述...",
                "...的名称是什么？",
            ],
            "understand": [
                "请解释...的含义",
                "请用你自己的话说明...",
                "请概括...的主要内容",
                "请举例说明...",
                "...和...有什么区别？",
                "为什么...？",
                "请预测...会发生什么",
            ],
            "apply": [
                "请运用...解决以下问题",
                "如何使用...来...",
                "请计算...",
                "请演示如何...",
                "如果...，应该怎么做？",
                "请将...应用到新情境中",
            ],
            "analyze": [
                "请分析...的原因",
                "...的各个部分是如何组织的？",
                "请比较...的异同点",
                "...背后的假设是什么？",
                "请找出...之间的关系",
                "为什么作者要这样写？",
                "请分解...的结构",
            ],
            "evaluate": [
                "你认为...的方案是否合理？为什么？",
                "请评价...的优缺点",
                "如果让你选择，你会选哪个？理由是什么？",
                "请判断...的说法是否正确",
                "你认为...有什么价值？",
                "请论证你的观点",
            ],
            "create": [
                "请设计一个...方案",
                "如果你来...，你会怎么做？",
                "请创作一个...",
                "如何将...和...结合起来解决新问题？",
                "请提出一个新的...",
                "请规划一个...项目",
            ],
        }
        return templates[self.value]

    @classmethod
    def get_all_levels(cls) -> List["BloomLevel"]:
        """获取所有认知层级（按从低到高排序）"""
        return [
            cls.REMEMBER,
            cls.UNDERSTAND,
            cls.APPLY,
            cls.ANALYZE,
            cls.EVALUATE,
            cls.CREATE,
        ]

    @classmethod
    def get_level_by_name(cls, name: str) -> Optional["BloomLevel"]:
        """根据名称获取认知层级"""
        name_lower = name.lower().strip()
        # 支持中文和英文
        name_mapping = {
            "记忆": "remember",
            "理解": "understand",
            "应用": "apply",
            "分析": "analyze",
            "评价": "evaluate",
            "创造": "create",
            "remember": "remember",
            "understand": "understand",
            "apply": "apply",
            "analyze": "analyze",
            "evaluate": "evaluate",
            "create": "create",
        }
        level_name = name_mapping.get(name_lower)
        if level_name:
            return cls(level_name)
        return None


class BloomTaxonomy:
    """
    布鲁姆目标分类法工具类

    提供认知层级的识别、标注、递进性检查等功能
    """

    def __init__(self):
        """初始化布鲁姆分类法工具"""
        self.levels = BloomLevel.get_all_levels()

    def get_level_info(self, level: BloomLevel) -> Dict[str, Any]:
        """
        获取指定层级的完整信息

        Args:
            level: 认知层级

        Returns:
            包含名称、描述、动词、问题模板的字典
        """
        return {
            "level": level.value,
            "chinese_name": level.chinese_name,
            "description": level.description,
            "key_verbs": level.key_verbs,
            "question_templates": level.question_templates,
        }

    def get_all_levels_info(self) -> List[Dict[str, Any]]:
        """
        获取所有层级的完整信息列表

        Returns:
            层级信息列表，按从低到高排序
        """
        return [self.get_level_info(level) for level in self.levels]

    def detect_level_from_verbs(self, verbs: List[str]) -> Optional[BloomLevel]:
        """
        根据行为动词检测认知层级

        Args:
            verbs: 行为动词列表

        Returns:
            匹配的认知层级，如果没有匹配则返回 None
        """
        verbs_lower = [v.lower().strip() for v in verbs]

        for level in self.levels:
            level_verbs = [v.lower() for v in level.key_verbs]
            if any(v in level_verbs for v in verbs_lower):
                return level

        return None

    def detect_level_from_question(self, question: str) -> Optional[BloomLevel]:
        """
        根据问题文本检测认知层级

        Args:
            question: 问题文本

        Returns:
            匹配的认知层级，如果没有匹配则返回 None
        """
        # 检查各层级的问题模板
        for level in self.levels:
            for template in level.question_templates:
                if template in question:
                    return level

        # 检查行为动词
        for level in self.levels:
            for verb in level.key_verbs:
                if verb in question:
                    return level

        return None

    def validate_progression(self, levels: List[BloomLevel]) -> bool:
        """
        验证认知层级的递进性是否合理

        合理的递进性应该：
        1. 不会出现大幅跳跃（如从记忆直接到创造）
        2. 整体呈现上升趋势

        Args:
            levels: 认知层级列表

        Returns:
            递进性是否合理
        """
        if len(levels) < 2:
            return True

        level_order = {level: i for i, level in enumerate(self.levels)}

        # 检查是否有大幅跳跃（跨越 2 个以上层级）
        for i in range(len(levels) - 1):
            current_idx = level_order[levels[i]]
            next_idx = level_order[levels[i + 1]]

            # 允许下降 1 级，但不允许大幅下降
            if next_idx - current_idx > 2:
                return False

        return True

    def suggest_next_level(self, current_level: BloomLevel,
                           allow_regression: bool = False) -> BloomLevel:
        """
        建议下一个认知层级

        Args:
            current_level: 当前层级
            allow_regression: 是否允许回退（用于复习巩固）

        Returns:
            建议的下一个层级
        """
        current_idx = self.levels.index(current_level)

        if current_idx >= len(self.levels) - 1:
            # 已经是最高级，建议回到低级进行综合应用
            return BloomLevel.APPLY

        next_idx = current_idx + 1
        return self.levels[next_idx]

    def get_exercise_template(self, level: BloomLevel,
                              subject: str = "general") -> Dict[str, Any]:
        """
        获取指定认知层级的练习题模板

        Args:
            level: 认知层级
            subject: 学科

        Returns:
            练习题模板
        """
        templates = {
            BloomLevel.REMEMBER: {
                "type": "知识回忆题",
                "formats": ["填空题", "选择题", "判断题", "匹配题", "简答题"],
                "example": "请写出/列举/定义...",
                "scoring_focus": "准确性和完整性",
            },
            BloomLevel.UNDERSTAND: {
                "type": "理解说明题",
                "formats": ["解释题", "举例题", "改写的", "图表题", "归纳题"],
                "example": "请解释...的含义/请举例说明...",
                "scoring_focus": "理解的深度和准确性",
            },
            BloomLevel.APPLY: {
                "type": "应用操作题",
                "formats": ["计算题", "操作题", "应用题", "演示题"],
                "example": "请运用...解决以下问题",
                "scoring_focus": "方法的正确性和结果的准确性",
            },
            BloomLevel.ANALYZE: {
                "type": "分析探究题",
                "formats": ["分析题", "比较题", "关系题", "归因题"],
                "example": "请分析...的原因/请比较...的异同",
                "scoring_focus": "分析的深度和逻辑性",
            },
            BloomLevel.EVALUATE: {
                "type": "评价判断题",
                "formats": ["评价题", "论证题", "选择题（含理由）", "批判题"],
                "example": "请评价.../你认为...是否正确",
                "scoring_focus": "判断的合理性和论证的充分性",
            },
            BloomLevel.CREATE: {
                "type": "创造设计题",
                "formats": ["设计题", "创作题", "规划题", "方案题"],
                "example": "请设计一个...方案/请创作一个...",
                "scoring_focus": "创意性、可行性和完整性",
            },
        }

        return templates.get(level, {})

    def build_bloom_prompt_section(self, grade: str, subject: str) -> str:
        """
        构建布鲁姆分类法的提示词段落

        用于添加到学科提示词中，指导教师设计递进性的问题和练习

        Args:
            grade: 年级
            subject: 学科

        Returns:
            提示词段落
        """
        return f"""
【布鲁姆目标分类法 - 认知层级递进要求】

为确保思维训练的递进性，请按照布鲁姆认知目标分类法设计问题和练习：

**6 个认知层级（从低到高）**：

1. **记忆 (Remember)** - 回忆事实、概念、定义
   - 适用题型：填空题、选择题、判断题、复述题
   - 示例："什么是...？"、"请列举..."、"请定义..."

2. **理解 (Understand)** - 解释、说明、归纳
   - 适用题型：解释题、举例题、改写的、图表题
   - 示例："请解释...的含义"、"请概括..."、"...和...有什么区别？"

3. **应用 (Apply)** - 在新情境中使用知识
   - 适用题型：计算题、应用题、操作题、演示题
   - 示例："请运用...解决问题"、"如何使用..."

4. **分析 (Analyze)** - 区分、组织、找出关系
   - 适用题型：分析题、比较题、关系题、归因题
   - 示例："请分析...的原因"、"比较...的异同"、"找出...之间的关系"

5. **评价 (Evaluate)** - 基于标准作出判断
   - 适用题型：评价题、论证题、批判题、辩护题
   - 示例："你认为...是否合理？为什么？"、"请评价...的优缺点"

6. **创造 (Create)** - 整合要素形成新的整体
   - 适用题型：设计题、创作题、规划题、方案题
   - 示例："请设计一个...方案"、"如果让你来...你会怎么做？"

【递进性设计原则】：

1. **梯度递进**：练习设计应从低阶思维（记忆、理解）向高阶思维（分析、评价、创造）递进
2. **比例合理**：建议比例 - 记忆理解 (40%)、应用 (30%)、分析评价创造 (30%)
3. **避免跳跃**：认知层级之间不应跨越超过 2 级，确保学生思维有过渡
4. **年级适配**：
   - 小学低年级 (1-3)：侧重记忆、理解，适当应用
   - 小学高年级 (4-6)：增加应用、分析
   - 初中 (7-9)：平衡各层级，加强分析、评价
   - 高中 (10-12)：侧重分析、评价、创造，培养高阶思维

【{subject}学科认知层级设计建议】：

- 在"课堂练习页"和"变式训练页"中，明确标注每道题的认知层级
- 确保练习序列呈现递进性（从记忆→理解→应用→分析→评价→创造）
- 在"总结回顾页"中，提供跨层级的综合挑战题
"""


# 便捷函数
def get_bloom_taxonomy() -> BloomTaxonomy:
    """获取布鲁姆分类法工具实例"""
    return BloomTaxonomy()


def get_level_info(level_name: str) -> Optional[Dict[str, Any]]:
    """根据名称获取层级信息"""
    level = BloomLevel.get_level_by_name(level_name)
    if level:
        taxonomy = BloomTaxonomy()
        return taxonomy.get_level_info(level)
    return None


def detect_question_level(question: str) -> Optional[str]:
    """检测问题的认知层级"""
    taxonomy = BloomTaxonomy()
    level = taxonomy.detect_level_from_question(question)
    return level.value if level else None
