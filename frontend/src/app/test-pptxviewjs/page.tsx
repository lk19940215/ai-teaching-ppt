"use client"

import * as React from "react"
import { PptxViewJSPreview } from "@/components/pptxviewjs-preview"

/**
 * feat-171: PptxViewJSRenderer 测试页面
 * 验证 PPTX 前端渲染功能
 */

export default function PptxViewJSTestPage() {
  const [fileA, setFileA] = React.useState<File | null>(null)
  const [selectedPages, setSelectedPages] = React.useState<number[]>([])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setFileA(file)
      setSelectedPages([])
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          PptxViewJS 渲染测试
        </h1>

        {/* 上传区域 */}
        <div className="mb-6 bg-white rounded-lg p-4 border">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            上传 PPTX 文件进行测试
          </label>
          <input
            type="file"
            accept=".pptx"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-indigo-50 file:text-indigo-700
              hover:file:bg-indigo-100"
          />
          {fileA && (
            <p className="mt-2 text-sm text-gray-500">
              已选择: {fileA.name} ({(fileA.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>

        {/* 预览区域 */}
        <PptxViewJSPreview
          label="PPT 预览"
          file={fileA}
          selectedPages={selectedPages}
          onSelectionChange={setSelectedPages}
          usePptxViewJS={true}
        />

        {/* 已选页面信息 */}
        {selectedPages.length > 0 && (
          <div className="mt-4 bg-indigo-50 rounded-lg p-4 border border-indigo-200">
            <p className="text-sm text-indigo-700">
              已选择 {selectedPages.length} 页: {selectedPages.sort((a, b) => a - b).map(p => `P${p + 1}`).join(", ")}
            </p>
          </div>
        )}

        {/* 测试说明 */}
        <div className="mt-6 bg-white rounded-lg p-4 border">
          <h2 className="text-lg font-medium text-gray-900 mb-2">测试要点</h2>
          <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
            <li>上传 PPTX 文件后应显示预览</li>
            <li>左右箭头可翻页</li>
            <li>底部缩略图可点击跳转</li>
            <li>点击主预览区可选中/取消选中页面</li>
            <li>页码标签显示正确</li>
          </ul>
        </div>
      </div>
    </div>
  )
}