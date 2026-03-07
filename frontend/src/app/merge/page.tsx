"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { apiBaseUrl } from '@/lib/api'
import PptCanvasPreview, { type PptPageData } from '@/components/ppt-canvas-preview'
import PromptEditor from '@/components/prompt-editor'
import { PptxjsRenderer, type PptxjsPageData as PptxjsParsedData } from '@/components/pptxjs-renderer'

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
 * feat-076：集成 PPT 预览组件
 */
export default function MergePage() {
  // A/B PPT 文件状态
  const [pptA, setPptA] = useState<File | null>(null)
  const [pptB, setPptB] = useState<File | null>(null)

  // A/B PPT 页面数据（用于预览）
  const [pptAPages, setPptAPages] = useState<PptPageData[]>([])
  const [pptBPages, setPptBPages] = useState<PptPageData[]>([])

  // A/B PPT 加载状态
  const [isLoadingA, setIsLoadingA] = useState(false)
  const [isLoadingB, setIsLoadingB] = useState(false)

  // A/B PPT 选中的页面索引
  const [selectedPagesA, setSelectedPagesA] = useState<number[]>([])
  const [selectedPagesB, setSelectedPagesB] = useState<number[]>([])

  // 提示语状态
  const [pagePrompts, setPagePrompts] = useState<Record<string, string>>({})
  const [globalPrompt, setGlobalPrompt] = useState("")

  // 生成状态
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [progress, setProgress] = useState(0) // 生成进度 0-100
  const [progressStatus, setProgressStatus] = useState("") // 当前进度状态描述

  // 解析 PPT 文件获取页面数据
  const parsePptFile = async (file: File): Promise<PptPageData[]> => {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${apiBaseUrl}/api/v1/ppt/parse`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error('PPT 解析失败')
    }

    const result = await response.json()
    return result.pages || []
  }

  // 监听 PPT A 文件变化，自动解析
  useEffect(() => {
    if (!pptA) {
      setPptAPages([])
      return
    }

    const loadPptA = async () => {
      setIsLoadingA(true)
      try {
        const pages = await parsePptFile(pptA)
        setPptAPages(pages)
        setSelectedPagesA([]) // 重置选择
      } catch (err) {
        console.error('解析 PPT A 失败:', err)
        setError('解析 PPT A 失败，请重试')
      } finally {
        setIsLoadingA(false)
      }
    }

    loadPptA()
  }, [pptA])

  // 监听 PPT B 文件变化，自动解析
  useEffect(() => {
    if (!pptB) {
      setPptBPages([])
      return
    }

    const loadPptB = async () => {
      setIsLoadingB(true)
      try {
        const pages = await parsePptFile(pptB)
        setPptBPages(pages)
        setSelectedPagesB([]) // 重置选择
      } catch (err) {
        console.error('解析 PPT B 失败:', err)
        setError('解析 PPT B 失败，请重试')
      } finally {
        setIsLoadingB(false)
      }
    }

    loadPptB()
  }, [pptB])

  // 处理页面选择变化（用于后续提示语编辑）
  const handleSelectionChangeA = (selected: number[]) => {
    setSelectedPagesA(selected)
  }

  const handleSelectionChangeB = (selected: number[]) => {
    setSelectedPagesB(selected)
  }

  // 处理合并生成（feat-078）
  const handleMerge = async () => {
    if (!pptA || !pptB) {
      setError("请上传 A/B 两个 PPT 文件")
      return
    }

    // 从 localStorage 获取 LLM 配置
    const llmConfigStr = localStorage.getItem("llm_config")
    if (!llmConfigStr) {
      setError("请先在设置页配置 LLM API Key")
      return
    }

    const llmConfig = JSON.parse(llmConfigStr)
    if (!llmConfig.apiKey) {
      setError("LLM API Key 未配置")
      return
    }

    setIsGenerating(true)
    setError(null)
    setDownloadUrl(null)
    setProgress(0)
    setProgressStatus("准备合并...")

    // 准备 FormData
    const formData = new FormData()
    formData.append("file_a", pptA)
    formData.append("file_b", pptB)

    // 转换 pagePrompts 格式：从 { "A-0": "提示语", "B-1": "提示语" } 转为 { "a_pages": { "1": "提示语" }, "b_pages": { "2": "提示语" } }
    const formattedPrompts: { a_pages: Record<string, string>; b_pages: Record<string, string> } = {
      a_pages: {},
      b_pages: {}
    }
    Object.entries(pagePrompts).forEach(([key, prompt]) => {
      if (!prompt.trim()) return
      const [pptSource, pageIndex] = key.split("-")
      const pageNum = (parseInt(pageIndex) + 1).toString()
      if (pptSource === "A") {
        formattedPrompts.a_pages[pageNum] = prompt
      } else {
        formattedPrompts.b_pages[pageNum] = prompt
      }
    })

    formData.append("page_prompts", JSON.stringify(formattedPrompts))
    formData.append("global_prompt", globalPrompt)
    formData.append("api_key", llmConfig.apiKey)
    formData.append("provider", llmConfig.provider || "deepseek")
    formData.append("title", "智能合并课件")
    formData.append("temperature", "0.3")
    formData.append("max_tokens", "2000")

    // 使用 EventSource 监听 SSE 流
    // 由于 EventSource 不支持 POST + FormData，使用 fetch + ReadableStream
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/smart-merge-stream`, {
        method: "POST",
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "请求失败" }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error("无法读取响应流")
      }

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || "" // 保留不完整行

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6)
            try {
              const event = JSON.parse(dataStr)

              // 更新进度
              if (event.progress) {
                setProgress(event.progress)
              }
              if (event.message) {
                setProgressStatus(event.message)
              }

              // 处理错误
              if (event.stage === "error") {
                setError(event.message || "合并失败")
                setIsGenerating(false)
                return
              }

              // 处理完成
              if (event.stage === "complete" && event.result) {
                setDownloadUrl(`${apiBaseUrl}${event.result.download_url}`)
                setFileName(event.result.file_name)
                setIsGenerating(false)
              }
            } catch (e) {
              console.warn("解析 SSE 事件失败:", e)
            }
          }
        }
      }
    } catch (err: any) {
      console.error("合并失败:", err)
      setError(err.message || "合并失败，请重试")
      setIsGenerating(false)
      setProgress(0)
    }
  }

  // 重置状态
  const handleReset = () => {
    setPptA(null)
    setPptB(null)
    setPptAPages([])
    setPptBPages([])
    setSelectedPagesA([])
    setSelectedPagesB([])
    setPagePrompts({})
    setGlobalPrompt("")
    setError(null)
    setDownloadUrl(null)
    setFileName(null)
    setProgress(0)
    setProgressStatus("")
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

          {/* PPT A 预览组件 */}
          <PptCanvasPreview
            label="PPT A 预览"
            pages={pptAPages}
            isLoading={isLoadingA}
            selectedPages={selectedPagesA}
            onSelectionChange={handleSelectionChangeA}
          />

          {/* PPT B 预览组件 */}
          <PptCanvasPreview
            label="PPT B 预览"
            pages={pptBPages}
            isLoading={isLoadingB}
            selectedPages={selectedPagesB}
            onSelectionChange={handleSelectionChangeB}
          />
        </div>

        {/* 右侧：提示语编辑面板 */}
        <div className="lg:col-span-1">
          <div className="bg-white border rounded-lg p-6 sticky top-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              合并提示语
            </h3>

            {/* 已选页面提示 */}
            {(selectedPagesA.length > 0 || selectedPagesB.length > 0) && (
              <div className="mb-4 p-3 bg-indigo-50 border border-indigo-200 rounded">
                <p className="text-sm font-medium text-indigo-900 mb-2">已选择页面：</p>
                {selectedPagesA.length > 0 && (
                  <p className="text-xs text-indigo-700">
                    PPT A: {selectedPagesA.map(p => `P${p + 1}`).join(", ")}
                  </p>
                )}
                {selectedPagesB.length > 0 && (
                  <p className="text-xs text-indigo-700">
                    PPT B: {selectedPagesB.map(p => `P${p + 1}`).join(", ")}
                  </p>
                )}
              </div>
            )}

            {/* PromptEditor 组件（feat-077） */}
            <PromptEditor
              pagesA={pptAPages}
              pagesB={pptBPages}
              selectedPagesA={selectedPagesA}
              selectedPagesB={selectedPagesB}
              pagePrompts={pagePrompts}
              onPagePromptsChange={setPagePrompts}
              globalPrompt={globalPrompt}
              onGlobalPromptChange={setGlobalPrompt}
              disabled={isGenerating}
            />

            {/* 进度反馈（feat-078） */}
            {isGenerating && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{progressStatus}</span>
                  <span className="font-medium text-indigo-600">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex flex-col gap-3 pt-4 border-t mt-4">
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
