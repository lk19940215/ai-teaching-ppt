"use client"

import * as React from "react"
import { useState, useRef, useEffect, useMemo } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/ppt-canvas-renderer"
import { PptxjsRenderer, type PptxjsPageData } from "@/components/pptxjs-renderer"
import { apiBaseUrl } from '@/lib/api'

// 兼容旧的 PPT 页面数据结构
export interface PptPageData {
  index: number
  title: string
  content: string[]
  shapes?: string[]
}

// PPT Canvas 预览组件属性
interface PptCanvasPreviewProps {
  // PPT 名称标签（如 "PPT A" 或 "PPT B"）
  label: string
  // 页面数据数组（支持增强数据和基础数据）
  pages: PptPageData[] | EnhancedPptPageData[]
  // 是否已加载数据
  isLoading?: boolean
  // 选中的页面索引数组（支持多选）
  selectedPages?: number[]
  // 页面选择变化回调
  onSelectionChange?: (selectedPages: number[]) => void
  // 是否禁用选择（只读模式）
  disableSelection?: boolean
  // 当前预览页码（用于分页）
  currentPage?: number
  // 页码变化回调
  onPageChange?: (page: number) => void
  // 使用 Canvas 渲染（默认 true）
  useCanvas?: boolean
  // 启用虚拟滚动（默认 true，50 页以上自动启用）
  enableVirtualScroll?: boolean
  // PPT 来源标识（用于右键菜单操作）
  pptSource?: 'A' | 'B'
  // 跳转到指定页面回调（用于右键菜单）
  onJumpToPage?: (source: 'A' | 'B', pageIndex: number) => void
  // 复制页面回调（用于右键菜单）
  onCopyPage?: (source: 'A' | 'B', pageIndex: number) => void
  // 删除页面回调（用于右键菜单）
  onDeletePage?: (source: 'A' | 'B', pageIndex: number) => void
  // 降级模式：使用后端解析数据（feat-097）
  fallbackMode?: boolean
  // 降级模式切换回调（feat-097）
  onFallbackModeChange?: (fallback: boolean) => void
  // PPT 文件引用（用于降级时调用后端 API，feat-097）
  file?: File | null
  // Canvas 渲染失败回调（feat-097）
  onRenderError?: (error: Error) => void
  // feat-098: 格式兼容性警告回调
  onCompatibilityWarning?: (warnings: string[]) => void
}

// 每页显示的缩略图数量
const THUMBNAILS_PER_PAGE = 6

// 虚拟滚动配置
const VIRTUAL_SCROLL_THRESHOLD = 12 // 超过 12 页启用虚拟滚动
const RENDER_AHEAD = 3 // 预渲染前方 3 个缩略图

/**
 * PPT Canvas 预览组件（feat-084）
 *
 * 功能：
 * - 使用 Canvas 渲染真实 PPT 页面效果
 * - 支持文本、图片、表格、形状的显示
 * - 支持点击选择页面（可多选）
 * - 分页显示缩略图
 * - 选中状态高亮显示
 * - 上一页/下一页导航
 */
export function PptCanvasPreview({
  label,
  pages,
  isLoading = false,
  selectedPages = [],
  onSelectionChange,
  disableSelection = false,
  currentPage = 1,
  onPageChange,
  useCanvas = true,
  enableVirtualScroll = true,
  pptSource,
  onJumpToPage,
  onCopyPage,
  onDeletePage,
  fallbackMode = false,
  onFallbackModeChange,
  file,
  onRenderError,
}: PptCanvasPreviewProps) {
  const [internalCurrentPage, setInternalCurrentPage] = useState(1)
  // 虚拟滚动：滚动容器引用
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  // 虚拟滚动：当前滚动位置
  const [scrollTop, setScrollTop] = useState(0)
  // 虚拟滚动：缩略图高度（含间距）
  const thumbnailHeight = 180 // 估算每个缩略图的高度（像素）

  // feat-097: 降级模式状态（内部）
  const [internalFallbackMode, setInternalFallbackMode] = useState(fallbackMode)
  // feat-097: 降级提示消息
  const [fallbackMessage, setFallbackMessage] = useState<string | null>(null)
  // feat-098: 超时重试状态
  const [retryCount, setRetryCount] = useState(0)
  // feat-098: 格式兼容性警告
  const [compatibilityWarnings, setCompatibilityWarnings] = useState<string[]>([])

  // 使用外部控制的降级模式或内部状态
  const isFallbackMode = onFallbackModeChange ? fallbackMode : internalFallbackMode
  const setFallbackModeState = onFallbackModeChange || setInternalFallbackMode

  // feat-089: 右键菜单状态
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean
    x: number
    y: number
    pageIndex: number
  }>({ visible: false, x: 0, y: 0, pageIndex: 0 })

  // feat-089: 记录上次点击的页面索引（用于 Shift 多选）
  const lastClickedIndex = useRef<number | null>(null)

  // feat-089: 性能优化 - 防抖滚动更新
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // 使用外部控制的页码或内部状态
  const currentPg = onPageChange ? currentPage : internalCurrentPage

  // 计算总页数
  const totalPages = Math.max(1, Math.ceil(pages.length / THUMBNAILS_PER_PAGE))

  // 获取当前页显示的缩略图索引范围
  const startIndex = (currentPg - 1) * THUMBNAILS_PER_PAGE
  const endIndex = Math.min(startIndex + THUMBNAILS_PER_PAGE, pages.length)
  const currentPageThumbnails = pages.slice(startIndex, endIndex)

  // 虚拟滚动：计算可见范围
  const visibleRange = useMemo(() => {
    if (!enableVirtualScroll || pages.length <= VIRTUAL_SCROLL_THRESHOLD) {
      return { start: 0, end: pages.length }
    }

    // 容器可见高度
    const containerHeight = scrollContainerRef.current?.clientHeight || 600
    // 可见区域能显示的缩略图数量
    const visibleCount = Math.ceil(containerHeight / thumbnailHeight) + RENDER_AHEAD
    // 当前滚动位置对应的起始索引
    const start = Math.floor(scrollTop / thumbnailHeight)
    // 结束索引（多渲染 RENDER_AHEAD 个）
    const end = Math.min(start + visibleCount, pages.length)

    return {
      start: Math.max(0, start - RENDER_AHEAD),
      end: Math.min(end, pages.length)
    }
  }, [scrollTop, pages.length, enableVirtualScroll])

  // 虚拟滚动：处理滚动事件（feat-089: 防抖优化）
  const handleScroll = React.useCallback(() => {
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current)
    }

    scrollTimeoutRef.current = setTimeout(() => {
      if (scrollContainerRef.current) {
        setScrollTop(scrollContainerRef.current.scrollTop)
      }
    }, 50) // 50ms 防抖
  }, [])

  // 转换为基础数据（用于兼容）
  const convertToEnhanced = (page: PptPageData | EnhancedPptPageData, pageIndex: number): EnhancedPptPageData => {
    // 检查是否已经是完整的 EnhancedPptPageData（有 shapes 且有 text_content）
    const maybeEnhanced = page as EnhancedPptPageData
    const hasRealShapes = maybeEnhanced.shapes && maybeEnhanced.shapes.length > 0 &&
                          maybeEnhanced.shapes[0]?.text_content

    if (hasRealShapes) {
      // 确保有 layout 属性
      if (!maybeEnhanced.layout) {
        maybeEnhanced.layout = { width: 960, height: 540 }
      }
      return maybeEnhanced
    }

    // 基础数据转换为增强数据
    // 将 content 字符串数组转换为 shapes
    const shapes: any[] = []
    const content = page.content as string[]

    if (content && content.length > 0) {
      // 创建文本框形状
      shapes.push({
        type: 'text_box',
        name: `content-${pageIndex}`,
        position: { x: 50, y: 80, width: 860, height: 400 },
        text_content: content.map((text: string) => ({
          runs: [{ text, font: { size: 18, color: '000000' } }]
        }))
      })
    }

    return {
      index: page.index,
      title: page.title,
      content: content.map((text: string) => ({ type: 'text' as const, text })),
      shapes,
      layout: { width: 960, height: 540 },
    }
  }

  // 处理页面点击选择（feat-089: 支持 Shift/Ctrl 多选）
  const handlePageClick = (pageIndex: number, event?: React.MouseEvent) => {
    if (disableSelection) return
    if (!onSelectionChange) return

    const nativeEvent = event?.nativeEvent || event

    // 如果按下 Shift 键，选择连续范围
    if (event?.shiftKey && lastClickedIndex.current !== null) {
      const start = lastClickedIndex.current
      const end = pageIndex
      const rangeStart = Math.min(start, end)
      const rangeEnd = Math.max(start, end)

      // 生成连续范围
      const range = []
      for (let i = rangeStart; i <= rangeEnd; i++) {
        if (!selectedPages.includes(i)) {
          range.push(i)
        }
      }
      onSelectionChange([...selectedPages, ...range])
      lastClickedIndex.current = pageIndex
      return
    }

    // 如果按下 Ctrl/Cmd 键，切换单个页面选择状态
    if (event?.ctrlKey || event?.metaKey) {
      const newSelection = selectedPages.includes(pageIndex)
        ? selectedPages.filter(p => p !== pageIndex)
        : [...selectedPages, pageIndex]
      onSelectionChange(newSelection)
      lastClickedIndex.current = pageIndex
      return
    }

    // 普通点击：单选
    onSelectionChange([pageIndex])
    lastClickedIndex.current = pageIndex
  }

  // feat-089: 处理右键菜单
  const handleContextMenu = (event: React.MouseEvent, pageIndex: number) => {
    event.preventDefault()
    if (disableSelection) return

    setContextMenu({
      visible: true,
      x: event.clientX,
      y: event.clientY,
      pageIndex
    })
  }

  // feat-089: 关闭右键菜单
  const closeContextMenu = () => {
    setContextMenu(prev => ({ ...prev, visible: false }))
  }

  // feat-089: 处理右键菜单操作
  const handleMenuAction = (action: 'jump' | 'copy' | 'delete') => {
    const { pageIndex } = contextMenu
    if (!pptSource) return

    switch (action) {
      case 'jump':
        onJumpToPage?.(pptSource, pageIndex)
        break
      case 'copy':
        onCopyPage?.(pptSource, pageIndex)
        break
      case 'delete':
        onDeletePage?.(pptSource, pageIndex)
        break
    }
    closeContextMenu()
  }

  // 点击其他地方关闭右键菜单
  React.useEffect(() => {
    if (!contextMenu.visible) return
    const handleClick = () => closeContextMenu()
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [contextMenu.visible])

  // feat-089: 组件卸载时清理定时器
  React.useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current)
      }
    }
  }, [])

  // feat-097: 从后端 API 获取降级数据（需要文件作为参数）
  const fetchFallbackData = React.useCallback(async (file: File) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('extract_enhanced', 'false')

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/parse`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        console.error('后端解析 API 调用失败:', response.status)
        return null
      }

      const data = await response.json()
      return data.pages || []
    } catch (error) {
      console.error('获取降级数据失败:', error)
      return null
    }
  }, [apiBaseUrl])

  // feat-098: 处理重试
  const handleRetry = async () => {
    if (!file) return

    setRetryCount(prev => prev + 1)
    setFallbackMessage(null)
    setCompatibilityWarnings([])

    // 重置降级模式，尝试重新渲染
    if (onFallbackModeChange) {
      onFallbackModeChange(false)
    } else {
      setInternalFallbackMode(false)
    }

    // 触发父组件重新解析
    if (onRenderError) {
      // 通过重新调用 onRenderError 来触发重试逻辑
      // 实际重试由父组件的 useEffect 处理
    }
  }

  // 处理上一页
  const handlePrevPage = () => {
    const newPage = Math.max(1, currentPg - 1)
    if (onPageChange) {
      onPageChange(newPage)
    } else {
      setInternalCurrentPage(newPage)
    }
  }

  // 处理下一页
  const handleNextPage = () => {
    const newPage = Math.min(totalPages, currentPg + 1)
    if (onPageChange) {
      onPageChange(newPage)
    } else {
      setInternalCurrentPage(newPage)
    }
  }

  // 获取页面类型的背景色
  const getPageBgColor = (index: number) => {
    const colors = [
      "bg-gradient-to-br from-indigo-500 to-purple-600",
      "bg-gradient-to-br from-emerald-500 to-teal-600",
      "bg-gradient-to-br from-amber-500 to-orange-600",
      "bg-gradient-to-br from-blue-500 to-cyan-600",
      "bg-gradient-to-br from-rose-500 to-pink-600",
      "bg-gradient-to-br from-violet-500 to-purple-600",
    ]
    if (index === 0) return colors[0]
    return colors[(index - 1) % colors.length]
  }

  // 获取页面类型的图标
  const getPageTypeIcon = (index: number) => {
    const icons = ["📖", "📑", "📚", "💬", "✍️", "✅", "🔤", "📝", "💭", "🔍"]
    if (index === 0) return icons[0]
    return icons[(index - 1) % icons.length]
  }

  // 渲染 Canvas 缩略图（feat-089: 支持右键菜单）
  const renderCanvasThumbnail = (page: PptPageData | EnhancedPptPageData) => {
    const enhancedPage = convertToEnhanced(page, page.index)
    const isSelected = selectedPages.includes(page.index)

    return (
      <div
        key={page.index}
        onClick={(e) => handlePageClick(page.index, e)}
        onContextMenu={(e) => handleContextMenu(e, page.index)}
        className={cn(
          "flex-shrink-0 w-full aspect-[4/3] rounded-lg overflow-hidden border-2 transition-all duration-200 relative cursor-pointer group",
          isSelected
            ? "border-indigo-500 ring-2 ring-indigo-200 shadow-md bg-indigo-50/30"
            : "border-gray-200 hover:border-gray-300",
          disableSelection ? "cursor-default" : "hover:shadow-sm"
        )}
        role={disableSelection ? "button" : undefined}
        aria-disabled={disableSelection}
      >
        {/* 注意：PptCanvasRenderer 的 onClick 不传递事件，点击事件由外层 div 的 onClick 处理 */}
        <PptCanvasRenderer
          pageData={enhancedPage}
          width={300}
          height={169}
          isSelected={isSelected}
          onClick={() => {}} // 空回调，点击事件由外层 div 捕获
          quality={0.8}
        />
        {/* feat-089: 选中指示器 */}
        {isSelected && (
          <div className="absolute top-1 right-1 w-5 h-5 bg-indigo-500 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        )}
        {/* feat-089: 悬停提示 */}
        {!disableSelection && (
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors pointer-events-none" />
        )}
      </div>
    )
  }

  // 渲染虚拟滚动缩略图列表（只渲染可见区域）
  const renderVirtualScrollList = () => {
    const { start, end } = visibleRange
    const visiblePages = pages.slice(start, end)
    // 每行 3 个缩略图，计算总行数
    const thumbnailsPerRow = 3
    const totalRows = Math.ceil(pages.length / thumbnailsPerRow)
    const rowHeight = thumbnailHeight
    const totalHeight = totalRows * rowHeight

    return (
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="overflow-y-auto"
        style={{ height: '600px', maxHeight: '600px' }}
      >
        <div style={{ height: `${totalHeight}px`, position: 'relative' }}>
          <div style={{
            position: 'absolute',
            top: `${Math.floor(start / thumbnailsPerRow) * rowHeight}px`,
            left: 0,
            right: 0
          }}>
            <div className="grid grid-cols-3 gap-3">
              {visiblePages.map(page => renderCanvasThumbnail(page))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 渲染 CSS 缩略图（ fallback）
  const renderCssThumbnail = (page: PptPageData) => {
    const isSelected = selectedPages.includes(page.index)
    const bgColor = getPageBgColor(page.index)

    return (
      <button
        key={page.index}
        onClick={() => handlePageClick(page.index)}
        disabled={disableSelection}
        className={cn(
          "flex-shrink-0 w-full aspect-[4/3] rounded-lg overflow-hidden border-2 transition-all duration-200 flex flex-col",
          isSelected
            ? "border-indigo-500 ring-2 ring-indigo-200 shadow-md"
            : "border-gray-200 hover:border-gray-300",
          disableSelection ? "cursor-default" : "cursor-pointer hover:shadow-sm",
          bgColor
        )}
      >
        {/* 缩略图顶部：页面类型图标 */}
        <div className="flex-1 flex items-center justify-center text-2xl">
          {getPageTypeIcon(page.index)}
        </div>
        {/* 缩略图底部：标题（截断） */}
        <div className="h-1/3 bg-black/20 w-full px-1 py-0.5">
          <p className="text-white text-[10px] line-clamp-2 text-center leading-tight">
            {page.title.substring(0, 12)}{page.title.length > 12 ? "..." : ""}
          </p>
        </div>
        {/* 页码标签 */}
        <div className="absolute top-1 left-1 bg-black/50 text-white text-[9px] px-1.5 py-0.5 rounded">
          P{page.index + 1}
        </div>
      </button>
    )
  }

  return (
    <div className="border rounded-lg p-6 bg-white">
      {/* 头部：标签 + 页码信息 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          {label}
        </h3>
        <span className="text-sm text-gray-500">
          共 {pages.length} 页
        </span>
      </div>

      {/* feat-097: 降级模式警告提示 */}
      {isFallbackMode && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm text-amber-800 font-medium">已启用降级渲染模式</p>
              <p className="text-xs text-amber-700 mt-1">
                {fallbackMessage || 'Canvas 渲染不可用，已切换到后端解析模式，仅显示文本内容。'}
              </p>
              {/* feat-098: 重试按钮 */}
              <button
                onClick={handleRetry}
                className="mt-2 text-xs text-amber-900 underline hover:no-underline"
              >
                尝试重新渲染（重试 {retryCount} 次）
              </button>
            </div>
          </div>
        </div>
      )}

      {/* feat-098: 格式兼容性警告 */}
      {compatibilityWarnings.length > 0 && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <svg className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm text-blue-800 font-medium">格式兼容性提示</p>
              <ul className="text-xs text-blue-700 mt-1 list-disc list-inside">
                {compatibilityWarnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* 加载状态 */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-gray-500 text-sm">正在加载 PPT 预览...</p>
        </div>
      ) : pages.length === 0 ? (
        /* 空状态 */
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <p className="mt-2 text-sm text-gray-500">上传 PPT 文件后显示分页预览</p>
        </div>
      ) : enableVirtualScroll && pages.length > VIRTUAL_SCROLL_THRESHOLD ? (
        renderVirtualScrollList()
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          {currentPageThumbnails.map(page =>
            useCanvas ? renderCanvasThumbnail(page) : renderCssThumbnail(page as PptPageData)
          )}
        </div>
      )}

      {/* 分页导航（虚拟滚动模式下隐藏） */}
      {pages.length > 0 && !(enableVirtualScroll && pages.length > VIRTUAL_SCROLL_THRESHOLD) && (
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrevPage}
            disabled={currentPg === 1}
            className="text-sm"
          >
            ← 上一页
          </Button>
          <span className="text-sm text-gray-600">
            第 {currentPg} 页 / 共 {totalPages} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={handleNextPage}
            disabled={currentPg === totalPages}
            className="text-sm"
          >
            下一页 →
          </Button>
        </div>
      )}

      {/* 选中提示（如果有选中的页面） */}
      {selectedPages.length > 0 && (
        <div className="mt-3 pt-3 border-t text-sm text-indigo-600">
          已选择 {selectedPages.length} 页：
          <span className="font-mono ml-1">
            {selectedPages.map(p => `P${p + 1}`).join(", ")}
          </span>
        </div>
      )}

      {/* feat-089: 右键菜单 */}
      {contextMenu.visible && pptSource && (
        <div
          className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[160px]"
          style={{ left: contextMenu.x, top: contextMenu.y }}
        >
          <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-100">
            页面 {contextMenu.pageIndex + 1}
          </div>
          <button
            onClick={() => handleMenuAction('jump')}
            className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            跳转查看
          </button>
          <button
            onClick={() => handleMenuAction('copy')}
            className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            复制页面
          </button>
          <button
            onClick={() => handleMenuAction('delete')}
            className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            删除页面
          </button>
        </div>
      )}
    </div>
  )
}

export default PptCanvasPreview
