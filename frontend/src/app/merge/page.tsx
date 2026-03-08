"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { apiBaseUrl } from '@/lib/api'
import PptCanvasPreview, { type PptPageData } from '@/components/ppt-canvas-preview'
import PromptEditor, { type StructuredPagePrompt } from '@/components/prompt-editor'

// PPT 文件上传区域属性
interface PptUploadAreaProps {
  label: string
  file: File | null
  onFileSelect: (file: File | null) => void
  disabled?: boolean
}

// feat-097: 降级模式数据结构
interface FallbackPageData {
  index: number
  title: string
  content: string[]
  shapes?: any[]
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
        // feat-098: 详细的错误提示
        const errorMsg = !selectedFile.name.endsWith('.pptx')
          ? `文件格式错误："${selectedFile.name}" 不是 PPTX 格式，请选择 .pptx 文件`
          : `文件格式错误："${selectedFile.name}" 格式无法识别，请选择 .pptx 文件`
        onFileSelect(null)
        throw new Error(errorMsg)
      }
      // 验证文件大小（20MB 限制）
      const maxSize = 20 * 1024 * 1024
      if (selectedFile.size > maxSize) {
        const sizeMB = (selectedFile.size / 1024 / 1024).toFixed(1)
        throw new Error(`文件大小超出限制：${sizeMB}MB > 20MB，请上传小于 20MB 的文件`)
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
        // feat-098: 详细的错误提示
        const errorMsg = !droppedFile.name.endsWith('.pptx')
          ? `文件格式错误："${droppedFile.name}" 不是 PPTX 格式，请选择 .pptx 文件`
          : `文件格式错误："${droppedFile.name}" 格式无法识别，请选择 .pptx 文件`
        throw new Error(errorMsg)
      }
      // 验证文件大小（20MB 限制）
      const maxSize = 20 * 1024 * 1024
      if (droppedFile.size > maxSize) {
        const sizeMB = (droppedFile.size / 1024 / 1024).toFixed(1)
        throw new Error(`文件大小超出限制：${sizeMB}MB > 20MB，请上传小于 20MB 的文件`)
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

  // feat-097: A/B PPT 降级模式状态
  const [fallbackModeA, setFallbackModeA] = useState(false)
  const [fallbackModeB, setFallbackModeB] = useState(false)
  // feat-097: A/B PPT 降级模式获取的数据
  const [fallbackDataA, setFallbackDataA] = useState<FallbackPageData[]>([])
  const [fallbackDataB, setFallbackDataB] = useState<FallbackPageData[]>([])

  // A/B PPT 选中的页面索引
  const [selectedPagesA, setSelectedPagesA] = useState<number[]>([])
  const [selectedPagesB, setSelectedPagesB] = useState<number[]>([])

  // 提示语状态（结构化：保留/废弃）
  const [pagePrompts, setPagePrompts] = useState<Record<string, StructuredPagePrompt>>({})
  const [globalPrompt, setGlobalPrompt] = useState("")
  // 聚焦状态：记录需要从 Canvas 点击后聚焦到哪个输入框
  const [focusPage, setFocusPage] = useState<{ pptSource: 'A' | 'B'; pageIndex: number } | null>(null)

  // 生成状态
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [progress, setProgress] = useState(0) // 生成进度 0-100
  const [progressStatus, setProgressStatus] = useState("") // 当前进度状态描述

  // 解析 PPT 文件获取页面数据
  const parsePptFile = async (file: File): Promise<PptPageData[]> => {
    // feat-098: 超时检测（30 秒）
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/parse`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // feat-098: 详细的错误处理
      if (!response.ok) {
        // 文件不存在
        if (response.status === 404) {
          throw new Error(`文件 "${file.name}" 无法访问或不存在`)
        }
        // 文件格式不支持
        if (response.status === 415) {
          throw new Error(`文件格式不支持："${file.name}"，仅支持 .pptx 格式`)
        }
        // 文件损坏
        if (response.status === 400) {
          const errorData = await response.json().catch(() => ({ detail: '文件损坏或格式错误' }))
          throw new Error(`文件损坏或无法解析：${errorData.detail || '请检查文件是否完整'}`)
        }
        // 服务器错误
        if (response.status >= 500) {
          throw new Error(`服务器错误（${response.status}）：PPT 解析服务暂时不可用，请稍后重试`)
        }
        // 其他错误
        throw new Error(`PPT 解析失败（HTTP ${response.status}）：${response.statusText}`)
      }

      const result = await response.json()

      // 验证返回数据
      if (!result.pages || !Array.isArray(result.pages)) {
        throw new Error('PPT 解析返回数据格式错误，无法读取页面内容')
      }

      // feat-098: 检测空 PPT
      if (result.pages.length === 0) {
        throw new Error(`PPT 文件 "${file.name}" 中没有检测到页面内容`)
      }

      // 记录到全局性能指标
      const win = window as any
      if (win.perfMetrics) {
        win.perfMetrics.apiEnd = performance.now()
      }

      return result.pages || []
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new Error('PPT 解析超时（30 秒），文件可能过大或网络连接不稳定，请重试')
      }
      // 重新抛出已处理的错误
      throw err
    }
  }

  // feat-097: 从后端获取降级数据（简化模式）
  const fetchFallbackData = async (file: File): Promise<FallbackPageData[]> => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('extract_enhanced', 'false')

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/parse`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        console.error('后端降级数据获取失败:', response.status)
        return []
      }

      const result = await response.json()
      return result.pages || []
    } catch (err) {
      console.error('获取降级数据失败:', err)
      return []
    }
  }

  // feat-097: Canvas 渲染失败回调（切换到降级模式）
  const handleRenderError = async (source: 'A' | 'B', file: File | null, errorMsg: string) => {
    if (!file) return

    console.warn(`${source} PPT Canvas 渲染失败，切换到降级模式：${errorMsg}`)

    // feat-098: 错误分类处理
    const isTimeout = errorMsg.includes('超时') || errorMsg.includes('timeout')
    const isMemoryLow = errorMsg.includes('内存') || errorMsg.includes('memory')
    const isCanvasUnsupported = errorMsg.includes('Canvas') || errorMsg.includes('2D') || errorMsg.includes('上下文')
    const isFormatIncompatible = errorMsg.includes('格式') || errorMsg.includes('compatibility')

    // 设置错误消息
    let message = ''
    if (isTimeout) {
      message = `渲染超时（5 秒），PPT 页面内容过多或浏览器性能不足，已切换到简化渲染模式。建议：关闭其他浏览器标签页释放内存。`
    } else if (isMemoryLow) {
      message = `内存不足，无法渲染此 PPT 页面。建议：关闭其他浏览器标签页，或重启浏览器释放内存后重试。`
    } else if (isCanvasUnsupported) {
      message = `浏览器不支持 Canvas 2D 渲染，已切换到后端解析模式（仅显示文本内容）。建议使用 Chrome、Firefox、Edge 等现代浏览器。`
    } else if (isFormatIncompatible) {
      message = `PPT 格式部分不兼容，某些元素可能无法正确显示。`
    } else {
      message = errorMsg || 'Canvas 渲染失败，已切换到简化模式。'
    }
    setError(message)

    if (source === 'A') {
      setFallbackModeA(true)
      const data = await fetchFallbackData(file)
      setFallbackDataA(data)
    } else {
      setFallbackModeB(true)
      const data = await fetchFallbackData(file)
      setFallbackDataB(data)
    }
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
      } catch (err: any) {
        console.error('解析 PPT A 失败:', err)
        // feat-098: 详细的错误提示
        const errorMsg = err.message || '解析 PPT A 失败，请重试'
        setError(errorMsg)
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
      } catch (err: any) {
        console.error('解析 PPT B 失败:', err)
        // feat-098: 详细的错误提示
        const errorMsg = err.message || '解析 PPT B 失败，请重试'
        setError(errorMsg)
      } finally {
        setIsLoadingB(false)
      }
    }

    loadPptB()
  }, [pptB])

  // 处理页面选择变化（用于后续提示语编辑）
  // 当选中页面时，自动聚焦到对应的提示语输入框
  const handleSelectionChangeA = (selected: number[]) => {
    setSelectedPagesA(selected)
    // 如果是单选（只有一个选中项），设置聚焦
    if (selected.length === 1) {
      const newIndex = selected[0]
      // 只有新增选中时才聚焦
      if (!selectedPagesA.includes(newIndex) || selectedPagesA.length === 1) {
        setFocusPage({ pptSource: 'A', pageIndex: newIndex })
      }
    }
  }

  const handleSelectionChangeB = (selected: number[]) => {
    setSelectedPagesB(selected)
    // 如果是单选（只有一个选中项），设置聚焦
    if (selected.length === 1) {
      const newIndex = selected[0]
      if (!selectedPagesB.includes(newIndex) || selectedPagesB.length === 1) {
        setFocusPage({ pptSource: 'B', pageIndex: newIndex })
      }
    }
  }

  // 当 focusPage 被消费后（PromptEditor 中的 useEffect 会触发），重置聚焦状态
  useEffect(() => {
    if (focusPage) {
      const timer = setTimeout(() => {
        setFocusPage(null)
      }, 500) // 0.5 秒后重置，给用户时间聚焦
      return () => clearTimeout(timer)
    }
  }, [focusPage])

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

    // 转换结构化提示词格式：{ "A-0": { keep, discard } } → { a_pages: { "1": { keep, discard } }, b_pages: {...} }
    const formattedPrompts: { a_pages: Record<string, any>; b_pages: Record<string, any> } = {
      a_pages: {},
      b_pages: {}
    }
    Object.entries(pagePrompts).forEach(([key, prompt]) => {
      if (!prompt.keep?.trim() && !prompt.discard?.trim()) return
      const [pptSource, pageIndex] = key.split("-")
      const pageNum = (parseInt(pageIndex) + 1).toString()
      const structured = {
        keep: prompt.keep?.trim() || "",
        discard: prompt.discard?.trim() || ""
      }
      if (pptSource === "A") {
        formattedPrompts.a_pages[pageNum] = structured
      } else {
        formattedPrompts.b_pages[pageNum] = structured
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

              // 心跳事件：仅更新活跃时间，不处理其他逻辑
              if (event.type === "heartbeat") continue

              // 更新进度
              if (event.progress !== undefined) {
                setProgress(event.progress)
              }

              // 增强进度提示
              let enhancedMessage = event.message || ""
              if (event.stage === "parsing") {
                enhancedMessage = "📚 正在解析 PPT 内容..."
              } else if (event.stage === "calling_llm") {
                enhancedMessage = "🤖 AI 正在分析内容并生成合并策略..."
              } else if (event.stage === "thinking") {
                enhancedMessage = `🧠 ${event.message || 'AI 正在深度分析...'}`
              } else if (event.stage === "merging") {
                enhancedMessage = "🔧 正在根据 AI 策略执行智能合并..."
              } else if (event.stage === "complete") {
                enhancedMessage = "✅ 合并完成！"
              }

              if (enhancedMessage) {
                setProgressStatus(enhancedMessage)
              }

              if (event.stage === "error") {
                setError(event.message || "合并失败")
                setIsGenerating(false)
                return
              }

              if (event.stage === "complete" && event.result) {
                const downloadUrl = event.result.download_url.startsWith('/')
                  ? `${apiBaseUrl}${event.result.download_url}`
                  : `${apiBaseUrl}/${event.result.download_url}`
                setDownloadUrl(downloadUrl)
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

  // 处理下载（优化下载方式，使用 blob）
  const handleDownload = async () => {
    if (!downloadUrl) return

    try {
      console.log('[Download] 开始下载:', downloadUrl)

      const response = await fetch(downloadUrl)
      console.log('[Download] 响应状态:', response.status, 'Content-Type:', response.headers.get('content-type'))

      if (!response.ok) {
        throw new Error(`下载失败: HTTP ${response.status}`)
      }

      const blob = await response.blob()
      console.log('[Download] Blob 信息:', { type: blob.type, size: blob.size })

      // 验证 blob 类型和大小
      if (!blob.type.includes('presentation') && blob.size === 0) {
        console.error('[Download] 警告：下载的文件可能损坏或类型不正确')
      }

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName || `merged_${Date.now()}.pptx`
      document.body.appendChild(a)
      console.log('[Download] 触发下载:', a.download)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      setTimeout(() => {
        setDownloadUrl(null)
        setFileName(null)
      }, 3000)
    } catch (err: any) {
      console.error('[Download] 下载失败:', err)
      setError(`下载失败: ${err.message}`)
    }
  }

  // 重置状态（feat-097: 添加降级模式重置）
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
    // feat-097: 重置降级模式状态
    setFallbackModeA(false)
    setFallbackModeB(false)
    setFallbackDataA([])
    setFallbackDataB([])
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
          <Button
            onClick={handleDownload}
            className="text-sm font-medium"
          >
            📥 点击下载合并后的 PPT
          </Button>
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

          {/* PPT A 单页预览 */}
          <PptCanvasPreview
            label="PPT A 预览"
            pages={fallbackModeA && fallbackDataA.length > 0 ? fallbackDataA : pptAPages}
            isLoading={isLoadingA}
            selectedPages={selectedPagesA}
            onSelectionChange={handleSelectionChangeA}
            pptSource="A"
            fallbackMode={fallbackModeA}
            onFallbackModeChange={(fallback) => {
              setFallbackModeA(fallback)
              if (fallback && pptA) {
                handleRenderError('A', pptA, 'Canvas 渲染失败')
              }
            }}
            file={pptA}
            onRenderError={(error) => {
              handleRenderError('A', pptA, error.message)
            }}
          />

          {/* PPT B 单页预览 */}
          <PptCanvasPreview
            label="PPT B 预览"
            pages={fallbackModeB && fallbackDataB.length > 0 ? fallbackDataB : pptBPages}
            isLoading={isLoadingB}
            selectedPages={selectedPagesB}
            onSelectionChange={handleSelectionChangeB}
            pptSource="B"
            fallbackMode={fallbackModeB}
            onFallbackModeChange={(fallback) => {
              setFallbackModeB(fallback)
              if (fallback && pptB) {
                handleRenderError('B', pptB, 'Canvas 渲染失败')
              }
            }}
            file={pptB}
            onRenderError={(error) => {
              handleRenderError('B', pptB, error.message)
            }}
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
              focusPage={focusPage}
            />

            {/* 进度反馈（脉冲动画防卡死感） */}
            {isGenerating && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                    {progressStatus}
                  </span>
                  <span className="font-medium text-indigo-600">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-500 via-indigo-600 to-indigo-500 h-2 rounded-full transition-all duration-500 relative"
                    style={{ width: `${Math.max(progress, 5)}%`, backgroundSize: '200% 100%', animation: progress < 100 ? 'shimmer 2s infinite' : 'none' }}
                  />
                </div>
                <style jsx>{`
                  @keyframes shimmer {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                  }
                `}</style>
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
