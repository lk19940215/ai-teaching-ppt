"use client"

import * as React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { apiBaseUrl } from '@/lib/api'

// PPT 文件上传区域属性
interface PptUploadAreaProps {
  label: string
  file: File | null
  onFileSelect: (file: File | null) => void
  disabled?: boolean
}

/**
 * PPT 上传区域组件（复用）
 */
function PptUploadArea({ label, file, onFileSelect, disabled = false }: PptUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      // 验证文件类型
      if (!selectedFile.type.includes('presentation') && !selectedFile.name.endsWith('.pptx')) {
        alert('请选择 PPTX 格式文件')
        return
      }
      onFileSelect(selectedFile)
    }
    // 清空 input 值，允许重复选择同一文件
    e.target.value = ''
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    if (disabled) return

    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      if (!droppedFile.type.includes('presentation') && !droppedFile.name.endsWith('.pptx')) {
        alert('请选择 PPTX 格式文件')
        return
      }
      onFileSelect(droppedFile)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleRemove = () => {
    onFileSelect(null)
  }

  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center bg-gray-50 hover:bg-gray-100 transition-colors">
      <Label className="text-sm font-medium text-gray-700 mb-2 block">
        {label}
      </Label>

      {file ? (
        <div className="flex items-center justify-between bg-white border border-gray-200 rounded p-3">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-sm text-gray-600">{file.name}</span>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleRemove}
            disabled={disabled}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            删除
          </Button>
        </div>
      ) : (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`cursor-pointer ${isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300'}`}
        >
          <label className="cursor-pointer">
            <div className="py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                <span className="text-indigo-600 hover:text-indigo-500">点击上传</span> 或拖拽 PPTX 文件到此处
              </p>
              <p className="mt-1 text-xs text-gray-500">
                仅支持 .pptx 格式
              </p>
            </div>
            <input
              type="file"
              accept=".pptx"
              onChange={handleFileChange}
              className="hidden"
              disabled={disabled}
            />
          </label>
        </div>
      )}
    </div>
  )
}

/**
 * 智能合并页面 - 基础框架
 * feat-075：创建 /merge 独立页面
 */
export default function MergePage() {
  // A/B PPT 文件状态
  const [pptA, setPptA] = useState<File | null>(null)
  const [pptB, setPptB] = useState<File | null>(null)

  // 提示语状态（预留，feat-077 实现）
  const [pagePrompts, setPagePrompts] = useState<Record<number, string>>({})
  const [globalPrompt, setGlobalPrompt] = useState("")

  // 生成状态
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)

  // 处理合并生成（预留，feat-078 实现）
  const handleMerge = async () => {
    if (!pptA || !pptB) {
      setError("请上传 A/B 两个 PPT 文件")
      return
    }

    setIsGenerating(true)
    setError(null)

    // TODO: feat-078 实现合并逻辑
    console.log('准备合并:', {
      pptA: pptA.name,
      pptB: pptB.name,
      pagePrompts,
      globalPrompt
    })
  }

  // 重置状态
  const handleReset = () => {
    setPptA(null)
    setPptB(null)
    setPagePrompts({})
    setGlobalPrompt("")
    setError(null)
    setDownloadUrl(null)
  }

  return (
    <div className="max-w-7xl mx-auto px-6">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          PPT 智能合并
        </h1>
        <p className="text-gray-600">
          上传两个 PPT 文件，通过 AI 提示语指导，智能合并生成新的教学课件
        </p>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* 成功下载提示 */}
      {downloadUrl && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 text-sm mb-2">合并成功！</p>
          <a
            href={downloadUrl}
            className="text-indigo-600 hover:underline text-sm font-medium"
            download
          >
            点击下载合并后的 PPT
          </a>
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            className="ml-4"
          >
            重新合并
          </Button>
        </div>
      )}

      {/* 主内容区域：左右布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：PPT 上传和预览区域 */}
        <div className="lg:col-span-2 space-y-4">
          {/* PPT A 上传区域 */}
          <PptUploadArea
            label="PPT A（基础课件）"
            file={pptA}
            onFileSelect={setPptA}
            disabled={isGenerating}
          />

          {/* PPT B 上传区域 */}
          <PptUploadArea
            label="PPT B（补充内容）"
            file={pptB}
            onFileSelect={setPptB}
            disabled={isGenerating}
          />

          {/* TODO: feat-076 实现 PPT 分页预览组件 */}
          <div className="border rounded-lg p-6 bg-white">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              PPT 预览
            </h3>
            <div className="text-center text-gray-500 py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              <p className="mt-2 text-sm">上传 PPT 文件后显示分页预览</p>
              <p className="text-xs text-gray-400 mt-1">（feat-076 实现）</p>
            </div>
          </div>
        </div>

        {/* 右侧：提示语编辑面板 */}
        <div className="lg:col-span-1">
          <div className="bg-white border rounded-lg p-6 sticky top-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              合并提示语
            </h3>

            {/* 页面级提示语列表（预留） */}
            <div className="mb-4">
              <Label className="text-sm font-medium text-gray-700 mb-2 block">
                页面级提示语
              </Label>
              <div className="text-center text-gray-500 py-4 border-2 border-dashed border-gray-200 rounded">
                <p className="text-sm">选择页面后添加提示语</p>
                <p className="text-xs text-gray-400 mt-1">（feat-077 实现）</p>
              </div>
            </div>

            {/* 总提示语输入框 */}
            <div className="mb-4">
              <Label htmlFor="global-prompt" className="text-sm font-medium text-gray-700 mb-2 block">
                总体合并策略
              </Label>
              <textarea
                id="global-prompt"
                value={globalPrompt}
                onChange={(e) => setGlobalPrompt(e.target.value)}
                placeholder="例如：保留 PPT A 的课程结构，将 PPT B 的例题插入到对应知识点..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                disabled={isGenerating}
              />
            </div>

            {/* 操作按钮 */}
            <div className="flex flex-col gap-3 pt-4 border-t">
              <Button
                onClick={handleMerge}
                disabled={!pptA || !pptB || isGenerating}
                className="w-full"
              >
                {isGenerating ? '合并中...' : '开始智能合并'}
              </Button>
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={isGenerating}
              >
                重置
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
