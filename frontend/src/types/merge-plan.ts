/**
 * SlidePlan 类型定义
 * feat-142: AI 融合交互面板
 */

/** 合并动作类型 */
export type MergeAction = 'keep' | 'merge' | 'create' | 'skip' | 'polish' | 'expand' | 'rewrite' | 'extract'

/** 合并来源 */
export interface MergeSource {
  source: 'A' | 'B'
  slide: number  // 页码（0-indexed）
}

/** 单页处理计划 */
export interface SlidePlanItem {
  action: MergeAction
  source?: 'A' | 'B'           // 来源文档
  slide_index?: number         // 源页码（0-indexed）
  sources?: MergeSource[]      // 多页合并时的来源
  new_content?: string         // AI 生成的新内容
  instruction?: string         // 处理指令
  reason?: string              // 原因说明
}

/** 合并计划 */
export interface MergePlan {
  merge_strategy: string       // 合并策略说明
  slide_plan: SlidePlanItem[]  // 每页处理计划
  summary: string              // 摘要说明
  knowledge_points: string[]   // 涉及的知识点
}

/** 单页处理结果 */
export interface SinglePageResult {
  action: string
  original_slide: any
  new_content: {
    title?: string
    main_points?: string[]
    additional_content?: string
  }
  changes: string[]
  success: boolean
  error?: string
}

/** 多页融合结果 */
export interface PartialMergeResult {
  merge_strategy: string
  content_relationship: string
  new_slide: {
    title: string
    elements: Array<{
      type: string
      content: string
    }>
  }
  preserved_from_a: string[]
  preserved_from_b: string[]
  success: boolean
}

/** AI 融合结果统一类型 */
export type MergeResult = MergePlan | SinglePageResult | PartialMergeResult

/** 判断是否为 MergePlan */
export function isMergePlan(result: any): result is MergePlan {
  return result && Array.isArray(result.slide_plan)
}

/** 判断是否为单页处理结果 */
export function isSinglePageResult(result: any): result is SinglePageResult {
  return result && result.action && result.new_content !== undefined
}

/** 判断是否为多页融合结果 */
export function isPartialMergeResult(result: any): result is PartialMergeResult {
  return result && result.new_slide !== undefined && result.merge_strategy !== undefined
}

/** 获取动作中文描述 */
export function getActionDescription(action: MergeAction): string {
  const descriptions: Record<MergeAction, string> = {
    keep: '保留原页',
    merge: '合并多页',
    create: '创建新页',
    skip: '跳过',
    polish: '润色文字',
    expand: '扩展内容',
    rewrite: '改写风格',
    extract: '提取知识点'
  }
  return descriptions[action] || action
}

/** 获取动作对应的颜色样式 */
export function getActionColor(action: MergeAction): string {
  const colors: Record<MergeAction, string> = {
    keep: 'bg-green-100 text-green-700 border-green-200',
    merge: 'bg-blue-100 text-blue-700 border-blue-200',
    create: 'bg-purple-100 text-purple-700 border-purple-200',
    skip: 'bg-gray-100 text-gray-600 border-gray-200',
    polish: 'bg-amber-100 text-amber-700 border-amber-200',
    expand: 'bg-indigo-100 text-indigo-700 border-indigo-200',
    rewrite: 'bg-pink-100 text-pink-700 border-pink-200',
    extract: 'bg-teal-100 text-teal-700 border-teal-200'
  }
  return colors[action] || 'bg-gray-100 text-gray-700 border-gray-200'
}

/** 获取来源文档标签 */
export function getSourceLabel(source?: 'A' | 'B'): string {
  if (!source) return ''
  return source === 'A' ? 'PPT A' : 'PPT B'
}
