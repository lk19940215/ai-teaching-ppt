"use client"

import * as React from "react"
import { useState, useCallback, useRef, useEffect } from "react"
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
import { cn } from "@/lib/utils"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/ppt-canvas-renderer"
import type { SlideStatus } from '@/lib/version-api'

// 页面数据接口（兼容 PptPageData 和 EnhancedPptPageData）
type SlideItem = {
  index: number
  title: string
  content: any  // 兼容 string[] 和 EnhancedPptPageData.content
  shapes?: any
  layout?: any
}

interface DraggableSlideListProps {
  pages: SlideItem[]
  currentIndex: number
  selectedPages: number[]
  slideImageUrls: Record<number, string>
  slideStatuses: Record<number, SlideStatus>
  onPageClick: (index: number) => void
  onReorder: (oldIndex: number, newIndex: number) => void
  convertToEnhanced: (page: SlideItem, pageIndex: number) => EnhancedPptPageData
  disableDrag?: boolean
}

/**
 * 可排序的单个缩略图项
 */
function SortableSlideItem({
  page,
  idx,
  isActive,
  isSelected,
  isDeleted,
  thumbnailUrl,
  enhanced,
  onClick,
}: {
  page: SlideItem
  idx: number
  isActive: boolean
  isSelected: boolean
  isDeleted: boolean
  thumbnailUrl?: string
  enhanced: EnhancedPptPageData
  onClick: () => void
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: page.index })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : 'auto',
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={cn(
        "flex-shrink-0 w-24 h-14 rounded border-2 overflow-hidden cursor-pointer transition-all relative select-none",
        isDragging && "shadow-xl ring-2 ring-indigo-400 scale-105",
        isActive ? "border-indigo-500 ring-1 ring-indigo-300 shadow" :
        isDeleted ? "border-red-300 opacity-60" :
        isSelected ? "border-green-400 ring-1 ring-green-200" :
        "border-gray-200 hover:border-gray-400 opacity-70 hover:opacity-100"
      )}
    >
      {/* feat-150: 优先显示图片缩略图 */}
      {thumbnailUrl ? (
        <img
          src={thumbnailUrl}
          alt={`第 ${idx + 1} 页`}
          className="w-full h-full object-cover pointer-events-none"
        />
      ) : (
        <div className="pointer-events-none">
          <PptCanvasRenderer pageData={enhanced} width={96} height={54} isSelected={false} onClick={() => {}} quality={0.5} />
        </div>
      )}
      {/* 页码标签 */}
      <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-center text-[9px] py-0.5 pointer-events-none">
        P{page.index + 1}
      </div>
      {/* feat-157: 已删除页面标识 */}
      {isDeleted && (
        <div className="absolute inset-0 bg-gray-500/50 flex items-center justify-center pointer-events-none">
          <span className="text-white text-[8px] font-medium bg-red-500 px-1 rounded">已删除</span>
        </div>
      )}
      {/* 选中状态指示器 */}
      {isSelected && !isDeleted && (
        <div className="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full flex items-center justify-center pointer-events-none">
          <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}
      {/* 拖拽手柄指示器 */}
      {!isDeleted && (
        <div className="absolute top-0.5 left-0.5 text-gray-400 pointer-events-none">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path d="M7 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM7 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM13 14a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
          </svg>
        </div>
      )}
    </div>
  )
}

/**
 * 拖拽覆盖层组件（跟随鼠标移动）
 */
function DragOverlayItem({
  page,
  idx,
  thumbnailUrl,
  enhanced,
}: {
  page: SlideItem
  idx: number
  thumbnailUrl?: string
  enhanced: EnhancedPptPageData
}) {
  return (
    <div
      className={cn(
        "w-24 h-14 rounded border-2 overflow-hidden cursor-grabbing shadow-2xl ring-2 ring-indigo-500 scale-110",
        "border-indigo-500 bg-white"
      )}
    >
      {thumbnailUrl ? (
        <img
          src={thumbnailUrl}
          alt={`第 ${idx + 1} 页`}
          className="w-full h-full object-cover"
        />
      ) : (
        <PptCanvasRenderer pageData={enhanced} width={96} height={54} isSelected={false} onClick={() => {}} quality={0.5} />
      )}
      <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-center text-[9px] py-0.5">
        P{page.index + 1}
      </div>
    </div>
  )
}

/**
 * feat-158: 可拖拽排序的缩略图列表组件
 *
 * 使用 @dnd-kit 实现拖拽排序功能，支持：
 * - 拖拽调整页面顺序
 * - 拖拽时的视觉反馈（缩放、阴影）
 * - 键盘无障碍操作
 */
export function DraggableSlideList({
  pages,
  currentIndex,
  selectedPages,
  slideImageUrls,
  slideStatuses,
  onPageClick,
  onReorder,
  convertToEnhanced,
  disableDrag = false,
}: DraggableSlideListProps) {
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // 滚动到当前页面
  useEffect(() => {
    if (containerRef.current) {
      const thumbEl = containerRef.current.children[currentIndex] as HTMLElement
      if (thumbEl) {
        thumbEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      }
    }
  }, [currentIndex])

  // 配置拖拽传感器
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 需要移动 8px 才开始拖拽，避免误触
      },
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

    if (over && active.id !== over.id) {
      const oldIndex = pages.findIndex(p => p.index === active.id)
      const newIndex = pages.findIndex(p => p.index === over.id)

      if (oldIndex !== -1 && newIndex !== -1) {
        onReorder(oldIndex, newIndex)
      }
    }

    setActiveId(null)
  }, [pages, onReorder])

  // 获取当前拖拽的项
  const activeItem = activeId ? pages.find(p => p.index === activeId) : null
  const activeIndex = activeItem ? pages.findIndex(p => p.index === activeId) : -1

  if (disableDrag) {
    // 禁用拖拽时渲染普通列表
    return (
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
        {pages.map((page, idx) => {
          const isActive = idx === currentIndex
          const isSelected = selectedPages.includes(page.index)
          const thumbnailUrl = slideImageUrls[idx]
          const slideStatus = slideStatuses[idx]
          const isDeleted = slideStatus === 'deleted'
          const enhanced = convertToEnhanced(page, page.index)

          return (
            <div
              key={page.index}
              onClick={() => onPageClick(idx)}
              className={cn(
                "flex-shrink-0 w-24 h-14 rounded border-2 overflow-hidden cursor-pointer transition-all relative",
                isActive ? "border-indigo-500 ring-1 ring-indigo-300 shadow" :
                isDeleted ? "border-red-300 opacity-60" :
                isSelected ? "border-green-400 ring-1 ring-green-200" :
                "border-gray-200 hover:border-gray-400 opacity-70 hover:opacity-100"
              )}
            >
              {thumbnailUrl ? (
                <img src={thumbnailUrl} alt={`第 ${idx + 1} 页`} className="w-full h-full object-cover" />
              ) : (
                <PptCanvasRenderer pageData={enhanced} width={96} height={54} isSelected={false} onClick={() => {}} quality={0.5} />
              )}
              <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-center text-[9px] py-0.5">
                P{page.index + 1}
              </div>
              {isDeleted && (
                <div className="absolute inset-0 bg-gray-500/50 flex items-center justify-center">
                  <span className="text-white text-[8px] font-medium bg-red-500 px-1 rounded">已删除</span>
                </div>
              )}
              {isSelected && !isDeleted && (
                <div className="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full flex items-center justify-center">
                  <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <SortableContext
        items={pages.map(p => p.index)}
        strategy={horizontalListSortingStrategy}
      >
        <div ref={containerRef} className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
          {pages.map((page, idx) => {
            const isActive = idx === currentIndex
            const isSelected = selectedPages.includes(page.index)
            const thumbnailUrl = slideImageUrls[idx]
            const slideStatus = slideStatuses[idx]
            const isDeleted = slideStatus === 'deleted'
            const enhanced = convertToEnhanced(page, page.index)

            return (
              <SortableSlideItem
                key={page.index}
                page={page}
                idx={idx}
                isActive={isActive}
                isSelected={isSelected}
                isDeleted={isDeleted}
                thumbnailUrl={thumbnailUrl}
                enhanced={enhanced}
                onClick={() => onPageClick(idx)}
              />
            )
          })}
        </div>
      </SortableContext>

      {/* 拖拽覆盖层 */}
      <DragOverlay>
        {activeItem && activeIndex !== -1 && (
          <DragOverlayItem
            page={activeItem}
            idx={activeIndex}
            thumbnailUrl={slideImageUrls[activeIndex]}
            enhanced={convertToEnhanced(activeItem, activeItem.index)}
          />
        )}
      </DragOverlay>
    </DndContext>
  )
}

export default DraggableSlideList