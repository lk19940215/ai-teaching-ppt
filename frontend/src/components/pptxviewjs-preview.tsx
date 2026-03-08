"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { PptxViewJSRenderer } from "@/components/pptxviewjs-renderer"

export interface EnhancedPptPageData {
  index: number
  title: string
  content: Array<{
    type: 'text' | 'image' | 'table'
    text?: string
    image_base64?: string
    table_data?: string[][]
  }>
  shapes: Array<{
    type: string
    name: string
    position: {
      x: number
      y: number
      width: number
      height: number
    }
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
  layout: {
    width: number
    height: number
  }
}

interface PptxViewJSPreviewProps {
  label: string
  file: File | null
  isLoading?: boolean
  selectedPages?: number[]
  onSelectionChange?: (selectedPages: number[]) => void
  disableSelection?: boolean
  pptSource?: 'A' | 'B'
  fallbackMode?: boolean
  onFallbackModeChange?: (fallback: boolean) => void
  onRenderError?: (error: Error) => void
  onPageChange?: (pageIndex: number) => void
  usePptxViewJS?: boolean
}

/**
 * PptxViewJS 预览组件（feat-208）
 *
 * 功能：
 * - 使用 PptxViewJS 渲染 PPTX 文件
 * - 单页预览模式（左右翻页）
 * - 底部缩略图条
 * - 键盘快捷键支持（← →）
 * - 点击选中页面
 */
export function PptxViewJSPreview({
  label,
  file,
  isLoading = false,
  selectedPages = [],
  onSelectionChange,
  disableSelection = false,
  pptSource,
  fallbackMode = false,
  onFallbackModeChange,
  onRenderError,
  onPageChange,
  usePptxViewJS = true,
}: PptxViewJSPreviewProps) {
  const [currentIndex, setCurrentIndex] = React.useState(0)
  const [slideCount, setSlideCount] = React.useState(0)
  const [internalError, setInternalError] = React.useState<Error | null>(null)
  const thumbnailStripRef = React.useRef<HTMLDivElement>(null)
  const containerRef = React.useRef<HTMLDivElement>(null)

  // 错误处理
  const handleError = React.useCallback((error: Error) => {
    setInternalError(error)
    onRenderError?.(error)
    // 触发降级模式
    if (onFallbackModeChange) {
      onFallbackModeChange(true)
    }
  }, [onRenderError, onFallbackModeChange])

  // 当文件变化时重置状态
  React.useEffect(() => {
    if (!file) {
      setSlideCount(0)
      setCurrentIndex(0)
      setInternalError(null)
    }
  }, [file])

  // 加载完成回调
  const handleLoad = React.useCallback((count: number) => {
    setSlideCount(count)
    if (currentIndex >= count) {
      setCurrentIndex(0)
    }
  }, [currentIndex])

  // 翻页控制
  const goToPage = React.useCallback((index: number) => {
    if (index >= 0 && index < slideCount) {
      setCurrentIndex(index)
      onPageChange?.(index)
    }
  }, [slideCount, onPageChange])

  const goPrev = React.useCallback(() => goToPage(currentIndex - 1), [currentIndex, goToPage])
  const goNext = React.useCallback(() => goToPage(currentIndex + 1), [currentIndex, goToPage])

  // 键盘快捷键
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!containerRef.current?.contains(document.activeElement) &&
          document.activeElement !== containerRef.current) return

      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        goPrev()
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        goNext()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [goPrev, goNext])

  // 缩略图自动滚动
  React.useEffect(() => {
    if (thumbnailStripRef.current) {
      const thumbEl = thumbnailStripRef.current.children[currentIndex] as HTMLElement
      if (thumbEl) {
        thumbEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
      }
    }
  }, [currentIndex])

  // 选中/取消选中页面
  const togglePageSelection = React.useCallback((pageIndex: number, e?: React.MouseEvent) => {
    if (disableSelection || !onSelectionChange) return

    if (e?.ctrlKey || e?.metaKey) {
      // Ctrl/Cmd + 点击：切换单个页面
      const newSelection = selectedPages.includes(pageIndex)
        ? selectedPages.filter(p => p !== pageIndex)
        : [...selectedPages, pageIndex]
      onSelectionChange(newSelection)
    } else if (e?.shiftKey && selectedPages.length > 0) {
      // Shift + 点击：选择范围
      const lastSelected = selectedPages[selectedPages.length - 1]
      const start = Math.min(lastSelected, pageIndex)
      const end = Math.max(lastSelected, pageIndex)
      const range: number[] = []
      for (let i = start; i <= end; i++) {
        if (!selectedPages.includes(i)) range.push(i)
      }
      onSelectionChange([...selectedPages, ...range])
    } else {
      // 普通点击：单选或取消
      if (selectedPages.includes(pageIndex) && selectedPages.length === 1) {
        onSelectionChange([])
      } else {
        onSelectionChange([pageIndex])
      }
    }
  }, [disableSelection, onSelectionChange, selectedPages])

  // 当前页面是否被选中
  const isCurrentSelected = selectedPages.includes(currentIndex)

  if (!file) {
    return (
      <div className="border rounded-lg p-6 bg-white" ref={containerRef}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">{label}</h3>
        </div>
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          <p className="mt-2 text-sm text-gray-500">上传 PPT 文件后显示预览</p>
        </div>
      </div>
    )
  }

  // 加载中状态（file 存在但 slideCount 还是 0）
  if (slideCount === 0) {
    return (
      <div className="border rounded-lg p-6 bg-white" ref={containerRef}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">{label}</h3>
          <span className="text-xs text-gray-500">正在加载...</span>
        </div>
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500 text-sm">正在解析 PPT 文件...</p>
        </div>
      </div>
    )
  }

  return (
    <div
      className="border rounded-lg bg-white overflow-hidden"
      ref={containerRef}
      tabIndex={0}
      onFocus={() => {}}
    >
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <h3 className="text-sm font-medium text-gray-900">{label}</h3>
        <div className="flex items-center gap-3">
          {selectedPages.length > 0 && (
            <span className="text-xs text-indigo-600 font-medium">
              已选 {selectedPages.length} 页
            </span>
          )}
          <span className="text-xs text-gray-500">共 {slideCount} 页</span>
        </div>
      </div>

      {/* 降级模式提示 */}
      {fallbackMode && (
        <div className="mx-4 mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
          PptxViewJS 渲染不可用，已切换到简化模式
        </div>
      )}

      {/* 主预览区 */}
      <div className="relative group">
        {/* 当前页面大图 */}
        <div
          className={cn(
            "mx-4 mt-3 rounded-lg overflow-hidden border-2 transition-all cursor-pointer",
            isCurrentSelected
              ? "border-indigo-500 ring-2 ring-indigo-200 shadow-lg"
              : "border-gray-200 hover:border-gray-300"
          )}
          onClick={(e) => togglePageSelection(currentIndex, e)}
        >
          {usePptxViewJS && !fallbackMode ? (
            <PptxViewJSRenderer
              file={file}
              slideIndex={currentIndex}
              width={800}
              height={450}
              isSelected={isCurrentSelected}
              onClick={() => {}}
              quality="high"
              onError={handleError}
              onLoad={handleLoad}
            />
          ) : (
            <div className="w-[800px] h-[450px] bg-gray-100 flex items-center justify-center text-gray-500">
              降级模式：请使用 Canvas 渲染器
            </div>
          )}

          {/* 选中标记 */}
          {isCurrentSelected && (
            <div className="absolute top-6 right-6 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center shadow-md">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
          )}
        </div>

        {/* 左箭头 */}
        <button
          onClick={(e) => { e.stopPropagation(); goPrev() }}
          disabled={currentIndex === 0}
          className={cn(
            "absolute left-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all z-10",
            currentIndex === 0
              ? "bg-gray-200/50 text-gray-400 cursor-not-allowed"
              : "bg-white/90 text-gray-700 shadow-md hover:bg-white hover:shadow-lg"
          )}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* 右箭头 */}
        <button
          onClick={(e) => { e.stopPropagation(); goNext() }}
          disabled={currentIndex === slideCount - 1}
          className={cn(
            "absolute right-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all z-10",
            currentIndex === slideCount - 1
              ? "bg-gray-200/50 text-gray-400 cursor-not-allowed"
              : "bg-white/90 text-gray-700 shadow-md hover:bg-white hover:shadow-lg"
          )}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* 页码控制栏 */}
      <div className="flex items-center justify-center gap-4 px-4 py-2">
        <span className="text-sm text-gray-600 font-medium">
          第 {currentIndex + 1} 页 / 共 {slideCount} 页
        </span>
        {!disableSelection && (
          <button
            onClick={() => togglePageSelection(currentIndex)}
            className={cn(
              "px-3 py-1 rounded-full text-xs font-medium transition-colors",
              isCurrentSelected
                ? "bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            )}
          >
            {isCurrentSelected ? '取消选择' : '选择此页'}
          </button>
        )}
      </div>

      {/* 底部缩略图条 */}
      <div className="border-t bg-gray-50 px-2 py-2">
        <div
          ref={thumbnailStripRef}
          className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin"
          style={{ scrollbarWidth: 'thin' }}
        >
          {Array.from({ length: slideCount }).map((_, idx) => {
            const isActive = idx === currentIndex
            const isSelected = selectedPages.includes(idx)

            return (
              <div
                key={idx}
                onClick={() => goToPage(idx)}
                className={cn(
                  "flex-shrink-0 w-24 h-14 rounded border-2 overflow-hidden cursor-pointer transition-all relative",
                  isActive
                    ? "border-indigo-500 ring-1 ring-indigo-300 shadow"
                    : isSelected
                    ? "border-green-400 ring-1 ring-green-200"
                    : "border-gray-200 hover:border-gray-400 opacity-70 hover:opacity-100"
                )}
              >
                {usePptxViewJS && !fallbackMode ? (
                  <PptxViewJSRenderer
                    file={file}
                    slideIndex={idx}
                    width={96}
                    height={54}
                    isSelected={false}
                    onClick={() => {}}
                    quality="low"
                  />
                ) : (
                  <div className="w-full h-full bg-gray-200 flex items-center justify-center text-xs text-gray-500">
                    P{idx + 1}
                  </div>
                )}
                {/* 页码标签 */}
                <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-center text-[9px] py-0.5">
                  P{idx + 1}
                </div>
                {/* 选中标记 */}
                {isSelected && (
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
      </div>

      {/* 已选页面汇总 */}
      {selectedPages.length > 0 && (
        <div className="px-4 py-2 border-t text-xs text-indigo-600 bg-indigo-50/50">
          已选择：{selectedPages.sort((a, b) => a - b).map(p => `P${p + 1}`).join(", ")}
        </div>
      )}
    </div>
  )
}

export default PptxViewJSPreview
