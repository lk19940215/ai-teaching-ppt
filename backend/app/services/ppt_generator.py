from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import jieba

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

            # 保存文件
            output_path.parent.mkdir(parents=True, exist_ok=True)
            prs.save(str(output_path))
            logger.info(f"PPT 文件已生成: {output_path}")
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


# 全局 PPT 生成器实例
_ppt_generator_instance: Optional[PPTGenerator] = None

def get_ppt_generator() -> PPTGenerator:
    """获取 PPT 生成器单例"""
    global _ppt_generator_instance
    if _ppt_generator_instance is None:
        _ppt_generator_instance = PPTGenerator()
    return _ppt_generator_instance