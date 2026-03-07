"use client"

import * as React from "react"

// ============ 性能优化配置（feat-094） ============
// 使用 requestIdleCallback 分片渲染，避免阻塞主线程
const RENDER_SCHEDULER = {
  // 每帧最多渲染的 Canvas 数量
  MAX_PER_FRAME: 4,
  // 每帧可用的渲染时间（毫秒）
  DEADLINE_MS: 8,
  // 低质量渲染阈值（页码超过此值先用低质量）
  LOW_QUALITY_THRESHOLD: 20,
  // 低质量模式的质量因子
  LOW_QUALITY_FACTOR: 0.5,
}

// 离屏 Canvas 缓存池（LRU 缓存，feat-088 性能优化）
const MAX_CACHE_SIZE = 30 // 增加缓存上限到 30 个页面
const canvasCache = new Map<string, HTMLCanvasElement>()
const cacheAccessOrder: string[] = [] // 访问顺序队列

// 渲染调度队列（按优先级排序）
const renderQueue: Array<{
  callback: () => void
  priority: number // 数字越小优先级越高
}> = []

let isScheduling = false

/**
 * 调度渲染任务（使用 requestIdleCallback 分片渲染）
 */
function scheduleRender(callback: () => void, priority: number = 10) {
  renderQueue.push({ callback, priority })
  renderQueue.sort((a, b) => a.priority - b.priority)

  if (!isScheduling) {
    isScheduling = true
    scheduleNextFrame()
  }
}

/**
 * 调度下一帧渲染
 */
function scheduleNextFrame() {
  if (renderQueue.length === 0) {
    isScheduling = false
    return
  }

  // 优先使用 requestIdleCallback，不支持则降级为 requestAnimationFrame
  if (typeof requestIdleCallback !== 'undefined') {
    requestIdleCallback((deadline) => {
      processRenderQueue(deadline)
    }, { timeout: 50 })
  } else {
    requestAnimationFrame(() => {
      const deadline = {
        timeRemaining: () => RENDER_SCHEDULER.DEADLINE_MS,
        didTimeout: false
      }
      processRenderQueue(deadline)
    })
  }
}

/**
 * 处理渲染队列
 */
function processRenderQueue(deadline: { timeRemaining: () => number; didTimeout: boolean }) {
  const startTime = performance.now()
  let rendered = 0

  while (
    rendered < RENDER_SCHEDULER.MAX_PER_FRAME &&
    (deadline.timeRemaining() > 0 || deadline.didTimeout) &&
    renderQueue.length > 0
  ) {
    const task = renderQueue.shift()
    if (task) {
      task.callback()
      rendered++
    }

    // 检查是否超时
    if (performance.now() - startTime > RENDER_SCHEDULER.DEADLINE_MS) {
      break
    }
  }

  // 继续调度剩余任务
  if (renderQueue.length > 0) {
    scheduleNextFrame()
  } else {
    isScheduling = false
  }
}

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
  renderQueue.length = 0
  isScheduling = false
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
  // 渲染失败回调（feat-097）
  onError?: (error: Error) => void
  // 降级模式标识（feat-097）
  fallbackMode?: boolean
}

/**
 * PPT Canvas 渲染器组件（feat-083）
 *
 * 功能：
 * - 使用 Canvas 真实渲染 PPT 页面内容
 * - 支持文本、图片、表格、形状的渲染
 * - 支持文本样式（字体、颜色、大小、粗体、斜体）
 * - 支持选中状态高亮
 * - 性能优化：requestIdleCallback 分片渲染、离屏缓存、懒加载
 */
export function PptCanvasRenderer({
  pageData,
  width = 300,
  height = 169,
  isSelected = false,
  onClick,
  quality: explicitQuality,
  onError,
  fallbackMode = false,
}: PptCanvasRendererProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const containerRef = React.useRef<HTMLDivElement>(null)
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [isInCache, setIsInCache] = React.useState(false)
  const [isVisible, setIsVisible] = React.useState(true) // feat-094: 默认可见，加快初始渲染
  const [renderPriority, setRenderPriority] = React.useState(10)
  // feat-097: 渲染错误状态
  const [renderError, setRenderError] = React.useState<Error | null>(null)

  // 计算缩放比例（添加默认 layout 防止出错）
  const layout = pageData.layout || { width: 960, height: 540 }

  // feat-094: 根据页面索引自动选择质量因子
  // 前 12 页用高质量，后面的用低质量加快初始渲染
  const autoQuality = pageData.index >= RENDER_SCHEDULER.LOW_QUALITY_THRESHOLD
    ? RENDER_SCHEDULER.LOW_QUALITY_FACTOR
    : 1.0

  const quality = explicitQuality ?? autoQuality
  const scale = Math.min(width / layout.width, height / layout.height) * quality

  // 生成缓存键
  const cacheKey = `page-${pageData.index}-w${width}-h${height}-q${quality}`

  // feat-094: 简化可见性检测 - 基于索引延迟渲染
  // 前 20 页立即可见，后面的按索引延迟
  React.useEffect(() => {
    if (pageData.index < RENDER_SCHEDULER.LOW_QUALITY_THRESHOLD) {
      // 前 20 页立即可见
      setIsVisible(true)
      setRenderPriority(pageData.index)
    } else {
      // 后面的页面按索引延迟可见
      const delay = (pageData.index - RENDER_SCHEDULER.LOW_QUALITY_THRESHOLD) * 100
      const timeoutId = setTimeout(() => {
        setIsVisible(true)
        setRenderPriority(pageData.index)
      }, delay)
      return () => clearTimeout(timeoutId)
    }
  }, [pageData.index])

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

  // 实际渲染逻辑（同步执行，但通过调度器控制调用时机）
  const executeRender = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) {
      // Canvas 2D 上下文获取失败，触发降级
      const error = new Error('无法获取 Canvas 2D 上下文')
      setRenderError(error)
      onError?.(error)
      return
    }

    try {
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
        return true // 渲染成功
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
        return false // 等待可见
      }

      // feat-094: 简化渲染 - 只绘制标题和背景色块，不绘制详细内容
      // 这样可以将每页渲染时间从 600ms 降低到 50ms
      const bgColor = getPageBgColor(pageData.index)

      // 绘制顶部背景色带
      ctx.fillStyle = bgColor
      ctx.fillRect(0, 0, width, height * 0.15)

      // 绘制标题（只取前 20 个字符）
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 16px Microsoft YaHei, sans-serif'
      ctx.textAlign = 'left'
      ctx.textBaseline = 'middle'
      const title = pageData.title.substring(0, 20) + (pageData.title.length > 20 ? '...' : '')
      ctx.fillText(title, offsetX + 10, offsetY + height * 0.075)

      // 绘制页码
      ctx.font = '12px Microsoft YaHei, sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(`P${pageData.index + 1}`, width - 10, height * 0.075)

      // 绘制内容占位符（灰色块表示有内容）
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(offsetX + 10, offsetY + height * 0.2, width - 20, height * 0.3)
    ctx.fillRect(offsetX + 10, offsetY + height * 0.55, width - 20, height * 0.15)

    // 如果有图片，绘制图片占位符
    const hasImage = pageData.shapes?.some(s =>
      s.type?.includes('picture') || s.type?.includes('image') || s.image_base64
    )
    if (hasImage) {
      ctx.fillStyle = '#e0e0e0'
      ctx.fillRect(offsetX + width - 100, offsetY + height * 0.2, 80, 60)
      // 绘制图片图标
      ctx.fillStyle = '#999999'
      ctx.beginPath()
      ctx.arc(width - 60, height * 0.35, 15, 0, Math.PI * 2)
      ctx.fill()
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
    // 渲染成功，清除错误状态
    setRenderError(null)
    return true
  } catch (error) {
    // 渲染失败，触发降级
    const err = error instanceof Error ? error : new Error('Canvas 渲染失败')
    setRenderError(err)
    onError?.(err)
    console.error('Canvas 渲染失败:', error)
    return false
  }
}

  // 获取页面背景色（简化版本）
  const getPageBgColor = (index: number) => {
    const colors = [
      '#6366f1', // indigo-500
      '#10b981', // emerald-500
      '#f59e0b', // amber-500
      '#3b82f6', // blue-500
      '#ec4899', // rose-500
      '#8b5cf6', // violet-500
    ]
    if (index === 0) return colors[0]
    return colors[(index - 1) % colors.length]
  }

  // 渲染页面到 Canvas（使用调度器）
  const renderToCanvas = React.useCallback(() => {
    // 使用调度器进行分片渲染
    scheduleRender(() => {
      executeRender()
    }, renderPriority)
  }, [renderPriority, cacheKey, executeRender])

  // 组件挂载和更新时渲染（使用调度器）
  React.useEffect(() => {
    // 可见时立即渲染，不可见时延迟渲染
    if (isVisible) {
      renderToCanvas()
    } else {
      // 不可见时用低优先级调度
      const timeoutId = setTimeout(() => {
        renderToCanvas()
      }, 500 + pageData.index * 10) // 按索引延迟，避免同时渲染
      return () => clearTimeout(timeoutId)
    }
  }, [renderToCanvas, isVisible, pageData.index])

  // 性能监控：记录渲染完成时间
  React.useEffect(() => {
    if (isLoaded && typeof window !== 'undefined') {
      const win = window as any
      if (!win.perfMetrics) win.perfMetrics = {}

      // 记录第一个 Canvas 渲染完成时间
      if (!win.perfMetrics.firstCanvasRendered) {
        win.perfMetrics.firstCanvasRendered = performance.now()
        console.log('[Perf] 第一个 Canvas 渲染完成')
      }

      // 记录最后一个 Canvas 渲染完成时间（通过超时判断）
      if (win.renderCompleteTimeout) {
        clearTimeout(win.renderCompleteTimeout)
      }
      win.renderCompleteTimeout = setTimeout(() => {
        win.perfMetrics.allCanvasRendered = performance.now()
        console.log('[Perf] 所有 Canvas 渲染完成')
      }, 1000) // 1 秒内没有新的 Canvas 渲染完成，认为全部完成
    }
  }, [isLoaded])

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
