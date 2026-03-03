from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

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

class PPTPageType:
    """PPT 页面类型"""
    COVER = "封面页"
    TOC = "目录页"
    CONTENT = "知识点讲解页"
    INTERACTION = "互动问答页"
    EXERCISE = "课堂练习页"
    SUMMARY = "总结回顾页"

    # 英语学科特殊页面类型
    VOCABULARY = "单词学习页"
    GRAMMAR = "语法讲解页"
    DIALOGUE = "情景对话页"
    ANALYSIS = "课文分析页"


class PPTStyle:
    """PPT 样式配置"""

    # 年级样式配置
    GRADE_STYLES = {
        "1": {"font_size": 32, "title_size": 44, "primary": _COLOR_RED, "secondary": COLOR_TURQUOISE_2},
        "2": {"font_size": 30, "title_size": 40, "primary": _COLOR_ORANGE, "secondary": COLOR_TURQUOISE_3},
        "3": {"font_size": 28, "title_size": 38, "primary": _COLOR_GOLD, "secondary": _COLOR_DARK_ORANGE},
        "4": {"font_size": 24, "title_size": 34, "primary": _COLOR_TURQUOISE, "secondary": COLOR_TURQUOISE_2},
        "5": {"font_size": 22, "title_size": 32, "primary": COLOR_BLUE_1, "secondary": COLOR_BLUE_2},
        "6": {"font_size": 20, "title_size": 30, "primary": COLOR_BLUE_3, "secondary": COLOR_BLUE_4},
        "7": {"font_size": 18, "title_size": 28, "primary": COLOR_BLUE_5, "secondary": COLOR_GREEN_1},
        "8": {"font_size": 16, "title_size": 26, "primary": COLOR_GREEN_2, "secondary": COLOR_GREEN_3},
        "9": {"font_size": 16, "title_size": 24, "primary": COLOR_BLUE_6, "secondary": COLOR_GREEN_4},
    }

    @classmethod
    def get_style(cls, grade: str) -> Dict[str, Any]:
        """获取年级对应的样式"""
        return cls.GRADE_STYLES.get(grade, cls.GRADE_STYLES["6"])


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
        style: str = "simple"
    ) -> Path:
        """
        生成 PPT 文件
        Args:
            content: PPT 内容数据
            output_path: 输出文件路径
            grade: 年级
            style: PPT 风格
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

            # 生成封面页
            self._add_cover_slide(
                prs,
                content.get("title", "教学 PPT"),
                title_size,
                primary_color
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
        color: RGBColor
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
        """添加内容页"""
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


# 全局 PPT 生成器实例
_ppt_generator_instance: Optional[PPTGenerator] = None

def get_ppt_generator() -> PPTGenerator:
    """获取 PPT 生成器单例"""
    global _ppt_generator_instance
    if _ppt_generator_instance is None:
        _ppt_generator_instance = PPTGenerator()
    return _ppt_generator_instance