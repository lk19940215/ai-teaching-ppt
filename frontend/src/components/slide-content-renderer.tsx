/**
 * AI 内容渲染器组件
 * feat-175: 将 AI 产出的结构化内容渲染为美观的教学幻灯片预览卡片
 *
 * 功能：
 * - 根据 action 类型自动选择布局模板
 * - BulletTemplate: 要点列表模板（polish/expand）
 * - KnowledgeTemplate: 知识卡片模板（extract）
 * - MergeTemplate: 融合结果模板（merge）
 * - 支持缩略图模式（简化内容、缩小字体）
 *
 * 设计文档：docs/research-ai-content-rendering.md
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import type { SlideContent } from "@/types/merge-plan"
import type { SlidePoolItem, SlideAction } from "@/types/merge-session"

// ============ 组件接口定义 ============

export interface SlideContentRendererProps {
  /** AI 返回的内容 */
  content: SlideContent
  /** 操作类型（用于选模板） */
  action?: SlideAction
  /** 幻灯片信息（来源标记等） */
  slide?: SlidePoolItem
  /** 渲染尺寸：preview（大预览）或 thumbnail（缩略图） */
  size?: "preview" | "thumbnail"
  /** 自定义类名 */
  className?: string
  /** 是否启用动画（Phase 2 增强） */
  animated?: boolean
}

// ============ 配色方案 ============

const COLORS = {
  // 主色
  primary: "#3B82F6", // 蓝色 - 标题、强调
  // 辅助色
  success: "#10B981", // 绿色 - 正确/要点
  warning: "#F59E0B", // 琥珀 - 警告/易错
  accent: "#8B5CF6", // 紫色 - 融合/创意
  danger: "#EF4444", // 红色 - 重要/错误
  // 背景色
  bgWhite: "#FFFFFF",
  bgLight: "#F8FAFC",
  // 文字色
  textDark: "#1E293B",
  textMuted: "#64748B",
  textLight: "#94A3B8",
}

// ============ 模板类型 ============

type TemplateType = "bullet" | "knowledge" | "merge" | "content"

/**
 * 根据内容和 action 选择模板
 */
function selectTemplate(content: SlideContent, action?: SlideAction): TemplateType {
  // 融合结果
  if (action === "merge" || (content.elements && content.elements.length > 0)) {
    return "merge"
  }

  // 知识点提取
  if (action === "extract") {
    return "knowledge"
  }

  // 改写（可能有前后对比）
  if (action === "rewrite") {
    return "content"
  }

  // 要点少于 2 条且有大段内容
  if ((content.main_points?.length || 0) <= 1 && content.additional_content) {
    return "content"
  }

  // 默认：要点列表
  return "bullet"
}

// ============ 缩略图模式辅助函数 ============

/**
 * 截断文本
 */
function truncateText(text: string, maxLength: number): string {
  if (!text) return ""
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + "..."
}

/**
 * 获取缩略图模式的样式配置
 */
function getThumbnailStyles() {
  return {
    container: "p-2",
    title: "text-[10px] font-semibold",
    body: "text-[9px]",
    bullet: "text-[8px]",
    gap: "gap-1",
    padding: "p-1.5",
  }
}

/**
 * 获取预览模式的样式配置
 */
function getPreviewStyles() {
  return {
    container: "p-4",
    title: "text-sm font-semibold",
    body: "text-xs",
    bullet: "text-xs",
    gap: "gap-2",
    padding: "p-3",
  }
}

// ============ BulletTemplate: 要点列表模板 ============

interface BulletTemplateProps {
  content: SlideContent
  isThumbnail: boolean
}

function BulletTemplate({ content, isThumbnail }: BulletTemplateProps) {
  const styles = isThumbnail ? getThumbnailStyles() : getPreviewStyles()
  const maxPoints = isThumbnail ? 3 : 6
  const maxTitleLength = isThumbnail ? 15 : 40
  const maxPointLength = isThumbnail ? 20 : 60

  const points = (content.main_points || []).slice(0, maxPoints)
  const title = truncateText(content.title || "未命名幻灯片", maxTitleLength)

  return (
    <div className={cn("flex flex-col h-full", styles.gap)}>
      {/* 蓝色色带标题 */}
      <div
        className={cn(
          "rounded-md flex items-center gap-2",
          styles.padding,
          isThumbnail ? "bg-blue-500" : "bg-gradient-to-r from-blue-500 to-blue-600"
        )}
      >
        <span className="text-white text-base">📘</span>
        <h3 className={cn("text-white truncate", styles.title)}>{title}</h3>
      </div>

      {/* 要点列表 */}
      <div className={cn("flex-1 flex flex-col", styles.gap)}>
        {points.map((point, idx) => (
          <div key={idx} className="flex items-start gap-2">
            <span className={cn("text-blue-500 flex-shrink-0", isThumbnail ? "text-[8px]" : "text-sm")}>
              ●
            </span>
            <p className={cn("text-gray-700 leading-relaxed", styles.bullet)}>
              {truncateText(point, maxPointLength)}
            </p>
          </div>
        ))}
      </div>

      {/* 补充说明区域（仅预览模式且存在时显示） */}
      {!isThumbnail && content.additional_content && (
        <div className="mt-auto p-3 bg-blue-50 rounded-md border border-blue-100">
          <div className="flex items-center gap-2 text-blue-600 text-xs font-medium mb-1">
            <span>💡</span>
            <span>补充说明</span>
          </div>
          <p className="text-xs text-gray-600 leading-relaxed">
            {truncateText(content.additional_content, 100)}
          </p>
        </div>
      )}
    </div>
  )
}

// ============ KnowledgeTemplate: 知识卡片模板 ============

interface KnowledgeTemplateProps {
  content: SlideContent
  isThumbnail: boolean
}

/**
 * 解析 extract 返回的结构化知识点
 * 后端返回格式：
 * { core_concepts: [], formulas: [], methods: [], common_mistakes: [] }
 */
function parseKnowledgePoints(content: SlideContent) {
  // 如果 main_points 中包含结构化标签，尝试解析
  const points = content.main_points || []

  const knowledge: {
    core: string[]
    formulas: string[]
    methods: string[]
    mistakes: string[]
  } = {
    core: [],
    formulas: [],
    methods: [],
    mistakes: [],
  }

  // 简单解析：根据关键词分类
  for (const point of points) {
    const lower = point.toLowerCase()
    if (lower.includes("公式") || lower.includes("formula") || /^[=\+\-\*\/\d]+$/.test(point)) {
      knowledge.formulas.push(point)
    } else if (lower.includes("易错") || lower.includes("注意") || lower.includes("mistake")) {
      knowledge.mistakes.push(point)
    } else if (lower.includes("方法") || lower.includes("步骤") || lower.includes("method")) {
      knowledge.methods.push(point)
    } else {
      knowledge.core.push(point)
    }
  }

  return knowledge
}

function KnowledgeTemplate({ content, isThumbnail }: KnowledgeTemplateProps) {
  const styles = isThumbnail ? getThumbnailStyles() : getPreviewStyles()
  const knowledge = parseKnowledgePoints(content)
  const maxTitleLength = isThumbnail ? 12 : 30
  const title = truncateText(content.title || "知识点提取", maxTitleLength)

  // 知识卡片配置
  const cards = [
    { key: "core", label: "核心概念", icon: "🔑", items: knowledge.core, color: "blue" },
    { key: "formulas", label: "公式", icon: "📐", items: knowledge.formulas, color: "green" },
    { key: "methods", label: "方法", icon: "📝", items: knowledge.methods, color: "amber" },
    { key: "mistakes", label: "易错", icon: "⚠️", items: knowledge.mistakes, color: "red" },
  ].filter((card) => card.items.length > 0)

  // 缩略图模式：只显示最多 2 个卡片
  const displayCards = isThumbnail ? cards.slice(0, 2) : cards

  return (
    <div className={cn("flex flex-col h-full", styles.gap)}>
      {/* 标题 */}
      <div className="flex items-center gap-2">
        <span className="text-base">📚</span>
        <h3 className={cn("font-semibold text-gray-800", styles.title)}>{title}</h3>
      </div>

      {/* 知识卡片网格 */}
      <div
        className={cn(
          "flex-1 grid gap-2",
          isThumbnail ? "grid-cols-2" : "grid-cols-2"
        )}
      >
        {displayCards.map((card) => (
          <div
            key={card.key}
            className={cn(
              "rounded-md border",
              styles.padding,
              card.color === "blue" && "bg-blue-50 border-blue-200",
              card.color === "green" && "bg-green-50 border-green-200",
              card.color === "amber" && "bg-amber-50 border-amber-200",
              card.color === "red" && "bg-red-50 border-red-200"
            )}
          >
            <div className="flex items-center gap-1 mb-1">
              <span className={isThumbnail ? "text-[9px]" : "text-xs"}>{card.icon}</span>
              <span
                className={cn(
                  "font-medium",
                  styles.bullet,
                  card.color === "blue" && "text-blue-700",
                  card.color === "green" && "text-green-700",
                  card.color === "amber" && "text-amber-700",
                  card.color === "red" && "text-red-700"
                )}
              >
                {card.label}
              </span>
            </div>
            <ul className={cn("space-y-0.5", isThumbnail ? "text-[8px]" : "text-[10px]")}>
              {card.items.slice(0, isThumbnail ? 2 : 3).map((item, idx) => (
                <li key={idx} className="text-gray-600 truncate">
                  {truncateText(item, isThumbnail ? 10 : 25)}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}

// ============ MergeTemplate: 融合结果模板 ============

interface MergeTemplateProps {
  content: SlideContent
  slide?: SlidePoolItem
  isThumbnail: boolean
}

/**
 * 解析 elements 数组
 * 后端返回格式：[{ type: "title" | "text_body" | "list_item", content: string }]
 */
function parseElements(content: SlideContent) {
  const elements = content.elements || []

  const parsed: {
    title: string
    textBodies: string[]
    listItems: string[]
  } = {
    title: content.title || "",
    textBodies: [],
    listItems: [],
  }

  for (const el of elements) {
    if (el.type === "title") {
      parsed.title = el.content
    } else if (el.type === "text_body") {
      parsed.textBodies.push(el.content)
    } else if (el.type === "list_item") {
      parsed.listItems.push(el.content)
    }
  }

  return parsed
}

/**
 * 获取融合来源标记
 */
function getMergeSourceLabel(slide?: SlidePoolItem): string | null {
  if (!slide || slide.original_source !== "merge") return null

  const firstVersion = slide.versions[0]
  if (!firstVersion?.source_merge_sources) return null

  const sources = firstVersion.source_merge_sources
  const labels = sources.map((s) => {
    const pptLabel = s.source === "ppt_a" ? "A" : "B"
    return `${pptLabel}:P${s.slide_index + 1}`
  })

  return `融合自 ${labels.join(" + ")}`
}

function MergeTemplate({ content, slide, isThumbnail }: MergeTemplateProps) {
  const styles = isThumbnail ? getThumbnailStyles() : getPreviewStyles()
  const parsed = parseElements(content)
  const mergeLabel = getMergeSourceLabel(slide)

  const maxTitleLength = isThumbnail ? 15 : 40
  const maxTextLength = isThumbnail ? 30 : 100
  const maxItems = isThumbnail ? 3 : 6

  const title = truncateText(parsed.title || content.title || "融合结果", maxTitleLength)

  return (
    <div className={cn("flex flex-col h-full", styles.gap)}>
      {/* 紫色色带标题 */}
      <div
        className={cn(
          "rounded-md flex items-center gap-2",
          styles.padding,
          isThumbnail ? "bg-purple-500" : "bg-gradient-to-r from-purple-500 to-violet-600"
        )}
      >
        <span className="text-white text-base">🔀</span>
        <h3 className={cn("text-white truncate", styles.title)}>{title}</h3>
      </div>

      {/* 正文内容 */}
      {parsed.textBodies.length > 0 && (
        <div className={cn("space-y-1", isThumbnail ? "text-[8px]" : "text-xs")}>
          {parsed.textBodies.slice(0, isThumbnail ? 1 : 2).map((text, idx) => (
            <p key={idx} className="text-gray-600 leading-relaxed border-l-2 border-purple-300 pl-2">
              {truncateText(text, maxTextLength)}
            </p>
          ))}
        </div>
      )}

      {/* 列表项 */}
      {parsed.listItems.length > 0 && (
        <div className={cn("flex-1 flex flex-col", styles.gap)}>
          {parsed.listItems.slice(0, maxItems).map((item, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <span className={cn("text-purple-500 flex-shrink-0", isThumbnail ? "text-[8px]" : "text-sm")}>
                ▎
              </span>
              <p className={cn("text-gray-700", styles.bullet)}>
                {truncateText(item, isThumbnail ? 20 : 50)}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* 如果没有 elements，使用 main_points */}
      {!parsed.textBodies.length && !parsed.listItems.length && content.main_points && (
        <div className={cn("flex-1 flex flex-col", styles.gap)}>
          {content.main_points.slice(0, maxItems).map((point, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <span className={cn("text-purple-500 flex-shrink-0", isThumbnail ? "text-[8px]" : "text-sm")}>
                ▎
              </span>
              <p className={cn("text-gray-700", styles.bullet)}>
                {truncateText(point, isThumbnail ? 20 : 50)}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* 融合来源标记（仅预览模式显示） */}
      {!isThumbnail && mergeLabel && (
        <div className="mt-auto pt-2 border-t border-gray-100">
          <span className="text-[10px] text-gray-400">{mergeLabel}</span>
        </div>
      )}
    </div>
  )
}

// ============ ContentTemplate: 内容模板（rewrite） ============

interface ContentTemplateProps {
  content: SlideContent
  isThumbnail: boolean
}

function ContentTemplate({ content, isThumbnail }: ContentTemplateProps) {
  const styles = isThumbnail ? getThumbnailStyles() : getPreviewStyles()
  const maxTitleLength = isThumbnail ? 15 : 40
  const maxContentLength = isThumbnail ? 50 : 200

  const title = truncateText(content.title || "改写内容", maxTitleLength)
  const mainContent = content.main_points?.join("\n") || content.additional_content || ""

  return (
    <div className={cn("flex flex-col h-full", styles.gap)}>
      {/* 标题 */}
      <div className="flex items-center gap-2">
        <span className="text-base">📝</span>
        <h3 className={cn("font-semibold text-gray-800", styles.title)}>{title}</h3>
      </div>

      {/* 正文内容 */}
      <div className="flex-1">
        <p
          className={cn(
            "text-gray-600 leading-relaxed whitespace-pre-wrap",
            styles.body
          )}
        >
          {truncateText(mainContent, maxContentLength)}
        </p>
      </div>
    </div>
  )
}

// ============ 主组件 ============

/**
 * AI 内容渲染器
 * feat-175: 根据 action 类型选择模板，渲染美观的教学幻灯片预览卡片
 */
export function SlideContentRenderer({
  content,
  action,
  slide,
  size = "preview",
  className,
  animated = false,
}: SlideContentRendererProps) {
  const isThumbnail = size === "thumbnail"
  const templateType = selectTemplate(content, action)

  // 选择模板组件
  const renderContent = () => {
    switch (templateType) {
      case "bullet":
        return <BulletTemplate content={content} isThumbnail={isThumbnail} />
      case "knowledge":
        return <KnowledgeTemplate content={content} isThumbnail={isThumbnail} />
      case "merge":
        return <MergeTemplate content={content} slide={slide} isThumbnail={isThumbnail} />
      case "content":
        return <ContentTemplate content={content} isThumbnail={isThumbnail} />
      default:
        return <BulletTemplate content={content} isThumbnail={isThumbnail} />
    }
  }

  // 获取模板类型标签（用于调试）
  const getTemplateLabel = () => {
    switch (templateType) {
      case "bullet":
        return "要点模板"
      case "knowledge":
        return "知识卡片"
      case "merge":
        return "融合模板"
      case "content":
        return "内容模板"
      default:
        return ""
    }
  }

  return (
    <div
      className={cn(
        "bg-white rounded-lg border border-gray-200 overflow-hidden",
        isThumbnail ? "p-2" : "p-4 shadow-sm",
        animated && "transition-all duration-300",
        className
      )}
    >
      {/* 内容区域 */}
      <div className={cn("h-full", isThumbnail ? "min-h-[60px]" : "min-h-[200px]")}>
        {renderContent()}
      </div>

      {/* 底部标记（缩略图模式隐藏） */}
      {!isThumbnail && (
        <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
          <span className="text-[10px] text-gray-400">{getTemplateLabel()}</span>
          {action && (
            <span className="text-[10px] text-indigo-500 font-medium">
              {action === "polish" && "✨ 已润色"}
              {action === "expand" && "📈 已扩展"}
              {action === "rewrite" && "📝 已改写"}
              {action === "extract" && "🎯 已提取"}
              {action === "merge" && "🔀 已融合"}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default SlideContentRenderer