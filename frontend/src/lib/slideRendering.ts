/**
 * 幻灯片渲染决策工具函数
 * feat-219: 统一的渲染决策逻辑
 *
 * 渲染优先级（feat-173, feat-185）：
 * 1. 有 imageUrl（LibreOffice预览图）→ ImageRenderer
 * 2. 是原始版本（无 action）且有 PPT file → PptxViewJSRenderer（失败时降级到 PptCanvasRenderer）
 * 3. 是 AI 版本（有 action）→ SlideContentRenderer
 * 4. 有 content 数据 → PptCanvasRenderer
 * 5. 兜底 → 占位符
 */

import type { SlidePoolItem, SlideVersion, SlideAction } from "@/types/merge-session"
import type { SlideContent } from "@/types/merge-plan"
// feat-219: 从渲染器组件导入类型，确保类型一致性
import type { EnhancedPptPageData } from "@/components/merge/renderers/ppt-canvas-renderer"

// 重导出 EnhancedPptPageData 类型，供其他模块使用
export type { EnhancedPptPageData }

// ============ 类型定义 ============

/** 渲染器类型 */
export type RendererType =
  | "image"           // 图片渲染（LibreOffice 预览图）
  | "pptxviewjs"      // PptxViewJS 渲染器
  | "pptxviewjs_fallback"  // PptxViewJS 降级到 Canvas
  | "slide_content"   // AI 内容渲染器
  | "ppt_canvas"      // Canvas 渲染器
  | "placeholder"     // 占位符

/** 渲染决策结果 */
export interface RenderDecision {
  /** 渲染器类型 */
  renderer: RendererType
  /** 是否使用降级模式 */
  fallbackMode: boolean
  /** 决策原因（用于调试） */
  reason: string
  /** 原始版本是否有 action */
  hasAction: boolean
  /** 是否有 PPT 文件可用 */
  hasPptFile: boolean
  /** 是否有预览图 URL */
  hasImageUrl: boolean
  /** 是否有 content 数据 */
  hasContent: boolean
  /** 是否有 shapes 数据 */
  hasShapes: boolean
}

/** 渲染决策输入参数 */
export interface RenderDecisionInput {
  /** 幻灯片信息 */
  slide: SlidePoolItem | null
  /** 版本信息 */
  version: SlideVersion | null
  /** 预览图 URL */
  imageUrl?: string | null
  /** PPT 文件（A 或 B） */
  pptFile?: File | null
  /** 是否处于降级模式（来自 usePptxFallback） */
  fallbackMode?: boolean
}

/** 渲染器组件 Props 基础类型 */
export interface BaseRendererProps {
  width?: number
  height?: number
  quality?: number | 'low' | 'medium' | 'high'
  className?: string
}

/** ImageRenderer Props */
export interface ImageRendererProps extends BaseRendererProps {
  src: string
  alt: string
}

/** PptxViewJSRenderer Props */
export interface PptxViewJSRendererProps extends BaseRendererProps {
  file: File
  slideIndex: number
  onError?: (error: Error) => void
  onLoad?: (slideCount: number) => void
}

/** PptCanvasRenderer Props */
export interface PptCanvasRendererProps extends BaseRendererProps {
  pageData: EnhancedPptPageData
}

/** SlideContentRenderer Props */
export interface SlideContentRendererProps extends BaseRendererProps {
  content: SlideContent
  action?: SlideAction
  slide?: SlidePoolItem
  size?: "preview" | "thumbnail"
  animated?: boolean
}

// ============ 核心决策函数 ============

/**
 * 获取幻灯片渲染器类型
 *
 * 根据幻灯片和版本信息，决定使用哪个渲染器
 *
 * @param input 渲染决策输入参数
 * @returns 渲染决策结果
 *
 * @example
 * ```ts
 * const decision = getSlideRenderer({
 *   slide: activeSlide,
 *   version: activeVersion,
 *   imageUrl: version?.preview_url,
 *   pptFile: getPptFile(slide?.original_source, fileA, fileB),
 *   fallbackMode: fallbackModeFromHook,
 * })
 *
 * switch (decision.renderer) {
 *   case "image":
 *     return <img src={imageUrl} />
 *   case "pptxviewjs":
 *     return <PptxViewJSRenderer file={pptFile} slideIndex={slide.original_index} />
 *   case "slide_content":
 *     return <SlideContentRenderer content={version.content} />
 *   case "ppt_canvas":
 *     return <PptCanvasRenderer pageData={...} />
 *   default:
 *     return <Placeholder />
 * }
 * ```
 */
export function getSlideRenderer(input: RenderDecisionInput): RenderDecision {
  const { slide, version, imageUrl, pptFile, fallbackMode = false } = input

  // 默认决策结果
  const baseResult: Omit<RenderDecision, "renderer" | "reason"> = {
    fallbackMode,
    hasAction: !!version?.action,
    hasPptFile: !!pptFile,
    hasImageUrl: !!imageUrl,
    hasContent: !!(version?.content && (version.content.title || version.content.main_points?.length)),
    hasShapes: !!(version?.shapes && version.shapes.length > 0),
  }

  // 优先级 1: 有预览图 URL → ImageRenderer
  if (imageUrl) {
    return {
      ...baseResult,
      renderer: "image",
      reason: "有预览图 URL，使用 ImageRenderer",
    }
  }

  // 优先级 2: 原始版本（无 action）且有 PPT file
  if (!version?.action && pptFile) {
    if (fallbackMode) {
      return {
        ...baseResult,
        renderer: "pptxviewjs_fallback",
        reason: "原始版本且有 PPT 文件，但处于降级模式，使用 PptCanvasRenderer",
      }
    }
    return {
      ...baseResult,
      renderer: "pptxviewjs",
      reason: "原始版本且有 PPT 文件，使用 PptxViewJSRenderer",
    }
  }

  // 优先级 3: AI 版本（有 action）且有 content → SlideContentRenderer
  if (version?.action && version.content) {
    return {
      ...baseResult,
      renderer: "slide_content",
      reason: `AI 版本（action: ${version.action}），使用 SlideContentRenderer`,
    }
  }

  // 优先级 4: 有 content 数据 → PptCanvasRenderer
  if (version?.content && (version.content.title || version.content.main_points?.length || version.shapes?.length)) {
    return {
      ...baseResult,
      renderer: "ppt_canvas",
      reason: "有 content 或 shapes 数据，使用 PptCanvasRenderer",
    }
  }

  // 优先级 5: 兜底 → 占位符
  return {
    ...baseResult,
    renderer: "placeholder",
    reason: "无可用渲染数据，使用占位符",
  }
}

// ============ 辅助函数 ============

/**
 * 将 SlideVersion 转换为 EnhancedPptPageData
 * feat-180: 优先使用保存的 shapes 数据（来自后端增强模式）
 *
 * @param version 幻灯片版本
 * @param pageIndex 页面索引
 * @returns EnhancedPptPageData
 */
export function versionToPageData(version: SlideVersion, pageIndex: number): EnhancedPptPageData {
  // 优先使用保存的 shapes 数据（来自后端增强模式）
  if (version.shapes && version.shapes.length > 0) {
    const content = version.content
    const mainPoints = content.main_points || []
    return {
      index: pageIndex,
      title: content.title || "",
      content: mainPoints.map((text) => ({
        type: "text" as const,
        text,
      })),
      shapes: version.shapes,
      layout: version.layout || { width: 960, height: 540 },
    }
  }

  // 降级：从 content 构造简化的 shapes
  const content = version.content
  const mainPoints = content.main_points || []
  const additionalContent = content.additional_content || ""

  return {
    index: pageIndex,
    title: content.title || "",
    content: [...mainPoints, additionalContent]
      .filter(Boolean)
      .map((text) => ({
        type: "text" as const,
        text,
      })),
    shapes: [
      {
        type: "text_box",
        name: "main_content",
        position: { x: 50, y: 100, width: 860, height: 380 },
        text_content: [
          {
            runs: mainPoints.map((text) => ({
              text: text + "\n",
              font: { size: 18, color: "#333333" },
            })),
          },
        ],
      },
    ],
    layout: { width: 960, height: 540 },
  }
}

/**
 * 获取对应的 PPT 文件
 *
 * @param originalSource 幻灯片来源
 * @param fileA PPT A 文件
 * @param fileB PPT B 文件
 * @returns 对应的 File 或 null
 */
export function getPptFile(
  originalSource: string | undefined,
  fileA?: File | null,
  fileB?: File | null
): File | null {
  if (originalSource === "ppt_a") return fileA ?? null
  if (originalSource === "ppt_b") return fileB ?? null
  return null
}

/**
 * 判断是否应该使用 PptxViewJSRenderer
 *
 * @param decision 渲染决策结果
 * @returns 是否应该使用 PptxViewJSRenderer
 */
export function shouldUsePptxViewJS(decision: RenderDecision): boolean {
  return decision.renderer === "pptxviewjs" || decision.renderer === "pptxviewjs_fallback"
}

/**
 * 判断是否应该使用 Canvas 渲染器
 *
 * @param decision 渲染决策结果
 * @returns 是否应该使用 Canvas 渲染器
 */
export function shouldUseCanvas(decision: RenderDecision): boolean {
  return (
    decision.renderer === "ppt_canvas" ||
    decision.renderer === "pptxviewjs_fallback"
  )
}

/**
 * 判断是否应该使用 SlideContentRenderer
 *
 * @param decision 渲染决策结果
 * @returns 是否应该使用 SlideContentRenderer
 */
export function shouldUseSlideContent(decision: RenderDecision): boolean {
  return decision.renderer === "slide_content"
}

/**
 * 获取渲染器的中文描述
 *
 * @param renderer 渲染器类型
 * @returns 渲染器描述
 */
export function getRendererLabel(renderer: RendererType): string {
  const labels: Record<RendererType, string> = {
    image: "图片渲染",
    pptxviewjs: "PptxViewJS 渲染",
    pptxviewjs_fallback: "Canvas 降级渲染",
    slide_content: "AI 内容渲染",
    ppt_canvas: "Canvas 渲染",
    placeholder: "占位符",
  }
  return labels[renderer] || renderer
}

/**
 * 获取渲染决策的调试信息
 *
 * @param decision 渲染决策结果
 * @returns 调试信息字符串
 */
export function getRenderDecisionDebug(decision: RenderDecision): string {
  return [
    `渲染器: ${getRendererLabel(decision.renderer)}`,
    `原因: ${decision.reason}`,
    `有 action: ${decision.hasAction}`,
    `有 PPT 文件: ${decision.hasPptFile}`,
    `有预览图: ${decision.hasImageUrl}`,
    `有 content: ${decision.hasContent}`,
    `有 shapes: ${decision.hasShapes}`,
    `降级模式: ${decision.fallbackMode}`,
  ].join("\n")
}

// ============ 常量导出 ============

/** 渲染器默认尺寸配置 */
export const RENDERER_DEFAULTS = {
  width: 800,
  height: 450,
  thumbnailWidth: 300,
  thumbnailHeight: 169,
  quality: 1.0 as const,
  thumbnailQuality: 0.5 as const,
} as const

/** 渲染器质量选项 */
export const RENDER_QUALITY = {
  low: 0.5,
  medium: 0.75,
  high: 1.0,
} as const