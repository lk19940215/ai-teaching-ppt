"use client"

import * as React from "react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/ppt-canvas-renderer"

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
}

// 每页显示的缩略图数量
const THUMBNAILS_PER_PAGE = 6

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
}: PptCanvasPreviewProps) {
  const [internalCurrentPage, setInternalCurrentPage] = useState(1)

  // 使用外部控制的页码或内部状态
  const currentPg = onPageChange ? currentPage : internalCurrentPage

  // 计算总页数
  const totalPages = Math.max(1, Math.ceil(pages.length / THUMBNAILS_PER_PAGE))

  // 获取当前页显示的缩略图索引范围
  const startIndex = (currentPg - 1) * THUMBNAILS_PER_PAGE
  const endIndex = Math.min(startIndex + THUMBNAILS_PER_PAGE, pages.length)
  const currentPageThumbnails = pages.slice(startIndex, endIndex)

  // 转换为基础数据（用于兼容）
  const convertToEnhanced = (page: PptPageData | EnhancedPptPageData): EnhancedPptPageData => {
    if ((page as EnhancedPptPageData).shapes && Array.isArray((page as EnhancedPptPageData).shapes)) {
      return page as EnhancedPptPageData
    }
    // 基础数据转换为增强数据
    return {
      index: page.index,
      title: page.title,
      content: (page.content as string[]).map(text => ({ type: 'text' as const, text })),
      shapes: [],
      layout: { width: 960, height: 540 },
    }
  }

  // 处理页面点击选择
  const handlePageClick = (pageIndex: number) => {
    if (disableSelection) return

    if (onSelectionChange) {
      const newSelection = selectedPages.includes(pageIndex)
        ? selectedPages.filter(p => p !== pageIndex)
        : [...selectedPages, pageIndex]
      onSelectionChange(newSelection)
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

  // 渲染 Canvas 缩略图
  const renderCanvasThumbnail = (page: PptPageData | EnhancedPptPageData) => {
    const enhancedPage = convertToEnhanced(page)
    const isSelected = selectedPages.includes(page.index)

    return (
      <div
        key={page.index}
        onClick={() => handlePageClick(page.index)}
        className={cn(
          "flex-shrink-0 w-full aspect-[4/3] rounded-lg overflow-hidden border-2 transition-all duration-200 relative cursor-pointer",
          isSelected
            ? "border-indigo-500 ring-2 ring-indigo-200 shadow-md"
            : "border-gray-200 hover:border-gray-300",
          disableSelection ? "cursor-default" : "hover:shadow-sm"
        )}
        role={disableSelection ? "button" : undefined}
        aria-disabled={disableSelection}
      >
        <PptCanvasRenderer
          pageData={enhancedPage}
          width={300}
          height={169}
          isSelected={isSelected}
          onClick={() => handlePageClick(page.index)}
          quality={0.8}
        />
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
      ) : (
        /* 缩略图网格 */
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          {currentPageThumbnails.map(page =>
            useCanvas ? renderCanvasThumbnail(page) : renderCssThumbnail(page as PptPageData)
          )}
        </div>
      )}

      {/* 分页导航 */}
      {pages.length > 0 && (
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
    </div>
  )
}

export default PptCanvasPreview
