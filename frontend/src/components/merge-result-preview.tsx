"use client"

import * as React from "react"
import { useState, useCallback, useMemo } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  UniqueIdentifier,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  horizontalListSortingStrategy,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import type { MergePlan, SlidePlanItem, MergeAction } from "@/types/merge-plan"
import { getActionDescription, getSourceLabel, getActionColor, parseSlideContent, slideContentToText } from "@/types/merge-plan"
import { ScrollArea } from "@/components/ui/scroll-area"

// 辅助函数：获取 new_content 的文本表示
function getNewContentText(newContent: string | any): string {
  if (!newContent) return ''
  if (typeof newContent === 'string') return newContent
  return slideContentToText(parseSlideContent(newContent))
}

/**
 * feat-159: 合并结果预览面板
 *
 * 显示 AI 合并后的结果预览，包括：
 * - 页面缩略图列表
 * - 每页的来源标注
 * - 拖拽排序功能
 * - 操作按钮（重新生成 / 下载 PPT）
 */

/** 预览页面数据（基于 SlidePlanItem 扩展） */
interface PreviewSlide {
  id: string                    // 唯一标识
  order: number                 // 显示顺序
  item: SlidePlanItem           // 原始 slide_plan 项
  // 以下字段用于缩略图显示（后续可对接实际图片 URL）
  thumbnailUrl?: string
  title?: string
}

interface MergeResultPreviewProps {
  /** 合并计划数据 */
  mergePlan: MergePlan | null
  /** 原始 PPT A 页面数据（用于显示缩略图） */
  pptAPages?: any[]
  /** 原始 PPT B 页面数据（用于显示缩略图） */
  pptBPages?: any[]
  /** PPT A 图片 URL 映射 */
  pptAImageUrls?: Record<number, string>
  /** PPT B 图片 URL 映射 */
  pptBImageUrls?: Record<number, string>
  /** 文件名 */
  fileName?: string | null
  /** 下载 URL */
  downloadUrl?: string | null
  /** 是否正在生成 */
  isGenerating?: boolean
  /** 当用户点击下载时触发 */
  onDownload?: () => void
  /** 当用户点击重新生成时触发 */
  onRegenerate?: () => void
  /** 当用户调整顺序时触发 */
  onReorder?: (newPlan: MergePlan) => void
  /** 当用户点击返回时触发 */
  onBack?: () => void
  /** 当用户点击重新开始时触发 */
  onRestart?: () => void
  className?: string
}

/** 获取动作图标 */
function getActionIcon(action: MergeAction): React.ReactNode {
  const icons: Record<MergeAction, React.ReactNode> = {
    keep: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
    merge: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
    create: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
      </svg>
    ),
    skip: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    ),
    polish: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    expand: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
      </svg>
    ),
    rewrite: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    extract: (
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    )
  }
  return icons[action] || null
}

/** 可排序的单个预览缩略图 */
function SortablePreviewSlide({
  slide,
  isActive,
  onClick,
  pptAImageUrls,
  pptBImageUrls,
}: {
  slide: PreviewSlide
  isActive: boolean
  onClick: () => void
  pptAImageUrls?: Record<number, string>
  pptBImageUrls?: Record<number, string>
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: slide.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : 'auto',
  }

  const { item } = slide
  const action = item.action

  // 获取缩略图 URL
  let thumbnailUrl: string | undefined
  if (item.source === 'A' && item.slide_index !== undefined && pptAImageUrls) {
    thumbnailUrl = pptAImageUrls[item.slide_index]
  } else if (item.source === 'B' && item.slide_index !== undefined && pptBImageUrls) {
    thumbnailUrl = pptBImageUrls[item.slide_index]
  }

  // 获取来源标签
  const getSourceDisplay = () => {
    if (item.sources && item.sources.length > 0) {
      // 多页合并
      return item.sources.map(s => `${getSourceLabel(s.source)}P${s.slide + 1}`).join(' + ')
    }
    if (item.source && item.slide_index !== undefined) {
      return `${getSourceLabel(item.source)} 第${item.slide_index + 1}页`
    }
    if (action === 'create') {
      return 'AI 新建'
    }
    return ''
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={cn(
        "flex-shrink-0 w-32 rounded-lg border-2 overflow-hidden cursor-pointer transition-all relative select-none bg-white",
        isDragging && "shadow-xl ring-2 ring-indigo-400 scale-105",
        isActive ? "border-indigo-500 ring-2 ring-indigo-300 shadow-md" : "border-gray-200 hover:border-gray-400"
      )}
    >
      {/* 缩略图区域 */}
      <div className="h-20 bg-gray-100 relative overflow-hidden">
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt={`第 ${slide.order + 1} 页`}
            className="w-full h-full object-cover pointer-events-none"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
            <div className="text-center p-2">
              <div className={cn(
                "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border mb-1",
                getActionColor(action)
              )}>
                {getActionIcon(action)}
                {getActionDescription(action)}
              </div>
              {item.new_content && (
                <p className="text-[10px] text-gray-500 line-clamp-2 max-w-[100px]">
                  {getNewContentText(item.new_content).slice(0, 50)}...
                </p>
              )}
            </div>
          </div>
        )}

        {/* 页码标签 */}
        <div className="absolute top-1 left-1 bg-indigo-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
          {slide.order + 1}
        </div>

        {/* 拖拽手柄指示器 */}
        <div className="absolute top-1 right-1 text-gray-400 opacity-60">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
          </svg>
        </div>
      </div>

      {/* 来源标注区域 */}
      <div className="p-2 border-t border-gray-100">
        <div className="flex items-center gap-1 flex-wrap">
          <span className={cn(
            "text-[10px] px-1 py-0.5 rounded font-medium border flex items-center gap-0.5",
            getActionColor(action)
          )}>
            {getActionIcon(action)}
            {getActionDescription(action)}
          </span>
        </div>
        <p className="text-[10px] text-gray-500 mt-1 truncate" title={getSourceDisplay()}>
          {getSourceDisplay()}
        </p>
      </div>
    </div>
  )
}

/** 拖拽覆盖层组件 */
function DragOverlaySlide({
  slide,
  pptAImageUrls,
  pptBImageUrls,
}: {
  slide: PreviewSlide
  pptAImageUrls?: Record<number, string>
  pptBImageUrls?: Record<number, string>
}) {
  const { item } = slide
  const action = item.action

  let thumbnailUrl: string | undefined
  if (item.source === 'A' && item.slide_index !== undefined && pptAImageUrls) {
    thumbnailUrl = pptAImageUrls[item.slide_index]
  } else if (item.source === 'B' && item.slide_index !== undefined && pptBImageUrls) {
    thumbnailUrl = pptBImageUrls[item.slide_index]
  }

  return (
    <div className="w-32 rounded-lg border-2 border-indigo-500 overflow-hidden shadow-2xl ring-2 ring-indigo-400 scale-110 bg-white">
      <div className="h-20 bg-gray-100 relative overflow-hidden">
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt="" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
            <span className={cn(
              "text-xs px-2 py-1 rounded border font-medium",
              getActionColor(action)
            )}>
              {getActionDescription(action)}
            </span>
          </div>
        )}
        <div className="absolute top-1 left-1 bg-indigo-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
          {slide.order + 1}
        </div>
      </div>
      <div className="p-2 border-t border-gray-100">
        <p className="text-[10px] text-gray-500 truncate">
          {item.source && item.slide_index !== undefined
            ? `${getSourceLabel(item.source)} 第${item.slide_index + 1}页`
            : action === 'create' ? 'AI 新建' : ''}
        </p>
      </div>
    </div>
  )
}

/** 合并结果预览面板主组件 */
export function MergeResultPreview({
  mergePlan,
  pptAPages,
  pptBPages,
  pptAImageUrls,
  pptBImageUrls,
  fileName,
  downloadUrl,
  isGenerating = false,
  onDownload,
  onRegenerate,
  onReorder,
  onBack,
  onRestart,
  className,
}: MergeResultPreviewProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null)

  // 将 MergePlan 转换为预览页面列表
  const previewSlides: PreviewSlide[] = useMemo(() => {
    if (!mergePlan?.slide_plan) return []
    return mergePlan.slide_plan.map((item, idx) => ({
      id: `slide-${idx}`,
      order: idx,
      item,
      thumbnailUrl: undefined, // 后续可从 pptAImageUrls/pptBImageUrls 获取
      title: getNewContentText(item.new_content).slice(0, 30) || `第 ${idx + 1} 页`
    }))
  }, [mergePlan])

  // 拖拽传感器配置
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 }
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  )

  // 拖拽开始
  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id)
  }, [])

  // 拖拽结束
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id && onReorder && mergePlan) {
      const oldIndex = previewSlides.findIndex(s => s.id === active.id)
      const newIndex = previewSlides.findIndex(s => s.id === over.id)

      if (oldIndex !== -1 && newIndex !== -1) {
        // 创建新的排序后的 slide_plan
        const newSlidePlan = [...mergePlan.slide_plan]
        const [removed] = newSlidePlan.splice(oldIndex, 1)
        newSlidePlan.splice(newIndex, 0, removed)

        onReorder({
          ...mergePlan,
          slide_plan: newSlidePlan
        })
      }
    }

    setActiveId(null)
  }, [previewSlides, mergePlan, onReorder])

  // 当前拖拽的项
  const activeSlide = activeId ? previewSlides.find(s => s.id === activeId) : null

  // 无数据但下载链接可用时，显示单页处理模式的结果
  if (!mergePlan || previewSlides.length === 0) {
    // feat-168: 支持单页处理模式，无需 mergePlan 也可下载
    if (downloadUrl) {
      return (
        <div className={cn("max-w-md mx-auto", className)}>
          <div className="bg-white border rounded-lg p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">PPT 生成完成</h2>
            <p className="text-sm text-gray-600 mb-2">
              已根据您的修改生成最终 PPT
            </p>
            {fileName && (
              <p className="text-xs text-gray-500 mb-6">
                文件名：{fileName}
              </p>
            )}
            <div className="flex gap-3 justify-center">
              {onDownload && (
                <Button onClick={onDownload} className="bg-green-600 hover:bg-green-700">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  下载 PPT
                </Button>
              )}
              {onRestart && (
                <Button variant="outline" onClick={onRestart}>
                  重新开始
                </Button>
              )}
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className={cn("max-w-md mx-auto", className)}>
        <div className="bg-white border rounded-lg p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">暂无合并结果</h2>
          <p className="text-sm text-gray-600 mb-6">
            请返回上一步完成 AI 合并配置
          </p>
          {onBack && (
            <Button variant="outline" onClick={onBack}>
              返回合并设置
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={cn("max-w-4xl mx-auto", className)}>
      {/* 成功提示头部 */}
      <div className="bg-white border rounded-lg p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900">合并完成</h2>
            <p className="text-sm text-gray-600">
              AI 已成功合并 {previewSlides.length} 页内容，您可以在下方预览并调整
            </p>
          </div>
        </div>

        {/* 合并策略摘要 */}
        {mergePlan.merge_strategy && (
          <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 mb-4">
            <p className="text-sm text-indigo-800">
              <span className="font-medium">合并策略：</span>
              {mergePlan.merge_strategy}
            </p>
          </div>
        )}

        {/* 知识点标签 */}
        {mergePlan.knowledge_points && mergePlan.knowledge_points.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500">知识点：</span>
            {mergePlan.knowledge_points.map((kp, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {kp}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* 预览区域 */}
      <div className="bg-white border rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-900">
            合并结果预览（共 {previewSlides.length} 页）
          </h3>
          <p className="text-xs text-gray-500">
            拖拽调整页面顺序
          </p>
        </div>

        {/* 缩略图列表（支持拖拽） */}
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={previewSlides.map(s => s.id)}
            strategy={horizontalListSortingStrategy}
          >
            <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
              {previewSlides.map((slide, idx) => (
                <SortablePreviewSlide
                  key={slide.id}
                  slide={slide}
                  isActive={idx === currentIndex}
                  onClick={() => setCurrentIndex(idx)}
                  pptAImageUrls={pptAImageUrls}
                  pptBImageUrls={pptBImageUrls}
                />
              ))}
            </div>
          </SortableContext>

          {/* 拖拽覆盖层 */}
          <DragOverlay>
            {activeSlide && (
              <DragOverlaySlide
                slide={activeSlide}
                pptAImageUrls={pptAImageUrls}
                pptBImageUrls={pptBImageUrls}
              />
            )}
          </DragOverlay>
        </DndContext>

        {/* 当前选中页面的详情 */}
        {previewSlides[currentIndex] && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-900">
                    第 {currentIndex + 1} 页
                  </span>
                  <span className={cn(
                    "text-xs px-2 py-0.5 rounded border",
                    getActionColor(previewSlides[currentIndex].item.action)
                  )}>
                    {getActionDescription(previewSlides[currentIndex].item.action)}
                  </span>
                </div>
                {previewSlides[currentIndex].item.new_content && (
                  <p className="text-sm text-gray-600 whitespace-pre-wrap">
                    {getNewContentText(previewSlides[currentIndex].item.new_content)}
                  </p>
                )}
                {previewSlides[currentIndex].item.reason && (
                  <p className="text-xs text-gray-500 mt-2">
                    原因：{previewSlides[currentIndex].item.reason}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 操作按钮区域 */}
      <div className="bg-white border rounded-lg p-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex gap-2">
            {onBack && (
              <Button variant="outline" onClick={onBack} disabled={isGenerating}>
                返回修改
              </Button>
            )}
            {onRestart && (
              <Button variant="ghost" onClick={onRestart} disabled={isGenerating}>
                重新开始
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {onRegenerate && (
              <Button variant="outline" onClick={onRegenerate} disabled={isGenerating}>
                {isGenerating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                    生成中...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    重新生成
                  </>
                )}
              </Button>
            )}
            {onDownload && (
              <Button onClick={onDownload} disabled={isGenerating || !downloadUrl}>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                下载 PPT
              </Button>
            )}
          </div>
        </div>

        {/* 文件名显示 */}
        {fileName && (
          <div className="mt-4 pt-4 border-t flex items-center gap-2">
            <span className="text-xs text-gray-500">文件名：</span>
            <span className="text-sm text-gray-900">{fileName}</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default MergeResultPreview