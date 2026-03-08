"use client"

import * as React from "react"
import dynamic from 'next/dynamic'

// 动态导入 PPTXViewer，确保只在客户端加载
const PPTXViewerPromise = import('pptxviewjs').then(mod => mod.PPTXViewer)

/**
 * PptxViewJS Canvas 渲染器组件（feat-208）
 *
 * 功能：
 * - 使用 PptxViewJS 库渲染 PPTX 文件
 * - Canvas 原生渲染（比手动解析更真实）
 * - 内置翻页 API（previousSlide, nextSlide, goToSlide）
 * - 支持缩放和质量控制
 * - 支持缩略图模式
 */

// 渲染器配置
interface PptxViewJSRendererProps {
  // PPTX 文件（用于前端解析）
  file?: File | null
  // 当前渲染的页面索引
  slideIndex: number
  // 画布宽度
  width?: number
  // 画布高度
  height?: number
  // 是否选中状态
  isSelected?: boolean
  // 点击回调
  onClick?: () => void
  // 渲染质量
  quality?: 'low' | 'medium' | 'high'
  // 渲染失败回调
  onError?: (error: Error) => void
  // 加载完成回调
  onLoad?: (slideCount: number) => void
  // 是否启用缩略图模式
  enableThumbnails?: boolean
  // 缩放比例
  scale?: number
}

/**
 * PptxViewJS 渲染器组件
 */
export function PptxViewJSRenderer({
  file,
  slideIndex = 0,
  width = 300,
  height = 169,
  isSelected = false,
  onClick,
  quality = 'high',
  onError,
  onLoad,
  enableThumbnails = false,
  scale,
}: PptxViewJSRendererProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const viewerRef = React.useRef<any>(null)
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [slideCount, setSlideCount] = React.useState(0)
  const [error, setError] = React.useState<Error | null>(null)
  const [isRendering, setIsRendering] = React.useState(false)
  const [PPTXViewer, setPPTXViewer] = React.useState<any>(null)

  // 加载 PPTXViewer 库（仅客户端）
  React.useEffect(() => {
    if (typeof window === 'undefined') return
    PPTXViewerPromise.then(mod => setPPTXViewer(() => mod))
  }, [])

  // 初始化 PPTXViewer
  React.useEffect(() => {
    if (!file || !canvasRef.current || !PPTXViewer) return

    let destroyed = false
    const canvas = canvasRef.current

    // 创建 PPTXViewer 实例
    const options: any = {
      canvas,
      debug: process.env.NODE_ENV === 'development',
      enableThumbnails,
      slideSizeMode: scale ? 'custom' : 'fit',
      backgroundColor: '#ffffff',
    }

    const viewer = new PPTXViewer(options)
    viewerRef.current = viewer

    // 事件监听
    const handleLoaded = () => {
      if (destroyed) return
      const count = viewer.getSlideCount()
      setSlideCount(count)
      setIsLoaded(true)
      onLoad?.(count)
      console.log(`[PptxViewJS] 加载完成，共 ${count} 页`)
    }

    const handleError = (...args: unknown[]) => {
      if (destroyed) return
      const err = args[0] instanceof Error ? args[0] : new Error(String(args[0]))
      console.error('[PptxViewJS] 加载失败:', err)
      setError(err)
      onError?.(err)
      setIsLoaded(true)
    }

    viewer.on('loaded', handleLoaded)
    viewer.on('error', handleError)

    // 加载文件
    const loadPptx = async () => {
      try {
        setIsRendering(true)
        await viewer.loadFile(file)
        await viewer.renderSlide(slideIndex, canvas, { quality, scale })
        setIsRendering(false)
      } catch (err) {
        handleError(err instanceof Error ? err : new Error('加载失败'))
        setIsRendering(false)
      }
    }

    loadPptx()

    // 清理
    return () => {
      destroyed = true
      viewer.off('loaded', handleLoaded)
      viewer.off('error', handleError)
      viewer.destroy()
      viewerRef.current = null
    }
  }, [file]) // 仅当文件变化时重新初始化

  // 切换页面时渲染
  React.useEffect(() => {
    if (!viewerRef.current || !isLoaded || !canvasRef.current) return

    const renderSlide = async () => {
      try {
        setIsRendering(true)
        const viewer = viewerRef.current!
        const canvas = canvasRef.current!

        // 使用 goToSlide 跳转到指定页面
        await viewer.goToSlide(slideIndex, canvas)
        await viewer.render(canvas, { quality, scale })
        setIsRendering(false)
      } catch (err) {
        console.error('[PptxViewJS] 渲染失败:', err)
        setError(err instanceof Error ? err : new Error('渲染失败'))
        onError?.(err instanceof Error ? err : new Error('渲染失败'))
        setIsRendering(false)
      }
    }

    renderSlide()
  }, [slideIndex, isLoaded, quality, scale])

  // 获取当前渲染的 Canvas
  const currentCanvas = viewerRef.current ? null : canvasRef.current

  return (
    <div
      className="relative"
      style={{ width: `${width}px`, height: `${height}px` }}
      onClick={onClick}
    >
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className={`w-full h-full rounded-lg transition-all duration-200 ${
          onClick ? 'cursor-pointer hover:shadow-md' : ''
        } ${isSelected ? 'ring-2 ring-indigo-500' : ''}`}
      />

      {/* 加载状态 */}
      {!isLoaded && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {/* 渲染中状态 */}
      {isLoaded && isRendering && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/50 rounded-lg">
          <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {/* 错误状态 */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-50 rounded-lg">
          <div className="text-center p-2">
            <svg className="w-6 h-6 text-red-500 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-xs text-red-600">渲染失败</p>
          </div>
        </div>
      )}

      {/* 页码标签 */}
      {isLoaded && (
        <div className="absolute bottom-1 left-1 bg-black/50 text-white text-[9px] px-1.5 py-0.5 rounded">
          P{slideIndex + 1}/{slideCount}
        </div>
      )}
    </div>
  )
}

export default PptxViewJSRenderer
