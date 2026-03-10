"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ProcessingProgressProps {
  processed: number
  total: number
  className?: string
}

/**
 * feat-167: 处理进度组件
 *
 * 显示当前处理进度：已处理 N/M 页
 * 包含进度条和文字说明
 */
export function ProcessingProgress({ processed, total, className }: ProcessingProgressProps) {
  // 避免除以零
  if (total === 0) return null

  const percentage = (processed / total) * 100

  return (
    <div className={cn("flex items-center gap-3", className)}>
      {/* 进度条 */}
      <div className="flex items-center gap-2">
        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-600 transition-all duration-300 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        <span className="text-sm text-gray-600 whitespace-nowrap">
          已处理 {processed}/{total} 页
        </span>
      </div>

      {/* 处理完成标记 */}
      {processed === total && processed > 0 && (
        <div className="flex items-center gap-1 text-green-600">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <span className="text-xs font-medium">全部完成</span>
        </div>
      )}
    </div>
  )
}

export default ProcessingProgress