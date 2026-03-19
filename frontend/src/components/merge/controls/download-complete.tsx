/**
 * 下载完成页面组件
 * 显示合并完成的下载链接和操作按钮
 */

"use client"

import { Button } from "@/components/ui/button"

export interface DownloadCompleteProps {
  fileName: string | null
  downloadUrl: string | null
  onDownload: () => void
  onBack: () => void
  onRestart: () => void
}

export function DownloadComplete({
  fileName,
  downloadUrl,
  onDownload,
  onBack,
  onRestart,
}: DownloadCompleteProps) {
  return (
    <div className="max-w-md mx-auto">
      <div className="bg-white border rounded-lg p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">✅ 合并完成！</h2>
        <p className="text-sm text-gray-600 mb-6">
          您的 PPT 已成功生成，点击下方按钮下载文件
        </p>

        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <p className="text-xs text-gray-500 mb-1">文件名</p>
          <p className="text-sm font-medium text-gray-900">{fileName || '智能合并课件.pptx'}</p>
        </div>

        <div className="space-y-3">
          <Button onClick={onDownload} className="w-full" disabled={!downloadUrl}>
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            下载 PPT
          </Button>
          <div className="flex gap-3">
            <Button variant="outline" onClick={onBack} className="flex-1">
              ← 返回上一步
            </Button>
            <Button variant="outline" onClick={onRestart} className="flex-1">
              重新合并
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}