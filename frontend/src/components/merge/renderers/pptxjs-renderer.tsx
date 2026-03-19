"use client"

import * as React from "react"
import JSZip from "jszip"

/**
 * 前端 PPTX 解析器 + Canvas 渲染器（feat-087）
 *
 * 功能：
 * - 使用 JSZip 直接在前端解析 PPTX 文件
 * - 提取文本、图片、表格、样式等信息
 * - 使用 Canvas 真实渲染 PPT 页面效果
 * - 支持降级机制：解析失败时自动切换到后端解析模式
 */

// PPTX 解析后的页面数据
export interface PptxjsPageData {
  index: number
  title: string
  slides: PptxjsSlide[]
  layout: {
    width: number
    height: number
  }
}

export interface PptxjsSlide {
  type: 'text' | 'image' | 'table' | 'shape'
  content: PptxjsTextContent | PptxjsImageContent | PptxjsTableContent | PptxjsShapeContent
  position: {
    x: number
    y: number
    width: number
    height: number
  }
}

export interface PptxjsTextContent {
  text: string
  runs: PptxjsTextRun[]
  fontSize?: number
  fontFamily?: string
  color?: string
  bold?: boolean
  italic?: boolean
  align?: 'left' | 'center' | 'right'
}

export interface PptxjsTextRun {
  text: string
  fontSize?: number
  fontFamily?: string
  color?: string
  bold?: boolean
  italic?: boolean
  underline?: boolean
}

export interface PptxjsImageContent {
  src: string // Base64
  width: number
  height: number
}

export interface PptxjsTableContent {
  rows: string[][]
  border?: boolean
}

export interface PptxjsShapeContent {
  shapeType: 'rect' | 'ellipse' | 'triangle' | 'arrow'
  fillColor?: string
  strokeColor?: string
  strokeWidth?: number
}

// 渲染器配置
interface PptxjsRendererProps {
  // PPTX 文件（用于前端解析）
  file?: File
  // 或者使用已解析的数据
  pageData?: PptxjsPageData
  // 画布宽度
  width?: number
  // 画布高度
  height?: number
  // 是否选中
  isSelected?: boolean
  // 点击回调
  onClick?: () => void
  // 渲染质量
  quality?: number
  // 降级模式：使用后端解析数据
  fallbackData?: any
  // 解析/渲染失败回调
  onError?: (error: Error) => void
}

/**
 * 解析 PPTX 文件
 * PPTX 本质是 ZIP 文件，包含 XML 和媒体资源
 */
async function parsePptxFile(file: File): Promise<PptxjsPageData | null> {
  try {
    const zip = await JSZip.loadAsync(file)

    // 读取演示文稿配置
    const presProps = zip.file("ppt/presentation.xml")
    const slideLayouts: Map<number, any> = new Map()
    const slideMasters: Map<number, any> = new Map()

    // 获取幻灯片数量
    const slideFiles = zip.file(/^ppt\/slides\/slide\d+\.xml$/)
    const slideCount = slideFiles.length

    if (slideCount === 0) {
      throw new Error("PPTX 文件中没有幻灯片")
    }

    // 解析每张幻灯片
    const slides: PptxjsSlide[][] = []

    for (let i = 1; i <= slideCount; i++) {
      const slideFile = zip.file(`ppt/slides/slide${i}.xml`)
      if (!slideFile) continue

      const slideXml = await slideFile.async("text")
      const slideData = await parseSlideXml(slideXml, zip, i - 1)
      slides.push(slideData)
    }

    // PPT 标准尺寸（16:9）
    const layout = { width: 960, height: 540 }

    return {
      index: 0,
      title: "PPTX 预览",
      slides: slides[0] || [],
      layout
    }
  } catch (error) {
    console.error("PPTX 解析失败:", error)
    throw error
  }
}

/**
 * 解析单张幻灯片的 XML
 */
async function parseSlideXml(
  xml: string,
  zip: JSZip,
  slideIndex: number
): Promise<PptxjsSlide[]> {
  const parser = new DOMParser()
  const doc = parser.parseFromString(xml, "application/xml")
  const slides: PptxjsSlide[] = []

  // 命名空间
  const ns = {
    a: "http://schemas.openxmlformats.org/drawingml/2006/main",
    p: "http://schemas.openxmlformats.org/presentationml/2006/main",
    r: "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  }

  // 查找所有形状（文本框、图片、形状等）
  const spNodes = doc.getElementsByTagNameNS(ns.p, "sp")
  const picNodes = doc.getElementsByTagNameNS(ns.p, "pic")
  const graphicFrameNodes = doc.getElementsByTagNameNS(ns.p, "graphicFrame")

  // 解析文本框
  for (let i = 0; i < spNodes.length; i++) {
    const spNode = spNodes[i]
    const slide = parseTextBox(spNode, ns, slideIndex)
    if (slide) slides.push(slide)
  }

  // 解析图片
  for (let i = 0; i < picNodes.length; i++) {
    const picNode = picNodes[i]
    const slide = await parsePicture(picNode, ns, zip, slideIndex)
    if (slide) slides.push(slide)
  }

  // 解析表格
  for (let i = 0; i < graphicFrameNodes.length; i++) {
    const gfNode = graphicFrameNodes[i]
    const tableNode = gfNode.getElementsByTagNameNS(ns.a, "tbl")[0]
    if (tableNode) {
      const slide = parseTable(gfNode, tableNode, ns, slideIndex)
      if (slide) slides.push(slide)
    }
  }

  return slides
}

/**
 * 解析文本框
 */
function parseTextBox(
  node: Element,
  ns: any,
  slideIndex: number
): PptxjsSlide | null {
  try {
    // 获取位置信息
    const spPrNode = node.getElementsByTagNameNS(ns.p, "spPr")[0]
    const xfrmNode = spPrNode?.getElementsByTagNameNS(ns.a, "xfrm")[0]

    let position = { x: 0, y: 0, width: 100, height: 100 }
    if (xfrmNode) {
      const off = xfrmNode.getElementsByTagNameNS(ns.a, "off")[0]
      const ext = xfrmNode.getElementsByTagNameNS(ns.a, "ext")[0]
      position = {
        x: parseInt(off?.getAttribute("x") || "0") / 9525, // EMU 转像素
        y: parseInt(off?.getAttribute("y") || "0") / 9525,
        width: parseInt(ext?.getAttribute("cx") || "100000") / 9525,
        height: parseInt(ext?.getAttribute("cy") || "100000") / 9525
      }
    }

    // 获取文本内容
    const txBodyNode = node.getElementsByTagNameNS(ns.p, "txBody")[0]
    const runs: PptxjsTextRun[] = []
    let fullText = ""

    if (txBodyNode) {
      const aNodes = txBodyNode.getElementsByTagNameNS(ns.a, "a")
      for (let i = 0; i < aNodes.length; i++) {
        const aNode = aNodes[i]
        const rNodes = aNode.getElementsByTagNameNS(ns.a, "r")
        for (let j = 0; j < rNodes.length; j++) {
          const rNode = rNodes[j]
          const tNode = rNode.getElementsByTagNameNS(ns.a, "t")[0]
          const text = tNode?.textContent || ""
          fullText += text

          // 解析字体样式
          const rPrNode = rNode.getElementsByTagNameNS(ns.a, "rPr")[0]
          const colorAttr = rPrNode?.getElementsByTagNameNS(ns.a, "srgbClr")[0]?.getAttribute("val")
          const run: PptxjsTextRun = {
            text,
            fontSize: rPrNode ? parseInt(rPrNode.getAttribute("sz") || "1800") / 100 : 18,
            color: colorAttr || undefined,
            bold: rPrNode?.getAttribute("b") === "1",
            italic: rPrNode?.getAttribute("i") === "1",
            underline: rPrNode?.getAttribute("u") === "sng"
          }
          runs.push(run)
        }
      }
    }

    return {
      type: "text",
      content: {
        text: fullText,
        runs,
        align: "left"
      } as PptxjsTextContent,
      position
    }
  } catch (error) {
    console.warn("解析文本框失败:", error)
    return null
  }
}

/**
 * 解析图片
 */
async function parsePicture(
  node: Element,
  ns: any,
  zip: JSZip,
  slideIndex: number
): Promise<PptxjsSlide | null> {
  try {
    // 获取位置
    const spPrNode = node.getElementsByTagNameNS(ns.p, "spPr")[0]
    const xfrmNode = spPrNode?.getElementsByTagNameNS(ns.a, "xfrm")[0]

    let position = { x: 0, y: 0, width: 100, height: 100 }
    if (xfrmNode) {
      const off = xfrmNode.getElementsByTagNameNS(ns.a, "off")[0]
      const ext = xfrmNode.getElementsByTagNameNS(ns.a, "ext")[0]
      position = {
        x: parseInt(off?.getAttribute("x") || "0") / 9525,
        y: parseInt(off?.getAttribute("y") || "0") / 9525,
        width: parseInt(ext?.getAttribute("cx") || "100000") / 9525,
        height: parseInt(ext?.getAttribute("cy") || "100000") / 9525
      }
    }

    // 获取图片关系 ID
    const blipFillNode = node.getElementsByTagNameNS(ns.p, "blipFill")[0]
    const blipNode = blipFillNode?.getElementsByTagNameNS(ns.a, "blip")[0]
    const embedId = blipNode?.getAttributeNS(ns.r, "embed")

    if (!embedId) return null

    // 从 ZIP 中读取图片
    const relsFile = zip.file(`ppt/slides/_rels/slide${slideIndex + 1}.xml.rels`)
    if (!relsFile) return null

    const relsXml = await relsFile.async("text")
    const relParser = new DOMParser()
    const relsDoc = relParser.parseFromString(relsXml, "application/xml")

    const relNode = Array.from(relsDoc.getElementsByTagName("Relationship"))
      .find(r => r.getAttribute("Id") === embedId)

    const target = relNode?.getAttribute("Target")
    if (!target) return null

    // 图片路径
    const imagePath = target.startsWith("/ppt/") ? target.slice(1) : `ppt/${target}`
    const imageFile = zip.file(imagePath)

    if (!imageFile) return null

    // 转换为 Base64
    const imageBlob = await imageFile.async("blob")
    const base64 = await blobToBase64(imageBlob)

    return {
      type: "image",
      content: {
        src: base64,
        width: position.width,
        height: position.height
      } as PptxjsImageContent,
      position
    }
  } catch (error) {
    console.warn("解析图片失败:", error)
    return null
  }
}

/**
 * 解析表格
 */
function parseTable(
  gfNode: Element,
  tableNode: Element,
  ns: any,
  slideIndex: number
): PptxjsSlide | null {
  try {
    // 获取位置
    const xfrmNode = gfNode.getElementsByTagNameNS(ns.a, "xfrm")[0]
    let position = { x: 0, y: 0, width: 200, height: 100 }
    if (xfrmNode) {
      const off = xfrmNode.getElementsByTagNameNS(ns.a, "off")[0]
      const ext = xfrmNode.getElementsByTagNameNS(ns.a, "ext")[0]
      position = {
        x: parseInt(off?.getAttribute("x") || "0") / 9525,
        y: parseInt(off?.getAttribute("y") || "0") / 9525,
        width: parseInt(ext?.getAttribute("cx") || "200000") / 9525,
        height: parseInt(ext?.getAttribute("cy") || "100000") / 9525
      }
    }

    // 解析表格数据
    const rows: string[][] = []
    const trNodes = tableNode.getElementsByTagNameNS(ns.a, "tr")

    for (let i = 0; i < trNodes.length; i++) {
      const trNode = trNodes[i]
      const tcNodes = trNode.getElementsByTagNameNS(ns.a, "tc")
      const rowData: string[] = []

      for (let j = 0; j < tcNodes.length; j++) {
        const tcNode = tcNodes[j]
        const tNode = tcNode.getElementsByTagNameNS(ns.a, "t")[0]
        rowData.push(tNode?.textContent || "")
      }

      rows.push(rowData)
    }

    return {
      type: "table",
      content: {
        rows
      } as PptxjsTableContent,
      position
    }
  } catch (error) {
    console.warn("解析表格失败:", error)
    return null
  }
}

/**
 * Blob 转 Base64
 */
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      const result = reader.result as string
      // 转换为 data URL
      const base64 = result.split(",")[1] || result
      const mimeType = blob.type || "image/png"
      resolve(`data:${mimeType};base64,${base64}`)
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

/**
 * PptxjsRenderer 组件
 *
 * 前端直接解析 PPTX 文件并渲染到 Canvas
 */
export function PptxjsRenderer({
  file,
  pageData,
  width = 300,
  height = 169,
  isSelected = false,
  onClick,
  quality = 0.8,
  fallbackData,
  onError
}: PptxjsRendererProps) {
  const canvasRef = React.useRef<HTMLCanvasElement>(null)
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [parsedData, setParsedData] = React.useState<PptxjsPageData | null>(null)
  const [error, setError] = React.useState<Error | null>(null)

  // 解析 PPTX 文件
  React.useEffect(() => {
    if (!file) return

    const parseFile = async () => {
      try {
        setError(null)
        const data = await parsePptxFile(file)
        setParsedData(data)
        setIsLoaded(true)
      } catch (err) {
        const error = err as Error
        console.error("前端解析 PPTX 失败，使用降级模式:", error)
        setError(error)
        // 触发降级：使用后端解析数据
        if (fallbackData && onError) {
          onError(error)
        }
      }
    }

    parseFile()
  }, [file])

  // 渲染到 Canvas
  React.useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, width, height)

    // 绘制白色背景
    ctx.fillStyle = "#ffffff"
    ctx.fillRect(0, 0, width, height)

    // 确定使用哪个数据源
    const dataToRender = parsedData?.slides || []
    const scale = Math.min(width / 960, height / 540) * quality

    // 渲染每个元素
    for (const slide of dataToRender) {
      try {
        const x = slide.position.x * scale
        const y = slide.position.y * scale
        const w = slide.position.width * scale
        const h = slide.position.height * scale

        if (slide.type === "text") {
          renderText(ctx, slide.content as PptxjsTextContent, x, y, w, h)
        } else if (slide.type === "image") {
          renderImage(ctx, slide.content as PptxjsImageContent, x, y, w, h)
        } else if (slide.type === "table") {
          renderTable(ctx, slide.content as PptxjsTableContent, x, y, w, h)
        } else if (slide.type === "shape") {
          renderShape(ctx, slide.content as PptxjsShapeContent, x, y, w, h)
        }
      } catch (err) {
        console.warn("渲染元素失败:", err)
      }
    }

    // 绘制选中边框
    if (isSelected) {
      ctx.strokeStyle = "#6366f1"
      ctx.lineWidth = 2
      ctx.setLineDash([4, 2])
      ctx.strokeRect(0, 0, width, height)
      ctx.setLineDash([])
    }

    setIsLoaded(true)
  }, [parsedData, width, height, isSelected, quality])

  // 使用 fallbackData 渲染（降级模式）
  React.useEffect(() => {
    if (!fallbackData || parsedData) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    ctx.clearRect(0, 0, width, height)
    ctx.fillStyle = "#ffffff"
    ctx.fillRect(0, 0, width, height)

    // 使用后端解析数据渲染
    renderFallbackData(ctx, fallbackData, width, height, isSelected)
    setIsLoaded(true)
  }, [fallbackData, parsedData, width, height, isSelected])

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
          onClick ? "cursor-pointer hover:shadow-md" : ""
        } ${isSelected ? "ring-2 ring-indigo-500" : ""}`}
      />

      {/* 加载状态 */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {/* 错误/降级提示 */}
      {error && (
        <div className="absolute bottom-1 right-1 bg-amber-500 text-white text-[8px] px-1.5 py-0.5 rounded">
          降级模式
        </div>
      )}
    </div>
  )
}

// 渲染文本
function renderText(
  ctx: CanvasRenderingContext2D,
  content: PptxjsTextContent,
  x: number,
  y: number,
  maxWidth: number,
  maxHeight: number
) {
  ctx.textAlign = "left"
  ctx.textBaseline = "top"

  let currentY = y + 5
  const lineHeight = 20

  for (const run of content.runs || []) {
    const fontSize = (run.fontSize || 18) * 0.8
    const fontFamily = run.fontFamily || "Microsoft YaHei, sans-serif"
    const fontWeight = run.bold ? "bold" : "normal"
    const fontStyle = run.italic ? "italic" : "normal"

    ctx.font = `${fontStyle} ${fontWeight} ${fontSize}px ${fontFamily}`
    ctx.fillStyle = run.color ? `#${run.color}` : "#000000"

    ctx.fillText(run.text, x, currentY, maxWidth)

    if (run.underline) {
      const textWidth = ctx.measureText(run.text).width
      ctx.strokeStyle = run.color ? `#${run.color}` : "#000000"
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(x, currentY + fontSize + 1)
      ctx.lineTo(x + textWidth, currentY + fontSize + 1)
      ctx.stroke()
    }

    currentY += lineHeight
  }
}

// 渲染图片
function renderImage(
  ctx: CanvasRenderingContext2D,
  content: PptxjsImageContent,
  x: number,
  y: number,
  w: number,
  h: number
) {
  const img = new Image()
  img.onload = () => {
    ctx.drawImage(img, x, y, w, h)
  }
  img.src = content.src
}

// 渲染表格
function renderTable(
  ctx: CanvasRenderingContext2D,
  content: PptxjsTableContent,
  x: number,
  y: number,
  w: number,
  h: number
) {
  const rows = content.rows || []
  if (rows.length === 0) return

  const cols = rows[0]?.length || 1
  const cellWidth = w / cols
  const cellHeight = h / rows.length

  // 绘制边框
  ctx.strokeStyle = "#000000"
  ctx.lineWidth = 1

  // 外框
  ctx.strokeRect(x, y, w, h)

  // 行线
  for (let i = 1; i < rows.length; i++) {
    const rowY = y + i * cellHeight
    ctx.beginPath()
    ctx.moveTo(x, rowY)
    ctx.lineTo(x + w, rowY)
    ctx.stroke()
  }

  // 列线
  for (let j = 1; j < cols; j++) {
    const colX = x + j * cellWidth
    ctx.beginPath()
    ctx.moveTo(colX, y)
    ctx.lineTo(colX, y + h)
    ctx.stroke()
  }

  // 单元格内容
  ctx.textAlign = "center"
  ctx.textBaseline = "middle"
  ctx.font = "12px Microsoft YaHei, sans-serif"
  ctx.fillStyle = "#000000"

  for (let i = 0; i < rows.length; i++) {
    for (let j = 0; j < cols; j++) {
      const cellText = rows[i]?.[j] || ""
      const cellX = x + j * cellWidth + cellWidth / 2
      const cellY = y + i * cellHeight + cellHeight / 2

      if (cellText) {
        ctx.fillText(cellText, cellX, cellY, cellWidth - 8)
      }
    }
  }
}

// 渲染形状
function renderShape(
  ctx: CanvasRenderingContext2D,
  content: PptxjsShapeContent,
  x: number,
  y: number,
  w: number,
  h: number
) {
  ctx.fillStyle = content.fillColor || "#f0f0f0"
  ctx.strokeStyle = content.strokeColor || "#cccccc"
  ctx.lineWidth = content.strokeWidth || 1

  if (content.shapeType === "rect") {
    ctx.fillRect(x, y, w, h)
    ctx.strokeRect(x, y, w, h)
  } else if (content.shapeType === "ellipse") {
    ctx.beginPath()
    ctx.ellipse(x + w/2, y + h/2, w/2, h/2, 0, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
  }
}

// 降级模式渲染（使用后端解析数据）
function renderFallbackData(
  ctx: CanvasRenderingContext2D,
  data: any,
  width: number,
  height: number,
  isSelected: boolean
) {
  const scale = Math.min(width / 960, height / 540) * 0.8

  if (data?.shapes) {
    for (const shape of data.shapes) {
      try {
        const x = shape.position.x * scale
        const y = shape.position.y * scale
        const w = shape.position.width * scale
        const h = shape.position.height * scale

        if (shape.type === "text_box" || shape.type === "placeholder") {
          renderFallbackText(ctx, shape, x, y, w, h)
        } else if (shape.type === "picture") {
          renderFallbackImage(ctx, shape, x, y, w, h)
        } else if (shape.type === "table") {
          renderFallbackTable(ctx, shape, x, y, w, h)
        } else {
          ctx.fillStyle = "#f0f0f0"
          ctx.fillRect(x, y, w, h)
        }
      } catch (err) {
        console.warn("降级渲染失败:", err)
      }
    }
  }

  // 绘制选中边框
  if (isSelected) {
    ctx.strokeStyle = "#6366f1"
    ctx.lineWidth = 2
    ctx.setLineDash([4, 2])
    ctx.strokeRect(0, 0, width, height)
    ctx.setLineDash([])
  }
}

function renderFallbackText(
  ctx: CanvasRenderingContext2D,
  shape: any,
  x: number,
  y: number,
  w: number,
  h: number
) {
  if (!shape.text_content || shape.text_content.length === 0) return

  let currentY = y + 10
  ctx.textAlign = "left"
  ctx.textBaseline = "top"

  for (const paragraph of shape.text_content) {
    for (const run of paragraph.runs || []) {
      const fontSize = (run.font.size || 18) * 0.8
      ctx.font = `${fontSize}px Microsoft YaHei, sans-serif`
      ctx.fillStyle = run.font.color || "#000000"
      ctx.fillText(run.text, x, currentY, w)
      currentY += 18
    }
  }
}

function renderFallbackImage(
  ctx: CanvasRenderingContext2D,
  shape: any,
  x: number,
  y: number,
  w: number,
  h: number
) {
  if (!shape.image_base64) return

  const img = new Image()
  img.onload = () => {
    ctx.drawImage(img, x, y, w, h)
  }
  img.src = shape.image_base64
}

function renderFallbackTable(
  ctx: CanvasRenderingContext2D,
  shape: any,
  x: number,
  y: number,
  w: number,
  h: number
) {
  if (!shape.table_data || shape.table_data.length === 0) return

  const rows = shape.table_data.length
  const cols = shape.table_data[0]?.length || 1
  const cellWidth = w / cols
  const cellHeight = h / rows

  ctx.strokeStyle = "#000000"
  ctx.lineWidth = 1
  ctx.strokeRect(x, y, w, h)

  for (let i = 1; i < rows; i++) {
    ctx.beginPath()
    ctx.moveTo(x, y + i * cellHeight)
    ctx.lineTo(x + w, y + i * cellHeight)
    ctx.stroke()
  }

  for (let j = 1; j < cols; j++) {
    ctx.beginPath()
    ctx.moveTo(x + j * cellWidth, y)
    ctx.lineTo(x + j * cellWidth, y + h)
    ctx.stroke()
  }

  ctx.textAlign = "center"
  ctx.textBaseline = "middle"
  ctx.font = "12px Microsoft YaHei, sans-serif"

  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      const text = shape.table_data[i]?.[j] || ""
      ctx.fillText(text, x + j * cellWidth + cellWidth/2, y + i * cellHeight + cellHeight/2)
    }
  }
}

export default PptxjsRenderer
