"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import type { MergeMode } from "./merge-mode-selector"

/**
 * 模式引导面板属性
 */
export interface ModeGuidePanelProps {
  mode: MergeMode
  selectedPagesA: number[]
  selectedPagesB: number[]
  className?: string
}

/**
 * 模式引导内容配置
 */
const MODE_GUIDES: Record<MergeMode, {
  title: string
  description: string
  steps: string[]
  icon: React.ReactNode
  highlight: string
}> = {
  full: {
    title: "整体合并",
    description: "将两个 PPT 的所有页面进行智能融合",
    steps: [
      "AI 将分析两个 PPT 的全部内容",
      "自动识别知识点关联和内容重叠",
      "生成优化后的融合方案"
    ],
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    ),
    highlight: "直接点击「开始 AI 融合」即可"
  },
  partial: {
    title: "选择页面融合",
    description: "从两个 PPT 中选择特定页面进行融合",
    steps: [
      "在左侧预览区点击选择要融合的页面",
      "可同时选择 PPT A 和 B 的页面",
      "AI 将对选中页面进行智能融合"
    ],
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
    highlight: "请选择至少一个页面"
  },
  single: {
    title: "单页处理",
    description: "对单个页面进行润色、扩展或改写操作",
    steps: [
      "在左侧预览区点击选择一个页面",
      "选择处理方式：润色/扩展/改写/提取",
      "AI 将对选中页面进行处理"
    ],
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    highlight: "请选择单个页面进行处理"
  }
}

/**
 * 模式引导面板组件
 * feat-160: 根据融合模式显示不同的操作引导
 */
export function ModeGuidePanel({
  mode,
  selectedPagesA,
  selectedPagesB,
  className
}: ModeGuidePanelProps) {
  const guide = MODE_GUIDES[mode]

  // 检查选择状态
  const hasSelection = selectedPagesA.length > 0 || selectedPagesB.length > 0
  const totalSelected = selectedPagesA.length + selectedPagesB.length
  const isSingleSelection = totalSelected === 1

  return (
    <div className={cn("bg-white border rounded-lg p-4", className)}>
      {/* 模式标题和图标 */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
          {guide.icon}
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-900">{guide.title}</h3>
          <p className="text-xs text-gray-500 mt-0.5">{guide.description}</p>
        </div>
      </div>

      {/* 操作步骤 */}
      <div className="space-y-2 mb-4">
        {guide.steps.map((step, index) => (
          <div key={index} className="flex items-start gap-2 text-xs text-gray-600">
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 font-medium">
              {index + 1}
            </span>
            <span className="pt-0.5">{step}</span>
          </div>
        ))}
      </div>

      {/* 高亮提示 */}
      <div className={cn(
        "rounded-lg p-3 text-sm",
        mode === 'full' && "bg-green-50 text-green-700 border border-green-200",
        mode === 'partial' && (hasSelection ? "bg-green-50 text-green-700 border border-green-200" : "bg-amber-50 text-amber-700 border border-amber-200"),
        mode === 'single' && (isSingleSelection ? "bg-green-50 text-green-700 border border-green-200" : "bg-amber-50 text-amber-700 border border-amber-200")
      )}>
        <div className="flex items-center gap-2">
          {(mode === 'partial' && hasSelection) || (mode === 'single' && isSingleSelection) || mode === 'full' ? (
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          )}
          <span>
            {mode === 'full' && guide.highlight}
            {mode === 'partial' && (hasSelection ? `已选择 ${totalSelected} 个页面` : guide.highlight)}
            {mode === 'single' && (isSingleSelection ? "已选择页面，可在下方设置处理方式" : guide.highlight)}
          </span>
        </div>
      </div>

      {/* 已选页面详情 */}
      {mode !== 'full' && hasSelection && (
        <div className="mt-3 pt-3 border-t space-y-2">
          {selectedPagesA.length > 0 && (
            <div className="text-xs">
              <span className="font-medium text-gray-700">PPT A: </span>
              <span className="text-gray-600">
                {selectedPagesA.map(p => `第${p + 1}页`).join("、")}
              </span>
            </div>
          )}
          {selectedPagesB.length > 0 && (
            <div className="text-xs">
              <span className="font-medium text-gray-700">PPT B: </span>
              <span className="text-gray-600">
                {selectedPagesB.map(p => `第${p + 1}页`).join("、")}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ModeGuidePanel