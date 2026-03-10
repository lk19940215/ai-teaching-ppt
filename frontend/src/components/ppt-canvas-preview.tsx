"use client"

import * as React from "react"
import { useState, useRef, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/ppt-canvas-renderer"
import { VersionSwitcher } from '@/components/version-switcher'
import { VersionHistoryPanel } from '@/components/version-history-panel'
import type { SlideStatus, SessionData } from '@/lib/version-api'
import { getSession, getVersionHistory, restoreVersion, toggleSlide } from '@/lib/version-api'

export interface PptPageData {
  index: number
  title: string
  content: string[]
  shapes?: string[]
}

interface PptCanvasPreviewProps {
  label: string
  pages: PptPageData[] | EnhancedPptPageData[]
  isLoading?: boolean
  selectedPages?: number[]
  onSelectionChange?: (selectedPages: number[]) => void
  disableSelection?: boolean
  pptSource?: 'A' | 'B'
  fallbackMode?: boolean
  onFallbackModeChange?: (fallback: boolean) => void
  file?: File | null
  onRenderError?: (error: Error) => void
  onPageChange?: (pageIndex: number) => void
  // 版本化功能 props (feat-141)
  sessionId?: string
  documentId?: 'ppt_a' | 'ppt_b'
  enableVersioning?: boolean
}

export function PptCanvasPreview({
  label,
  pages,
  isLoading = false,
  selectedPages = [],
  onSelectionChange,
  disableSelection = false,
  pptSource,
  fallbackMode = false,
  onFallbackModeChange,
  file,
  onRenderError,
  onPageChange: onPageChangeExternal,
  sessionId,
  documentId,
  enableVersioning = false,
}: PptCanvasPreviewProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [internalFallbackMode, setInternalFallbackMode] = useState(fallbackMode)
  const thumbnailStripRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // feat-141: 版本化状态
  const [versionHistory, setVersionHistory] = useState<Array<{ version: string; image_url: string; created_at: string; operation: string; prompt?: string }>>([])
  const [currentSlideVersion, setCurrentSlideVersion] = useState<string | null>('v1')
  const [currentSlideStatus, setCurrentSlideStatus] = useState<SlideStatus>('active')
  const [isHistoryPanelOpen, setIsHistoryPanelOpen] = useState(false)
  const [isVersionLoading, setIsVersionLoading] = useState(false)

  // feat-150: 图片预览状态（存储每页的图片 URL）
  const [slideImageUrls, setSlideImageUrls] = useState<Record<number, string>>({})

  const isFallbackMode = onFallbackModeChange ? fallbackMode : internalFallbackMode

  // feat-141: 加载版本历史
  useEffect(() => {
    if (!enableVersioning || !sessionId || !documentId || pages.length === 0) return

    const loadVersionHistory = async () => {
      setIsVersionLoading(true)
      try {
        const session = await getSession(sessionId)
        const history = await getVersionHistory(sessionId, documentId, currentIndex)
        setVersionHistory(history)

        // feat-150: 从会话数据提取每页的图片 URL
        const docState = session.documents[documentId]
        if (docState) {
          const imageUrls: Record<number, string> = {}
          for (const [slideIdx, slideState] of Object.entries(docState.slides)) {
            // 获取当前版本的图片 URL
            const currentVersion = slideState.current_version
            const versionData = slideState.versions.find(v => v.version === currentVersion)
            if (versionData?.image_url) {
              imageUrls[parseInt(slideIdx)] = versionData.image_url
            }
          }
          setSlideImageUrls(imageUrls)
        }

        if (docState && docState.slides[currentIndex]) {
          const slideState = docState.slides[currentIndex]
          setCurrentSlideVersion(slideState.current_version)
          setCurrentSlideStatus(slideState.status)
        } else {
          setCurrentSlideVersion('v1')
          setCurrentSlideStatus('active')
        }
      } catch (err) {
        console.error('加载版本历史失败:', err)
        setVersionHistory([])
        setCurrentSlideVersion('v1')
        setCurrentSlideStatus('active')
      } finally {
        setIsVersionLoading(false)
      }
    }

    loadVersionHistory()
  }, [enableVersioning, sessionId, documentId, currentIndex, pages.length])

  useEffect(() => {
    if (pages.length > 0 && currentIndex >= pages.length) {
      setCurrentIndex(0)
    }
  }, [pages.length, currentIndex])

  const convertToEnhanced = useCallback((page: PptPageData | EnhancedPptPageData, pageIndex: number): EnhancedPptPageData => {
    const maybeEnhanced = page as EnhancedPptPageData
    const hasRealShapes = maybeEnhanced.shapes && maybeEnhanced.shapes.length > 0 && maybeEnhanced.shapes[0]?.text_content

    if (hasRealShapes) {
      if (!maybeEnhanced.layout) maybeEnhanced.layout = { width: 960, height: 540 }
      return maybeEnhanced
    }

    const shapes: any[] = []
    const content = page.content as string[]
    if (content && content.length > 0) {
      shapes.push({
        type: 'text_box',
        name: `content-${pageIndex}`,
        position: { x: 50, y: 80, width: 860, height: 400 },
        text_content: content.map((text: string) => ({ runs: [{ text, font: { size: 18, color: '000000' } }] }))
      })
    }

    return { index: page.index, title: page.title, content: content.map((text: string) => ({ type: 'text' as const, text })), shapes, layout: { width: 960, height: 540 } }
  }, [])

  const goToPage = useCallback((index: number) => {
    if (index >= 0 && index < pages.length) {
      setCurrentIndex(index)
      onPageChangeExternal?.(index)
    }
  }, [pages.length, onPageChangeExternal])

  const goPrev = useCallback(() => goToPage(currentIndex - 1), [currentIndex, goToPage])
  const goNext = useCallback(() => goToPage(currentIndex + 1), [currentIndex, goToPage])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!containerRef.current?.contains(document.activeElement)) return
      if (e.key === 'ArrowLeft') { e.preventDefault(); goPrev() }
      else if (e.key === 'ArrowRight') { e.preventDefault(); goNext() }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [goPrev, goNext])

  useEffect(() => {
    if (thumbnailStripRef.current) {
      const thumbEl = thumbnailStripRef.current.children[currentIndex] as HTMLElement
      if (thumbEl) thumbEl.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
    }
  }, [currentIndex])

  const togglePageSelection = useCallback((pageIndex: number, e?: React.MouseEvent) => {
    if (disableSelection || !onSelectionChange) return
    if (e?.ctrlKey || e?.metaKey) {
      onSelectionChange(selectedPages.includes(pageIndex) ? selectedPages.filter(p => p !== pageIndex) : [...selectedPages, pageIndex])
    } else if (e?.shiftKey && selectedPages.length > 0) {
      const lastSelected = selectedPages[selectedPages.length - 1]
      const start = Math.min(lastSelected, pageIndex), end = Math.max(lastSelected, pageIndex)
      const range: number[] = []
      for (let i = start; i <= end; i++) if (!selectedPages.includes(i)) range.push(i)
      onSelectionChange([...selectedPages, ...range])
    } else {
      onSelectionChange(selectedPages.includes(pageIndex) && selectedPages.length === 1 ? [] : [pageIndex])
    }
  }, [disableSelection, onSelectionChange, selectedPages])

  // feat-141: 版本切换函数
  const handleSwitchVersion = useCallback(async (direction: 'prev' | 'next') => {
    if (!sessionId || !documentId || !currentSlideVersion) return
    const currentNum = parseInt(currentSlideVersion.slice(1))
    const targetNum = direction === 'prev' ? currentNum - 1 : currentNum + 1
    if (targetNum < 1 || targetNum > versionHistory.length) return

    try {
      await restoreVersion({ session_id: sessionId, document_id: documentId, slide_index: currentIndex, target_version: `v${targetNum}` })
      setCurrentSlideVersion(`v${targetNum}`)
      setCurrentSlideStatus('active')
    } catch (err) {
      console.error('切换版本失败:', err)
      onRenderError?.(new Error(`切换版本失败：${err}`))
    }
  }, [sessionId, documentId, currentSlideVersion, versionHistory.length, currentIndex, onRenderError])

  const handleOpenHistory = useCallback(() => setIsHistoryPanelOpen(true), [])
  const handleCloseHistory = useCallback(() => setIsHistoryPanelOpen(false), [])

  const handleSelectVersion = useCallback(async (version: string) => {
    if (!sessionId || !documentId) return
    try {
      await restoreVersion({ session_id: sessionId, document_id: documentId, slide_index: currentIndex, target_version: version })
      setCurrentSlideVersion(version)
      setCurrentSlideStatus('active')
      setIsHistoryPanelOpen(false)
    } catch (err) {
      console.error('恢复版本失败:', err)
      onRenderError?.(new Error(`恢复版本失败：${err}`))
    }
  }, [sessionId, documentId, currentIndex, onRenderError])

  const handleToggleSlide = useCallback(async () => {
    if (!sessionId || !documentId) return
    const action = currentSlideStatus === 'deleted' ? 'restore' : 'delete'
    try {
      await toggleSlide({ session_id: sessionId, document_id: documentId, slide_index: currentIndex, action })
      setCurrentSlideStatus(action === 'delete' ? 'deleted' : 'active')
      if (action === 'delete') setCurrentSlideVersion(null)
      setIsHistoryPanelOpen(false)
    } catch (err) {
      console.error('切换页面状态失败:', err)
      onRenderError?.(new Error(`切换页面状态失败：${err}`))
    }
  }, [sessionId, documentId, currentIndex, currentSlideStatus, onRenderError])

  const currentPage = pages[currentIndex]
  const isCurrentSelected = currentPage ? selectedPages.includes(currentPage.index) : false

  if (isLoading) {
    return (
      <div className="border rounded-lg p-6 bg-white" ref={containerRef}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">{label}</h3>
        </div>
        <div className="text-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-500 text-sm">正在加载 PPT 预览...</p>
        </div>
      </div>
    )
  }

  if (pages.length === 0) {
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

  const enhancedCurrentPage = currentPage ? convertToEnhanced(currentPage, currentPage.index) : null

  // feat-150: 获取当前页的图片 URL
  const currentImageUrl = slideImageUrls[currentIndex]

  return (
    <div className="border rounded-lg bg-white overflow-hidden" ref={containerRef} tabIndex={0} onFocus={() => {}}>
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
        <h3 className="text-sm font-medium text-gray-900">{label}</h3>
        <div className="flex items-center gap-3">
          {enableVersioning && sessionId && documentId && (
            <VersionSwitcher
              currentVersion={currentSlideVersion}
              totalVersions={versionHistory.length}
              slideStatus={currentSlideStatus}
              onSwitchVersion={handleSwitchVersion}
              onOpenHistory={handleOpenHistory}
              disabled={isVersionLoading || isFallbackMode}
            />
          )}
          {selectedPages.length > 0 && <span className="text-xs text-indigo-600 font-medium">已选 {selectedPages.length} 页</span>}
          <span className="text-xs text-gray-500">共 {pages.length} 页</span>
          {/* feat-150: 显示预览模式标识 */}
          {currentImageUrl && <span className="text-xs text-green-600 font-medium">📷 图片预览</span>}
        </div>
      </div>

      {isFallbackMode && (
        <div className="mx-4 mt-3 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
          Canvas 渲染不可用，已切换到简化模式
        </div>
      )}

      {/* 主预览区 */}
      <div className="relative group">
        <div
          className={cn(
            "mx-4 mt-3 rounded-lg overflow-hidden border-2 transition-all cursor-pointer",
            isCurrentSelected ? "border-indigo-500 ring-2 ring-indigo-200 shadow-lg" : "border-gray-200 hover:border-gray-300"
          )}
          onClick={(e) => currentPage && togglePageSelection(currentPage.index, e)}
        >
          {/* feat-150: 优先显示图片，无图片时降级到 Canvas */}
          {currentImageUrl ? (
            <img
              src={currentImageUrl}
              alt={`第 ${currentIndex + 1} 页`}
              className="w-full h-auto object-contain"
              style={{ maxHeight: '450px' }}
              onError={(e) => {
                // 图片加载失败时降级到 Canvas
                console.warn('图片加载失败，降级到 Canvas 渲染')
                setSlideImageUrls(prev => {
                  const next = { ...prev }
                  delete next[currentIndex]
                  return next
                })
              }}
            />
          ) : enhancedCurrentPage ? (
            <PptCanvasRenderer pageData={enhancedCurrentPage} width={800} height={450} isSelected={isCurrentSelected} onClick={() => {}} quality={1.0} />
          ) : null}
          {isCurrentSelected && (
            <div className="absolute top-6 right-6 w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center shadow-md">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
          )}
        </div>

        <button onClick={(e) => { e.stopPropagation(); goPrev() }} disabled={currentIndex === 0}
          className={cn("absolute left-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all z-10", currentIndex === 0 ? "bg-gray-200/50 text-gray-400 cursor-not-allowed" : "bg-white/90 text-gray-700 shadow-md hover:bg-white hover:shadow-lg")}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        </button>

        <button onClick={(e) => { e.stopPropagation(); goNext() }} disabled={currentIndex === pages.length - 1}
          className={cn("absolute right-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all z-10", currentIndex === pages.length - 1 ? "bg-gray-200/50 text-gray-400 cursor-not-allowed" : "bg-white/90 text-gray-700 shadow-md hover:bg-white hover:shadow-lg")}>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>

      {/* 页码控制栏 */}
      <div className="flex items-center justify-center gap-4 px-4 py-2">
        <span className="text-sm text-gray-600 font-medium">第 {currentIndex + 1} 页 / 共 {pages.length} 页</span>
        {!disableSelection && currentPage && (
          <button onClick={() => currentPage && togglePageSelection(currentPage.index)}
            className={cn("px-3 py-1 rounded-full text-xs font-medium transition-colors", isCurrentSelected ? "bg-indigo-100 text-indigo-700 hover:bg-indigo-200" : "bg-gray-100 text-gray-600 hover:bg-gray-200")}>
            {isCurrentSelected ? '取消选择' : '选择此页'}
          </button>
        )}
      </div>

      {/* 底部缩略图条 */}
      <div className="border-t bg-gray-50 px-2 py-2">
        <div ref={thumbnailStripRef} className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin" style={{ scrollbarWidth: 'thin' }}>
          {pages.map((page, idx) => {
            const isActive = idx === currentIndex
            const isSelected = selectedPages.includes(page.index)
            const thumbnailUrl = slideImageUrls[idx]  // feat-150: 获取缩略图 URL
            const enhanced = convertToEnhanced(page, page.index)
            return (
              <div key={page.index} onClick={() => goToPage(idx)}
                className={cn("flex-shrink-0 w-24 h-14 rounded border-2 overflow-hidden cursor-pointer transition-all relative", isActive ? "border-indigo-500 ring-1 ring-indigo-300 shadow" : isSelected ? "border-green-400 ring-1 ring-green-200" : "border-gray-200 hover:border-gray-400 opacity-70 hover:opacity-100")}>
                {/* feat-150: 优先显示图片缩略图 */}
                {thumbnailUrl ? (
                  <img
                    src={thumbnailUrl}
                    alt={`第 ${idx + 1} 页`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <PptCanvasRenderer pageData={enhanced} width={96} height={54} isSelected={false} onClick={() => {}} quality={0.5} />
                )}
                <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-center text-[9px] py-0.5">P{page.index + 1}</div>
                {isSelected && (
                  <div className="absolute top-0.5 right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full flex items-center justify-center">
                    <svg className="w-2 h-2 text-white" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {selectedPages.length > 0 && (
        <div className="px-4 py-2 border-t text-xs text-indigo-600 bg-indigo-50/50">
          已选择：{selectedPages.sort((a, b) => a - b).map(p => `P${p + 1}`).join(", ")}
        </div>
      )}

      {/* feat-141: 版本历史面板 */}
      {enableVersioning && sessionId && documentId && (
        <VersionHistoryPanel
          currentVersion={currentSlideVersion}
          versions={versionHistory}
          slideStatus={currentSlideStatus}
          pageLabel={`${label} - 第 ${currentIndex + 1} 页`}
          open={isHistoryPanelOpen}
          onClose={handleCloseHistory}
          onSelectVersion={handleSelectVersion}
          onToggleSlide={handleToggleSlide}
          isLoading={isVersionLoading}
        />
      )}
    </div>
  )
}

export default PptCanvasPreview
