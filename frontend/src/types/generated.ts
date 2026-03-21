/**
 * 自动生成的 TypeScript 类型定义
 * feat-245: 从 Python Pydantic 模型生成
 * 
 * 警告：此文件由脚本自动生成，请勿手动修改！
 * 生成命令：cd backend && python scripts/generate_types.py
 */

// ==================== 枚举类型 ====================

/** 元素类型 */
export type ElementType = 'title' | 'subtitle' | 'text_body' | 'list_item' | 'image' | 'table' | 'shape' | 'placeholder' | 'unknown';

/** 页面类型 */
export type SlideType = 'title_slide' | 'outline_slide' | 'content_slide' | 'section_slide' | 'end_slide' | 'unknown';

/** 教学角色 */
export type TeachingRole = 'cover' | 'outline' | 'concept' | 'example' | 'exercise' | 'summary' | 'homework' | 'unknown';

/** 页面状态 */
export type SlideStatus = 'active' | 'deleted';

// ==================== 数据模型 ====================

export interface Position {
  /** 左边距百分比 (0-100) */
  x_pct: number
  /** 上边距百分比 (0-100) */
  y_pct: number
  /** 宽度百分比 (0-100) */
  width_pct: number
  /** 高度百分比 (0-100) */
  height_pct: number
}

export interface Style {
  /** 字体名称 */
  font_name?: string | null
  /** 字号 (pt) */
  font_size?: number | null
  /** 是否粗体 */
  bold?: boolean | null
  /** 是否斜体 */
  italic?: boolean | null
  /** 是否下划线 */
  underline?: boolean | null
  /** 颜色 (#RRGGBB 或主题色名称) */
  color?: string | null
  /** 对齐方式: left/center/right/justify */
  alignment?: string | null
  /** 行距倍数 (1.0 = 单倍行距) */
  line_spacing?: number | null
  /** 背景色 (#RRGGBB) */
  background_color?: string | null
  /** 缩进级别 (0-8) */
  indent_level?: number | null
}

export interface Paragraph {
  /** 段落文本 */
  text: string
  /** 段落角色: definition/example/note */
  role?: string | null
  /** 段落样式 */
  style?: Style | null
}

export interface ElementData {
  /** 元素唯一标识 (elem_000) */
  element_id: string
  /** 元素类型 */
  type: 'title' | 'subtitle' | 'text_body' | 'list_item' | 'image' | 'table' | 'shape' | 'placeholder' | 'unknown'
  /** 元素位置 */
  position: Position
  /** 文本内容 */
  text?: string | null
  /** 段落列表 */
  paragraphs?: Array<Paragraph>
  /** 文本样式 */
  style?: Style | null
  /** 图片 Base64 编码 */
  image_base64?: string | null
  /** 图片格式 (png/jpeg) */
  image_format?: string | null
  /** 图片描述 */
  image_description?: string | null
  /** 表格数据 */
  table_data?: Array<Array<string>> | null
  /** 表头 */
  table_headers?: Array<string> | null
  /** 原始 Shape 类型 */
  raw_shape_type?: string | null
}

export interface TeachingContent {
  /** 页面标题 */
  title?: string | null
  /** 主要要点 */
  main_points?: Array<string>
  /** 知识点列表 */
  knowledge_points?: Array<string>
  /** 示例列表 */
  examples?: Array<string>
  /** 是否包含图片 */
  has_images?: boolean
  /** 是否包含表格 */
  has_tables?: boolean
}

export interface SlideData {
  /** 幻灯片索引 (0-indexed) */
  slide_index: number
  /** 页面类型 */
  slide_type: 'title_slide' | 'outline_slide' | 'content_slide' | 'section_slide' | 'end_slide' | 'unknown'
  /** 教学角色 */
  teaching_role: 'cover' | 'outline' | 'concept' | 'example' | 'exercise' | 'summary' | 'homework' | 'unknown'
  /** 元素列表 */
  elements?: Array<ElementData>
  /** 教学语义内容 */
  teaching_content?: TeachingContent | null
  /** 布局宽度 (英寸) */
  layout_width?: number
  /** 布局高度 (英寸) */
  layout_height?: number
}

export interface DocumentData {
  /** 文档唯一标识 (UUID) */
  document_id: string
  /** 源文件名 */
  source_file: string
  /** 幻灯片列表 */
  slides?: Array<SlideData>
  /** 总页数 */
  total_slides?: number
  /** 学科 */
  subject?: string | null
  /** 年级 */
  grade?: string | null
  /** 是否检测到复杂元素 */
  complex_elements_detected?: boolean
  /** 包含复杂元素的页面索引 */
  complex_element_slides?: Array<number>
}

export interface SlideVersion {
  /** 版本号 (v1/v2/v3...) */
  version: string
  /** 预览图 URL */
  image_url: string
  /** 创建时间 (HH:MM:SS) */
  created_at: string
  /** 操作类型 */
  operation: string
  /** AI 操作提示语 */
  prompt?: string | null
  /** 源 PPTX 路径 */
  source_pptx?: string | null
  /** AI 修改的内容快照 */
  content_snapshot?: Record<string, any> | null
}

export interface SlideState {
  /** 当前版本 (v1/v2/...)，deleted 时为 null */
  current_version?: string | null
  /** 页面状态 */
  status: 'active' | 'deleted'
  /** 版本列表 */
  versions?: Array<SlideVersion>
}

export interface DocumentState {
  /** 源文件名 */
  source_file: string
  /** 幻灯片状态 (slide_index -> SlideState) */
  slides?: Record<number, SlideState>
}

export interface SessionData {
  /** 会话 ID */
  session_id: string
  /** 文档状态 (document_id -> DocumentState) */
  documents?: Record<string, DocumentState>
  /** 创建时间 */
  created_at: string
  /** 最后更新时间 */
  last_updated: string
}
