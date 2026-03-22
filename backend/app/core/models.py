"""
PPT 核心数据模型

三层模型设计：
  第一层: PPTX 解析模型 (ParsedPresentation) — 完整表示 PPTX 结构
  第二层: AI 友好内容模型 (SlideContent) — 纯文本 + 源映射
  第三层: 修改指令模型 (ProcessingResult) — 精确描述改什么、改成什么

技术文档: docs/technical-spec.md
"""

from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# 第一层: PPTX 解析模型
# ============================================================

class TextRun(BaseModel):
    """文本 Run — python-pptx 的最小文本单元，携带独立格式"""
    model_config = ConfigDict(extra="ignore")

    text: str
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    font_size: Optional[float] = None       # pt
    font_color: Optional[str] = None        # "#RRGGBB" 或 "theme_accent1"
    font_name: Optional[str] = None


class Paragraph(BaseModel):
    """段落（包含多个 Run）"""
    model_config = ConfigDict(extra="ignore")

    runs: list[TextRun] = []
    alignment: Optional[str] = None         # left / center / right / justify
    level: int = 0                          # 缩进级别 (0-8)
    line_spacing: Optional[float] = None    # 行距倍数


class Position(BaseModel):
    """元素位置（EMU 原始值，精确写回）"""
    model_config = ConfigDict(extra="ignore")

    left: int = 0       # EMU (1 inch = 914400 EMU)
    top: int = 0
    width: int = 0
    height: int = 0

    @property
    def left_inches(self) -> float:
        return self.left / 914400

    @property
    def top_inches(self) -> float:
        return self.top / 914400

    @property
    def width_inches(self) -> float:
        return self.width / 914400

    @property
    def height_inches(self) -> float:
        return self.height / 914400


class TableCell(BaseModel):
    """表格单元格"""
    model_config = ConfigDict(extra="ignore")

    text: str = ""
    paragraphs: list[Paragraph] = []
    row_span: int = 1
    col_span: int = 1


class ElementType(str, Enum):
    TEXT_BOX = "text_box"
    TABLE = "table"
    IMAGE = "image"
    SHAPE = "shape"
    GROUP = "group"
    CHART = "chart"
    MEDIA = "media"


class SlideElement(BaseModel):
    """幻灯片元素（对应 PPTX 的一个 Shape）

    shape_index 是写回定位的关键字段：
    PPTXWriter 通过 slide.shapes[shape_index] 找到原始 Shape 进行修改。
    """
    model_config = ConfigDict(extra="ignore")

    shape_index: int
    element_type: ElementType
    position: Position = Field(default_factory=Position)
    name: Optional[str] = None

    # 文本内容
    paragraphs: list[Paragraph] = []
    plain_text: Optional[str] = None

    # 表格内容
    table_data: Optional[list[list[TableCell]]] = None
    table_rows: int = 0
    table_cols: int = 0

    # 图片内容
    image_base64: Optional[str] = None
    image_format: Optional[str] = None

    # 语义标记
    is_title: bool = False
    is_placeholder: bool = False
    placeholder_type: Optional[str] = None
    has_hyperlink: bool = False


class ParsedSlide(BaseModel):
    """解析后的单页幻灯片"""
    model_config = ConfigDict(extra="ignore")

    slide_index: int
    elements: list[SlideElement] = []
    layout_name: Optional[str] = None
    has_notes: bool = False
    notes_text: Optional[str] = None
    has_animations: bool = False
    has_media: bool = False


class ParsedPresentation(BaseModel):
    """解析后的完整演示文稿"""
    model_config = ConfigDict(extra="ignore")

    filename: str
    slide_count: int = 0
    slide_width: int = 0    # EMU
    slide_height: int = 0   # EMU
    slides: list[ParsedSlide] = []
    title: Optional[str] = None


# ============================================================
# 第二层: AI 友好内容模型
# ============================================================

class TextBlock(BaseModel):
    """可被 AI 处理的文本块，通过 shape_index 映射回原始 Shape"""
    model_config = ConfigDict(extra="ignore")

    shape_index: int
    role: str           # title / body / subtitle / note
    text: str


class TableBlock(BaseModel):
    """可被 AI 处理的表格"""
    model_config = ConfigDict(extra="ignore")

    shape_index: int
    headers: list[str] = []
    rows: list[list[str]] = []


class SlideContent(BaseModel):
    """单页的 AI 可处理内容"""
    model_config = ConfigDict(extra="ignore")

    slide_index: int
    title: Optional[str] = None
    text_blocks: list[TextBlock] = []
    table_blocks: list[TableBlock] = []
    has_images: bool = False
    has_media: bool = False
    has_animations: bool = False
    layout_name: Optional[str] = None
    element_count: int = 0


# ============================================================
# 第三层: 修改指令模型
# ============================================================

class StyleHints(BaseModel):
    """可选的样式提示 — AI 可返回，由 StyleApplicator 应用"""
    model_config = ConfigDict(extra="ignore")

    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    font_size_pt: Optional[float] = None
    font_color: Optional[str] = None        # "#RRGGBB"
    font_name: Optional[str] = None
    alignment: Optional[str] = None         # left / center / right / justify


class AnimationHint(BaseModel):
    """可选的动画提示 — AI 可返回，由 AnimationApplicator 应用（可插拔）"""
    model_config = ConfigDict(extra="ignore")

    shape_index: int
    effect: str = "fade"                    # fade / fly_in / appear / zoom / wipe
    trigger: str = "on_click"              # on_click / with_previous / after_previous
    duration_ms: Optional[int] = None


class TextModification(BaseModel):
    """文本修改指令"""
    model_config = ConfigDict(extra="ignore")

    shape_index: int
    original_text: str
    new_text: str
    style_hints: Optional[StyleHints] = None


class TableCellModification(BaseModel):
    """表格单元格修改指令"""
    model_config = ConfigDict(extra="ignore")

    shape_index: int
    row: int
    col: int
    original_text: str
    new_text: str


class NewSlideContent(BaseModel):
    """AI 生成的全新页面内容（非修改已有 shape，而是从零创建）"""
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    body_texts: list[str] = []
    layout_hint: str = "blank"


class SlideModification(BaseModel):
    """单页的全部修改指令

    is_new_slide=False：修改已有页面（通过 slide_index + shape_index 定位）
    is_new_slide=True ：AI 要求创建新页面（new_slide_content 提供内容）
    """
    model_config = ConfigDict(extra="ignore")

    slide_index: int
    text_modifications: list[TextModification] = []
    table_modifications: list[TableCellModification] = []
    animation_hints: list[AnimationHint] = []
    ai_summary: Optional[str] = None
    is_new_slide: bool = False
    new_slide_content: Optional[NewSlideContent] = None


class ProcessingResult(BaseModel):
    """AI 处理的完整结果"""
    model_config = ConfigDict(extra="ignore")

    success: bool
    modifications: list[SlideModification] = []
    action: str = ""
    total_changes: int = 0
    error: Optional[str] = None


# ============================================================
# 第四层: 版本管理 & 会话模型
# ============================================================

class SlideSelector(BaseModel):
    """页面选择器：从某个 PPT 中选择一页"""
    model_config = ConfigDict(extra="ignore")

    source: str             # "ppt_a" / "ppt_b"
    slide_index: int


class PPTVersion(BaseModel):
    """PPT 版本（每次操作生成一个新版本）"""
    model_config = ConfigDict(extra="ignore")

    version_id: str
    version_number: int
    created_at: str                             # ISO 格式时间
    action: str                                 # polish/expand/rewrite/extract/compose/merge
    description: str = ""
    output_path: str                            # 生成的 PPTX 文件路径
    slide_selection: list[SlideSelector] = []   # 操作涉及的页面
    modifications: list[SlideModification] = [] # 具体修改内容
    preview_images: list[str] = []              # 每页预览图 URL

    # 用于对比
    source_version_id: Optional[str] = None     # 基于哪个版本修改的


class PPTSession(BaseModel):
    """PPT 处理会话"""
    model_config = ConfigDict(extra="ignore")

    session_id: str
    created_at: str
    original_files: dict[str, str] = {}         # {"ppt_a": "path", "ppt_b": "path"}
    parsed: dict[str, Any] = {}                 # {"ppt_a": ParsedPresentation.dict(), ...}
    versions: list[PPTVersion] = []
    current_version_id: Optional[str] = None
