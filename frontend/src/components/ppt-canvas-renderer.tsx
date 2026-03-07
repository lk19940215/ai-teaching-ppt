"use client"

import * as React from "react"

// 离屏 Canvas 缓存池（LRU 缓存，feat-088 性能优化）
const MAX_CACHE_SIZE = 20 // 最多缓存 20 个页面
const canvasCache = new Map<string, HTMLCanvasElement>()
const cacheAccessOrder: string[] = [] // 访问顺序队列

/**
 * LRU 缓存：获取缓存的 Canvas
 */
function getCachedCanvas(key: string): HTMLCanvasElement | null {
  const cached = canvasCache.get(key)
  if (cached) {
    // 更新访问顺序
    const idx = cacheAccessOrder.indexOf(key)
    if (idx > -1) {
      cacheAccessOrder.splice(idx, 1)
    }
    cacheAccessOrder.push(key)
    return cached
  }
  return null
}

/**
 * LRU 缓存：设置缓存
 */
function setCachedCanvas(key: string, canvas: HTMLCanvasElement) {
  // 如果已存在，先移除旧顺序
  const idx = cacheAccessOrder.indexOf(key)
  if (idx > -1) {
    cacheAccessOrder.splice(idx, 1)
  }

  // 添加新缓存
  cacheAccessOrder.push(key)
  canvasCache.set(key, canvas)

  // 如果超过缓存上限，移除最旧的
  if (canvasCache.size > MAX_CACHE_SIZE) {
    const oldestKey = cacheAccessOrder.shift()
    if (oldestKey) {
      canvasCache.delete(oldestKey)
    }
  }
}

/**
 * 清除缓存（用于内存清理）
 */
export function clearCanvasCache() {
  canvasCache.clear()
  cacheAccessOrder.length = 0
}

// 增强的 PPT 页面数据结构（与后端 parse-enhanced 返回结构对应）
export interface EnhancedPptPageData {
  index: number
  title: string
  content: Array<{
    type: 'text' | 'image' | 'table'
    text?: string
    image_base64?: string
    table_data?: string[][]
    font?: {
      name?: string
      size?: number
      color?: string
      bold?: boolean
      italic?: boolean
    }
    position?: {
      x: number
      y: number
      width: number
      height: number
    }
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
    position_relative?: {
      x: number
      y: number
      width: number
      height: number
    }
    image_base64?: string
    table_data?: string[][]
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

// Canvas 渲染器配置
interface PptCanvasRendererProps {
  // 增强的页面数据
  pageData: EnhancedPptPageData
  // 画布宽度（像素）
  width?: number
  // 画布高度（像素）
  height?: number
  // 是否选中状态
  isSelected?: boolean
  // 点击回调
  onClick?: () => void
  // 渲染质量（1.0 = 高质量，0.5 = 低质量）
  quality?: number
}

/**
 * PPT Canvas 渲染器组件（feat-083）
 *
 * 功能：
 * - 使用 Canvas 真实渲染 PPT 页面内容
 * - 支持文本、图片、表格、形状的渲染
 * - 支持文本样式（字体、颜色、大小、粗体、斜体）
 * - 支持选中状态高亮
 * - 性能优化：离屏缓存
 */
export function PptCanvasRenderer({
  pageData,
  width = 300,
  height = 169,
  isSelected = false,
  onClick,
  quality = 1.0,
}: PptCanvasRendererProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const containerRef = React.useRef<HTMLDivElement>(null)
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [isInCache, setIsInCache] = React.useState(false)
  const [isVisible, setIsVisible] = React.useState(false)

  // 计算缩放比例（添加默认 layout 防止出错）
  const layout = pageData.layout || { width: 960, height: 540 }
  const scale = Math.min(width / layout.width, height / layout.height) * quality

  // 生成缓存键
  const cacheKey = `page-${pageData.index}-w${width}-h${height}-q${quality}`

  // IntersectionObserver：图片懒加载（feat-088）
  React.useEffect(() => {
    if (!containerRef.current) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '200px', // 提前 200px 开始加载
        threshold: 0.01
      }
    )

    observer.observe(containerRef.current)

    return () => observer.disconnect()
  }, [])

  // 渲染单个文本运行
  const renderTextRun = (
    ctx: CanvasRenderingContext2D,
    run: {
      text: string
      font: {
        name?: string
        size?: number
        color?: string
        bold?: boolean
        italic?: boolean
        underline?: boolean
      }
    },
    x: number,
    y: number,
    maxWidth: number
  ) => {
    // 设置字体
    const fontSize = (run.font.size || 18) * scale
    const fontFamily = run.font.name || 'Microsoft YaHei, sans-serif'
    const fontWeight = run.font.bold ? 'bold' : 'normal'
    const fontStyle = run.font.italic ? 'italic' : 'normal'

    ctx.font = `${fontStyle} ${fontWeight} ${fontSize}px ${fontFamily}`
    ctx.fillStyle = run.font.color || '#000000'

    // 绘制文本
    ctx.fillText(run.text, x, y, maxWidth)

    // 绘制下划线
    if (run.font.underline) {
      const textWidth = ctx.measureText(run.text).width
      ctx.strokeStyle = run.font.color || '#000000'
      ctx.lineWidth = fontSize * 0.05
      ctx.beginPath()
      ctx.moveTo(x, y + fontSize * 0.1)
      ctx.lineTo(x + textWidth, y + fontSize * 0.1)
      ctx.stroke()
    }
  }

  // 渲染文本框
  const renderTextShape = (
    ctx: CanvasRenderingContext2D,
    shape: any,
    offsetX: number,
    offsetY: number
  ) => {
    if (!shape.text_content || shape.text_content.length === 0) return

    const x = shape.position.x * scale + offsetX
    const y = shape.position.y * scale + offsetY
    const maxWidth = (shape.position.width || layout.width) * scale

    let currentY = y + 20 * scale // 初始Y位置，留出顶部边距

    for (const paragraph of shape.text_content) {
      let currentX = x

      // 段落对齐
      if (paragraph.alignment && paragraph.alignment.includes('CENTER')) {
        currentX = x + maxWidth / 2
        ctx.textAlign = 'center'
      } else if (paragraph.alignment && paragraph.alignment.includes('RIGHT')) {
        currentX = x + maxWidth
        ctx.textAlign = 'right'
      } else {
        ctx.textAlign = 'left'
      }

      // 渲染段落中的所有运行
      for (const run of paragraph.runs) {
        renderTextRun(ctx, run, currentX, currentY, maxWidth)

        // 更新 X 位置（连续渲染）
        const textWidth = ctx.measureText(run.text).width
        currentX += textWidth
      }

      // 换行
      const lineHeight = 24 * scale
      currentY += lineHeight

      // 重置对齐
      ctx.textAlign = 'left'
    }
  }

  // 渲染图片（懒加载版本）
  const renderImageShape = (
    ctx: CanvasRenderingContext2D,
    shape: any,
    offsetX: number,
    offsetY: number
  ) => {
    if (!shape.image_base64) return

    // 懒加载：不可见时不加载图片
    if (!isVisible) return

    const x = shape.position.x * scale + offsetX
    const y = shape.position.y * scale + offsetY
    const w = shape.position.width * scale
    const h = shape.position.height * scale

    const img = new Image()
    img.onload = () => {
      ctx.drawImage(img, x, y, w, h)
      // 图片加载完成后重新渲染整个 Canvas（可选）
      setIsLoaded(true)
    }
    img.src = shape.image_base64
  }

  // 渲染表格
  const renderTableShape = (
    ctx: CanvasRenderingContext2D,
    shape: any,
    offsetX: number,
    offsetY: number
  ) => {
    if (!shape.table_data || shape.table_data.length === 0) return

    const x = shape.position.x * scale + offsetX
    const y = shape.position.y * scale + offsetY
    const w = shape.position.width * scale
    const h = shape.position.height * scale

    const rows = shape.table_data.length
    const cols = shape.table_data[0]?.length || 1
    const cellWidth = w / cols
    const cellHeight = h / rows

    // 绘制表格边框和单元格
    ctx.strokeStyle = '#000000'
    ctx.lineWidth = 1 * scale

    // 绘制表格外框
    ctx.strokeRect(x, y, w, h)

    // 绘制行和列
    for (let i = 1; i < rows; i++) {
      const rowY = y + i * cellHeight
      ctx.beginPath()
      ctx.moveTo(x, rowY)
      ctx.lineTo(x + w, rowY)
      ctx.stroke()
    }

    for (let j = 1; j < cols; j++) {
      const colX = x + j * cellWidth
      ctx.beginPath()
      ctx.moveTo(colX, y)
      ctx.lineTo(colX, y + h)
      ctx.stroke()
    }

    // 绘制单元格内容
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.font = `${12 * scale}px Microsoft YaHei, sans-serif`
    ctx.fillStyle = '#000000'

    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        const cellText = shape.table_data[i]?.[j] || ''
        const cellX = x + j * cellWidth + cellWidth / 2
        const cellY = y + i * cellHeight + cellHeight / 2

        if (cellText) {
          ctx.fillText(cellText, cellX, cellY, cellWidth - 8 * scale)
        }
      }
    }
  }

  // 渲染形状（矩形、圆形等）
  const renderAutoShape = (
    ctx: CanvasRenderingContext2D,
    shape: any,
    offsetX: number,
    offsetY: number
  ) => {
    const x = shape.position.x * scale + offsetX
    const y = shape.position.y * scale + offsetY
    const w = shape.position.width * scale
    const h = shape.position.height * scale

    // 填充背景
    ctx.fillStyle = '#f0f0f0'
    ctx.fillRect(x, y, w, h)

    // 绘制边框
    ctx.strokeStyle = '#cccccc'
    ctx.lineWidth = 1 * scale
    ctx.strokeRect(x, y, w, h)
  }

  // 绘制选中边框
  const drawSelectionBorder = (
    ctx: CanvasRenderingContext2D,
    canvasWidth: number,
    canvasHeight: number
  ) => {
    const padding = 4 * quality
    ctx.strokeStyle = '#6366f1' // indigo-500
    ctx.lineWidth = 2 * quality
    ctx.setLineDash([4 * quality, 2 * quality])
    ctx.strokeRect(padding, padding, canvasWidth - padding * 2, canvasHeight - padding * 2)
    ctx.setLineDash([])
  }

  // 渲染页面到 Canvas
  const renderToCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 检查缓存
    const cachedCanvas = getCachedCanvas(cacheKey)
    if (cachedCanvas) {
      // 使用缓存渲染
      ctx.drawImage(cachedCanvas, 0, 0)
      setIsInCache(true)
      setIsLoaded(true)

      // 绘制选中边框（如果需要）
      if (isSelected) {
        drawSelectionBorder(ctx, width, height)
      }
      return
    }

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 计算偏移（居中）
    const offsetX = (width - layout.width * scale) / 2
    const offsetY = (height - layout.height * scale) / 2

    // 绘制白色背景
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    // 不可见时只绘制背景和占位符
    if (!isVisible) {
      // 绘制占位符文本
      ctx.fillStyle = '#999999'
      ctx.font = '14px Microsoft YaHei, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('加载中...', width / 2, height / 2)
      return
    }

    // 按顺序渲染所有形状
    for (const shape of pageData.shapes || []) {
      try {
        const shapeType = shape.type?.toLowerCase() || ''
        if (shapeType.includes('text') || shapeType.includes('placeholder')) {
          renderTextShape(ctx, shape, offsetX, offsetY)
        } else if (shapeType.includes('picture') || shapeType.includes('image')) {
          renderImageShape(ctx, shape, offsetX, offsetY)
        } else if (shapeType.includes('table')) {
          renderTableShape(ctx, shape, offsetX, offsetY)
        } else if (shapeType.includes('auto_shape') || shapeType.includes('rect') || shapeType.includes('shape')) {
          renderAutoShape(ctx, shape, offsetX, offsetY)
        }
      } catch (error) {
        console.warn('渲染形状失败:', error)
      }
    }

    // 绘制选中边框
    if (isSelected) {
      drawSelectionBorder(ctx, width, height)
    }

    // 保存到缓存（创建离屏 Canvas）
    const offscreen = document.createElement('canvas')
    offscreen.width = width
    offscreen.height = height
    const offscreenCtx = offscreen.getContext('2d')
    if (offscreenCtx) {
      offscreenCtx.drawImage(canvas, 0, 0)
      setCachedCanvas(cacheKey, offscreen)
    }

    setIsInCache(false)
    setIsLoaded(true)
  }

  // 组件挂载和更新时渲染
  React.useEffect(() => {
    renderToCanvas()
  }, [pageData, width, height, isSelected, quality, isVisible])

  // 组件卸载时可选清理（不需要，LRU 会自动管理）

  return (
    <div
      ref={containerRef}
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

      {/* 加载状态（仅在无缓存时显示） */}
      {!isLoaded && !isInCache && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {/* 页码标签 */}
      <div className="absolute bottom-1 left-1 bg-black/50 text-white text-[9px] px-1.5 py-0.5 rounded">
        P{pageData.index + 1}
      </div>

      {/* 缓存命中指示器（开发调试用，可移除） */}
      {isInCache && process.env.NODE_ENV === 'development' && (
        <div className="absolute top-1 right-1 bg-green-500 text-white text-[8px] px-1 py-0.5 rounded opacity-70">
          缓存
        </div>
      )}
    </div>
  )
}

export default PptCanvasRenderer
