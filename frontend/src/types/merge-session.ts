/**
 * 合并会话数据模型
 * feat-171: 支持虚拟幻灯片池概念
 *
 * 设计理念：
 * - 所有幻灯片（原始/处理后的/融合生成的）统一存储在幻灯片池中
 * - 每个幻灯片可以有多个版本（原始版本、润色版本、扩展版本等）
 * - 最终 PPT 从幻灯片池中选择任意版本的页面组合
 *
 * feat-245: 重新导出后端生成的类型定义
 */

import type { SlideContent } from './merge-plan'

// feat-245: 从 generated.ts 重新导出后端同步的类型
export type {
  ElementType,
  SlideType,
  TeachingRole,
  SlideStatus,
  Position,
  Style,
  Paragraph,
  ElementData,
  TeachingContent,
  SlideData,
  DocumentData,
} from './generated'

export { type SlideVersion as BackendSlideVersion, type SlideState, type DocumentState, type SessionData } from './generated'

/** 幻灯片来源类型 */
export type SlideSourceType = 'ppt_a' | 'ppt_b' | 'merge' | 'generated'

/** 单页处理动作类型 */
export type SlideAction = 'polish' | 'expand' | 'rewrite' | 'extract' | 'merge' | 'create'

/** 幻灯片版本信息 */
export interface SlideVersion {
  /** 唯一标识：ppt_a_0_v2, merged_1_v1, generated_3_v1 */
  version_id: string
  /** 来源类型 */
  source_type: SlideSourceType
  /** 来源幻灯片索引（原始PPT），仅在 source_type 为 ppt_a/ppt_b 时有效 */
  source_slide_index?: number
  /** 融合来源（如果是 merge 类型） */
  source_merge_sources?: Array<{
    source: 'ppt_a' | 'ppt_b'
    slide_index: number
  }>
  /** 处理动作 */
  action?: SlideAction
  /** 结构化内容 */
  content: SlideContent
  /** feat-180: 增强模式的 shapes 数据，用于 PptCanvasRenderer 降级渲染 */
  shapes?: OriginalSlideData['shapes']
  /** feat-180: 页面布局信息 */
  layout?: { width: number; height: number }
  /** 预览图URL */
  preview_url?: string
  /** 创建时间戳 */
  created_at: number
  /** 父版本ID（用于追踪修改历史） */
  parent_version_id?: string
  /** 处理提示语 */
  prompt?: string
}

/** 幻灯片池项 */
export interface SlidePoolItem {
  /** 基础ID：ppt_a_0, ppt_b_1, merged_1, generated_3 */
  slide_id: string
  /** 原始来源 */
  original_source: 'ppt_a' | 'ppt_b' | 'merge' | 'generated'
  /** 原始索引（在原始PPT中的位置） */
  original_index: number
  /** 所有版本 */
  versions: SlideVersion[]
  /** 当前选中的版本ID */
  current_version: string
  /** 是否选中加入最终PPT */
  is_selected: boolean
  /** 显示标题（用于UI显示） */
  display_title?: string
}

/** 原始幻灯片数据 - feat-180: 支持增强模式返回的完整数据 */
export interface OriginalSlideData {
  index: number
  title: string
  content: string[]
  /** feat-180: 增强模式返回的 shapes 数据，包含 text_content runs */
  shapes?: Array<{
    type: string
    name: string
    position: { x: number; y: number; width: number; height: number }
    position_relative?: { x: number; y: number; width: number; height: number }
    image_base64?: string
    table_data?: string[][]
    text_content?: Array<{
      runs: Array<{
        text: string
        font: {
          name?: string
          size?: number
          color?: string
          bold?: boolean
          italic?: boolean
          underline?: boolean
        }
      }>
      alignment?: string
    }>
  }>
  /** 页面布局信息 */
  layout?: { width: number; height: number }
  has_complex_elements?: boolean
  complex_element_types?: string[]
}

/** 合并会话 */
export interface MergeSession {
  /** 会话ID */
  session_id: string
  /** 创建时间 */
  created_at: number

  // 原始数据
  /** PPT A 文件 */
  ppt_a_file: File | null
  /** PPT B 文件 */
  ppt_b_file: File | null
  /** PPT A 页面数据 */
  ppt_a_pages: OriginalSlideData[]
  /** PPT B 页面数据 */
  ppt_b_pages: OriginalSlideData[]

  // 幻灯片池
  /** 所有幻灯片（按 slide_id 索引） */
  slide_pool: Record<string, SlidePoolItem>

  // 最终选择
  /** 选中的 version_id 列表（按顺序） */
  final_selection: string[]

  // 当前操作状态
  /** 当前活动的幻灯片ID */
  active_slide_id: string | null
  /** 当前正在执行的操作 */
  active_operation: SlideAction | null
  /** 是否正在处理 */
  is_processing: boolean
  /** 处理进度信息 */
  progress_info?: {
    stage: string
    message: string
    percentage: number
    batch_current?: number
    batch_total?: number
  }
}

/** 操作类型 - 用于触发各种操作的参数 */
export type MergeOperation =
  | { type: 'polish'; slide_id: string; prompt?: string }
  | { type: 'expand'; slide_id: string; prompt?: string }
  | { type: 'rewrite'; slide_id: string; prompt?: string }
  | { type: 'extract'; slide_id: string; prompt?: string }
  | { type: 'merge_slides'; slide_ids: string[]; prompt?: string }
  | { type: 'select_for_final'; version_ids: string[] }
  | { type: 'remove_from_final'; version_ids: string[] }
  | { type: 'reorder_final'; from_index: number; to_index: number }
  | { type: 'switch_version'; slide_id: string; version_id: string }

/** 处理结果 */
export interface ProcessingResult {
  success: boolean
  new_version?: SlideVersion
  error?: string
}

/** 幻灯片池分组 */
export interface SlidePoolGroup {
  group_id: string
  group_label: string
  items: SlidePoolItem[]
}

/**
 * 创建初始版本的幻灯片池项
 * feat-180: 保存 shapes 和 layout 数据用于增强渲染
 */
export function createInitialSlidePoolItem(
  source: 'ppt_a' | 'ppt_b',
  slideIndex: number,
  slideData: OriginalSlideData
): SlidePoolItem {
  const slideId = `${source}_${slideIndex}`
  const versionId = `${slideId}_v1`

  return {
    slide_id: slideId,
    original_source: source,
    original_index: slideIndex,
    versions: [{
      version_id: versionId,
      source_type: source,
      source_slide_index: slideIndex,
      content: {
        title: slideData.title,
        main_points: slideData.content,
      },
      // feat-180: 保存增强模式的 shapes 和 layout 数据
      shapes: slideData.shapes,
      layout: slideData.layout,
      created_at: Date.now(),
    }],
    current_version: versionId,
    is_selected: false,
    display_title: slideData.title || `第 ${slideIndex + 1} 页`,
  }
}

/**
 * 创建融合生成的幻灯片池项
 */
export function createMergedSlidePoolItem(
  mergedIndex: number,
  sources: Array<{ source: 'ppt_a' | 'ppt_b'; slide_index: number }>,
  content: SlideContent
): SlidePoolItem {
  const slideId = `merged_${mergedIndex}`
  const versionId = `${slideId}_v1`

  return {
    slide_id: slideId,
    original_source: 'merge',
    original_index: mergedIndex,
    versions: [{
      version_id: versionId,
      source_type: 'merge',
      source_merge_sources: sources,
      action: 'merge',
      content,
      created_at: Date.now(),
    }],
    current_version: versionId,
    is_selected: false,
    display_title: content.title || `融合页 ${mergedIndex + 1}`,
  }
}

/**
 * 为现有幻灯片创建新版本
 */
export function createNewVersion(
  existingItem: SlidePoolItem,
  action: SlideAction,
  content: SlideContent,
  prompt?: string
): SlideVersion {
  const currentVersionNum = existingItem.versions.length
  const newVersionId = `${existingItem.slide_id}_v${currentVersionNum + 1}`

  return {
    version_id: newVersionId,
    source_type: existingItem.original_source === 'merge' ? 'merge' : existingItem.original_source,
    source_slide_index: existingItem.original_source !== 'merge' ? existingItem.original_index : undefined,
    source_merge_sources: existingItem.original_source === 'merge'
      ? existingItem.versions[0]?.source_merge_sources
      : undefined,
    action,
    content,
    created_at: Date.now(),
    parent_version_id: existingItem.current_version,
    prompt,
  }
}

/**
 * 获取幻灯片的当前版本
 */
export function getCurrentVersion(item: SlidePoolItem): SlideVersion | undefined {
  return item.versions.find(v => v.version_id === item.current_version)
}

/**
 * 获取幻灯片池的分组列表
 */
export function getSlidePoolGroups(slidePool: Record<string, SlidePoolItem>): SlidePoolGroup[] {
  const groups: SlidePoolGroup[] = []

  // PPT A 分组
  const pptAItems = Object.values(slidePool)
    .filter(item => item.original_source === 'ppt_a')
    .sort((a, b) => a.original_index - b.original_index)

  if (pptAItems.length > 0) {
    groups.push({
      group_id: 'ppt_a',
      group_label: 'PPT A',
      items: pptAItems,
    })
  }

  // PPT B 分组
  const pptBItems = Object.values(slidePool)
    .filter(item => item.original_source === 'ppt_b')
    .sort((a, b) => a.original_index - b.original_index)

  if (pptBItems.length > 0) {
    groups.push({
      group_id: 'ppt_b',
      group_label: 'PPT B',
      items: pptBItems,
    })
  }

  // 融合结果分组
  const mergedItems = Object.values(slidePool)
    .filter(item => item.original_source === 'merge')
    .sort((a, b) => a.original_index - b.original_index)

  if (mergedItems.length > 0) {
    groups.push({
      group_id: 'merged',
      group_label: '融合结果',
      items: mergedItems,
    })
  }

  // 生成结果分组
  const generatedItems = Object.values(slidePool)
    .filter(item => item.original_source === 'generated')
    .sort((a, b) => a.original_index - b.original_index)

  if (generatedItems.length > 0) {
    groups.push({
      group_id: 'generated',
      group_label: '新生成',
      items: generatedItems,
    })
  }

  return groups
}

export interface ActionConfig {
  label: string
  description: string
  icon: string
  template: string
}

export const ACTION_CONFIG: Record<SlideAction, ActionConfig> = {
  polish: {
    label: '润色',
    description: '优化文字表达',
    icon: '✨',
    template: '请润色优化：重点改善文字的流畅度和专业性，修正语病和冗余表述，确保教学语言清晰准确、适合课堂展示。保持原有信息完整，不增删知识点。',
  },
  expand: {
    label: '扩展',
    description: '增加细节内容',
    icon: '📈',
    template: '请扩展内容：为现有知识点补充具体示例、详细解释或应用场景，帮助学生更好地理解。优先添加贴近学生生活的实例，保持与原文主题一致。',
  },
  rewrite: {
    label: '改写',
    description: '调整语言风格',
    icon: '📝',
    template: '请改写内容：用全新的表达方式重新组织，可以改变句式结构、调整呈现顺序、转换表达视角。目标是让内容更易理解、更有教学吸引力，核心知识点不变。',
  },
  extract: {
    label: '提取',
    description: '提取核心知识点',
    icon: '🎯',
    template: '请提取知识点：从内容中提炼核心概念、关键方法和重要结论，按"核心概念→关键方法→注意事项"的层次组织，用简洁的列表格式呈现。',
  },
  merge: {
    label: '融合',
    description: '多页融合',
    icon: '🔀',
    template: '',
  },
  create: {
    label: '创建',
    description: '创建新幻灯片',
    icon: '➕',
    template: '',
  },
}

export function getActionLabel(action: SlideAction): string {
  return ACTION_CONFIG[action]?.label || action
}

/**
 * 获取来源的标签
 */
export function getSourceLabel(source: SlideSourceType): string {
  const labels: Record<SlideSourceType, string> = {
    ppt_a: 'PPT A',
    ppt_b: 'PPT B',
    merge: '融合',
    generated: '生成',
  }
  return labels[source] || source
}