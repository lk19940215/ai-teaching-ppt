# -*- coding: utf-8 -*-
"""
PPT 中间数据结构定义
用于 AI 内容融合引擎消费

设计文档: .claude-coder/plans/ppt-merge-technical-design.md#2-数据结构设计
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class ElementType(str, Enum):
    """元素类型"""
    TITLE = "title"
    SUBTITLE = "subtitle"
    TEXT_BODY = "text_body"
    LIST_ITEM = "list_item"
    IMAGE = "image"
    TABLE = "table"
    SHAPE = "shape"
    PLACEHOLDER = "placeholder"
    UNKNOWN = "unknown"


class SlideType(str, Enum):
    """页面类型"""
    TITLE_SLIDE = "title_slide"          # 封面页
    OUTLINE_SLIDE = "outline_slide"      # 目录页
    CONTENT_SLIDE = "content_slide"      # 内容页
    SECTION_SLIDE = "section_slide"      # 章节页
    END_SLIDE = "end_slide"              # 结束页
    UNKNOWN = "unknown"


class TeachingRole(str, Enum):
    """教学角色"""
    COVER = "cover"                      # 封面
    OUTLINE = "outline"                  # 目录
    CONCEPT = "concept"                  # 概念讲解
    EXAMPLE = "example"                  # 例题讲解
    EXERCISE = "exercise"                # 练习
    SUMMARY = "summary"                  # 总结
    HOMEWORK = "homework"                # 作业
    UNKNOWN = "unknown"


@dataclass
class Position:
    """元素位置（百分比，相对于幻灯片）"""
    x_pct: float  # 左边距百分比
    y_pct: float  # 上边距百分比
    width_pct: float  # 宽度百分比
    height_pct: float  # 高度百分比


@dataclass
class Style:
    """文本样式
    feat-242: 增强样式提取能力
    """
    # 基础字体样式
    font_name: Optional[str] = None
    font_size: Optional[float] = None  # pt
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    color: Optional[str] = None  # #RRGGBB 或主题色名称

    # feat-242: 新增样式字段
    alignment: Optional[str] = None      # 对齐方式: left/center/right/justify
    line_spacing: Optional[float] = None  # 行距倍数（1.0 = 单倍行距）
    background_color: Optional[str] = None  # 背景色: #RRGGBB
    indent_level: Optional[int] = None    # 缩进级别（0-8）


@dataclass
class Paragraph:
    """段落"""
    text: str
    role: Optional[str] = None  # definition, example, note, etc.
    style: Optional[Style] = None


@dataclass
class ElementData:
    """元素数据"""
    element_id: str
    type: ElementType
    position: Position

    # 文本内容
    text: Optional[str] = None
    paragraphs: List[Paragraph] = field(default_factory=list)
    style: Optional[Style] = None

    # 图片内容
    image_base64: Optional[str] = None
    image_format: Optional[str] = None
    image_description: Optional[str] = None

    # 表格内容
    table_data: Optional[List[List[str]]] = None
    table_headers: Optional[List[str]] = None

    # 原始属性（用于调试）
    raw_shape_type: Optional[str] = None


@dataclass
class TeachingContent:
    """教学语义内容"""
    title: Optional[str] = None
    main_points: List[str] = field(default_factory=list)
    knowledge_points: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    has_images: bool = False
    has_tables: bool = False


@dataclass
class SlideData:
    """幻灯片数据"""
    slide_index: int
    slide_type: SlideType
    teaching_role: TeachingRole
    elements: List[ElementData]
    teaching_content: Optional[TeachingContent] = None

    # 布局信息
    layout_width: float = 10.0  # 英寸
    layout_height: float = 5.625  # 英寸


@dataclass
class DocumentData:
    """文档数据"""
    document_id: str
    source_file: str
    slides: List[SlideData]

    # 元数据
    total_slides: int = 0
    subject: Optional[str] = None
    grade: Optional[str] = None

    # 复杂元素警告
    complex_elements_detected: bool = False
    complex_element_slides: List[int] = field(default_factory=list)


def to_dict(data) -> Dict[str, Any]:
    """将数据类转换为字典"""
    if isinstance(data, (ElementData, SlideData, DocumentData, Position, Style, Paragraph, TeachingContent)):
        result = {}
        for key, value in data.__dict__.items():
            if value is not None:
                result[key] = to_dict(value) if hasattr(value, '__dict__') or isinstance(value, list) else value
            elif isinstance(value, list) and len(value) == 0:
                continue  # 跳过空列表
        return result
    elif isinstance(data, list):
        return [to_dict(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    else:
        return data


# ============== 版本化管理数据模型 ==============

@dataclass
class SlideVersion:
    """幻灯片版本"""
    version: str  # v1, v2, v3...
    image_url: str
    created_at: str  # HH:MM:SS
    operation: str  # 原始上传，AI 润色，AI 扩展，etc.
    prompt: Optional[str] = None  # AI 操作提示语
    source_pptx: Optional[str] = None  # 源 PPTX 路径（用于恢复）
    content_snapshot: Optional[Dict[str, Any]] = None  # AI 修改的内容快照（用于最终生成）


class SlideStatus(str, Enum):
    """页面状态"""
    ACTIVE = "active"
    DELETED = "deleted"


@dataclass
class SlideState:
    """幻灯片状态"""
    current_version: Optional[str]  # 当前版本 v1/v2/...，deleted 时为 null
    status: SlideStatus
    versions: List[SlideVersion]


@dataclass
class DocumentState:
    """文档状态"""
    source_file: str
    slides: Dict[int, SlideState]  # slide_index -> SlideState


@dataclass
class SessionData:
    """会话数据"""
    session_id: str
    documents: Dict[str, DocumentState]  # document_id (ppt_a/ppt_b) -> DocumentState
    created_at: str
    last_updated: str