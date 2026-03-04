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

    # 互动课堂页面类型（feat-017）
    QUIZ = "互动选择题页"  # ABCD 选项选择题
    CLICK_TO_REVEAL = "点击显示答案页"  # 点击显示隐藏内容
    MATCHING = "拖拽匹配游戏页"  # 单词 - 释义配对
    QUIZ_GAME = "随堂测验页"  # 多题测验
    FILL_BLANK = "填空题页"  # 填空练习


class PPTStyle:
    """PPT 样式配置（优化版：细化年级自适应规则）"""

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
    }

    @classmethod
    def get_style(cls, grade: str) -> Dict[str, Any]:
        """获取年级对应的样式"""
        return cls.GRADE_STYLES.get(grade, cls.GRADE_STYLES["6"])

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

            # 获取样式配置
            style_config = PPTStyle.get_style(grade)
            title_size = style_config["title_size"]
            content_size = style_config["font_size"]
            primary_color = style_config["primary"]
            secondary_color = style_config["secondary"]
            grade_group = style_config.get("group", "elementary_high")
            use_pinyin = PPTStyle.need_pinyin(grade, subject)

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


# 全局 PPT 生成器实例
_ppt_generator_instance: Optional[PPTGenerator] = None

def get_ppt_generator() -> PPTGenerator:
    """获取 PPT 生成器单例"""
    global _ppt_generator_instance
    if _ppt_generator_instance is None:
        _ppt_generator_instance = PPTGenerator()
    return _ppt_generator_instance