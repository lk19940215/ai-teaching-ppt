"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { SlideVersion, SlideStatus } from "@/lib/version-api"

interface VersionHistoryPanelProps {
  /** 当前选中的版本 */
  currentVersion: string | null
  /** 版本历史列表 */
  versions: SlideVersion[]
  /** 页面状态 */
  slideStatus: SlideStatus
  /** 页面标签（如 "PPT A - 第 1 页"） */
  pageLabel: string
  /** 是否打开面板 */
  open: boolean
  /** 关闭面板回调 */
  onClose: () => void
  /** 选择版本回调 */
  onSelectVersion: (version: string) => void
  /** 删除/恢复页面回调 */
  onToggleSlide: () => void
  /** 加载中 */
  isLoading?: boolean
}

/**
 * 版本历史面板组件
 * 显示单个页面的所有版本历史，支持切换和恢复
 */
export function VersionHistoryPanel({
  currentVersion,
  versions,
  slideStatus,
  pageLabel,
  open,
  onClose,
  onSelectVersion,
  onToggleSlide,
  isLoading = false,
}: VersionHistoryPanelProps) {
  if (!open) return null

  const isDeleted = slideStatus === 'deleted'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[80vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="text-lg font-medium text-gray-900">
            版本历史 - {pageLabel}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* 内容区域 */}
        <ScrollArea className="h-[60vh] px-4 py-3">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-gray-500 text-sm">加载中...</p>
            </div>
          ) : versions.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              暂无版本历史
            </div>
          ) : (
            <div className="space-y-2">
              {/* 已删除提示 */}
              {isDeleted && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
                  <div className="flex items-center gap-2 text-red-800 text-sm">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <span>此页面已被删除</span>
                  </div>
                </div>
              )}

              {/* 版本列表 */}
              {versions.map((version, idx) => {
                const isCurrent = version.version === currentVersion
                const isLatest = idx === versions.length - 1

                return (
                  <div
                    key={version.version}
                    className={cn(
                      "p-3 border rounded-lg transition-all cursor-pointer",
                      isCurrent
                        ? "bg-indigo-50 border-indigo-300 shadow-sm"
                        : "bg-white border-gray-200 hover:bg-gray-50 hover:border-gray-300"
                    )}
                    onClick={() => !isCurrent && onSelectVersion(version.version)}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        {/* 版本号 + 操作类型 */}
                        <div className="flex items-center gap-2 mb-1">
                          <span className={cn(
                            "text-sm font-medium px-2 py-0.5 rounded",
                            isCurrent
                              ? "bg-indigo-200 text-indigo-800"
                              : "bg-gray-100 text-gray-700"
                          )}>
                            {version.version}
                          </span>
                          <span className="text-xs text-gray-500">
                            {version.operation}
                          </span>
                          {isLatest && !isCurrent && (
                            <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">
                              最新
                            </span>
                          )}
                        </div>

                        {/* 提示语（如果有） */}
                        {version.prompt && (
                          <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                            "{version.prompt}"
                          </p>
                        )}

                        {/* 时间 */}
                        <p className="text-xs text-gray-400 mt-1">
                          {version.created_at}
                        </p>
                      </div>

                      {/* 当前版本标记 */}
                      {isCurrent && (
                        <div className="flex-shrink-0">
                          <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                    </div>

                    {/* 图片预览（如果有） */}
                    {version.image_url && (
                      <div className="mt-2 rounded overflow-hidden border bg-white">
                        <img
                          src={version.image_url}
                          alt={`版本 ${version.version}`}
                          className="w-full h-auto"
                          loading="lazy"
                        />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </ScrollArea>

        {/* 底部操作按钮 */}
        <div className="px-4 py-3 border-t bg-gray-50 flex items-center justify-between">
          <Button
            variant={isDeleted ? "default" : "outline"}
            size="sm"
            onClick={onToggleSlide}
            className={isDeleted ? "bg-red-600 hover:bg-red-700 text-white" : ""}
          >
            {isDeleted ? "恢复页面" : "删除此页"}
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose}>
            关闭
          </Button>
        </div>
      </div>
    </div>
  )
}

export default VersionHistoryPanel
