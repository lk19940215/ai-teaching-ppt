/**
 * 幻灯片池面板组件
 * feat-171: 显示所有幻灯片（PPT A/B、融合结果）的池化管理
 * feat-185: PptxViewJSRenderer 降级到 PptCanvasRenderer 的自动切换
 *
 * 功能：
 * - 分组显示幻灯片（PPT A / PPT B / 融合结果）
 * - 点击选择幻灯片
 * - 显示版本数量标识
 * - 显示选中状态
 */

"use client"

import * as React from "react"
import { useState, useMemo, useCallback } from "react"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import type {
  SlidePoolItem,
  SlidePoolGroup,
  SlideVersion,
} from "@/types/merge-session"
import {
  getSlidePoolGroups,
  getCurrentVersion,
  getSourceLabel,
} from "@/types/merge-session"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/merge/renderers/ppt-canvas-renderer"
import { PptxViewJSRenderer } from "@/components/merge/renderers/pptxviewjs-renderer"
import { SlideContentRenderer } from "@/components/merge/renderers/slide-content-renderer"
import { usePptxFallback, getPptFile } from "@/hooks/use-pptx-fallback"

export interface SlidePoolPanelProps {
  /** 所有幻灯片池项 */
  slidePool: Record<string, SlidePoolItem>
  /** 当前选中的幻灯片ID */
  activeSlideId: string | null
  /** 最终选择的版本ID列表 */
  finalSelection: string[]
  /** 点击幻灯片回调 */
  onSlideClick: (slideId: string) => void
  /** 双击幻灯片回调（添加到最终选择） */
  onSlideDoubleClick?: (slideId: string) => void
  /** 外部传入的预览图片 URL */
  slideImageUrls?: Record<string, string>
  /** 是否正在处理 */
  isProcessing?: boolean
  /** 是否正在融合 */
  isMerging?: boolean
  /** 融合选中幻灯片回调 */
  onMergeSelected?: (slideIds: string[]) => void
  /** 拖拽添加到最终选择回调 */
  onDragToFinal?: (versionId: string) => void
  /** PPT A 文件引用（用于 PptxViewJSRenderer 渲染原始版本）*/
  fileA?: File | null
  /** PPT B 文件引用 */
  fileB?: File | null
  /** 类名 */
  className?: string
}

/**
 * 将 SlideVersion 内容转换为 EnhancedPptPageData
 * feat-180: 使用保存的 shapes 和 layout 数据实现精确渲染
 */
function versionToPageData(version: SlideVersion, pageIndex: number): EnhancedPptPageData {
  // feat-180: 优先使用保存的 shapes 数据（来自后端增强模式）
  if (version.shapes && version.shapes.length > 0) {
    return {
      index: pageIndex,
      title: version.content.title || '',
      content: (version.content.main_points || []).map(text => ({
        type: 'text' as const,
        text,
      })),
      shapes: version.shapes,
      layout: version.layout || { width: 960, height: 540 },
    }
  }

  // 降级：从 content 构造简化的 shapes（旧逻辑）
  const mainPoints = version.content.main_points || []
  const additionalContent = version.content.additional_content || ''

  return {
    index: pageIndex,
    title: version.content.title || '',
    content: [...mainPoints, additionalContent].filter(Boolean).map(text => ({
      type: 'text' as const,
      text,
    })),
    shapes: [{
      type: 'text_box',
      name: 'main_content',
      position: { x: 20, y: 40, width: 200, height: 100 },
      text_content: [{
        runs: mainPoints.map(text => ({
          text: text + '\n',
          font: { size: 10, color: '#333333' },
        })),
      }],
    }],
    layout: { width: 240, height: 135 },
  }
}

/**
 * 单个幻灯片缩略图
 * feat-172: 渲染优先级决策树
 * feat-185: PptxViewJSRenderer 降级到 PptCanvasRenderer 的自动切换
 * 1. LibreOffice 图片 URL → <img>
 * 2. 原始版本（v1，无 action）且有 PPT file → PptxViewJSRenderer（失败时降级）
 * 3. AI 版本（v2+，有 action）→ SlideContentRenderer
 * 4. 兜底 → PptCanvasRenderer
 */
function SlideThumbnail({
  item,
  isActive,
  isSelected,
  isMultiSelected,
  imageUrl: externalImageUrl,
  fileA,
  fileB,
  onClick,
  onDoubleClick,
}: {
  item: SlidePoolItem
  isActive: boolean
  isSelected: boolean
  isMultiSelected: boolean
  imageUrl?: string
  fileA?: File | null
  fileB?: File | null
  onClick: (e?: React.MouseEvent) => void
  onDoubleClick?: () => void
}) {
  const currentVersion = getCurrentVersion(item)
  const versionCount = item.versions.length
  const sourceLabel = getSourceLabel(item.original_source)
  const sourceColor =
    item.original_source === 'ppt_a' ? 'bg-blue-100 text-blue-700' :
    item.original_source === 'ppt_b' ? 'bg-green-100 text-green-700' :
    item.original_source === 'merge' ? 'bg-purple-100 text-purple-700' :
    'bg-amber-100 text-amber-700'

  // 优先使用外部传入的 URL（LibreOffice 生成的预览图）
  const imageUrl = externalImageUrl || currentVersion?.preview_url

  // 判断是否为原始版本（v1，无 action）
  const isOriginalVersion = !currentVersion?.action && item.versions.length === 1

  // 获取对应的 PPT 文件
  const pptFile = getPptFile(item.original_source, fileA, fileB)

  // feat-185: PptxViewJSRenderer 降级状态
  const { fallbackMode, handlePptxViewJSError } = usePptxFallback({
    resetDeps: [pptFile, item.slide_id]
  })

  // 判断是否为 AI 版本（有 action 或版本号 > 1）
  const isAIVersion = currentVersion?.action || item.versions.length > 1

  const handleDragStart = useCallback((e: React.DragEvent) => {
    const currentVer = getCurrentVersion(item)
    if (currentVer) {
      e.dataTransfer.setData('application/x-slide-version', currentVer.version_id)
      e.dataTransfer.setData('application/x-slide-id', item.slide_id)
      e.dataTransfer.effectAllowed = 'copy'
    }
  }, [item])

  return (
    <div
      draggable
      onDragStart={handleDragStart}
      className={cn(
        "relative group rounded-lg border-2 cursor-pointer transition-all",
        isActive
          ? "border-indigo-500 ring-2 ring-indigo-200 shadow-md"
          : isMultiSelected
          ? "border-purple-500 ring-2 ring-purple-200 shadow-md"
          : "border-gray-200 hover:border-gray-300 hover:shadow-sm",
        isSelected && "bg-indigo-50"
      )}
      onClick={onClick}
      onDoubleClick={onDoubleClick}
    >
      {/* 渲染优先级决策树（feat-177, feat-185）：
          1. LibreOffice 图片 URL → <img>
          2. 原始版本（无 action）且有 PPT file → PptxViewJSRenderer（降级时用 PptCanvasRenderer）
          3. AI 版本（有 action）→ SlideContentRenderer
          4. 有 content 数据 → PptCanvasRenderer
          5. 兜底 → 占位符 */}
      <div className="aspect-video bg-gray-50 rounded-t-md overflow-hidden">
        {/* 优先级 1: LibreOffice 图片 URL */}
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={item.display_title || `幻灯片 ${item.original_index + 1}`}
            className="w-full h-full object-cover"
            onError={(e) => {
              // 图片加载失败时隐藏
              (e.target as HTMLImageElement).style.display = 'none'
            }}
          />
        ) : /* 优先级 2: 原始版本（无 action）且有 PPT file */
        isOriginalVersion && pptFile ? (
          // feat-185: 根据 fallbackMode 选择渲染器
          fallbackMode ? (
            // 降级模式：使用 PptCanvasRenderer
            <PptCanvasRenderer
              pageData={versionToPageData(currentVersion!, item.original_index)}
              width={240}
              height={135}
              quality={0.7}
            />
          ) : (
            // 正常模式：使用 PptxViewJSRenderer，监听错误
            <PptxViewJSRenderer
              file={pptFile}
              slideIndex={item.original_index}
              width={240}
              height={135}
              quality="low"
              onError={handlePptxViewJSError}
            />
          )
        ) : /* 优先级 3: AI 版本（有 action）→ SlideContentRenderer */
        isAIVersion && currentVersion?.action && currentVersion?.content ? (
          <SlideContentRenderer
            content={currentVersion.content}
            action={currentVersion.action}
            slide={item}
            size="thumbnail"
          />
        ) : /* 优先级 4: 有 content 数据 → PptCanvasRenderer（优化版）*/
        currentVersion?.content ? (
          <PptCanvasRenderer
            pageData={versionToPageData(currentVersion, item.original_index)}
            width={240}
            height={135}
            quality={0.7}
          />
        ) : /* 优先级 5: 兜底 → 占位符 */ (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
            无预览
          </div>
        )}
      </div>

      {/* feat-185: 降级提示 Badge */}
      {fallbackMode && (
        <Badge
          variant="outline"
          className="absolute top-1 left-1 bg-amber-100 text-amber-700 border-amber-300 text-[9px] px-1.5 py-0.5 z-10"
        >
          降级渲染
        </Badge>
      )}

      {/* 信息栏 */}
      <div className="px-2 py-1.5">
        <div className="flex items-center justify-between gap-1">
          <span className="text-xs font-medium text-gray-700 truncate">
            {item.display_title || `第 ${item.original_index + 1} 页`}
          </span>
          {versionCount > 1 && (
            <Badge variant="secondary" className="text-[10px] px-1 py-0 h-4">
              v{versionCount}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1 mt-0.5">
          <span className={cn("text-[10px] px-1.5 py-0.5 rounded", sourceColor)}>
            {sourceLabel}
          </span>
          <span className="text-[10px] text-gray-400">
            P{item.original_index + 1}
          </span>
        </div>
      </div>

      {/* 选中标记 */}
      {isSelected && (
        <div className="absolute top-1 right-1 w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center shadow">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}

      {/* 多选标记 */}
      {isMultiSelected && !isSelected && (
        <div className="absolute top-1 right-1 w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center shadow">
          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
      )}

      {/* 版本标记 */}
      {versionCount > 1 && (
        <div className="absolute top-1 left-1 px-1.5 py-0.5 bg-amber-500 text-white text-[10px] rounded shadow">
          v{item.versions.length}
        </div>
      )}
    </div>
  )
}

/**
 * 幻灯片分组
 */
function SlideGroup({
  group,
  activeSlideId,
  finalSelection,
  multiSelectedIds,
  slideImageUrls,
  fileA,
  fileB,
  onSlideClick,
  onSlideDoubleClick,
}: {
  group: SlidePoolGroup
  activeSlideId: string | null
  finalSelection: string[]
  multiSelectedIds: string[]
  slideImageUrls?: Record<string, string>
  fileA?: File | null
  fileB?: File | null
  onSlideClick: (slideId: string, e?: React.MouseEvent) => void
  onSlideDoubleClick?: (slideId: string) => void
}) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <div className="mb-4">
      {/* 分组标题 */}
      <button
        type="button"
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center justify-between px-2 py-1.5 hover:bg-gray-100 rounded text-left"
      >
        <div className="flex items-center gap-2">
          <svg
            className={cn("w-3 h-3 text-gray-500 transition-transform", isCollapsed && "-rotate-90")}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          <span className="text-sm font-medium text-gray-700">{group.group_label}</span>
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-4">
            {group.items.length}
          </Badge>
        </div>
      </button>

      {/* 幻灯片列表 */}
      {!isCollapsed && (
        <div className="grid grid-cols-2 gap-2 mt-2 px-2">
          {group.items.map((item) => {
            const currentVersion = getCurrentVersion(item)
            const isSelected = currentVersion
              ? finalSelection.includes(currentVersion.version_id)
              : false
            const isMultiSelected = multiSelectedIds.includes(item.slide_id)
            const imageUrl = slideImageUrls?.[item.slide_id]

            return (
              <SlideThumbnail
                key={item.slide_id}
                item={item}
                isActive={activeSlideId === item.slide_id}
                isSelected={isSelected}
                isMultiSelected={isMultiSelected}
                imageUrl={imageUrl}
                fileA={fileA}
                fileB={fileB}
                onClick={(e) => onSlideClick(item.slide_id, e)}
                onDoubleClick={onSlideDoubleClick ? () => onSlideDoubleClick(item.slide_id) : undefined}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

/**
 * 幻灯片池面板
 */
export function SlidePoolPanel({
  slidePool,
  activeSlideId,
  finalSelection,
  onSlideClick,
  onSlideDoubleClick,
  slideImageUrls,
  isProcessing,
  isMerging,
  onMergeSelected,
  fileA,
  fileB,
  className,
}: SlidePoolPanelProps) {
  // 计算分组
  const groups = useMemo(() => getSlidePoolGroups(slidePool), [slidePool])

  // 多选状态
  const [multiSelectedIds, setMultiSelectedIds] = useState<string[]>([])

  // 检查是否为当前版本被选中
  const isVersionSelected = (item: SlidePoolItem): boolean => {
    const currentVersion = getCurrentVersion(item)
    return currentVersion ? finalSelection.includes(currentVersion.version_id) : false
  }

  // 处理幻灯片点击（支持 Ctrl/Cmd 多选）
  const handleSlideClick = useCallback((slideId: string, e?: React.MouseEvent) => {
    if (e?.ctrlKey || e?.metaKey) {
      // Ctrl/Cmd + 点击：添加到多选
      setMultiSelectedIds(prev =>
        prev.includes(slideId)
          ? prev.filter(id => id !== slideId)
          : [...prev, slideId]
      )
    } else {
      // 普通点击：设置为活动幻灯片，清除多选
      onSlideClick(slideId)
      setMultiSelectedIds([])
    }
  }, [onSlideClick])

  // 融合选中的幻灯片
  const handleMerge = useCallback(() => {
    if (multiSelectedIds.length >= 2 && onMergeSelected) {
      onMergeSelected(multiSelectedIds)
      setMultiSelectedIds([])
    }
  }, [multiSelectedIds, onMergeSelected])

  // 清除多选
  const clearMultiSelection = useCallback(() => {
    setMultiSelectedIds([])
  }, [])

  if (groups.length === 0) {
    return (
      <div className={cn("flex items-center justify-center h-64 text-gray-500", className)}>
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-300 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <p className="text-sm">上传 PPT 后显示幻灯片</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("bg-white border rounded-lg overflow-hidden", className)}>
      {/* 头部 */}
      <div className="px-3 py-2 border-b bg-gray-50 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">幻灯片池</h3>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>共 {Object.keys(slidePool).length} 页</span>
          {finalSelection.length > 0 && (
            <Badge variant="default" className="text-[10px]">
              已选 {finalSelection.length}
            </Badge>
          )}
        </div>
      </div>

      {/* 分组列表 */}
      <ScrollArea className="h-[calc(100vh-340px)]">
        <div className="py-2">
          {groups.map((group) => (
            <SlideGroup
              key={group.group_id}
              group={group}
              activeSlideId={activeSlideId}
              finalSelection={finalSelection}
              multiSelectedIds={multiSelectedIds}
              slideImageUrls={slideImageUrls}
              fileA={fileA}
              fileB={fileB}
              onSlideClick={handleSlideClick}
              onSlideDoubleClick={onSlideDoubleClick}
            />
          ))}
        </div>
      </ScrollArea>

      {/* 多选操作栏 */}
      {multiSelectedIds.length >= 2 && (
        <div className="px-3 py-2 border-t bg-purple-50 text-xs text-purple-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>已选择 {multiSelectedIds.length} 页</span>
            <button
              onClick={clearMultiSelection}
              className="text-purple-500 hover:text-purple-700 underline"
            >
              取消选择
            </button>
          </div>
          {onMergeSelected && (
            <button
              onClick={handleMerge}
              disabled={isMerging}
              className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1"
            >
              {isMerging ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  融合中...
                </>
              ) : (
                <>
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  融合选中页面
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* 多选提示 */}
      {multiSelectedIds.length === 0 && (
        <div className="px-3 py-2 border-t bg-gray-50 text-xs text-gray-500">
          💡 Ctrl/Cmd + 点击可多选页面进行融合
        </div>
      )}

      {/* 底部提示 */}
      {isProcessing && (
        <div className="px-3 py-2 border-t bg-indigo-50 text-xs text-indigo-600 flex items-center gap-2">
          <span className="w-3 h-3 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          处理中...
        </div>
      )}
    </div>
  )
}

export default SlidePoolPanel