from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import jieba

# 动画效果注入模块（条件导入）
try:
    from .pptx_animator import PPTXAnimator
    ANIMATION_AVAILABLE = True
except ImportError:
    ANIMATION_AVAILABLE = False

logger = logging.getLogger(__name__)

# 预定义颜色，供类属性使用
_COLOR_RED = RGBColor(255, 107, 107)
_COLOR_ORANGE = RGBColor(255, 159, 67)
_COLOR_GOLD = RGBColor(255, 215, 0)
_COLOR_DARK_ORANGE = RGBColor(255, 140, 0)
_COLOR_TURQUOISE = RGBColor(64, 224, 208)
COLOR_TURQUOISE_2 = RGBColor(78, 205, 196)
COLOR_TURQUOISE_3 = RGBColor(102, 205, 170)
COLOR_BLUE_1 = RGBColor(52, 152, 219)
COLOR_BLUE_2 = RGBColor(68, 138, 255)
COLOR_BLUE_3 = RGBColor(63, 81, 181)
COLOR_BLUE_4 = RGBColor(106, 90, 205)
COLOR_BLUE_5 = RGBColor(41, 128, 185)
COLOR_GREEN_1 = RGBColor(67, 160, 71)
COLOR_GREEN_2 = RGBColor(39, 174, 96)
COLOR_GREEN_3 = RGBColor(102, 187, 106)
COLOR_BLUE_6 = RGBColor(33, 150, 243)
COLOR_GREEN_4 = RGBColor(76, 175, 80)

# 学科主题色映射
SUBJECT_COLORS = {
    "math": {"primary": COLOR_BLUE_5, "secondary": COLOR_BLUE_1, "name": "数学蓝"},
    "english": {"primary": COLOR_GREEN_2, "secondary": COLOR_GREEN_3, "name": "英语绿"},
    "chinese": {"primary": _COLOR_RED, "secondary": _COLOR_GOLD, "name": "语文红"},
    "physics": {"primary": _COLOR_ORANGE, "secondary": COLOR_BLUE_5, "name": "物理橙"},
    "chemistry": {"primary": COLOR_BLUE_3, "secondary": COLOR_GREEN_1, "name": "化学蓝"},
    "biology": {"primary": COLOR_GREEN_1, "secondary": COLOR_TURQUOISE_2, "name": "生物绿"},
    "history": RGBColor(128, 0, 128),
    "politics": RGBColor(186, 85, 211),
    "geography": RGBColor(34, 139, 34),
    "general": {"primary": COLOR_BLUE_6, "secondary": COLOR_TURQUOISE_2, "name": "通用蓝"},
}


def add_pinyin_text(paragraph, text: str, font_size: int, is_title: bool = False):
    """
    添加带拼音的文本（简化版：仅对常见字添加拼音标注）
    实际项目中建议使用 pypinyin 库进行完整拼音转换
    Args:
        paragraph: 段落对象
        text: 要添加的文本
        font_size: 字号
        is_title: 是否标题
    """
    # 简化实现：直接添加文本，拼音标注需要额外的 pypinyin 库支持
    # 在实际部署时，可以安装 pypinyin: pip install pypinyin
    # 然后使用：from pypinyin import lazy_pinyin
    paragraph.text = text
    if is_title:
        paragraph.font.size = Pt(font_size + 4)
        paragraph.font.bold = True
    else:
        paragraph.font.size = Pt(font_size)


class PPTPageType:
    """PPT 页面类型"""
    COVER = "封面页"
    TOC = "目录页"
    CONTENT = "知识点讲解页"
    INTERACTION = "互动问答页"
    EXERCISE = "课堂练习页"
    SUMMARY = "总结回顾页"

    # 新增页面类型（优化版：增加页面类型多样性）
    DIAGRAM = "图示页"  # 流程图、结构图、概念图
    TABLE = "表格页"  # 对比表、分类表、数据表
    COMPARISON = "对比分析页"  # 对比两种或多种概念

    # 英语学科特殊页面类型
    VOCABULARY = "单词学习页"
    GRAMMAR = "语法讲解页"
    DIALOGUE = "情景对话页"
    ANALYSIS = "课文分析页"

    # 数学学科特殊页面类型
    CONCEPT = "概念引入页"  # 直观→抽象概念形成
    FORMULA_DERIVATION = "公式推导页"  # 逐步标注推导过程
    EXAMPLE_PROBLEM = "例题讲解页"  # 四步法（审题→分析→解题→反思）
    VARIATION_PRACTICE = "变式训练页"  # 梯度练习
    COMMON_MISTAKES = "易错警示页"  # 错误 vs 正确对比

    # 互动课堂页面类型（feat-017）
    QUIZ = "互动选择题页"  # ABCD 选项选择题
    CLICK_TO_REVEAL = "点击显示答案页"  # 点击显示隐藏内容
    MATCHING = "拖拽匹配游戏页"  # 单词 - 释义配对
    QUIZ_GAME = "随堂测验页"  # 多题测验
    FILL_BLANK = "填空题页"  # 填空练习

    # 理科实验页面类型（feat-031 物理/化学/生物）
    EXPERIMENT_DESIGN = "实验设计页"  # 探究目的、器材、步骤
    EXPERIMENT_OBSERVATION = "现象观察页"  # 实验现象记录
    DATA_ANALYSIS = "数据分析页"  # 数据处理、规律发现
    LAW_SUMMARY = "规律归纳页"  # 从实验提炼规律
    APPLICATION_TRANSFER = "应用迁移页"  # 联系实际应用
    EXPERIMENT_STEPS = "实验步骤页"  # 仪器、药品、操作流程
    REACTION_PHENOMENA = "反应现象页"  # 颜色变化、气体、沉淀
    CHEMICAL_EQUATION = "化学方程式页"  # 方程式书写、配平
    MICROSCOPIC_EXPLANATION = "微观解释页"  # 分子/原子/离子模型
    PERIODIC_TREND = "元素周期律页"  # 周期表位置、性质递变
    STRUCTURE_OBSERVATION = "结构观察页"  # 细胞/组织/器官结构
    FUNCTION_ANALYSIS = "功能分析页"  # 结构与功能适应
    PROCESS_DESCRIPTION = "过程描述页"  # 生命活动过程
    SYSTEM_THINKING = "系统思维页"  # 层次关系、整体协调
    EXPERIMENT_INQUIRY = "实验探究页"  # 观察实验、对照实验


class PPTStyle:
    """PPT 样式配置（优化版：细化年级自适应规则）"""

    # 风格配置（三种 PPT 风格）
    STYLE_CONFIG = {
        "fun": {
            "name": "活泼趣味",
            "description": "鲜艳暖色配色，活泼生动，适合低年级",
            "color_scheme": "warm",  # 暖色系
            "font_family": "rounded",  # 圆体
            "layout_density": "spacious",  # 宽松布局，大量留白
            "decoration_level": "high",  # 高装饰性
            "border_radius": 12,  # 大圆角
            "use_gradients": True,  # 使用渐变
            "animation_style": "bouncy",  # 活泼动画
        },
        "simple": {
            "name": "简约清晰",
            "description": "灰蓝冷色配色，简洁专业，适合高年级",
            "color_scheme": "cool",  # 冷色系
            "font_family": "sans-serif",  # 黑体
            "layout_density": "compact",  # 紧凑布局
            "decoration_level": "low",  # 低装饰性
            "border_radius": 4,  # 小圆角
            "use_gradients": False,  # 不使用渐变
            "animation_style": "fade",  # 淡入动画
        },
        "theme": {
            "name": "学科主题",
            "description": "根据学科自动选择主题色",
            "color_scheme": "dynamic",  # 动态配色
            "font_family": "sans-serif",  # 黑体
            "layout_density": "balanced",  # 平衡布局
            "decoration_level": "medium",  # 中等装饰性
            "border_radius": 8,  # 中圆角
            "use_gradients": False,
            "animation_style": "slide",  # 滑动动画
        },
    }

    # 年级组配置（三个学段）
    GRADE_GROUPS = {
        "elementary_low": {
            "name": "小学低年级（1-3 年级）",
            "grades": ["1", "2", "3"],
            "description": "特大字号、鲜艳配色、大量留白、趣味化表达",
            "teaching_strategy": "直观形象教学为主，多采用图片、动画、游戏等形式， attention span 短，每页内容少而精",
            "interaction_style": "简单问答、跟读、指认、小游戏",
        },
        "elementary_high": {
            "name": "小学高年级（4-6 年级）",
            "grades": ["4", "5", "6"],
            "description": "较大字号、明快配色、图文并茂、互动游戏式问答",
            "teaching_strategy": "逐步过渡到抽象思维，增加逻辑推理内容，培养自主学习能力",
            "interaction_style": "小组讨论、角色扮演、竞赛游戏、思维导图",
        },
        "middle": {
            "name": "初中（7-9 年级）",
            "grades": ["7", "8", "9"],
            "description": "标准字号、稳重配色、知识体系化、重点标注",
            "teaching_strategy": "系统化知识讲解，注重知识间的联系，培养批判性思维和综合运用能力",
            "interaction_style": "探究性问题、辩论、案例分析、项目式学习",
        },
        "high_school": {
            "name": "高中（10-12 年级）",
            "grades": ["10", "11", "12"],
            "description": "学术风格、严谨配色、高信息密度、高考导向",
            "teaching_strategy": "深度知识讲解，强调学科核心素养，注重知识迁移和综合运用，强化应试能力",
            "interaction_style": "学术研讨、高考真题分析、变式训练、专题探究",
        },
    }

    # 年级样式配置（细化到每个年级）
    GRADE_STYLES = {
        # 小学低年级（1-3 年级）：特大字号、鲜艳配色
        "1": {
            "font_size": 36,  # 增大字号
            "title_size": 48,
            "primary": _COLOR_RED,
            "secondary": COLOR_TURQUOISE_2,
            "group": "elementary_low",
            "need_pinyin": True,  # 语文需要拼音标注
            "max_content_lines": 3,  # 每页最多内容行数
            "use_icons": True,  # 使用图标辅助理解
            "animation_suggestion": "使用活泼的进入动画",
        },
        "2": {
            "font_size": 34,
            "title_size": 44,
            "primary": _COLOR_ORANGE,
            "secondary": COLOR_TURQUOISE_3,
            "group": "elementary_low",
            "need_pinyin": True,
            "max_content_lines": 4,
            "use_icons": True,
            "animation_suggestion": "使用活泼的进入动画",
        },
        "3": {
            "font_size": 30,
            "title_size": 40,
            "primary": _COLOR_GOLD,
            "secondary": _COLOR_DARK_ORANGE,
            "group": "elementary_low",
            "need_pinyin": True,
            "max_content_lines": 4,
            "use_icons": True,
            "animation_suggestion": "使用适中的进入动画",
        },
        # 小学高年级（4-6 年级）：较大字号、明快配色
        "4": {
            "font_size": 26,
            "title_size": 36,
            "primary": _COLOR_TURQUOISE,
            "secondary": COLOR_TURQUOISE_2,
            "group": "elementary_high",
            "need_pinyin": False,
            "max_content_lines": 5,
            "use_icons": True,
            "animation_suggestion": "使用简洁的进入动画",
        },
        "5": {
            "font_size": 24,
            "title_size": 34,
            "primary": COLOR_BLUE_1,
            "secondary": COLOR_BLUE_2,
            "group": "elementary_high",
            "need_pinyin": False,
            "max_content_lines": 6,
            "use_icons": False,
            "animation_suggestion": "使用简洁的进入动画",
        },
        "6": {
            "font_size": 22,
            "title_size": 32,
            "primary": COLOR_BLUE_3,
            "secondary": COLOR_BLUE_4,
            "group": "elementary_high",
            "need_pinyin": False,
            "max_content_lines": 6,
            "use_icons": False,
            "animation_suggestion": "使用淡入动画",
        },
        # 初中（7-9 年级）：标准字号、稳重配色
        "7": {
            "font_size": 20,
            "title_size": 30,
            "primary": COLOR_BLUE_5,
            "secondary": COLOR_GREEN_1,
            "group": "middle",
            "need_pinyin": False,
            "max_content_lines": 7,
            "use_icons": False,
            "animation_suggestion": "使用淡入或擦除动画",
        },
        "8": {
            "font_size": 18,
            "title_size": 28,
            "primary": COLOR_GREEN_2,
            "secondary": COLOR_GREEN_3,
            "group": "middle",
            "need_pinyin": False,
            "max_content_lines": 8,
            "use_icons": False,
            "animation_suggestion": "使用简洁的切换动画",
        },
        "9": {
            "font_size": 18,
            "title_size": 26,
            "primary": COLOR_BLUE_6,
            "secondary": COLOR_GREEN_4,
            "group": "middle",
            "need_pinyin": False,
            "max_content_lines": 8,
            "use_icons": False,
            "animation_suggestion": "使用无动画或简单切换",
        },
        # 高中（10-12 年级）：学术风格、严谨配色
        "10": {
            "font_size": 18,
            "title_size": 26,
            "primary": COLOR_BLUE_3,
            "secondary": COLOR_BLUE_5,
            "group": "high_school",
            "need_pinyin": False,
            "max_content_lines": 8,
            "use_icons": False,
            "animation_suggestion": "使用专业克制的切换动画",
        },
        "11": {
            "font_size": 16,
            "title_size": 24,
            "primary": COLOR_GREEN_2,
            "secondary": COLOR_BLUE_3,
            "group": "high_school",
            "need_pinyin": False,
            "max_content_lines": 9,
            "use_icons": False,
            "animation_suggestion": "使用简洁动画或无动画",
        },
        "12": {
            "font_size": 16,
            "title_size": 24,
            "primary": COLOR_BLUE_6,
            "secondary": COLOR_GREEN_1,
            "group": "high_school",
            "need_pinyin": False,
            "max_content_lines": 10,
            "use_icons": False,
            "animation_suggestion": "使用无动画，专注内容呈现",
        },
    }

    @classmethod
    def get_style(cls, grade: str) -> Dict[str, Any]:
        """获取年级对应的样式"""
        return cls.GRADE_STYLES.get(grade, cls.GRADE_STYLES["6"])

    @classmethod
    def get_style_config(cls, style: str = "simple") -> Dict[str, Any]:
        """获取 PPT 风格配置"""
        return cls.STYLE_CONFIG.get(style, cls.STYLE_CONFIG["simple"])

    @classmethod
    def get_subject_color(cls, subject: str) -> Dict[str, Any]:
        """获取学科主题色"""
        color_info = SUBJECT_COLORS.get(subject, SUBJECT_COLORS["general"])
        # 处理某些学科直接定义了颜色值的情况
        if isinstance(color_info, RGBColor):
            return {"primary": color_info, "secondary": SUBJECT_COLORS["general"]["secondary"], "name": subject}
        return color_info

    @classmethod
    def get_grade_group(cls, grade: str) -> str:
        """获取年级所属组别"""
        style = cls.get_style(grade)
        return style.get("group", "elementary_high")

    @classmethod
    def need_pinyin(cls, grade: str, subject: str = "chinese") -> bool:
        """判断是否需要拼音标注（仅小学低年级语文）"""
        if subject != "chinese":
            return False
        style = cls.get_style(grade)
        return style.get("need_pinyin", False)


class PPTGenerator:
    """PPT 文件生成器"""

    def __init__(self):
        """初始化 PPT 生成器"""
        pass

    def generate(
        self,
        content: Dict[str, Any],
        output_path: Path,
        grade: str = "6",
        style: str = "simple",
        subject: str = "general"
    ) -> Path:
        """
        生成 PPT 文件
        Args:
            content: PPT 内容数据
            output_path: 输出文件路径
            grade: 年级
            style: PPT 风格
            subject: 学科（用于拼音标注等特性）
        Returns:
            生成的 PPT 文件路径
        """
        try:
            prs = Presentation()
            prs.slide_width = Inches(10)
            prs.slide_height = Inches(7.5)

            # 获取年级样式配置
            grade_style = PPTStyle.get_style(grade)
            title_size = grade_style["title_size"]
            content_size = grade_style["font_size"]
            grade_group = grade_style.get("group", "elementary_high")
            use_pinyin = PPTStyle.need_pinyin(grade, subject)

            # 获取 PPT 风格配置
            ppt_style_config = PPTStyle.get_style_config(style)

            # 确定主色和辅助色：根据风格决定
            if style == "theme" and subject in SUBJECT_COLORS:
                # 学科主题模式：使用学科颜色
                subject_color = PPTStyle.get_subject_color(subject)
                primary_color = subject_color["primary"]
                secondary_color = subject_color["secondary"]
            else:
                # 其他模式：使用年级默认颜色
                primary_color = grade_style["primary"]
                secondary_color = grade_style["secondary"]

                # 活泼风格：调整为更鲜艳的暖色
                if style == "fun":
                    primary_color = _COLOR_RED if grade_group == "elementary_low" else _COLOR_ORANGE
                    secondary_color = COLOR_TURQUOISE_2 if grade_group == "elementary_low" else COLOR_TURQUOISE_3
                # 简约风格：使用冷色调
                elif style == "simple":
                    primary_color = COLOR_BLUE_5 if grade_group == "middle" else COLOR_BLUE_1
                    secondary_color = COLOR_GREEN_1 if grade_group == "middle" else COLOR_BLUE_2

            # 生成封面页
            self._add_cover_slide(
                prs,
                content.get("title", "教学 PPT"),
                title_size,
                primary_color,
                use_pinyin
            )

            # 生成目录页
            if any(s.get("page_type") == PPTPageType.TOC for s in content.get("slides", [])):
                self._add_toc_slide(
                    prs,
                    content.get("slides", []),
                    title_size,
                    content_size,
                    secondary_color
                )

            # 生成内容页
            for slide_data in content.get("slides", []):
                page_type = slide_data.get("page_type", PPTPageType.CONTENT)

                if page_type == PPTPageType.CONTENT:
                    self._add_content_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.INTERACTION:
                    self._add_interaction_slide(
                        prs,
                        slide_data,
                        content_size,
                        secondary_color
                    )
                elif page_type == PPTPageType.EXERCISE:
                    self._add_exercise_slide(
                        prs,
                        slide_data,
                        content_size,
                        secondary_color
                    )
                elif page_type == PPTPageType.SUMMARY:
                    self._add_summary_slide(
                        prs,
                        content,
                        title_size,
                        content_size,
                        primary_color
                    )
                # 新增页面类型支持
                elif page_type == PPTPageType.DIAGRAM:
                    self._add_diagram_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.TABLE:
                    self._add_table_slide(
                        prs,
                        slide_data,
                        content_size,
                        secondary_color
                    )
                elif page_type == PPTPageType.COMPARISON:
                    self._add_comparison_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color,
                        secondary_color
                    )
                # 英语学科专属页面类型
                elif page_type == PPTPageType.VOCABULARY:
                    self._add_vocabulary_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.GRAMMAR:
                    self._add_grammar_slide(
                        prs,
                        slide_data,
                        content_size,
                        secondary_color
                    )
                elif page_type == PPTPageType.DIALOGUE:
                    self._add_dialogue_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.ANALYSIS:
                    self._add_analysis_slide(
                        prs,
                        slide_data,
                        content_size,
                        secondary_color
                    )
                # 数学学科专属页面类型
                elif page_type == PPTPageType.CONCEPT:
                    # 概念引入页：复用内容页逻辑，增加概念字段处理
                    self._add_content_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.FORMULA_DERIVATION:
                    # 公式推导页：复用内容页逻辑，公式步骤在 content 中展示
                    self._add_content_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.EXAMPLE_PROBLEM:
                    # 例题讲解页：复用内容页逻辑
                    self._add_content_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.VARIATION_PRACTICE:
                    # 变式训练页：复用练习页逻辑
                    self._add_exercise_slide(
                        prs,
                        slide_data,
                        content_size,
                        secondary_color
                    )
                elif page_type == PPTPageType.COMMON_MISTAKES:
                    # 易错警示页：复用对比分析页逻辑（错误 vs 正确对比）
                    self._add_comparison_slide(
                        prs,
                        slide_data,
                        content_size,
                        _COLOR_RED,  # 红色表示错误
                        COLOR_GREEN_1  # 绿色表示正确
                    )
                # 互动课堂页面类型（feat-017）
                elif page_type == PPTPageType.QUIZ:
                    self._add_quiz_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color,
                        secondary_color
                    )
                elif page_type == PPTPageType.CLICK_TO_REVEAL:
                    self._add_click_to_reveal_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.MATCHING:
                    self._add_matching_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color,
                        secondary_color
                    )
                elif page_type == PPTPageType.QUIZ_GAME:
                    self._add_quiz_game_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.FILL_BLANK:
                    self._add_fill_blank_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color,
                        secondary_color
                    )
                # 理科实验页面类型（feat-031 物理/化学/生物）
                elif page_type == PPTPageType.EXPERIMENT_DESIGN:
                    self._add_experiment_design_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.EXPERIMENT_OBSERVATION:
                    self._add_experiment_observation_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.DATA_ANALYSIS:
                    self._add_data_analysis_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color,
                        secondary_color
                    )
                elif page_type == PPTPageType.LAW_SUMMARY:
                    self._add_law_summary_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.APPLICATION_TRANSFER:
                    self._add_application_transfer_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.EXPERIMENT_STEPS:
                    self._add_experiment_steps_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.REACTION_PHENOMENA:
                    self._add_reaction_phenomena_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.CHEMICAL_EQUATION:
                    self._add_chemical_equation_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.MICROSCOPIC_EXPLANATION:
                    self._add_microscopic_explanation_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.PERIODIC_TREND:
                    self._add_periodic_trend_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.STRUCTURE_OBSERVATION:
                    self._add_structure_observation_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.FUNCTION_ANALYSIS:
                    self._add_function_analysis_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.PROCESS_DESCRIPTION:
                    self._add_process_description_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.SYSTEM_THINKING:
                    self._add_system_thinking_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color
                    )
                elif page_type == PPTPageType.EXPERIMENT_INQUIRY:
                    self._add_experiment_inquiry_slide(
                        prs,
                        slide_data,
                        content_size,
                        primary_color,
                        secondary_color
                    )

            # 保存文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(output_path))
            logger.info(f"PPT 文件已生成: {output_path}")

            # 添加动画效果（如果动画模块可用）
            if ANIMATION_AVAILABLE:
                try:
                    from .pptx_animator import add_animation_to_ppt
                    logger.info(f"正在为 PPT 添加动画效果（年级：{grade}）...")
                    add_animation_to_ppt(str(output_path), str(output_path), grade, subject)
                    logger.info(f"动画效果已添加：{output_path}")
                except Exception as e:
                    logger.warning(f"动画添加失败：{e}，PPT 文件仍可正常使用")
            return output_path

        except Exception as e:
            logger.error(f"PPT 文件生成失败: {e}")
            raise RuntimeError(f"PPT 文件生成失败: {e}") from e

    def _add_cover_slide(
        self,
        prs: Presentation,
        title: str,
        title_size: int,
        color: RGBColor,
        use_pinyin: bool = False
    ):
        """添加封面页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        # 手动添加标题文本框（因为空白布局没有占位符）
        title_box = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1.5))
        text_frame = title_box.text_frame
        text_frame.text = title

        # 设置标题样式
        title_para = text_frame.paragraphs[0]
        title_para.alignment = PP_ALIGN.CENTER
        title_para.font.size = Pt(title_size)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 添加副标题
        subtitle_box = slide.shapes.add_textbox(Inches(2), Inches(4), Inches(6), Inches(1))
        subtitle_frame = subtitle_box.text_frame
        subtitle_frame.text = "AI 教学 PPT 生成器"

        subtitle_para = subtitle_frame.paragraphs[0]
        subtitle_para.alignment = PP_ALIGN.CENTER
        subtitle_para.font.size = Pt(title_size - 10)
        subtitle_para.font.color.rgb = RGBColor(128, 128, 128)

    def _add_toc_slide(
        self,
        prs: Presentation,
        slides: List[Dict[str, Any]],
        title_size: int,
        content_size: int,
        color: RGBColor
    ):
        """添加目录页"""
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # 标题和内容布局

        # 标题
        title_box = slide.shapes.title
        title_box.text = "目录"
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(title_size)
        title_para.font.color.rgb = color

        # 目录内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
        text_frame = content_box.text_frame

        for idx, slide_data in enumerate(slides):
            if slide_data.get("page_type") == PPTPageType.TOC:
                continue

            p = text_frame.add_paragraph()
            p.text = f"{idx + 1}. {slide_data.get('title', '未知标题')}"
            p.font.size = Pt(content_size)
            p.level = 0

    def _add_content_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加内容页（优化版：增加图示、表格、流程图支持）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])  # 标题和内容布局

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
        text_frame = content_box.text_frame

        for item in slide_data.get("content", []):
            p = text_frame.add_paragraph()
            p.text = item
            p.font.size = Pt(font_size)
            p.level = 0

        # 添加互动环节
        if slide_data.get("interaction"):
            p = text_frame.add_paragraph()
            p.text = f"\n💡 互动：{slide_data['interaction']}"
            p.font.size = Pt(font_size - 2)
            p.font.color.rgb = RGBColor(0, 128, 0)
            p.level = 0

        # 添加口诀
        if slide_data.get("mnemonic"):
            p = text_frame.add_paragraph()
            p.text = f"\n📝 记忆口诀：{slide_data['mnemonic']}"
            p.font.size = Pt(font_size - 2)
            p.font.color.rgb = RGBColor(128, 0, 128)
            p.level = 0

    def _add_diagram_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加图示页（优化版：支持流程图、结构图、概念图）"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        # 标题
        title_text = slide_data.get("title", "知识图示")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.alignment = PP_ALIGN.CENTER

        # 创建图示容器（用文本框模拟）
        diagram_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.4), Inches(5))
        diagram_frame = diagram_box.text_frame
        diagram_frame.word_wrap = True

        # 渲染图示内容
        diagram_type = slide_data.get("diagram_type", "flowchart")
        diagram_data = slide_data.get("diagram_content", [])

        if diagram_type == "flowchart":
            # 流程图样式
            for i, item in enumerate(diagram_data):
                p = diagram_frame.add_paragraph()
                p.text = f"┌{'─' * 50}┐" if i == 0 else f"│ {item}"
                p.font.size = Pt(font_size)
                p.alignment = PP_ALIGN.CENTER
        elif diagram_type == "structure":
            # 结构图样式
            for item in diagram_data:
                p = diagram_frame.add_paragraph()
                p.text = f"  ● {item}"
                p.font.size = Pt(font_size)
        else:
            # 默认列表样式
            for item in diagram_data:
                p = diagram_frame.add_paragraph()
                p.text = f"• {item}"
                p.font.size = Pt(font_size)

    def _add_table_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加表格页（优化版：支持对比表、分类表、数据表）"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        # 标题
        title_text = slide_data.get("title", "数据表格")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.alignment = PP_ALIGN.CENTER

        # 获取表格数据
        table_data = slide_data.get("table_data", [])
        if not table_data:
            return

        rows = len(table_data) + 1  # +1 for header
        cols = len(table_data[0]) if table_data else 4

        # 创建表格
        table_x, table_y = Inches(0.8), Inches(1.5)
        table_width, table_height = Inches(8.4), Inches(5)
        table = slide.shapes.add_table(rows, cols, table_x, table_y, table_width, table_height).table

        # 设置列宽
        for i in range(cols):
            table.columns[i].width = table_width / cols

        # 填充表头
        headers = slide_data.get("table_headers", [f"列{i+1}" for i in range(cols)])
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = header
            cell.fill.solid()
            cell.fill.fore_color.rgb = color
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(font_size)
                paragraph.font.color.rgb = RGBColor(255, 255, 255)
                paragraph.font.bold = True
                paragraph.alignment = PP_ALIGN.CENTER

        # 填充数据行
        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_text in enumerate(row_data):
                cell = table.cell(row_idx + 1, col_idx)
                cell.text = str(cell_text)
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(font_size - 2)
                    paragraph.alignment = PP_ALIGN.CENTER
                    # 交替行颜色
                    if row_idx % 2 == 0:
                        cell.fill.solid()
                        cell.fill.fore_color.rgb = RGBColor(245, 245, 245)

    def _add_interaction_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加互动问答页"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "互动问答")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
        text_frame = content_box.text_frame

        for item in slide_data.get("content", []):
            p = text_frame.add_paragraph()
            p.text = item
            p.font.size = Pt(font_size)

    def _add_exercise_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加课堂练习页"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "课堂练习")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
        text_frame = content_box.text_frame

        for item in slide_data.get("content", []):
            p = text_frame.add_paragraph()
            p.text = item
            p.font.size = Pt(font_size)

    def _add_summary_slide(
        self,
        prs: Presentation,
        content: Dict[str, Any],
        title_size: int,
        font_size: int,
        color: RGBColor
    ):
        """添加总结回顾页"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = "总结回顾"
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(title_size)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4))
        text_frame = content_box.text_frame

        p = text_frame.add_paragraph()
        p.text = content.get("summary", "")
        p.font.size = Pt(font_size)
        p.font.bold = True

        p = text_frame.add_paragraph()
        p.text = "\n重点："
        p.font.size = Pt(font_size)
        p.font.bold = True

        for point in content.get("key_points", []):
            p = text_frame.add_paragraph()
            p.text = f"• {point}"
            p.font.size = Pt(font_size)

    def _add_vocabulary_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加单词学习页（英语学科专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "单词学习")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        # 显示单词列表
        vocabulary = slide_data.get("vocabulary", [])
        if vocabulary:
            for vocab_item in vocabulary:
                word = vocab_item.get("word", "")
                phonetic = vocab_item.get("phonetic", "")
                meaning = vocab_item.get("meaning", "")
                example = vocab_item.get("example", "")

                # 单词（大号字体）
                p = text_frame.add_paragraph()
                p.text = word
                p.font.size = Pt(font_size + 4)
                p.font.color.rgb = color
                p.font.bold = True

                # 音标
                if phonetic:
                    p = text_frame.add_paragraph()
                    p.text = f"  [{phonetic}]"
                    p.font.size = Pt(font_size)
                    p.font.color.rgb = RGBColor(128, 128, 128)

                # 释义
                if meaning:
                    p = text_frame.add_paragraph()
                    p.text = f"  {meaning}"
                    p.font.size = Pt(font_size)

                # 例句
                if example:
                    p = text_frame.add_paragraph()
                    p.text = f"  例：{example}"
                    p.font.size = Pt(font_size - 2)
                    p.font.color.rgb = RGBColor(0, 100, 200)

                # 空行分隔
                p = text_frame.add_paragraph()
                p.text = ""
        else:
            # 没有词汇数据时，显示普通内容
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_grammar_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加语法讲解页（英语学科专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "语法讲解")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4.5))
        text_frame = content_box.text_frame

        # 语法规则说明
        grammar = slide_data.get("grammar", "")
        if grammar:
            p = text_frame.add_paragraph()
            p.text = "语法规则："
            p.font.size = Pt(font_size + 2)
            p.font.color.rgb = color
            p.font.bold = True

            p = text_frame.add_paragraph()
            p.text = grammar
            p.font.size = Pt(font_size)

            p = text_frame.add_paragraph()
            p.text = ""
        else:
            # 显示普通内容
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

        # 例句
        if slide_data.get("examples"):
            p = text_frame.add_paragraph()
            p.text = "\n例句："
            p.font.size = Pt(font_size + 2)
            p.font.color.rgb = RGBColor(0, 100, 200)
            p.font.bold = True

            for example in slide_data["examples"]:
                p = text_frame.add_paragraph()
                p.text = f"• {example}"
                p.font.size = Pt(font_size)

    def _add_dialogue_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加情景对话页（英语学科专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "情景对话")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4.5))
        text_frame = content_box.text_frame

        # 对话内容
        dialogue = slide_data.get("dialogue", [])
        if dialogue:
            for line in dialogue:
                if isinstance(line, dict):
                    speaker = line.get("speaker", "")
                    text = line.get("text", "")
                    p = text_frame.add_paragraph()
                    p.text = f"{speaker}: {text}" if speaker else text
                    p.font.size = Pt(font_size)
                else:
                    p = text_frame.add_paragraph()
                    p.text = line
                    p.font.size = Pt(font_size)
        else:
            # 显示普通内容
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_analysis_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加课文分析页（英语学科专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "课文分析")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color

        # 内容 - 手动添加文本框
        content_box = slide.shapes.add_textbox(Inches(1), Inches(2), Inches(8), Inches(4.5))
        text_frame = content_box.text_frame

        # 段落大意
        if slide_data.get("paragraph_summary"):
            p = text_frame.add_paragraph()
            p.text = "段落大意："
            p.font.size = Pt(font_size + 2)
            p.font.color.rgb = color
            p.font.bold = True

            p = text_frame.add_paragraph()
            p.text = slide_data["paragraph_summary"]
            p.font.size = Pt(font_size)

            p = text_frame.add_paragraph()
            p.text = ""

        # 关键句型
        if slide_data.get("key_sentences"):
            p = text_frame.add_paragraph()
            p.text = "关键句型："
            p.font.size = Pt(font_size + 2)
            p.font.color.rgb = RGBColor(0, 100, 200)
            p.font.bold = True

            for sentence in slide_data["key_sentences"]:
                p = text_frame.add_paragraph()
                p.text = f"• {sentence}"
                p.font.size = Pt(font_size)

            p = text_frame.add_paragraph()
            p.text = ""

        # 常用表达
        if slide_data.get("expressions"):
            p = text_frame.add_paragraph()
            p.text = "常用表达："
            p.font.size = Pt(font_size + 2)
            p.font.color.rgb = RGBColor(128, 0, 128)
            p.font.bold = True

            for expr in slide_data["expressions"]:
                p = text_frame.add_paragraph()
                p.text = f"• {expr}"
                p.font.size = Pt(font_size)
        else:
            # 显示普通内容
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_comparison_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor,
        secondary_color: RGBColor
    ):
        """添加对比分析页（优化版：支持两种或多种概念对比）"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        # 标题
        title_text = slide_data.get("title", "对比分析")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.alignment = PP_ALIGN.CENTER

        # 获取对比数据
        comparison_data = slide_data.get("comparison_items", [])
        if len(comparison_data) >= 2:
            # 左右分栏布局
            left_x, left_y = Inches(0.5), Inches(1.5)
            right_x, right_y = Inches(5.5), Inches(1.5)
            col_width, col_height = Inches(4), Inches(5)

            # 左侧内容
            left_item = comparison_data[0]
            left_box = slide.shapes.add_textbox(left_x, left_y, col_width, Inches(0.8))
            left_title = left_box.text_frame
            left_title.text = left_item.get("title", "概念 A")
            left_title.paragraphs[0].font.size = Pt(font_size + 2)
            left_title.paragraphs[0].font.color.rgb = color
            left_title.paragraphs[0].font.bold = True
            left_title.paragraphs[0].alignment = PP_ALIGN.CENTER

            left_content = slide.shapes.add_textbox(left_x, left_y + Inches(0.8), col_width, col_height)
            left_frame = left_content.text_frame
            for point in left_item.get("points", []):
                p = left_frame.add_paragraph()
                p.text = f"• {point}"
                p.font.size = Pt(font_size)

            # 右侧内容
            right_item = comparison_data[1] if len(comparison_data) > 1 else comparison_data[0]
            right_box = slide.shapes.add_textbox(right_x, right_y, col_width, Inches(0.8))
            right_title = right_box.text_frame
            right_title.text = right_item.get("title", "概念 B")
            right_title.paragraphs[0].font.size = Pt(font_size + 2)
            right_title.paragraphs[0].font.color.rgb = secondary_color
            right_title.paragraphs[0].font.bold = True
            right_title.paragraphs[0].alignment = PP_ALIGN.CENTER

            right_content = slide.shapes.add_textbox(right_x, right_y + Inches(0.8), col_width, col_height)
            right_frame = right_content.text_frame
            for point in right_item.get("points", []):
                p = right_frame.add_paragraph()
                p.text = f"• {point}"
                p.font.size = Pt(font_size)
        else:
            # 没有对比数据时，显示普通内容
            content_box = slide.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(5))
            content_frame = content_box.text_frame
            for item in slide_data.get("content", []):
                p = content_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_quiz_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor,
        secondary_color: RGBColor
    ):
        """添加互动选择题页（带 ABCD 选项按钮）"""
        from pptx.enum.shapes import MSO_SHAPE

        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局

        # 1. 添加标题
        title_text = slide_data.get("title", "互动问答")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True
        title_para.alignment = PP_ALIGN.CENTER

        # 2. 添加问题文本
        question = slide_data.get("question", "请选择正确答案")
        question_box = slide.shapes.add_textbox(Inches(1), Inches(1.2), Inches(8), Inches(1.2))
        question_frame = question_box.text_frame
        question_frame.word_wrap = True
        question_frame.text = question
        for para in question_frame.paragraphs:
            para.font.size = Pt(font_size)
            para.alignment = PP_ALIGN.CENTER

        # 3. 添加选项按钮
        options = slide_data.get("options", ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"])
        correct_index = slide_data.get("correct_index", 0)
        option_labels = ['A', 'B', 'C', 'D']

        button_width = Inches(3.5)
        button_height = Inches(0.8)
        button_spacing = Inches(0.3)
        start_y = Inches(2.6)

        for i, option in enumerate(options[:4]):
            col = i % 2
            row = i // 2
            left = Inches(1) + col * (button_width + button_spacing)
            top = start_y + row * (button_height + button_spacing)

            # 创建按钮形状
            button = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                left, top, button_width, button_height
            )
            button.fill.solid()
            button.fill.fore_color.rgb = secondary_color
            button.line.fill.background()

            # 添加选项文本
            tf = button.text_frame
            label = option_labels[i] if i < 4 else chr(ord('A') + i)
            tf.text = f"{label}. {option}"
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            tf.paragraphs[0].font.size = Pt(font_size)
            tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
            tf.paragraphs[0].font.bold = True

        # 4. 添加答案提示
        answer_text = f"正确答案：{option_labels[correct_index]}" if correct_index < 4 else "查看答案"
        answer_box = slide.shapes.add_textbox(Inches(2.5), Inches(5.5), Inches(5), Inches(0.8))
        answer_frame = answer_box.text_frame
        answer_frame.text = answer_text
        answer_para = answer_frame.paragraphs[0]
        answer_para.font.size = Pt(font_size)
        answer_para.font.color.rgb = RGBColor(76, 175, 80)  # 绿色
        answer_para.font.bold = True
        answer_para.alignment = PP_ALIGN.CENTER

    def _add_click_to_reveal_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加点击显示答案页"""
        from pptx.enum.shapes import MSO_SHAPE

        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # 1. 添加标题
        title_text = slide_data.get("title", "点击显示答案")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True
        title_para.alignment = PP_ALIGN.CENTER

        # 2. 添加问题文本
        question = slide_data.get("question", "问题是什么？")
        question_box = slide.shapes.add_textbox(Inches(1), Inches(1.2), Inches(8), Inches(2))
        question_frame = question_box.text_frame
        question_frame.word_wrap = True
        question_frame.text = question
        for para in question_frame.paragraphs:
            para.font.size = Pt(font_size)
            para.alignment = PP_ALIGN.CENTER

        # 3. 添加"点击显示"按钮区域
        reveal_btn = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(3), Inches(3.5), Inches(4), Inches(1)
        )
        reveal_btn.fill.solid()
        reveal_btn.fill.fore_color.rgb = RGBColor(156, 39, 176)  # 紫色
        reveal_btn.line.fill.background()

        btn_tf = reveal_btn.text_frame
        btn_tf.text = "点击查看答案"
        btn_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
        btn_tf.paragraphs[0].font.size = Pt(font_size)
        btn_tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        btn_tf.paragraphs[0].font.bold = True

        # 4. 添加答案框
        hidden_content = slide_data.get("answer", "这是隐藏的答案内容")
        answer_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(1), Inches(4.8), Inches(8), Inches(2)
        )
        answer_box.fill.solid()
        answer_box.fill.fore_color.rgb = RGBColor(245, 245, 245)
        answer_box.line.color.rgb = RGBColor(76, 175, 80)
        answer_box.line.width = Pt(2)

        ans_tf = answer_box.text_frame
        ans_tf.word_wrap = True
        ans_tf.text = hidden_content
        for para in ans_tf.paragraphs:
            para.font.size = Pt(font_size)
            para.alignment = PP_ALIGN.CENTER

    def _add_matching_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor,
        secondary_color: RGBColor
    ):
        """添加拖拽匹配游戏页"""
        from pptx.enum.shapes import MSO_SHAPE

        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # 1. 添加标题
        title_text = slide_data.get("title", "拖拽匹配游戏")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(1))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True
        title_para.alignment = PP_ALIGN.CENTER

        # 2. 添加左右列标题
        left_title = slide_data.get("left_title", "单词")
        right_title = slide_data.get("right_title", "释义")

        left_title_box = slide.shapes.add_textbox(Inches(1), Inches(1.3), Inches(3.5), Inches(0.5))
        lt_frame = left_title_box.text_frame
        lt_frame.text = left_title
        lt_frame.paragraphs[0].font.size = Pt(font_size + 2)
        lt_frame.paragraphs[0].font.color.rgb = color
        lt_frame.paragraphs[0].font.bold = True
        lt_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        right_title_box = slide.shapes.add_textbox(Inches(5.5), Inches(1.3), Inches(3.5), Inches(0.5))
        rt_frame = right_title_box.text_frame
        rt_frame.text = right_title
        rt_frame.paragraphs[0].font.size = Pt(font_size + 2)
        rt_frame.paragraphs[0].font.color.rgb = secondary_color
        rt_frame.paragraphs[0].font.bold = True
        rt_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        # 3. 添加匹配项
        pairs = slide_data.get("pairs", [])  # [(左，右), ...]
        left_y = Inches(2)
        item_height = Inches(0.7)
        spacing = Inches(0.2)

        for i, pair in enumerate(pairs[:6]):
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                left_item, right_item = pair[0], pair[1]
            else:
                continue

            # 左侧项目
            left_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(1), left_y + i * (item_height + spacing),
                Inches(3.5), item_height
            )
            left_box.fill.solid()
            left_box.fill.fore_color.rgb = color
            left_box.line.fill.background()

            left_tf = left_box.text_frame
            left_tf.text = str(left_item)
            left_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            left_tf.paragraphs[0].font.size = Pt(font_size)
            left_tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

            # 右侧项目
            right_box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(5.5), left_y + i * (item_height + spacing),
                Inches(3.5), item_height
            )
            right_box.fill.solid()
            right_box.fill.fore_color.rgb = RGBColor(200, 200, 200)
            right_box.line.fill.background()

            right_tf = right_box.text_frame
            right_tf.text = str(right_item)
            right_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            right_tf.paragraphs[0].font.size = Pt(font_size)
            right_tf.paragraphs[0].font.color.rgb = RGBColor(33, 33, 33)

    def _add_quiz_game_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加随堂测验页（多题展示）"""
        from pptx.enum.shapes import MSO_SHAPE

        slide = prs.slides.add_slide(prs.slide_layouts[6])
        option_labels = ['A', 'B', 'C', 'D']

        # 1. 添加标题
        title_text = slide_data.get("title", "随堂测验")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(0.8))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True
        title_para.alignment = PP_ALIGN.CENTER

        # 2. 添加说明
        hint_box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(0.5))
        hint_frame = hint_box.text_frame
        hint_frame.text = "请选择正确答案"
        hint_frame.paragraphs[0].font.size = Pt(font_size - 2)
        hint_frame.paragraphs[0].font.color.rgb = RGBColor(128, 128, 128)
        hint_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

        # 3. 添加问题
        questions = slide_data.get("questions", [])
        q_start_y = Inches(1.6)

        for i, q in enumerate(questions[:3]):  # 最多 3 题
            q_y = q_start_y + i * Inches(2.8)

            # 问题编号和文本
            q_text = q.get("question", f"问题 {i + 1}")
            q_box = slide.shapes.add_textbox(Inches(0.8), q_y, Inches(8.4), Inches(0.6))
            q_frame = q_box.text_frame
            q_frame.word_wrap = True
            q_frame.text = f"{i + 1}. {q_text}"
            q_frame.paragraphs[0].font.size = Pt(font_size)
            q_frame.paragraphs[0].font.bold = True

            # 选项
            options = q.get("options", [])
            for j, opt in enumerate(options[:4]):
                opt_x = Inches(1) + (j % 2) * Inches(4.2)
                opt_y = q_y + Inches(0.6) + (j // 2) * Inches(0.8)

                opt_btn = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    opt_x, opt_y, Inches(4), Inches(0.7)
                )
                opt_btn.fill.solid()
                opt_btn.fill.fore_color.rgb = color
                opt_btn.line.fill.background()

                opt_tf = opt_btn.text_frame
                label = option_labels[j] if j < 4 else chr(ord('A') + j)
                opt_tf.text = f"{label}. {opt}"
                opt_tf.paragraphs[0].alignment = PP_ALIGN.CENTER
                opt_tf.paragraphs[0].font.size = Pt(font_size - 2)
                opt_tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

    def _add_fill_blank_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor,
        secondary_color: RGBColor
    ):
        """添加填空题页"""
        from pptx.enum.shapes import MSO_SHAPE

        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # 1. 添加标题
        title_text = slide_data.get("title", "填空题")
        title_box = slide.shapes.add_textbox(Inches(1), Inches(0.3), Inches(8), Inches(0.8))
        title_frame = title_box.text_frame
        title_frame.text = title_text
        title_para = title_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True
        title_para.alignment = PP_ALIGN.CENTER

        # 2. 添加句子（用___表示空白）
        sentences = slide_data.get("sentences", [])
        y_pos = Inches(1.5)

        for i, sentence in enumerate(sentences[:6]):
            sent_box = slide.shapes.add_textbox(Inches(1), y_pos + i * Inches(1), Inches(8), Inches(0.8))
            sent_frame = sent_box.text_frame
            sent_frame.word_wrap = True
            sent_frame.text = sentence
            sent_frame.paragraphs[0].font.size = Pt(font_size)

        # 3. 添加答案框
        answers = slide_data.get("answers", [])
        ans_text = "答案：" + " | ".join(str(a) for a in answers) if answers else "答案：见教师用书"

        ans_box = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(1), Inches(6), Inches(8), Inches(1.2)
        )
        ans_box.fill.solid()
        ans_box.fill.fore_color.rgb = RGBColor(245, 245, 245)
        ans_box.line.color.rgb = secondary_color
        ans_box.line.width = Pt(2)

        ans_tf = ans_box.text_frame
        ans_tf.text = ans_text
        ans_tf.paragraphs[0].font.size = Pt(font_size)
        ans_tf.paragraphs[0].font.color.rgb = secondary_color
        ans_tf.paragraphs[0].font.bold = True
        ans_tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    # ========== 理科实验页面渲染方法（feat-031 物理/化学/生物）==========

    def _add_experiment_design_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加实验设计页（物理/化学/生物通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "实验设计")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        exp_design = slide_data.get("experiment_design", {})
        if exp_design:
            # 探究目的
            purpose = exp_design.get("purpose", "")
            if purpose:
                p = text_frame.add_paragraph()
                p.text = "【探究目的】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = purpose
                p.font.size = Pt(font_size)

            # 实验器材
            materials = exp_design.get("materials", [])
            if materials:
                p = text_frame.add_paragraph()
                p.text = "\n【实验器材】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for mat in materials:
                    p = text_frame.add_paragraph()
                    p.text = f"• {mat}"
                    p.font.size = Pt(font_size)

            # 实验步骤
            steps = exp_design.get("steps", [])
            if steps:
                p = text_frame.add_paragraph()
                p.text = "\n【实验步骤】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for step in steps:
                    if isinstance(step, dict):
                        step_desc = step.get("description", "")
                        p = text_frame.add_paragraph()
                        p.text = f"{step.get('step_number', '')}. {step_desc}"
                        p.font.size = Pt(font_size)
                    else:
                        p = text_frame.add_paragraph()
                        p.text = str(step)
                        p.font.size = Pt(font_size)

            # 注意事项
            notes = exp_design.get("notes", [])
            if notes:
                p = text_frame.add_paragraph()
                p.text = "\n【注意事项】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                for note in notes:
                    p = text_frame.add_paragraph()
                    p.text = f"⚠ {note}"
                    p.font.size = Pt(font_size)
        else:
            # 没有数据时显示普通内容
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_experiment_observation_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加现象观察页（物理/化学通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "现象观察")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容 - 三段式对比布局
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        obs = slide_data.get("experiment_observation", {})
        if obs:
            # 实验前
            before = obs.get("before", "")
            if before:
                p = text_frame.add_paragraph()
                p.text = "【实验前】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_BLUE_3
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = before
                p.font.size = Pt(font_size)

            # 实验过程现象
            process = obs.get("process", [])
            if process:
                p = text_frame.add_paragraph()
                p.text = "\n【实验现象】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for phen in process:
                    p = text_frame.add_paragraph()
                    p.text = f"→ {phen}"
                    p.font.size = Pt(font_size)

            # 实验后
            after = obs.get("after", "")
            if after:
                p = text_frame.add_paragraph()
                p.text = "\n【实验后】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = after
                p.font.size = Pt(font_size)

            # 关键现象
            key_points = obs.get("key_points", [])
            if key_points:
                p = text_frame.add_paragraph()
                p.text = "\n【关键现象】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                for kp in key_points:
                    p = text_frame.add_paragraph()
                    p.text = f"★ {kp}"
                    p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_data_analysis_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor,
        secondary_color: RGBColor
    ):
        """添加数据分析页（物理/化学通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "数据分析")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        data = slide_data.get("data_analysis", {})
        if data:
            # 数据处理方法
            method = data.get("processing_method", "")
            if method:
                p = text_frame.add_paragraph()
                p.text = "【数据处理方法】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = method
                p.font.size = Pt(font_size)

            # 发现的规律
            pattern = data.get("pattern_discovered", "")
            if pattern:
                p = text_frame.add_paragraph()
                p.text = "\n【发现的规律】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = pattern
                p.font.size = Pt(font_size)

            # 误差分析
            error = data.get("error_analysis", "")
            if error:
                p = text_frame.add_paragraph()
                p.text = "\n【误差分析】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = error
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_law_summary_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加规律归纳页（物理/化学通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "规律归纳")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        law = slide_data.get("physics_law", {})
        if law:
            # 规律名称
            name = law.get("name", "")
            if name:
                p = text_frame.add_paragraph()
                p.text = name
                p.font.size = Pt(font_size + 4)
                p.font.color.rgb = color
                p.font.bold = True

            # 文字表述
            statement = law.get("statement", "")
            if statement:
                p = text_frame.add_paragraph()
                p.text = "\n【文字表述】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = statement
                p.font.size = Pt(font_size)

            # 公式表达
            formula = law.get("formula", "")
            if formula:
                p = text_frame.add_paragraph()
                p.text = "\n【公式表达】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = formula
                p.font.size = Pt(font_size + 2)
                p.font.bold = True

            # 适用条件
            conditions = law.get("conditions", "")
            if conditions:
                p = text_frame.add_paragraph()
                p.text = "\n【适用条件】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = conditions
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_application_transfer_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加应用迁移页（物理/化学/生物通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "应用迁移")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        app = slide_data.get("application", {})
        if app:
            # 应用场景
            scenario = app.get("scenario", "")
            if scenario:
                p = text_frame.add_paragraph()
                p.text = "【应用场景】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = scenario
                p.font.size = Pt(font_size)

            # 实际问题
            problem = app.get("problem", "")
            if problem:
                p = text_frame.add_paragraph()
                p.text = "\n【实际问题】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = problem
                p.font.size = Pt(font_size)

            # 解决方案
            solution = app.get("solution", "")
            if solution:
                p = text_frame.add_paragraph()
                p.text = "\n【解决方案】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = solution
                p.font.size = Pt(font_size)

            # 拓展思考
            extension = app.get("extension", "")
            if extension:
                p = text_frame.add_paragraph()
                p.text = "\n【拓展思考】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = extension
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_experiment_steps_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加实验步骤页（化学专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "实验步骤")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        exp_steps = slide_data.get("experiment_steps", {})
        if exp_steps:
            # 实验目的
            purpose = exp_steps.get("purpose", "")
            if purpose:
                p = text_frame.add_paragraph()
                p.text = "【实验目的】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = purpose
                p.font.size = Pt(font_size)

            # 仪器和药品
            instruments = exp_steps.get("instruments", [])
            reagents = exp_steps.get("reagents", [])
            if instruments or reagents:
                p = text_frame.add_paragraph()
                p.text = "\n【实验用品】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                if instruments:
                    p = text_frame.add_paragraph()
                    p.text = "仪器：" + ", ".join(instruments)
                    p.font.size = Pt(font_size)
                if reagents:
                    p = text_frame.add_paragraph()
                    p.text = "药品：" + ", ".join(reagents)
                    p.font.size = Pt(font_size)

            # 操作步骤
            procedures = exp_steps.get("procedures", [])
            if procedures:
                p = text_frame.add_paragraph()
                p.text = "\n【操作步骤】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for proc in procedures:
                    if isinstance(proc, dict):
                        desc = proc.get("description", "")
                        p = text_frame.add_paragraph()
                        p.text = f"{proc.get('step_number', '')}. {desc}"
                        p.font.size = Pt(font_size)
                    else:
                        p = text_frame.add_paragraph()
                        p.text = str(proc)
                        p.font.size = Pt(font_size)

            # 安全事项
            safety = exp_steps.get("safety_notes", [])
            if safety:
                p = text_frame.add_paragraph()
                p.text = "\n【安全注意事项】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_RED
                p.font.bold = True
                for s in safety:
                    p = text_frame.add_paragraph()
                    p.text = f"⚠ {s}"
                    p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_reaction_phenomena_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加反应现象页（化学专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "反应现象")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容 - 反应前后对比
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        phen = slide_data.get("reaction_phenomena", {})
        if phen:
            # 反应前
            before = phen.get("before", {})
            if before:
                p = text_frame.add_paragraph()
                p.text = "【反应前】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_BLUE_3
                p.font.bold = True
                if isinstance(before, dict):
                    substances = before.get("substances", [])
                    appearance = before.get("appearance", "")
                    for sub in substances:
                        p = text_frame.add_paragraph()
                        p.text = f"• {sub}"
                        p.font.size = Pt(font_size)
                    if appearance:
                        p = text_frame.add_paragraph()
                        p.text = f"外观：{appearance}"
                        p.font.size = Pt(font_size)
                else:
                    p = text_frame.add_paragraph()
                    p.text = str(before)
                    p.font.size = Pt(font_size)

            # 反应过程现象
            process = phen.get("process", [])
            if process:
                p = text_frame.add_paragraph()
                p.text = "\n【反应现象】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                for p_item in process:
                    p = text_frame.add_paragraph()
                    p.text = f"→ {p_item}"
                    p.font.size = Pt(font_size)

            # 反应后
            after = phen.get("after", {})
            if after:
                p = text_frame.add_paragraph()
                p.text = "\n【反应后】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                if isinstance(after, dict):
                    products = after.get("products", [])
                    appearance = after.get("appearance", "")
                    for prod in products:
                        p = text_frame.add_paragraph()
                        p.text = f"• {prod}"
                        p.font.size = Pt(font_size)
                    if appearance:
                        p = text_frame.add_paragraph()
                        p.text = f"外观：{appearance}"
                        p.font.size = Pt(font_size)
                else:
                    p = text_frame.add_paragraph()
                    p.text = str(after)
                    p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_chemical_equation_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加化学方程式页（化学专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "化学方程式")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        eq = slide_data.get("chemical_equation", {})
        if eq:
            # 反应物
            reactants = eq.get("reactants", [])
            if reactants:
                p = text_frame.add_paragraph()
                p.text = "【反应物】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for r in reactants:
                    p = text_frame.add_paragraph()
                    p.text = f"• {r}"
                    p.font.size = Pt(font_size)

            # 生成物
            products = eq.get("products", [])
            if products:
                p = text_frame.add_paragraph()
                p.text = "\n【生成物】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for prod in products:
                    p = text_frame.add_paragraph()
                    p.text = f"• {prod}"
                    p.font.size = Pt(font_size)

            # 配平方程式
            balanced = eq.get("balanced_equation", "")
            if balanced:
                p = text_frame.add_paragraph()
                p.text = "\n【配平的化学方程式】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = balanced
                p.font.size = Pt(font_size + 4)
                p.font.bold = True

            # 反应条件
            condition = eq.get("condition", "")
            if condition:
                p = text_frame.add_paragraph()
                p.text = f"\n【反应条件】{condition}"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True

            # 方程式意义
            meaning = eq.get("meaning", "")
            if meaning:
                p = text_frame.add_paragraph()
                p.text = "\n【方程式意义】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = meaning
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_microscopic_explanation_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加微观解释页（化学/生物通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "微观解释")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        micro = slide_data.get("microscopic_explanation", {})
        if micro:
            # 微粒模型描述
            model = micro.get("model_description", "")
            if model:
                p = text_frame.add_paragraph()
                p.text = "【微粒模型】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = model
                p.font.size = Pt(font_size)

            # 微粒变化过程
            changes = micro.get("particle_changes", "")
            if changes:
                p = text_frame.add_paragraph()
                p.text = "\n【微粒变化】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = changes
                p.font.size = Pt(font_size)

            # 化学键变化
            bond_breaking = micro.get("bond_breaking", "")
            bond_forming = micro.get("bond_forming", "")
            if bond_breaking or bond_forming:
                p = text_frame.add_paragraph()
                p.text = "\n【化学键变化】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                if bond_breaking:
                    p = text_frame.add_paragraph()
                    p.text = f"断裂：{bond_breaking}"
                    p.font.size = Pt(font_size)
                if bond_forming:
                    p = text_frame.add_paragraph()
                    p.text = f"形成：{bond_forming}"
                    p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_periodic_trend_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加元素周期律页（化学专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "元素周期律")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        trend = slide_data.get("periodic_trend", {})
        if trend:
            # 元素名称和符号
            name = trend.get("element_name", "")
            symbol = trend.get("symbol", "")
            if name or symbol:
                p = text_frame.add_paragraph()
                p.text = f"{name} ({symbol})" if name and symbol else (name or symbol)
                p.font.size = Pt(font_size + 4)
                p.font.color.rgb = color
                p.font.bold = True

            # 周期表位置
            position = trend.get("position", {})
            if position:
                p = text_frame.add_paragraph()
                p.text = f"\n【周期表位置】第{position.get('period', '')}周期 第{position.get('group', '')}族"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True

            # 原子结构
            atomic = trend.get("atomic_structure", {})
            if atomic:
                p = text_frame.add_paragraph()
                p.text = "\n【原子结构】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                protons = atomic.get("protons", "")
                electrons = atomic.get("electrons", "")
                config = atomic.get("electron_configuration", "")
                if protons:
                    p = text_frame.add_paragraph()
                    p.text = f"质子数：{protons}"
                    p.font.size = Pt(font_size)
                if electrons:
                    p = text_frame.add_paragraph()
                    p.text = f"电子数：{electrons}"
                    p.font.size = Pt(font_size)
                if config:
                    p = text_frame.add_paragraph()
                    p.text = f"电子排布：{config}"
                    p.font.size = Pt(font_size)

            # 性质递变规律
            props_trend = trend.get("properties_trend", "")
            if props_trend:
                p = text_frame.add_paragraph()
                p.text = "\n【性质递变规律】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = props_trend
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_structure_observation_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加结构观察页（生物专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "结构观察")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        struct = slide_data.get("structure_observation", {})
        if struct:
            # 观察对象
            obj = struct.get("object", "")
            if obj:
                p = text_frame.add_paragraph()
                p.text = "【观察对象】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = obj
                p.font.size = Pt(font_size)

            # 结构组成部分
            parts = struct.get("parts", [])
            if parts:
                p = text_frame.add_paragraph()
                p.text = "\n【结构组成】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for part in parts:
                    if isinstance(part, dict):
                        p = text_frame.add_paragraph()
                        p.text = f"• {part.get('name', '')}: {part.get('description', '')}"
                        p.font.size = Pt(font_size)
                    else:
                        p = text_frame.add_paragraph()
                        p.text = f"• {part}"
                        p.font.size = Pt(font_size)

            # 观察方法
            method = struct.get("observation_method", "")
            if method:
                p = text_frame.add_paragraph()
                p.text = "\n【观察方法】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = method
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_function_analysis_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加功能分析页（生物专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "功能分析")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        func = slide_data.get("function_analysis", {})
        if func:
            # 结构名称
            struct_name = func.get("structure_name", "")
            if struct_name:
                p = text_frame.add_paragraph()
                p.text = "【结构名称】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = struct_name
                p.font.size = Pt(font_size)

            # 功能描述
            function = func.get("function", "")
            if function:
                p = text_frame.add_paragraph()
                p.text = "\n【功能】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = function
                p.font.size = Pt(font_size)

            # 功能实现机制
            mechanism = func.get("mechanism", "")
            if mechanism:
                p = text_frame.add_paragraph()
                p.text = "\n【功能实现机制】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = mechanism
                p.font.size = Pt(font_size)

            # 结构与功能相适应的证据
            adaptation = func.get("adaptation_evidence", "")
            if adaptation:
                p = text_frame.add_paragraph()
                p.text = "\n【结构与功能的适应性】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = adaptation
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_process_description_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加过程描述页（生物专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "过程描述")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        proc = slide_data.get("process_description", {})
        if proc:
            # 过程名称
            name = proc.get("process_name", "")
            if name:
                p = text_frame.add_paragraph()
                p.text = "【生命过程】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = name
                p.font.size = Pt(font_size)

            # 过程意义
            significance = proc.get("significance", "")
            if significance:
                p = text_frame.add_paragraph()
                p.text = "\n【生物学意义】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = significance
                p.font.size = Pt(font_size)

            # 阶段
            stages = proc.get("stages", [])
            if stages:
                p = text_frame.add_paragraph()
                p.text = "\n【过程阶段】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for stage in stages:
                    if isinstance(stage, dict):
                        stage_name = stage.get("name", "")
                        desc = stage.get("description", "")
                        p = text_frame.add_paragraph()
                        p.text = f"  {stage_name}: {desc}"
                        p.font.size = Pt(font_size)
                    else:
                        p = text_frame.add_paragraph()
                        p.text = str(stage)
                        p.font.size = Pt(font_size)

            # 调控机制
            regulation = proc.get("regulation", "")
            if regulation:
                p = text_frame.add_paragraph()
                p.text = "\n【调控机制】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = regulation
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_system_thinking_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor
    ):
        """添加系统思维页（生物专属）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "系统思维")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        system = slide_data.get("system_thinking", {})
        if system:
            # 结构层次
            level = system.get("level", "")
            if level:
                p = text_frame.add_paragraph()
                p.text = "【结构层次】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = level
                p.font.size = Pt(font_size)

            # 与其他系统的联系
            connections = system.get("connections", [])
            if connections:
                p = text_frame.add_paragraph()
                p.text = "\n【系统联系】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                for conn in connections:
                    if isinstance(conn, dict):
                        conn_sys = conn.get("connected_system", "")
                        rel = conn.get("relationship", "")
                        p = text_frame.add_paragraph()
                        p.text = f"• {conn_sys}: {rel}"
                        p.font.size = Pt(font_size)
                    else:
                        p = text_frame.add_paragraph()
                        p.text = f"• {conn}"
                        p.font.size = Pt(font_size)

            # 整体协调机制
            coordination = system.get("coordination", "")
            if coordination:
                p = text_frame.add_paragraph()
                p.text = "\n【整体协调】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = coordination
                p.font.size = Pt(font_size)

            # 稳态维持
            homeostasis = system.get("homeostasis", "")
            if homeostasis:
                p = text_frame.add_paragraph()
                p.text = "\n【稳态维持】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = COLOR_GREEN_1
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = homeostasis
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)

    def _add_experiment_inquiry_slide(
        self,
        prs: Presentation,
        slide_data: Dict[str, Any],
        font_size: int,
        color: RGBColor,
        secondary_color: RGBColor
    ):
        """添加实验探究页（生物/化学通用）"""
        slide = prs.slides.add_slide(prs.slide_layouts[1])

        # 标题
        title_box = slide.shapes.title
        title_box.text = slide_data.get("title", "实验探究")
        title_para = title_box.text_frame.paragraphs[0]
        title_para.font.size = Pt(font_size + 6)
        title_para.font.color.rgb = color
        title_para.font.bold = True

        # 内容
        content_box = slide.shapes.add_textbox(Inches(1), Inches(1.8), Inches(8), Inches(5))
        text_frame = content_box.text_frame

        inquiry = slide_data.get("experiment_inquiry", {})
        if inquiry:
            # 探究问题
            question = inquiry.get("question", "")
            if question:
                p = text_frame.add_paragraph()
                p.text = "【探究问题】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = question
                p.font.size = Pt(font_size)

            # 假设
            hypothesis = inquiry.get("hypothesis", "")
            if hypothesis:
                p = text_frame.add_paragraph()
                p.text = "\n【假设】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = hypothesis
                p.font.size = Pt(font_size)

            # 实验设计
            design = inquiry.get("design", {})
            if design:
                p = text_frame.add_paragraph()
                p.text = "\n【实验设计】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = color
                p.font.bold = True

                # 变量
                variables = design.get("variables", {})
                if variables:
                    p = text_frame.add_paragraph()
                    p.text = "变量控制："
                    p.font.size = Pt(font_size)
                    p.font.bold = True
                    indep = variables.get("independent", "")
                    dep = variables.get("dependent", "")
                    controlled = variables.get("controlled", [])
                    if indep:
                        p = text_frame.add_paragraph()
                        p.text = f"  自变量：{indep}"
                        p.font.size = Pt(font_size)
                    if dep:
                        p = text_frame.add_paragraph()
                        p.text = f"  因变量：{dep}"
                        p.font.size = Pt(font_size)
                    if controlled:
                        p = text_frame.add_paragraph()
                        p.text = f"  控制变量：{', '.join(controlled)}"
                        p.font.size = Pt(font_size)

                # 组别
                groups = design.get("groups", [])
                if groups:
                    p = text_frame.add_paragraph()
                    p.text = "\n实验组别："
                    p.font.size = Pt(font_size)
                    p.font.bold = True
                    for g in groups:
                        p = text_frame.add_paragraph()
                        p.text = f"  • {g}"
                        p.font.size = Pt(font_size)

            # 预期结果
            expected = inquiry.get("expected_result", "")
            if expected:
                p = text_frame.add_paragraph()
                p.text = "\n【预期结果】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = _COLOR_ORANGE
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = expected
                p.font.size = Pt(font_size)

            # 结论推导
            conclusion = inquiry.get("conclusion", "")
            if conclusion:
                p = text_frame.add_paragraph()
                p.text = "\n【结论推导】"
                p.font.size = Pt(font_size + 2)
                p.font.color.rgb = secondary_color
                p.font.bold = True
                p = text_frame.add_paragraph()
                p.text = conclusion
                p.font.size = Pt(font_size)
        else:
            for item in slide_data.get("content", []):
                p = text_frame.add_paragraph()
                p.text = item
                p.font.size = Pt(font_size)


# 全局 PPT 生成器实例
_ppt_generator_instance: Optional[PPTGenerator] = None

def get_ppt_generator() -> PPTGenerator:
    """获取 PPT 生成器单例"""
    global _ppt_generator_instance
    if _ppt_generator_instance is None:
        _ppt_generator_instance = PPTGenerator()
    return _ppt_generator_instance