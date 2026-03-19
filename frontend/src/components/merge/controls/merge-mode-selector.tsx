"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export type MergeMode = 'full' | 'partial' | 'single'

export interface MergeModeOption {
  value: MergeMode
  label: string
  description: string
  icon: React.ReactNode
}

export interface MergeModeSelectorProps {
  value: MergeMode
  onChange: (mode: MergeMode) => void
  disabled?: boolean
  className?: string
}

const MERGE_MODES: MergeModeOption[] = [
  {
    value: 'full',
    label: '整体合并',
    description: '将两个 PPT 的所有页面进行智能融合',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
    )
  },
  {
    value: 'partial',
    label: '选择页面融合',
    description: '从两个 PPT 中选择特定页面进行融合',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    )
  },
  {
    value: 'single',
    label: '单页处理',
    description: '对单个页面进行润色、扩展或改写',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    )
  }
]

/**
 * 融合方式选择器组件
 * feat-142: AI 融合交互面板
 */
export function MergeModeSelector({
  value,
  onChange,
  disabled = false,
  className
}: MergeModeSelectorProps) {
  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-col gap-2">
        {MERGE_MODES.map((mode) => (
          <button
            key={mode.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(mode.value)}
            className={cn(
              "flex items-start gap-3 p-4 rounded-lg border-2 transition-all text-left",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              value === mode.value
                ? "border-indigo-500 bg-indigo-50 shadow-sm"
                : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            )}
          >
            <div className={cn(
              "flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center",
              value === mode.value ? "bg-indigo-100 text-indigo-600" : "bg-gray-100 text-gray-500"
            )}>
              {mode.icon}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className={cn(
                  "text-sm font-medium",
                  value === mode.value ? "text-indigo-900" : "text-gray-900"
                )}>
                  {mode.label}
                </span>
                {value === mode.value && (
                  <svg className="w-4 h-4 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <p className={cn(
                "text-xs mt-1",
                value === mode.value ? "text-indigo-700" : "text-gray-500"
              )}>
                {mode.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default MergeModeSelector
