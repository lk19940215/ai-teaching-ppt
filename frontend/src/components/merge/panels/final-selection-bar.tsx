/**
 * 最终选择栏组件
 * feat-171: 显示最终选择的页面列表，支持拖拽排序
 *
 * 功能：
 * - 显示已选中的幻灯片缩略图列表
 * - 支持拖拽排序
 * - 支持移除
 * - 生成最终 PPT 按钮
 */

"use client"

import * as React from "react"
import { useState, useRef, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type {
  SlidePoolItem,
  SlideVersion,
} from "@/types/merge-session"
import { getSourceLabel } from "@/types/merge-session"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/merge/renderers/ppt-canvas-renderer"

export interface FinalSelectionItem {
  version_id: string
  slide_item: SlidePoolItem
  version: SlideVersion
}

export interface FinalSelectionBarProps {
  /** 最终选择列表 */
  items: FinalSelectionItem[]
  /** 预览图片 URL 映射 */
  slideImageUrls?: Record<string, string>
  /** 是否正在生成 */
  isGenerating?: boolean
  /** 重排序回调 */
  onReorder: (fromIndex: number, toIndex: number) => void
  /** 移除回调 */
  onRemove: (versionId: string) => void
  /** 生成最终 PPT 回调 */
  onGenerate: () => void
  /** 类名 */
  className?: string
}

/**
 * 将 SlideVersion 内容转换为 EnhancedPptPageData
 */
function versionToPageData(version: SlideVersion, pageIndex: number): EnhancedPptPageData {
  const mainPoints = version.content.main_points || []

  return {
    index: pageIndex,
    title: version.content.title || '',
    content: mainPoints.map(text => ({
      type: 'text' as const,
      text,
    })),
    shapes: [{
      type: 'text_box',
      name: 'main_content',
      position: { x: 20, y: 30, width: 140, height: 65 },
      text_content: [{
        runs: mainPoints.slice(0, 3).map(text => ({
          text: text.slice(0, 20) + (text.length > 20 ? '...' : ''),
          font: { size: 8, color: '#333333' },
        })),
      }],
    }],
    layout: { width: 180, height: 100 },
  }
}

/**
 * 可拖拽的选择项
 */
function DraggableSelectionItem({
  item,
  index,
  imageUrl,
  onDragStart,
  onDragOver,
  onDrop,
  onRemove,
  isDragging,
}: {
  item: FinalSelectionItem
  index: number
  imageUrl?: string
  onDragStart: (e: React.DragEvent, index: number) => void
  onDragOver: (e: React.DragEvent, index: number) => void
  onDrop: (e: React.DragEvent, index: number) => void
  onRemove: () => void
  isDragging: boolean
}) {
  const sourceLabel = getSourceLabel(item.slide_item.original_source)
  const sourceColor =
    item.slide_item.original_source === 'ppt_a' ? 'bg-blue-100 text-blue-700' :
    item.slide_item.original_source === 'ppt_b' ? 'bg-green-100 text-green-700' :
    item.slide_item.original_source === 'merge' ? 'bg-purple-100 text-purple-700' :
    'bg-amber-100 text-amber-700'

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragOver={(e) => onDragOver(e, index)}
      onDrop={(e) => onDrop(e, index)}
      className={cn(
        "relative group flex-shrink-0 rounded-lg border-2 bg-white cursor-move transition-all",
        isDragging ? "border-indigo-300 opacity-50" : "border-gray-200 hover:border-gray-300"
      )}
    >
      {/* 序号标记 */}
      <div className="absolute -top-1 -left-1 w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center text-white text-[10px] font-medium shadow">
        {index + 1}
      </div>

      {/* 缩略图 */}
      <div className="w-[100px] h-[56px] bg-gray-50 rounded overflow-hidden">
        {(imageUrl || item.version.preview_url) ? (
          <img
            src={imageUrl || item.version.preview_url}
            alt={item.version.content.title || ''}
            className="w-full h-full object-cover"
          />
        ) : (
          <PptCanvasRenderer
            pageData={versionToPageData(item.version, index)}
            width={100}
            height={56}
            quality={0.6}
          />
        )}
      </div>

      {/* 来源标签 */}
      <div className="px-1 py-0.5 text-center">
        <span className={cn("text-[8px] px-1 py-0.5 rounded", sourceColor)}>
          {sourceLabel}
        </span>
      </div>

      {/* 移除按钮 */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          onRemove()
        }}
        className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity shadow"
      >
        <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}

/**
 * 最终选择栏
 */
export function FinalSelectionBar({
  items,
  slideImageUrls,
  isGenerating,
  onReorder,
  onRemove,
  onGenerate,
  className,
}: FinalSelectionBarProps) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null)
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null)

  // 拖拽开始
  const handleDragStart = useCallback((e: React.DragEvent, index: number) => {
    setDraggedIndex(index)
    e.dataTransfer.effectAllowed = 'move'
    // 设置拖拽预览透明度
    const target = e.currentTarget as HTMLElement
    target.style.opacity = '0.5'
  }, [])

  // 拖拽经过
  const handleDragOver = useCallback((e: React.DragEvent, index: number) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverIndex(index)
  }, [])

  // 拖拽结束
  const handleDragEnd = useCallback((e: React.DragEvent) => {
    const target = e.currentTarget as HTMLElement
    target.style.opacity = '1'
    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [])

  // 放置
  const handleDrop = useCallback((e: React.DragEvent, toIndex: number) => {
    e.preventDefault()
    if (draggedIndex !== null && draggedIndex !== toIndex) {
      onReorder(draggedIndex, toIndex)
    }
    setDraggedIndex(null)
    setDragOverIndex(null)
  }, [draggedIndex, onReorder])

  return (
    <div className={cn("bg-white border-t rounded-lg", className)}>
      {/* 头部 */}
      <div className="px-4 py-2 border-b bg-gray-50 flex items-center gap-2">
        <h4 className="text-sm font-medium text-gray-900">最终 PPT 页面顺序</h4>
        <span className="text-xs text-gray-500">({items.length} 页)</span>
      </div>

      {/* 内容区域 */}
      <div className="px-4 py-3">
        {items.length === 0 ? (
          <div className="text-center py-4 text-gray-500 text-sm">
            <svg className="mx-auto h-8 w-8 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
            </svg>
            从幻灯片池中选择页面添加到此处
          </div>
        ) : (
          <>
            {/* 提示 */}
            <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
              拖拽调整顺序，点击 × 移除
            </div>

            {/* 选择列表 */}
            <div className="flex gap-2 overflow-x-auto pb-2">
              {items.map((item, index) => {
                const imageUrl = slideImageUrls?.[item.slide_item.slide_id]

                return (
                  <DraggableSelectionItem
                    key={item.version_id}
                    item={item}
                    index={index}
                    imageUrl={imageUrl}
                    onDragStart={handleDragStart}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
                    onRemove={() => onRemove(item.version_id)}
                    isDragging={draggedIndex === index}
                  />
                )
              })}

              {/* 放置指示器 */}
              {dragOverIndex !== null && draggedIndex !== null && dragOverIndex !== draggedIndex && (
                <div
                  className="flex-shrink-0 w-[100px] h-[80px] border-2 border-dashed border-indigo-300 rounded-lg flex items-center justify-center"
                  style={{
                    order: dragOverIndex > draggedIndex ? dragOverIndex + 1 : dragOverIndex,
                  }}
                >
                  <span className="text-xs text-indigo-400">放置此处</span>
                </div>
              )}
            </div>

            {/* 底部生成按钮 */}
            <div className="mt-3 pt-3 border-t">
              <Button
                onClick={onGenerate}
                disabled={isGenerating}
                className="w-full bg-green-600 hover:bg-green-700 h-10"
              >
                {isGenerating ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    正在生成 PPT...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    生成最终 PPT（{items.length} 页）
                  </>
                )}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default FinalSelectionBar