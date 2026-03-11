"use client"

import * as React from "react"

/**
 * PptxViewJS Canvas 渲染器组件（feat-171）
 * 使用 PptxViewJS 库渲染 PPTX 文件
 */

interface PptxViewJSRendererProps {
  file?: File | null
  slideIndex: number
  width?: number
  height?: number
  isSelected?: boolean
  onClick?: () => void
  quality?: 'low' | 'medium' | 'high'
  onError?: (error: Error) => void
  onLoad?: (slideCount: number) => void
  enableThumbnails?: boolean
  scale?: number
}

// 全局加载状态
type LibState = 'idle' | 'loading' | 'ready' | 'error'
let libState: LibState = 'idle'
let PPTXViewerClass: any = null
const loadCallbacks: Array<(success: boolean) => void> = []

function loadLibrary(): Promise<boolean> {
  return new Promise((resolve) => {
    if (libState === 'ready' && PPTXViewerClass) {
      resolve(true)
      return
    }

    if (libState === 'loading') {
      loadCallbacks.push(resolve)
      return
    }

    libState = 'loading'

    const loadScript = (src: string): Promise<void> => {
      return new Promise((res, rej) => {
        const script = document.createElement('script')
        script.src = src
        script.async = true
        script.onload = () => res()
        script.onerror = () => rej(new Error(`Failed to load ${src}`))
        document.head.appendChild(script)
      })
    }

    // 顺序加载依赖
    loadScript('/js/jszip.min.js')
      .then(() => loadScript('/js/chart.umd.min.js'))
      .then(() => loadScript('/js/PptxViewJS.min.js'))
      .then(() => {
        const win = window as any
        if (win.PptxViewJS?.PPTXViewer) {
          PPTXViewerClass = win.PptxViewJS.PPTXViewer
          libState = 'ready'
          console.log('[PptxViewJS] 库加载成功')
          resolve(true)
          loadCallbacks.forEach(cb => cb(true))
          loadCallbacks.length = 0
        } else {
          throw new Error('PptxViewJS.PPTXViewer not found')
        }
      })
      .catch((err) => {
        console.error('[PptxViewJS] 库加载失败:', err)
        libState = 'error'
        resolve(false)
        loadCallbacks.forEach(cb => cb(false))
        loadCallbacks.length = 0
      })
  })
}

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
  const [libReady, setLibReady] = React.useState(libState === 'ready')
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [slideCount, setSlideCount] = React.useState(0)
  const [error, setError] = React.useState<Error | null>(null)
  const [isRendering, setIsRendering] = React.useState(false)

  // 加载库
  React.useEffect(() => {
    if (typeof window === 'undefined') return

    loadLibrary().then(success => {
      if (success) {
        setLibReady(true)
      } else {
        setError(new Error('pptxviewjs 加载失败'))
      }
    })
  }, [])

  // 初始化 viewer
  React.useEffect(() => {
    if (!file || !canvasRef.current || !libReady || !PPTXViewerClass) return

    let destroyed = false
    const canvas = canvasRef.current

    setIsLoaded(false)
    setSlideCount(0)
    setError(null)

    const viewer = new PPTXViewerClass({
      canvas,
      debug: true,
      enableThumbnails,
      slideSizeMode: scale ? 'custom' : 'fit',
      backgroundColor: '#ffffff',
    })
    viewerRef.current = viewer

    const handleLoadComplete = (data: any) => {
      if (destroyed) return
      const count = typeof data === 'number' ? data : (data?.slideCount || 0)
      setSlideCount(count)
      setIsLoaded(true)
      onLoad?.(count)
    }

    const handleError = (err: any) => {
      if (destroyed) return
      const e = err instanceof Error ? err : new Error(String(err))
      setError(e)
      onError?.(e)
    }

    viewer.on('loadComplete', handleLoadComplete)
    viewer.on('error', handleError)
    viewer.loadFile(file).catch(handleError)

    return () => {
      destroyed = true
      viewer.off('loadComplete', handleLoadComplete)
      viewer.off('error', handleError)
      viewer.destroy()
      viewerRef.current = null
    }
  }, [file, libReady])

  // 渲染页面
  React.useEffect(() => {
    if (!viewerRef.current || !isLoaded || !canvasRef.current) return

    setIsRendering(true)
    viewerRef.current
      .renderSlide(slideIndex, canvasRef.current, { quality, scale })
      .catch((err: any) => setError(err instanceof Error ? err : new Error('渲染失败')))
      .finally(() => setIsRendering(false))
  }, [slideIndex, isLoaded, quality, scale])

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

      {!isLoaded && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {isLoaded && isRendering && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/50 rounded-lg">
          <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

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

      {isLoaded && (
        <div className="absolute bottom-1 left-1 bg-black/50 text-white text-[9px] px-1.5 py-0.5 rounded">
          P{slideIndex + 1}/{slideCount}
        </div>
      )}
    </div>
  )
}

export default PptxViewJSRenderer