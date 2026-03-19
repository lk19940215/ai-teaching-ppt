"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import type { SlideVersion, SlideStatus } from "@/lib/version-api"

interface VersionSwitcherProps {
  /** 当前版本号 */
  currentVersion: string | null
  /** 版本总数 */
  totalVersions: number
  /** 页面状态 */
  slideStatus: SlideStatus
  /** 切换版本回调 */
  onSwitchVersion: (direction: 'prev' | 'next') => void
  /** 打开历史面板回调 */
  onOpenHistory: () => void
  /** 禁用状态 */
  disabled?: boolean
}

/**
 * 版本切换器组件
 * 显示当前版本号，支持前后切换和查看历史
 */
export function VersionSwitcher({
  currentVersion,
  totalVersions,
  slideStatus,
  onSwitchVersion,
  onOpenHistory,
  disabled = false,
}: VersionSwitcherProps) {
  // 解析当前版本号 v1 -> 1
  const currentVersionNum = currentVersion ? parseInt(currentVersion.slice(1)) : 0
  const isDeleted = slideStatus === 'deleted'

  if (isDeleted) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-red-100 border border-red-300 rounded-full text-red-700 text-xs font-medium">
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
        已删除
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1.5">
      {/* 上一页按钮 */}
      <button
        onClick={() => onSwitchVersion('prev')}
        disabled={disabled || currentVersionNum <= 1}
        className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center transition-all",
          currentVersionNum <= 1
            ? "text-gray-300 cursor-not-allowed"
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        )}
      >
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      </button>

      {/* 当前版本号（可点击查看历史） */}
      <button
        onClick={onOpenHistory}
        disabled={disabled}
        className={cn(
          "px-3 py-1 rounded-full text-xs font-medium transition-all",
          "bg-indigo-100 text-indigo-700 hover:bg-indigo-200",
          "flex items-center gap-1.5"
        )}
      >
        <span>{currentVersion || 'v?'}</span>
        <span className="text-indigo-500">/</span>
        <span className="text-indigo-500">v{totalVersions}</span>
        {totalVersions > 1 && (
          <svg className="w-3 h-3 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        )}
      </button>

      {/* 下一页按钮 */}
      <button
        onClick={() => onSwitchVersion('next')}
        disabled={disabled || currentVersionNum >= totalVersions}
        className={cn(
          "w-6 h-6 rounded-full flex items-center justify-center transition-all",
          currentVersionNum >= totalVersions
            ? "text-gray-300 cursor-not-allowed"
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        )}
      >
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
        </svg>
      </button>
    </div>
  )
}

export default VersionSwitcher
