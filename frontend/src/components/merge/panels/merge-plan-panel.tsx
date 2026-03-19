"use client"

import * as React from "react"
import { useState, useCallback } from "react"
import { cn } from "@/lib/utils"
import type { MergePlan, SlidePlanItem, MergeAction, SinglePageResult, PartialMergeResult } from "@/types/merge-plan"
import { getActionDescription, getSourceLabel, getActionColor, isMergePlan, isSinglePageResult, isPartialMergeResult, parseSlideContent, slideContentToText } from "@/types/merge-plan"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"

export interface MergePlanPanelProps {
  /** 合并计划数据 */
  plan: MergePlan | any | null
  /** 是否加载中 */
  isLoading?: boolean
  /** 用户调整后的计划 */
  adjustedPlan?: MergePlan
  /** 当用户调整计划时触发 */
  onPlanAdjust?: (plan: MergePlan) => void
  /** 当用户确认计划时触发 */
  onConfirm?: (plan: MergePlan | SinglePageResult | PartialMergeResult) => void
  /** 当用户取消时触发 */
  onCancel?: () => void
  /** 当删除页面时触发 */
  onDeletePage?: (index: number) => void
  /** 当编辑页面内容时触发 */
  onEditPage?: (index: number, newContent: string) => void
  /** 当拖拽排序完成时触发 */
  onReorder?: (fromIndex: number, toIndex: number) => void
  /** feat-162: 当重新生成某页时触发 */
  onRegeneratePage?: (index: number, prompt: string) => void
  /** feat-162: 是否正在重新生成 */
  isRegenerating?: boolean
  /** SSE 进度信息 */
  progressInfo?: {
    stage: string
    message: string
    percentage: number
  }
  className?: string
}

/** 获取动作图标 */
function getActionIcon(action: MergeAction): React.ReactNode {
  const icons: Record<MergeAction, React.ReactNode> = {
    keep: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    merge: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
    create: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    ),
    skip: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
    polish: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    expand: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
      </svg>
    ),
    rewrite: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    extract: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    )
  }
  return icons[action] || null
}

/** 单页处理结果展示组件 */
function SinglePageResultCard({ result }: { result: any }) {
  if (!result || !result.new_content) return null

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-center gap-2 mb-3">
        <span className={cn(
          "px-2 py-1 rounded text-xs font-medium border",
          getActionColor(result.action as MergeAction)
        )}>
          {getActionDescription(result.action as MergeAction)}
        </span>
        {result.success ? (
          <span className="text-green-600 text-xs flex items-center gap-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            处理成功
          </span>
        ) : (
          <span className="text-red-600 text-xs">处理失败：{result.error}</span>
        )}
      </div>

      {result.new_content.title && (
        <h4 className="text-sm font-medium text-gray-900 mb-2">
          {result.new_content.title}
        </h4>
      )}

      {result.new_content.main_points && result.new_content.main_points.length > 0 && (
        <ul className="space-y-1 mb-3">
          {result.new_content.main_points.map((point: string, idx: number) => (
            <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
              <span className="text-indigo-500 mt-1">•</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      )}

      {result.new_content.additional_content && (
        <div className="bg-gray-50 rounded p-2 text-sm text-gray-600">
          {result.new_content.additional_content}
        </div>
      )}

      {result.changes && result.changes.length > 0 && (
        <div className="mt-3 pt-3 border-t">
          <p className="text-xs text-gray-500 mb-1">修改说明：</p>
          <ul className="space-y-1">
            {result.changes.map((change: string, idx: number) => (
              <li key={idx} className="text-xs text-gray-600 flex items-start gap-1">
                <span className="text-green-500">→</span>
                <span>{change}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

/** 多页融合结果展示组件 */
function PartialMergeResultCard({ result }: { result: any }) {
  if (!result || !result.new_slide) return null

  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">融合结果</h4>
        <span className="text-xs text-gray-500">
          {typeof result.content_relationship === 'string'
            ? result.content_relationship
            : result.content_relationship?.type || '融合'}
        </span>
      </div>

      {result.new_slide.title && (
        <h5 className="text-base font-medium text-indigo-900 mb-3">
          {result.new_slide.title}
        </h5>
      )}

      {result.new_slide.elements && result.new_slide.elements.length > 0 && (
        <div className="space-y-2">
          {result.new_slide.elements.map((element: any, idx: number) => (
            <div key={idx} className="bg-gray-50 rounded p-2">
              <span className="text-xs text-gray-500 uppercase">{element.type}</span>
              <p className="text-sm text-gray-700 mt-1">{element.content}</p>
            </div>
          ))}
        </div>
      )}

      {(result.preserved_from_a?.length > 0 || result.preserved_from_b?.length > 0) && (
        <div className="mt-3 pt-3 border-t grid grid-cols-2 gap-3">
          {result.preserved_from_a?.length > 0 && (
            <div className="bg-blue-50 rounded p-2">
              <p className="text-xs text-blue-700 font-medium mb-1">保留自 PPT A</p>
              <ul className="text-xs text-blue-600 space-y-1">
                {result.preserved_from_a.map((item: string, idx: number) => (
                  <li key={idx}>• {item}</li>
                ))}
              </ul>
            </div>
          )}
          {result.preserved_from_b?.length > 0 && (
            <div className="bg-green-50 rounded p-2">
              <p className="text-xs text-green-700 font-medium mb-1">保留自 PPT B</p>
              <ul className="text-xs text-green-600 space-y-1">
                {result.preserved_from_b.map((item: string, idx: number) => (
                  <li key={idx}>• {item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/** 合并计划展示面板 */
export function MergePlanPanel({
  plan,
  isLoading = false,
  adjustedPlan,
  onPlanAdjust,
  onConfirm,
  onCancel,
  onDeletePage,
  onEditPage,
  onReorder,
  onRegeneratePage,
  isRegenerating = false,
  progressInfo,
  className
}: MergePlanPanelProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [editingContent, setEditingContent] = useState("")
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
  const [deletingIndex, setDeletingIndex] = useState<number | null>(null)
  // feat-162: 重新生成相关状态
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false)
  const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null)
  const [regeneratePrompt, setRegeneratePrompt] = useState("")

  const displayPlan = adjustedPlan || plan

  if (isLoading) {
    return (
      <div className={cn("border rounded-lg p-6 bg-white", className)}>
        <div className="flex items-center justify-center py-8">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-500">AI 正在生成合并方案...</p>
          </div>
        </div>
      </div>
    )
  }

  // SSE 进度展示（加载中但已有进度信息）
  if (progressInfo) {
    return (
      <div className={cn("border rounded-lg p-6 bg-white", className)}>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm font-medium text-gray-900">AI 正在分析...</p>
          </div>

          {/* 阶段指示器 */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            {/* 阶段 1：解析 */}
            <div className={cn(
              "flex items-center gap-2 text-sm",
              progressInfo.stage === 'parsing' ? "text-indigo-600 font-medium" : "text-gray-500"
            )}>
              <span className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs">
                {progressInfo.stage === 'parsing' ? '◷' : '✓'}
              </span>
              <span>解析 PPT 内容</span>
            </div>

            {/* 阶段 2：AI 分析 */}
            <div className={cn(
              "flex items-center gap-2 text-sm",
              progressInfo.stage === 'calling_llm' || progressInfo.stage === 'thinking' ? "text-indigo-600 font-medium" : "text-gray-500"
            )}>
              <span className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs">
                {progressInfo.stage === 'calling_llm' || progressInfo.stage === 'thinking' ? '◷' : '○'}
              </span>
              <span>AI 深度分析</span>
            </div>

            {/* 阶段 3：生成方案 */}
            <div className={cn(
              "flex items-center gap-2 text-sm",
              progressInfo.stage === 'merging' ? "text-indigo-600 font-medium" : "text-gray-500"
            )}>
              <span className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs">
                {progressInfo.stage === 'merging' ? '◷' : '○'}
              </span>
              <span>生成合并方案</span>
            </div>
          </div>

          {/* 进度条 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <span>{progressInfo.message || '处理中...'}</span>
              <span className="font-medium">{progressInfo.percentage}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-300"
                style={{ width: `${progressInfo.percentage}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className={cn("border rounded-lg p-6 bg-white", className)}>
        <div className="text-center py-8 text-gray-500 text-sm">
          <svg className="mx-auto h-12 w-12 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p>选择融合方式并点击"开始 AI 融合"后，此处将显示合并方案</p>
        </div>
      </div>
    )
  }

  // 处理单页结果
  if (isSinglePageResult(plan)) {
    return (
      <div className={cn("border rounded-lg p-4 bg-white", className)}>
        <h3 className="text-base font-medium text-gray-900 mb-4">单页处理结果</h3>
        <SinglePageResultCard result={plan} />
        <div className="flex gap-2 mt-4">
          {onConfirm && (
            <Button onClick={() => onConfirm(plan)} className="flex-1">
              应用此结果
            </Button>
          )}
          {onCancel && (
            <Button variant="outline" onClick={onCancel} className="flex-1">
              取消
            </Button>
          )}
        </div>
      </div>
    )
  }

  // 处理多页融合结果
  if (isPartialMergeResult(plan)) {
    return (
      <div className={cn("border rounded-lg p-4 bg-white", className)}>
        <h3 className="text-base font-medium text-gray-900 mb-4">多页融合结果</h3>
        <PartialMergeResultCard result={plan} />
        <div className="flex gap-2 mt-4">
          {onConfirm && (
            <Button onClick={() => onConfirm(plan)} className="flex-1">
              应用此结果
            </Button>
          )}
          {onCancel && (
            <Button variant="outline" onClick={onCancel} className="flex-1">
              取消
            </Button>
          )}
        </div>
      </div>
    )
  }

  // 处理整体合并计划
  const mergePlan = plan as MergePlan

  // 拖拽开始
  const handleDragStart = (e: React.DragEvent, index: number) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    // 设置拖拽预览
    const dragImage = e.currentTarget as HTMLElement
    dragImage.style.opacity = '0.5'
  }

  // 拖拽结束
  const handleDragEnd = (e: React.DragEvent) => {
    const dragImage = e.currentTarget as HTMLElement
    dragImage.style.opacity = '1'
    setDraggedIndex(null)
  }

  // 拖拽越过
  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  // 拖拽放置
  const handleDrop = (e: React.DragEvent, toIndex: number) => {
    e.preventDefault()
    if (draggedIndex !== null && draggedIndex !== toIndex && onReorder) {
      onReorder(draggedIndex, toIndex)
    }
    setDraggedIndex(null)
  }

  // 编辑页面
  const handleEditClick = (index: number, content?: string) => {
    setEditingIndex(index)
    setEditingContent(content || '')
    setEditDialogOpen(true)
  }

  // 保存编辑
  const handleSaveEdit = () => {
    if (editingIndex !== null && onEditPage) {
      onEditPage(editingIndex, editingContent)
    }
    setEditDialogOpen(false)
    setEditingIndex(null)
    setEditingContent('')
  }

  // 删除确认
  const handleDeleteClick = (index: number) => {
    setDeletingIndex(index)
    setDeleteConfirmOpen(true)
  }

  // 确认删除
  const handleConfirmDelete = () => {
    if (deletingIndex !== null && onDeletePage) {
      onDeletePage(deletingIndex)
    }
    setDeleteConfirmOpen(false)
    setDeletingIndex(null)
  }

  // feat-162: 重新生成点击
  const handleRegenerateClick = (index: number) => {
    setRegeneratingIndex(index)
    setRegeneratePrompt('')
    setRegenerateDialogOpen(true)
  }

  // feat-162: 确认重新生成
  const handleConfirmRegenerate = () => {
    if (regeneratingIndex !== null && onRegeneratePage) {
      onRegeneratePage(regeneratingIndex, regeneratePrompt)
    }
    // 不关闭对话框，等待 isRegenerating 变为 false
  }

  // feat-162: 取消重新生成
  const handleCancelRegenerate = () => {
    if (!isRegenerating) {
      setRegenerateDialogOpen(false)
      setRegeneratingIndex(null)
      setRegeneratePrompt('')
    }
  }

  // AI 加载中且无计划时显示 loading 状态
  if (!mergePlan && isLoading) {
    return (
      <div className={cn("border rounded-lg bg-white overflow-hidden p-6", className)}>
        <div className="flex items-center justify-center py-8">
          <div className="flex flex-col items-center gap-3">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            {progressInfo && (
              <>
                <p className="text-sm text-gray-600">{(progressInfo as { message: string; percentage: number }).message}</p>
                <div className="w-48 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all"
                    style={{ width: `${(progressInfo as { percentage: number }).percentage}%` }}
                  ></div>
                </div>
                <p className="text-xs text-gray-500">{(progressInfo as { percentage: number }).percentage}%</p>
              </>
            )}
          </div>
        </div>
      </div>
    )
  }

  // 无计划数据时隐藏
  if (!mergePlan) {
    return null
  }

  // 安全检查：确保 slide_plan 存在
  const slidePlanItems = mergePlan.slide_plan || []
  if (!slidePlanItems.length && !isLoading) {
    return (
      <div className={cn("border rounded-lg bg-white overflow-hidden p-6", className)}>
        <div className="flex items-center justify-center py-8 text-gray-500">
          暂无合并方案数据
        </div>
      </div>
    )
  }

  return (
    <div className={cn("border rounded-lg bg-white overflow-hidden", className)}>
      {/* 头部：策略说明 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-b px-4 py-3">
        <h3 className="text-base font-semibold text-gray-900 mb-2">
          AI 合并方案
        </h3>
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <p className="text-sm text-gray-700">{mergePlan.merge_strategy || 'AI 正在生成合并策略...'}</p>
            {mergePlan.summary && (
              <p className="text-xs text-gray-500 mt-2">{mergePlan.summary}</p>
            )}
          </div>
        </div>
      </div>

      {/* 知识点标签 */}
      {mergePlan.knowledge_points && mergePlan.knowledge_points.length > 0 && (
        <div className="px-4 py-2 border-b bg-gray-50">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500">知识点：</span>
            {mergePlan.knowledge_points.map((kp, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {kp}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* 操作提示 */}
      <div className="px-4 py-2 bg-amber-50 border-b flex items-center gap-2">
        <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="text-xs text-amber-800">
          拖拽页面调整顺序 · 点击编辑按钮修改内容 · 点击删除按钮移除页面
        </span>
      </div>

      {/* Slide Plan 列表 */}
      <ScrollArea className="max-h-96">
        <div className="divide-y">
          {slidePlanItems.map((item, idx) => (
            <div
              key={idx}
              draggable
              onDragStart={(e) => handleDragStart(e, idx)}
              onDragEnd={handleDragEnd}
              onDragOver={(e) => handleDragOver(e, idx)}
              onDrop={(e) => handleDrop(e, idx)}
              className={cn(
                "p-3 transition-colors cursor-move",
                draggedIndex === idx ? "bg-indigo-50 opacity-50" : "hover:bg-gray-50"
              )}
            >
              <div className="flex items-start gap-3">
                {/* 拖拽手柄 + 页码 */}
                <div className="flex-shrink-0 flex flex-col items-center gap-1">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8h16M4 16h16" />
                  </svg>
                  <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-medium text-gray-600">
                    {idx + 1}
                  </div>
                </div>

                {/* 内容区 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    {/* 动作标签 */}
                    <span className={cn(
                      "px-2 py-0.5 rounded text-xs font-medium border flex items-center gap-1",
                      getActionColor(item.action)
                    )}>
                      {getActionIcon(item.action)}
                      {getActionDescription(item.action)}
                    </span>

                    {/* 来源标签 */}
                    {item.source && (
                      <span className="text-xs text-gray-500 bg-gray-100 rounded px-1.5 py-0.5">
                        {getSourceLabel(item.source)}
                        {item.slide_index !== undefined && ` 第${item.slide_index + 1}页`}
                      </span>
                    )}

                    {/* 多页合并来源 */}
                    {item.sources && item.sources.length > 0 && (
                      <span className="text-xs text-gray-500">
                        合并：{item.sources.map(s => `${getSourceLabel(s.source)}P${s.slide + 1}`).join(' + ')}
                      </span>
                    )}
                  </div>

                  {/* 处理指令/新内容 */}
                  {item.new_content && (
                    <div className="bg-indigo-50 border border-indigo-100 rounded p-2 text-xs text-indigo-800 mt-2">
                      <p className="font-medium mb-1">新内容：</p>
                      <p className="whitespace-pre-wrap">
                        {typeof item.new_content === 'string'
                          ? item.new_content
                          : slideContentToText(parseSlideContent(item.new_content))}
                      </p>
                    </div>
                  )}

                  {/* 原因说明 */}
                  {item.reason && (
                    <p className="text-xs text-gray-500 mt-1">{item.reason}</p>
                  )}

                  {/* 处理指令 */}
                  {item.instruction && (
                    <div className="mt-1 flex items-center gap-1 text-xs text-gray-500">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{item.instruction}</span>
                    </div>
                  )}
                </div>

                {/* 操作按钮 */}
                <div className="flex-shrink-0 flex gap-1">
                  {/* feat-162: 重新生成按钮 */}
                  <button
                    type="button"
                    onClick={() => handleRegenerateClick(idx)}
                    className="p-1.5 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded transition-colors"
                    title="重新生成此页"
                    disabled={isRegenerating}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleEditClick(idx, typeof item.new_content === 'string' ? item.new_content : slideContentToText(parseSlideContent(item.new_content)))}
                    className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                    title="编辑此页内容"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeleteClick(idx)}
                    className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="删除此页"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* 底部操作按钮 */}
      <div className="border-t px-4 py-3 bg-gray-50 flex gap-2">
        {onCancel && (
          <Button variant="outline" onClick={onCancel} className="flex-1">
            重新生成
          </Button>
        )}
        {onConfirm && (
          <Button onClick={() => onConfirm(mergePlan)} className="flex-1">
            确认并生成 PPT
          </Button>
        )}
      </div>

      {/* 编辑对话框 */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑第 {editingIndex !== null ? editingIndex + 1 : ''} 页内容</DialogTitle>
            <DialogDescription>
              修改 AI 生成的页面内容，或添加您自己的教学指令
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">
                页面内容/指令
              </label>
              <textarea
                className="w-full min-h-[200px] p-3 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={editingContent}
                onChange={(e) => setEditingContent(e.target.value)}
                placeholder="输入您希望在此页展示的内容或教学指令..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              取消
            </Button>
            <Button onClick={handleSaveEdit}>
              保存修改
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              您确定要删除第 {deletingIndex !== null ? deletingIndex + 1 : ''} 页吗？此操作不会从源 PPT 中删除，仅从合并方案中移除。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)}>
              取消
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* feat-162: 重新生成对话框 */}
      <Dialog open={regenerateDialogOpen} onOpenChange={setRegenerateDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>重新生成第 {regeneratingIndex !== null ? regeneratingIndex + 1 : ''} 页</DialogTitle>
            <DialogDescription>
              AI 将根据您的指令重新生成此页的内容。留空则使用默认指令。
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <textarea
              className="w-full min-h-[100px] p-3 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              value={regeneratePrompt}
              onChange={(e) => setRegeneratePrompt(e.target.value)}
              placeholder="输入重新生成的指令，例如：增加更多例题、简化语言、添加互动环节..."
              disabled={isRegenerating}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCancelRegenerate} disabled={isRegenerating}>
              取消
            </Button>
            <Button onClick={handleConfirmRegenerate} disabled={isRegenerating}>
              {isRegenerating ? (
                <>
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  生成中...
                </>
              ) : (
                '重新生成'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default MergePlanPanel
