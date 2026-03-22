/**
 * 幻灯片预览面板组件
 * feat-171: 显示当前幻灯片的大图预览，支持版本切换和操作
 * feat-173: 原始版本使用 PptxViewJSRenderer，AI版本使用 PptCanvasRenderer
 * feat-185: PptxViewJSRenderer 降级到 PptCanvasRenderer 的自动切换
 * feat-219: 使用统一的渲染决策工具函数
 *
 * 功能：
 * - 大图预览当前幻灯片
 * - 版本切换器（v1, v2, v3...）
 * - 操作按钮（润色、扩展、改写、提取）- 点击注入模板到全局提示词
 * - 添加到最终选择
 *
 * 渲染优先级（feat-173, feat-185, feat-219）：
 * 1. 有 imageUrl（LibreOffice预览图）→ <img>
 * 2. 是原始版本（无 action）且有 PPT file → PptxViewJSRenderer（失败时降级到 PptCanvasRenderer）
 * 3. 是 AI 版本（有 action）→ SlideContentRenderer
 * 4. 有 content 数据 → PptCanvasRenderer
 * 5. 兜底 → 占位符
 */

"use client"

import * as React from "react"
import { useMemo, useState, useCallback } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import type {
  SlidePoolItem,
  SlideVersion,
  SlideAction,
} from "@/types/merge-session"
import {
  getCurrentVersion,
  getSourceLabel,
  getActionLabel,
  ACTION_CONFIG,
} from "@/types/merge-session"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/merge/renderers/ppt-canvas-renderer"
import { PptxViewJSRenderer } from "@/components/merge/renderers/pptxviewjs-renderer"
import { SlideContentRenderer } from "@/components/merge/renderers/slide-content-renderer"
import type { SlideContent } from "@/types/merge-plan"
import { usePptxFallback } from "@/hooks/use-pptx-fallback"
import {
  getSlideRenderer,
  versionToPageData,
  getPptFile,
  RENDERER_DEFAULTS,
  type RenderDecision,
} from "@/lib/slideRendering"

export interface SlidePreviewPanelProps {
  /** 当前幻灯片 */
  slide: SlidePoolItem | null
  /** 当前版本 */
  version: SlideVersion | null
  /** 预览图片 URL */
  imageUrl?: string
  /** 是否在最终选择中 */
  isInFinalSelection: boolean
  /** 是否正在处理 */
  isProcessing?: boolean
  /** 当前处理动作 */
  currentAction?: SlideAction | null
  /** 处理进度信息 */
  progressInfo?: {
    stage: string
    message: string
    percentage: number
  }
  /** 全局提示词（从父组件传入） */
  globalPrompt?: string
  /** PPT A 文件引用（用于 PptxViewJSRenderer 渲染原始版本）*/
  fileA?: File | null
  /** PPT B 文件引用 */
  fileB?: File | null

  /** 学科 */
  subject?: string
  /** 年级 */
  grade?: string
  /** 学科选项 */
  subjectOptions?: ReadonlyArray<{ value: string; label: string }>
  /** 年级选项 */
  gradeOptions?: ReadonlyArray<{ value: string; label: string }>
  /** 学科变更回调 */
  onSubjectChange?: (subject: string) => void
  /** 年级变更回调 */
  onGradeChange?: (grade: string) => void

  // 回调
  /** 切换版本 */
  onSwitchVersion: (versionId: string) => void
  /** 处理幻灯片 */
  onProcess: (action: SlideAction, prompt?: string) => void
  /** 注入提示词模板到全局输入框 */
  onInjectPrompt?: (prompt: string) => void
  /** 添加到最终选择 */
  onAddToFinal: () => void
  /** 从最终选择移除 */
  onRemoveFromFinal: () => void
  /** 融合选中幻灯片 */
  onMergeSelected?: (slideIds: string[]) => void

  /** 类名 */
  className?: string
}

/**
 * 版本切换器
 */
function VersionSwitcher({
  versions,
  currentVersionId,
  onSwitch,
  disabled,
}: {
  versions: SlideVersion[]
  currentVersionId: string
  onSwitch: (versionId: string) => void
  disabled?: boolean
}) {
  return (
    <select
      value={currentVersionId}
      onChange={(e) => onSwitch(e.target.value)}
      disabled={disabled}
      className={cn(
        "text-xs font-medium bg-white border border-gray-300 rounded-md px-2 py-1 cursor-pointer focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      {versions.map((v, idx) => (
        <option key={v.version_id} value={v.version_id}>
          v{idx + 1}{v.action ? ` (${getActionLabel(v.action)})` : ''}
        </option>
      ))}
    </select>
  )
}

/**
 * 幻灯片预览面板
 */
export function SlidePreviewPanel({
  slide,
  version,
  imageUrl: externalImageUrl,
  isInFinalSelection,
  isProcessing,
  currentAction,
  progressInfo,
  globalPrompt = '',
  fileA,
  fileB,
  subject,
  grade,
  subjectOptions,
  gradeOptions,
  onSubjectChange,
  onGradeChange,
  onSwitchVersion,
  onProcess,
  onInjectPrompt,
  onAddToFinal,
  onRemoveFromFinal,
  onMergeSelected,
  className,
}: SlidePreviewPanelProps) {
  // 当前选中的操作
  const [selectedAction, setSelectedAction] = React.useState<SlideAction | null>(null)

  // 优先使用外部传入的 URL，其次使用版本中的 preview_url
  const imageUrl = externalImageUrl || version?.preview_url

  // feat-185: 获取对应的 PPT 文件
  const pptFile = getPptFile(slide?.original_source, fileA, fileB)

  // feat-185: PptxViewJSRenderer 降级状态
  const { fallbackMode, handlePptxViewJSError } = usePptxFallback({
    resetDeps: [pptFile, slide?.slide_id]
  })

  // feat-219: 使用统一的渲染决策函数
  const renderDecision = useMemo<RenderDecision>(() => {
    return getSlideRenderer({
      slide,
      version,
      imageUrl,
      pptFile,
      fallbackMode,
    })
  }, [slide, version, imageUrl, pptFile, fallbackMode])

  // 处理操作点击 - 设置选中的操作并注入模板
  const handleActionClick = (action: SlideAction) => {
    const template = ACTION_CONFIG[action]?.template
    setSelectedAction(action)
    if (template && onInjectPrompt) {
      // 注入模板到全局输入框
      onInjectPrompt(template)
    }
  }

  // 执行处理
  const handleExecute = () => {
    if (selectedAction) {
      onProcess(selectedAction, globalPrompt || undefined)
    }
  }

  // feat-219: 根据 renderDecision 渲染幻灯片内容
  const renderSlideContent = () => {
    switch (renderDecision.renderer) {
      case "image":
        return (
          <img
            key={imageUrl}
            src={imageUrl!}
            alt={slide?.display_title || `幻灯片 ${(slide?.original_index ?? 0) + 1}`}
            className="w-full h-full object-contain"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none'
            }}
          />
        )

      case "pptxviewjs":
        return (
          <PptxViewJSRenderer
            file={pptFile!}
            slideIndex={slide!.original_index}
            width={RENDERER_DEFAULTS.width}
            height={RENDERER_DEFAULTS.height}
            quality="high"
            onError={handlePptxViewJSError}
          />
        )

      case "pptxviewjs_fallback":
        return (
          <PptCanvasRenderer
            pageData={versionToPageData(version!, slide!.original_index)}
            width={RENDERER_DEFAULTS.width}
            height={RENDERER_DEFAULTS.height}
            quality={RENDERER_DEFAULTS.quality}
          />
        )

      case "slide_content":
        return (
          <SlideContentRenderer
            content={version!.content}
            action={version!.action}
            slide={slide!}
            size="preview"
          />
        )

      case "ppt_canvas":
        return (
          <PptCanvasRenderer
            pageData={versionToPageData(version!, slide!.original_index)}
            width={RENDERER_DEFAULTS.width}
            height={RENDERER_DEFAULTS.height}
            quality={RENDERER_DEFAULTS.quality}
          />
        )

      case "placeholder":
      default:
        return (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            无预览
          </div>
        )
    }
  }

  // 无幻灯片时的提示
  if (!slide || !version) {
    return (
      <div className={cn("bg-gray-50 border rounded-lg p-6 text-center", className)}>
        <svg className="mx-auto h-16 w-16 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        <p className="text-sm text-gray-500">请在左侧幻灯片池中选择一个幻灯片</p>
      </div>
    )
  }

  const sourceLabel = getSourceLabel(slide.original_source)
  const sourceColor =
    slide.original_source === 'ppt_a' ? 'bg-blue-100 text-blue-700' :
    slide.original_source === 'ppt_b' ? 'bg-green-100 text-green-700' :
    slide.original_source === 'merge' ? 'bg-purple-100 text-purple-700' :
    'bg-amber-100 text-amber-700'

  return (
    <div className={cn("bg-white border rounded-lg overflow-hidden flex flex-col", className)}>
      {/* 头部：信息栏 */}
      <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-medium text-gray-900">
            {slide.display_title || `第 ${slide.original_index + 1} 页`}
          </h3>
          <Badge className={cn("text-xs", sourceColor)}>
            {sourceLabel} P{slide.original_index + 1}
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          {slide.versions.length > 1 && (
            <VersionSwitcher
              versions={slide.versions}
              currentVersionId={slide.current_version}
              onSwitch={onSwitchVersion}
              disabled={isProcessing}
            />
          )}
          <span className="text-xs text-gray-500">
            v{slide.versions.findIndex(v => v.version_id === slide.current_version) + 1}/{slide.versions.length}
          </span>
        </div>
      </div>

      {/* 预览区域 */}
      <div className="flex-1 p-4">
        <div key={version.version_id} className="aspect-video bg-gray-50 rounded-lg overflow-hidden border relative group">
          {fallbackMode && (
            <Badge
              variant="outline"
              className="absolute top-2 left-2 bg-amber-100 text-amber-700 border-amber-300 z-10"
            >
              渲染降级：使用简化模式
            </Badge>
          )}

          {isProcessing ? (
            <div className="w-full h-full flex flex-col items-center justify-center">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
              <p className="text-sm text-gray-600">{progressInfo?.message || '处理中...'}</p>
              {progressInfo && (
                <div className="w-48 mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-indigo-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${progressInfo.percentage}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          ) : (
            renderSlideContent()
          )}

          {/* 悬浮操作按钮（居中显示） */}
          {!isProcessing && (
            <div className="absolute inset-x-0 bottom-4 flex justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10">
              {isInFinalSelection ? (
                <button
                  onClick={onRemoveFromFinal}
                  className="flex items-center gap-2 px-5 py-2.5 bg-white/95 border-2 border-red-300 text-red-600 text-sm font-semibold rounded-xl shadow-lg hover:bg-red-50 transition-colors backdrop-blur-sm"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  从最终选择移除
                </button>
              ) : (
                <button
                  onClick={onAddToFinal}
                  className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600/95 text-white text-sm font-semibold rounded-xl shadow-lg hover:bg-indigo-700 transition-colors backdrop-blur-sm"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  添加到最终选择
                </button>
              )}
            </div>
          )}
        </div>

        {/* 内容摘要 */}
        {version.content.main_points && version.content.main_points.length > 0 && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg">
            <h4 className="text-xs font-medium text-gray-700 mb-2">内容摘要</h4>
            <ul className="space-y-1 text-xs text-gray-600">
              {version.content.main_points.slice(0, 5).map((point, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-indigo-500 mt-0.5">•</span>
                  <span className="truncate">{point}</span>
                </li>
              ))}
              {version.content.main_points.length > 5 && (
                <li className="text-gray-400">...还有 {version.content.main_points.length - 5} 条</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

export default SlidePreviewPanel