# -*- coding: utf-8 -*-
"""
PPT 中间数据结构定义
用于 AI 内容融合引擎消费

设计文档: .claude-coder/plans/ppt-merge-technical-design.md#2-数据结构设计

feat-244: 使用 Pydantic 重构数据结构模型
- 提供数据验证
- 自动生成 TypeScript 类型
- 支持 exclude_none 序列化
"""

from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ==================== 枚举定义 ====================

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


class SlideStatus(str, Enum):
    """页面状态"""
    ACTIVE = "active"
    DELETED = "deleted"


# ==================== Pydantic 模型定义 ====================

class Position(BaseModel):
    """元素位置（百分比，相对于幻灯片）

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    x_pct: float = Field(..., description="左边距百分比 (0-100)")
    y_pct: float = Field(..., description="上边距百分比 (0-100)")
    width_pct: float = Field(..., description="宽度百分比 (0-100)")
    height_pct: float = Field(..., description="高度百分比 (0-100)")


class Style(BaseModel):
    """文本样式

    feat-242: 增强样式提取能力
    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    # 基础字体样式
    font_name: Optional[str] = Field(None, description="字体名称")
    font_size: Optional[float] = Field(None, ge=0, description="字号 (pt)")
    bold: Optional[bool] = Field(None, description="是否粗体")
    italic: Optional[bool] = Field(None, description="是否斜体")
    underline: Optional[bool] = Field(None, description="是否下划线")
    color: Optional[str] = Field(None, description="颜色 (#RRGGBB 或主题色名称)")

    # feat-242: 新增样式字段
    alignment: Optional[str] = Field(None, description="对齐方式: left/center/right/justify")
    line_spacing: Optional[float] = Field(None, ge=0, description="行距倍数 (1.0 = 单倍行距)")
    background_color: Optional[str] = Field(None, description="背景色 (#RRGGBB)")
    indent_level: Optional[int] = Field(None, ge=0, le=8, description="缩进级别 (0-8)")


class Paragraph(BaseModel):
    """段落

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    text: str = Field(..., description="段落文本")
    role: Optional[str] = Field(None, description="段落角色: definition/example/note")
    style: Optional[Style] = Field(None, description="段落样式")


class ElementData(BaseModel):
    """元素数据

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    # 必填字段
    element_id: str = Field(..., description="元素唯一标识 (elem_000)")
    type: ElementType = Field(..., description="元素类型")
    position: Position = Field(..., description="元素位置")

    # 文本内容（选填）
    text: Optional[str] = Field(None, description="文本内容")
    paragraphs: List[Paragraph] = Field(default_factory=list, description="段落列表")
    style: Optional[Style] = Field(None, description="文本样式")

    # 图片内容（选填）
    image_base64: Optional[str] = Field(None, description="图片 Base64 编码")
    image_format: Optional[str] = Field(None, description="图片格式 (png/jpeg)")
    image_description: Optional[str] = Field(None, description="图片描述")

    # 表格内容（选填）
    table_data: Optional[List[List[str]]] = Field(None, description="表格数据")
    table_headers: Optional[List[str]] = Field(None, description="表头")

    # 原始属性（用于调试）
    raw_shape_type: Optional[str] = Field(None, description="原始 Shape 类型")


class TeachingContent(BaseModel):
    """教学语义内容

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    title: Optional[str] = Field(None, description="页面标题")
    main_points: List[str] = Field(default_factory=list, description="主要要点")
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")
    examples: List[str] = Field(default_factory=list, description="示例列表")
    has_images: bool = Field(False, description="是否包含图片")
    has_tables: bool = Field(False, description="是否包含表格")


class SlideData(BaseModel):
    """幻灯片数据

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    # 必填字段
    slide_index: int = Field(..., ge=0, description="幻灯片索引 (0-indexed)")
    slide_type: SlideType = Field(..., description="页面类型")
    teaching_role: TeachingRole = Field(..., description="教学角色")
    elements: List[ElementData] = Field(default_factory=list, description="元素列表")

    # 选填字段
    teaching_content: Optional[TeachingContent] = Field(None, description="教学语义内容")

    # 布局信息
    layout_width: float = Field(10.0, description="布局宽度 (英寸)")
    layout_height: float = Field(5.625, description="布局高度 (英寸)")


class DocumentData(BaseModel):
    """文档数据

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    # 必填字段
    document_id: str = Field(..., description="文档唯一标识 (UUID)")
    source_file: str = Field(..., description="源文件名")
    slides: List[SlideData] = Field(default_factory=list, description="幻灯片列表")

    # 元数据
    total_slides: int = Field(0, ge=0, description="总页数")
    subject: Optional[str] = Field(None, description="学科")
    grade: Optional[str] = Field(None, description="年级")

    # 复杂元素警告
    complex_elements_detected: bool = Field(False, description="是否检测到复杂元素")
    complex_element_slides: List[int] = Field(default_factory=list, description="包含复杂元素的页面索引")


# ==================== 版本化管理数据模型 ====================

class SlideVersion(BaseModel):
    """幻灯片版本

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    version: str = Field(..., description="版本号 (v1/v2/v3...)")
    image_url: str = Field(..., description="预览图 URL")
    created_at: str = Field(..., description="创建时间 (HH:MM:SS)")
    operation: str = Field(..., description="操作类型")
    prompt: Optional[str] = Field(None, description="AI 操作提示语")
    source_pptx: Optional[str] = Field(None, description="源 PPTX 路径")
    content_snapshot: Optional[Dict[str, Any]] = Field(None, description="AI 修改的内容快照")


class SlideState(BaseModel):
    """幻灯片状态

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    current_version: Optional[str] = Field(None, description="当前版本 (v1/v2/...)，deleted 时为 null")
    status: SlideStatus = Field(..., description="页面状态")
    versions: List[SlideVersion] = Field(default_factory=list, description="版本列表")


class DocumentState(BaseModel):
    """文档状态

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    source_file: str = Field(..., description="源文件名")
    slides: Dict[int, SlideState] = Field(default_factory=dict, description="幻灯片状态 (slide_index -> SlideState)")


class SessionData(BaseModel):
    """会话数据

    feat-244: 使用 Pydantic BaseModel
    """
    model_config = ConfigDict(exclude_none=True)

    session_id: str = Field(..., description="会话 ID")
    documents: Dict[str, DocumentState] = Field(default_factory=dict, description="文档状态 (document_id -> DocumentState)")
    created_at: str = Field(..., description="创建时间")
    last_updated: str = Field(..., description="最后更新时间")


# ==================== 工具函数 ====================

def to_dict(data) -> Dict[str, Any]:
    """将 Pydantic 模型转换为字典

    feat-244: 兼容 Pydantic model_dump 和旧版 dataclass

    Args:
        data: Pydantic 模型实例、枚举、列表或其他数据

    Returns:
        字典表示
    """
    # Pydantic 模型
    if isinstance(data, BaseModel):
        return data.model_dump(exclude_none=True, mode='json')

    # 枚举
    if isinstance(data, Enum):
        return data.value

    # 列表
    if isinstance(data, list):
        return [to_dict(item) for item in data]

    # 字典
    if isinstance(data, dict):
        return {k: to_dict(v) for k, v in data.items()}

    # 其他类型直接返回
    return data