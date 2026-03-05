"""
注意力节奏引擎

设计注意捕捉→保持→转移的内容编排，防止学生注意力涣散
基于注意力周期理论，优化 PPT 页面序列的教学节奏
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class AttentionLevel(Enum):
    """注意力水平等级"""
    LOW = "low"           # 低年级：注意力周期短
    MEDIUM = "medium"     # 初中：注意力周期中等
    HIGH = "high"         # 高中：注意力周期较长


class PageCategory(Enum):
    """页面类别（用于节奏控制）"""
    LECTURE = "lecture"       # 讲解类：概念讲解、公式推导、原理说明
    INTERACTIVE = "interactive"  # 互动类：提问、讨论、问答
    PRACTICE = "practice"      # 练习类：课堂练习、变式训练
    VISUAL = "visual"         # 视觉类：图示页、表格页、视频页
    SUMMARY = "summary"       # 总结类：总结回顾、知识框架
    HOOK = "hook"            # 吸引类：情境导入、趣味事实


class AttentionRhythmOptimizer:
    """
    注意力节奏优化器

    核心功能：
    1. 注意力周期模型：根据年级设定每轮注意力的页数
    2. 页面类型节奏规则：避免连续同类页面，确保讲解 - 互动 - 练习交替
    3. Engagement Hooks：在注意力低点插入趣味内容
    4. 页面序列优化：重新编排页面顺序以符合注意力节奏
    """

    # 年级到注意力水平的映射
    GRADE_TO_ATTENTION_LEVEL = {
        "1": AttentionLevel.LOW,
        "2": AttentionLevel.LOW,
        "3": AttentionLevel.LOW,
        "4": AttentionLevel.LOW,
        "5": AttentionLevel.MEDIUM,
        "6": AttentionLevel.MEDIUM,
        "7": AttentionLevel.MEDIUM,
        "8": AttentionLevel.MEDIUM,
        "9": AttentionLevel.HIGH,
        "10": AttentionLevel.HIGH,
        "11": AttentionLevel.HIGH,
        "12": AttentionLevel.HIGH,
    }

    # 注意力周期配置（每轮注意力可持续的页数）
    ATTENTION_CYCLE_CONFIG = {
        AttentionLevel.LOW: {
            "min_pages": 2,
            "max_pages": 3,
            "hook_frequency": 2,  # 每 2 页需要一个吸引点
            "max_same_type": 2,   # 禁止连续超过 2 页同类型
        },
        AttentionLevel.MEDIUM: {
            "min_pages": 3,
            "max_pages": 4,
            "hook_frequency": 3,
            "max_same_type": 2,
        },
        AttentionLevel.HIGH: {
            "min_pages": 4,
            "max_pages": 5,
            "hook_frequency": 4,
            "max_same_type": 3,
        },
    }

    # 页面类型到类别的映射
    PAGE_TYPE_TO_CATEGORY = {
        "封面页": PageCategory.VISUAL,
        "目录页": PageCategory.SUMMARY,
        "情境导入页": PageCategory.HOOK,
        "概念引入页": PageCategory.LECTURE,
        "公式推导页": PageCategory.LECTURE,
        "知识点讲解页": PageCategory.LECTURE,
        "原理讲解页": PageCategory.LECTURE,
        "图示页": PageCategory.VISUAL,
        "表格页": PageCategory.VISUAL,
        "互动问答页": PageCategory.INTERACTIVE,
        "讨论页": PageCategory.INTERACTIVE,
        "课堂练习页": PageCategory.PRACTICE,
        "变式训练页": PageCategory.PRACTICE,
        "易错警示页": PageCategory.INTERACTIVE,
        "总结回顾页": PageCategory.SUMMARY,
        "知识框架页": PageCategory.SUMMARY,
        "对比分析页": PageCategory.LECTURE,
        "实验步骤页": PageCategory.VISUAL,
        "时间轴页": PageCategory.VISUAL,
        # 英语专属
        "单词学习页": PageCategory.INTERACTIVE,
        "语法讲解页": PageCategory.LECTURE,
        "情景对话页": PageCategory.INTERACTIVE,
        "课文分析页": PageCategory.LECTURE,
        # 数学专属
        "例题讲解页": PageCategory.LECTURE,
        # 趣味钩子
        "趣味事实页": PageCategory.HOOK,
        "你知道吗页": PageCategory.HOOK,
        "挑战时刻页": PageCategory.INTERACTIVE,
    }

    # Engagement Hooks 模板
    ENGAGEMENT_HOOKS = {
        "fun_fact": "趣味事实：{content}",
        "did_you_know": "你知道吗？{content}",
        "challenge": "挑战时刻：{content}",
        "real_world": "生活中的应用：{content}",
        "story": "相关故事：{content}",
        "question": "思考问题：{content}",
        "quiz": "快速测验：{content}",
    }

    def __init__(self, grade: str, subject: str = "general"):
        """
        初始化注意力节奏优化器

        Args:
            grade: 年级（1-12）
            subject: 学科
        """
        self.grade = grade
        self.subject = subject
        self.attention_level = self.GRADE_TO_ATTENTION_LEVEL.get(
            grade, AttentionLevel.MEDIUM
        )
        self.config = self.ATTENTION_CYCLE_CONFIG[self.attention_level]

    def get_attention_cycle_length(self) -> Tuple[int, int]:
        """
        获取注意力周期长度

        Returns:
            (min_pages, max_pages): 最小和最大页数
        """
        return (self.config["min_pages"], self.config["max_pages"])

    def get_max_consecutive_same_type(self) -> int:
        """
        获取允许的最大连续同类型页面数

        Returns:
            最大连续页数
        """
        return self.config["max_same_type"]

    def categorize_page(self, page_type: str) -> PageCategory:
        """
        将页面类型分类

        Args:
            page_type: 页面类型

        Returns:
            页面类别
        """
        return self.PAGE_TYPE_TO_CATEGORY.get(
            page_type, PageCategory.LECTURE
        )

    def analyze_rhythm(self, slides: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析页面序列的节奏

        Args:
            slides: 页面列表

        Returns:
            节奏分析报告
        """
        if not slides:
            return {"valid": True, "issues": [], "suggestions": []}

        issues = []
        suggestions = []

        # 检查连续同类型页面
        current_type = None
        consecutive_count = 0
        consecutive_start = 0

        for i, slide in enumerate(slides):
            page_type = slide.get("page_type", "知识点讲解页")
            category = self.categorize_page(page_type)

            if category == current_type:
                consecutive_count += 1
            else:
                # 检查上一组是否超限
                if consecutive_count > self.config["max_same_type"]:
                    issues.append({
                        "type": "consecutive_limit",
                        "start": consecutive_start,
                        "end": i - 1,
                        "count": consecutive_count,
                        "category": current_type.value,
                        "message": f"连续{consecutive_count}页{current_type.value}类型，超过限制{self.config['max_same_type']}"
                    })
                current_type = category
                consecutive_count = 1
                consecutive_start = i

        # 检查最后一组
        if consecutive_count > self.config["max_same_type"]:
            issues.append({
                "type": "consecutive_limit",
                "start": consecutive_start,
                "end": len(slides) - 1,
                "count": consecutive_count,
                "category": current_type.value,
                "message": f"连续{consecutive_count}页{current_type.value}类型，超过限制{self.config['max_same_type']}"
            })

        # 检查互动频率
        interactive_count = sum(
            1 for s in slides
            if self.categorize_page(s.get("page_type", "")) == PageCategory.INTERACTIVE
        )
        hook_count = sum(
            1 for s in slides
            if self.categorize_page(s.get("page_type", "")) == PageCategory.HOOK
        )

        total = len(slides)
        interactive_ratio = interactive_count / total if total > 0 else 0
        hook_ratio = hook_count / total if total > 0 else 0

        # 互动页面应占至少 20%
        if interactive_ratio < 0.2:
            issues.append({
                "type": "low_interaction",
                "ratio": interactive_ratio,
                "message": f"互动页面占比{interactive_ratio:.1%}，建议至少 20%"
            })
            suggestions.append("增加互动问答、讨论或练习页面")

        # 吸引点应每 N 页出现一次
        required_hook_frequency = self.config["hook_frequency"]
        if hook_count > 0:
            avg_gap = total / hook_count
            if avg_gap > required_hook_frequency:
                issues.append({
                    "type": "low_hooks",
                    "avg_gap": avg_gap,
                    "message": f"吸引点平均间隔{avg_gap:.1f}页，建议每{required_hook_frequency}页一个"
                })
                suggestions.append(f"每{required_hook_frequency}页插入一个趣味事实或挑战时刻")

        # 检查页面类型多样性
        unique_categories = set(
            self.categorize_page(s.get("page_type", "")) for s in slides
        )
        if len(unique_categories) < 3:
            issues.append({
                "type": "low_variety",
                "categories": [c.value for c in unique_categories],
                "message": f"页面类型单一，仅{len(unique_categories)}种类型"
            })
            suggestions.append("增加视觉类、互动类、练习类页面的混合使用")

        return {
            "valid": len(issues) == 0,
            "attention_level": self.attention_level.value,
            "cycle_config": self.config,
            "issues": issues,
            "suggestions": suggestions,
            "stats": {
                "total_pages": total,
                "interactive_pages": interactive_count,
                "hook_pages": hook_count,
                "interactive_ratio": interactive_ratio,
                "unique_categories": len(unique_categories)
            }
        }

    def optimize_sequence(self, slides: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        优化页面序列

        策略：
        1. 打散连续同类型页面
        2. 确保讲解 - 互动 - 练习的交替
        3. 在合适位置插入吸引点

        Args:
            slides: 原始页面列表

        Returns:
            优化后的页面列表
        """
        if len(slides) <= 3:
            return slides  # 太短不需要优化

        # 按类别分组
        categorized = {}
        for i, slide in enumerate(slides):
            page_type = slide.get("page_type", "知识点讲解页")
            category = self.categorize_page(page_type)

            if category not in categorized:
                categorized[category] = []
            categorized[category].append((i, slide))

        # 保持封面、目录、总结在原有位置
        fixed_positions = {}
        optimized = []

        for i, slide in enumerate(slides):
            page_type = slide.get("page_type", "")
            if page_type in ["封面页", "目录页", "总结回顾页", "知识框架页"]:
                fixed_positions[i] = slide

        # 获取可移动的页面
        movable = [
            (i, s) for i, s in enumerate(slides)
            if i not in fixed_positions
        ]

        if not movable:
            return slides

        # 重新排列：交替不同类别
        result = []
        used = set()
        categories_order = [
            PageCategory.LECTURE,
            PageCategory.INTERACTIVE,
            PageCategory.VISUAL,
            PageCategory.PRACTICE,
            PageCategory.HOOK,
        ]

        current_idx = 0
        category_idx = 0

        while len(used) < len(movable):
            category = categories_order[category_idx % len(categories_order)]
            category_idx += 1

            if category not in categorized:
                continue

            # 找该类别中未使用的第一个页面
            for pos, slide in categorized[category]:
                if pos not in used and pos not in fixed_positions:
                    result.append(slide)
                    used.add(pos)
                    break

        # 插入固定位置的页面
        final_result = []
        result_idx = 0

        for i in range(len(slides)):
            if i in fixed_positions:
                final_result.append(fixed_positions[i])
            elif result_idx < len(result):
                final_result.append(result[result_idx])
                result_idx += 1

        return final_result

    def suggest_hooks(self, slides: List[Dict[str, Any]], slide_index: int) -> List[Dict[str, str]]:
        """
        为指定位置建议 Engagement Hooks

        Args:
            slides: 页面列表
            slide_index: 插入位置

        Returns:
            建议的钩子列表
        """
        suggestions = []

        # 获取当前内容的主题
        if slide_index < len(slides):
            current_slide = slides[slide_index]
            topic = current_slide.get("title", "当前内容")
        else:
            topic = "相关知识"

        # 生成不同类型的钩子建议
        hook_templates = [
            ("fun_fact", f"趣味事实：与{topic}相关的有趣发现"),
            ("did_you_know", f"你知道吗？{topic}背后的故事"),
            ("challenge", f"挑战时刻：关于{topic}的小测验"),
            ("real_world", f"生活中的应用：{topic}在实际生活中的例子"),
            ("question", f"思考问题：如果...会发生什么？"),
        ]

        for hook_type, content in hook_templates:
            suggestions.append({
                "type": hook_type,
                "template": self.ENGAGEMENT_HOOKS[hook_type],
                "suggested_content": content,
                "page_type": "趣味事实页" if hook_type == "fun_fact" else
                            "你知道吗页" if hook_type == "did_you_know" else
                            "挑战时刻页" if hook_type == "challenge" else
                            "互动问答页"
            })

        return suggestions

    def get_rhythm_prompt(self) -> str:
        """
        获取用于 LLM 的节奏编排提示词

        Returns:
            节奏编排指令
        """
        min_pages, max_pages = self.get_attention_cycle_length()
        max_same = self.get_max_consecutive_same_type()
        hook_freq = self.config["hook_frequency"]

        return f"""【注意力节奏编排要求】

基于注意力周期理论，请按以下规则组织 PPT 页面序列：

1. **注意力周期控制**：
   - 每{min_pages}-{max_pages}页为一个注意力周期
   - 每个周期内必须包含至少 1 个互动或视觉元素
   - 避免长时间单向讲解

2. **页面类型多样性**：
   - 禁止连续超过{max_same}页相同类型的页面（如连续讲解）
   - 确保"讲解→互动→练习"的交替节奏
   - 每{hook_freq}页插入一个吸引点（趣味事实/你知道吗/挑战时刻）

3. ** Engagement Hooks（注意力吸引点）**：
   - 在连续讲解 2 页后，插入互动或视觉页面
   - 在复杂概念讲解前，先用生活实例或趣味事实引入
   - 在练习前，设置挑战时刻激发兴趣

4. **建议的页面序列模式**：
   - 开场：情境导入（钩子）→ 目标展示
   - 新知：概念引入（视觉）→ 讲解（1-2 页）→ 互动问答 → 讲解（1-2 页）
   - 巩固：示例演示 → 课堂练习 → 易错警示（互动）
   - 结尾：总结回顾 → 拓展思考（钩子）

5. **年级适配**：
   - 低年级（1-4 年级）：更快的节奏，每 2 页切换类型，大量视觉和互动
   - 中年级（5-8 年级）：中等节奏，每 3 页切换，平衡讲解与互动
   - 高年级（9-12 年级）：较深的内容，每 4 页切换，但仍需保持变化"""


def get_attention_optimizer(grade: str, subject: str = "general") -> AttentionRhythmOptimizer:
    """
    获取注意力节奏优化器实例

    Args:
        grade: 年级（1-12）
        subject: 学科

    Returns:
        AttentionRhythmOptimizer 实例
    """
    return AttentionRhythmOptimizer(grade, subject)
