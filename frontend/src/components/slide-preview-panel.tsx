/**
 * 幻灯片预览面板组件
 * feat-171: 显示当前幻灯片的大图预览，支持版本切换和操作
 *
 * 功能：
 * - 大图预览当前幻灯片
 * - 版本切换器（v1, v2, v3...）
 * - 操作按钮（润色、扩展、改写、提取）- 点击注入模板到全局提示词
 * - 添加到最终选择
 */

"use client"

import * as React from "react"
import { useMemo } from "react"
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
} from "@/types/merge-session"
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/ppt-canvas-renderer"
import type { SlideContent } from "@/types/merge-plan"

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

/** 操作配置 - 包含模板提示词 */
const ACTION_CONFIG: Record<SlideAction, { label: string; description: string; icon: string; template: string }> = {
  polish: {
    label: '润色',
    description: '优化文字表达',
    icon: '✨',
    template: '请优化这段内容的文字表达，使语言更加流畅自然、通俗易懂，同时保持教学内容的准确性和完整性。'
  },
  expand: {
    label: '扩展',
    description: '增加细节内容',
    icon: '📈',
    template: '请在保持原有内容基础上，适当增加细节、例子或解释说明，使教学内容更加丰富和完整。'
  },
  rewrite: {
    label: '改写',
    description: '调整语言风格',
    icon: '📝',
    template: '请调整这段内容的语言风格，使其更符合目标学生的认知水平，保持专业性的同时增强可读性。'
  },
  extract: {
    label: '提取',
    description: '提取核心知识点',
    icon: '🎯',
    template: '请提取这段内容的核心知识点，以简洁清晰的方式呈现关键信息，去除冗余内容。'
  },
  merge: {
    label: '融合',
    description: '多页融合',
    icon: '🔀',
    template: ''
  },
  create: {
    label: '创建',
    description: '创建新幻灯片',
    icon: '➕',
    template: ''
  },
}

/**
 * 将 SlideContent 转换为 EnhancedPptPageData
 */
function contentToPageData(content: SlideContent, pageIndex: number): EnhancedPptPageData {
  const mainPoints = content.main_points || []
  const additionalContent = content.additional_content || ''

  return {
    index: pageIndex,
    title: content.title || '',
    content: [...mainPoints, additionalContent].filter(Boolean).map(text => ({
      type: 'text' as const,
      text,
    })),
    shapes: [{
      type: 'text_box',
      name: 'main_content',
      position: { x: 50, y: 100, width: 860, height: 380 },
      text_content: [{
        runs: mainPoints.map(text => ({
          text: text + '\n',
          font: { size: 18, color: '#333333' },
        })),
      }],
    }],
    layout: { width: 960, height: 540 },
  }
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
    <div className="flex items-center gap-1">
      {versions.map((v, idx) => (
        <button
          key={v.version_id}
          type="button"
          onClick={() => onSwitch(v.version_id)}
          disabled={disabled}
          className={cn(
            "px-2 py-1 text-xs font-medium rounded transition-colors",
            v.version_id === currentVersionId
              ? "bg-indigo-100 text-indigo-700"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          v{idx + 1}
        </button>
      ))}
    </div>
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

  // 优先使用外部传入的 URL，其次使用版本中的 preview_url
  const imageUrl = externalImageUrl || version?.preview_url

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
          {/* 版本切换器 */}
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

      {/* 主预览区 */}
      <div className="flex-1 p-4">
        <div className="aspect-video bg-gray-50 rounded-lg overflow-hidden border">
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
          ) : imageUrl ? (
            <img
              src={imageUrl}
              alt={slide.display_title || `幻灯片 ${slide.original_index + 1}`}
              className="w-full h-full object-contain"
            />
          ) : (
            <PptCanvasRenderer
              pageData={contentToPageData(version.content, slide.original_index)}
              width={800}
              height={450}
              quality={1.0}
            />
          )}
        </div>

        {/* 内容摘要 */}
        {version.content.main_points && version.content.main_points.length > 0 && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
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

      {/* 操作面板 */}
      <div className="px-4 py-3 border-t bg-gray-50">
        {/* 处理操作按钮 - 点击选择操作并注入模板 */}
        <div className="mb-3">
          <p className="text-xs text-gray-500 mb-2">选择操作类型</p>
          <div className="grid grid-cols-4 gap-2">
            {(['polish', 'expand', 'rewrite', 'extract'] as SlideAction[]).map((action) => (
              <Button
                key={action}
                variant={selectedAction === action ? "default" : "outline"}
                size="sm"
                onClick={() => handleActionClick(action)}
                disabled={isProcessing}
                title={ACTION_CONFIG[action].template}
                className={cn(
                  "flex flex-col items-center gap-1 h-auto py-2",
                  selectedAction === action && "ring-2 ring-indigo-300"
                )}
              >
                <span className="text-lg">{ACTION_CONFIG[action].icon}</span>
                <span className="text-xs">{ACTION_CONFIG[action].label}</span>
              </Button>
            ))}
          </div>
        </div>

        {/* 执行处理按钮 - 当选择了操作且有提示词时显示 */}
        {selectedAction && globalPrompt && (
          <div className="mb-3">
            <Button
              onClick={handleExecute}
              disabled={isProcessing}
              className="w-full"
            >
              {isProcessing ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  {ACTION_CONFIG[selectedAction]?.label || '处理'}中...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  执行{ACTION_CONFIG[selectedAction]?.label || '处理'}
                </>
              )}
            </Button>
          </div>
        )}

        {/* 最终选择按钮 */}
        <div className="flex gap-2">
          {isInFinalSelection ? (
            <Button
              variant="outline"
              onClick={onRemoveFromFinal}
              disabled={isProcessing}
              className="flex-1"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              从最终选择移除
            </Button>
          ) : (
            <Button
              onClick={onAddToFinal}
              disabled={isProcessing}
              className="flex-1"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              添加到最终选择
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

export default SlidePreviewPanel