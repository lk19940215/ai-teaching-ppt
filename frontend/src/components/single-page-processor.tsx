"use client"

import * as React from "react"
import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { apiBaseUrl } from "@/lib/api"

// 单页处理动作类型
type SinglePageAction = "polish" | "expand" | "rewrite" | "extract"

// 动作配置
const ACTION_CONFIG: Record<SinglePageAction, { label: string; description: string; icon: string }> = {
  polish: {
    label: "润色",
    description: "优化文字表达，使内容更加流畅自然",
    icon: "✨"
  },
  expand: {
    label: "扩展",
    description: "增加细节、例子或解释，丰富内容",
    icon: "📈"
  },
  rewrite: {
    label: "改写",
    description: "调整语言风格，改变表达方式",
    icon: "📝"
  },
  extract: {
    label: "提取",
    description: "总结关键信息，提取核心知识点",
    icon: "🎯"
  }
}

// 页面数据结构
interface PageData {
  index: number
  title: string
  content: string[]
  slide_type?: string
  teaching_role?: string
}

// 处理结果
interface ProcessingResult {
  action: SinglePageAction
  original_summary: string
  new_content: {
    title: string
    main_points: string[]
    additional_content?: string
  }
  changes: string[]
}

// 组件属性
interface SinglePageProcessorProps {
  // 当前选中的页面（来自 PPT A 或 B）
  pageData: PageData | null
  source: "A" | "B" | null
  sessionId: string | null
  documentId: "ppt_a" | "ppt_b" | null
  // PPT 文件（用于调用 API）
  pptFile: File | null
  // 是否正在处理
  isProcessing?: boolean
  // 回调
  onProcessingStart?: () => void
  onProcessingComplete?: (result: ProcessingResult) => void
  onProcessingError?: (error: string) => void
  onApplyResult?: (result: ProcessingResult) => void
  onCancel?: () => void
}

export function SinglePageProcessor({
  pageData,
  source,
  sessionId,
  documentId,
  pptFile,
  isProcessing: externalProcessing = false,
  onProcessingStart,
  onProcessingComplete,
  onProcessingError,
  onApplyResult,
  onCancel
}: SinglePageProcessorProps) {
  // 当前选中的动作
  const [selectedAction, setSelectedAction] = useState<SinglePageAction | null>(null)
  // 自定义提示语
  const [customPrompt, setCustomPrompt] = useState("")
  // 处理结果
  const [result, setResult] = useState<ProcessingResult | null>(null)
  // 内部处理状态
  const [isProcessing, setIsProcessing] = useState(false)
  // 处理进度
  const [progress, setProgress] = useState<{ stage: string; message: string } | null>(null)

  const processing = isProcessing || externalProcessing

  // 执行单页处理
  const handleProcess = useCallback(async () => {
    if (!selectedAction || !pageData || !pptFile || !source) {
      onProcessingError?.("缺少必要参数")
      return
    }

    setIsProcessing(true)
    setProgress({ stage: "calling", message: "正在调用 AI 处理..." })
    setResult(null)
    onProcessingStart?.()

    const llmConfigStr = localStorage.getItem("llm_config")
    if (!llmConfigStr) {
      setIsProcessing(false)
      setProgress(null)
      onProcessingError?.("请先在设置页配置 LLM API Key")
      return
    }

    const llmConfig = JSON.parse(llmConfigStr)
    if (!llmConfig.apiKey) {
      setIsProcessing(false)
      setProgress(null)
      onProcessingError?.("LLM API Key 未配置")
      return
    }

    const formData = new FormData()
    formData.append("file_a", source === "A" ? pptFile : new File([], "placeholder"))
    formData.append("file_b", source === "B" ? pptFile : new File([], "placeholder"))
    formData.append("merge_type", "single")
    formData.append("single_page_index", pageData.index.toString())
    formData.append("single_page_action", selectedAction)
    formData.append("source_doc", source)
    formData.append("provider", llmConfig.provider || "deepseek")
    formData.append("api_key", llmConfig.apiKey)
    formData.append("temperature", "0.3")
    formData.append("max_tokens", "3000")

    if (customPrompt) {
      formData.append("custom_prompt", customPrompt)
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/ai-merge`, {
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
      let finalResult: ProcessingResult | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6)
            try {
              const event = JSON.parse(dataStr)

              if (event.type === "heartbeat") continue

              if (event.stage) {
                const stageMessages: Record<string, string> = {
                  parsing: "正在解析页面内容...",
                  calling_llm: "正在调用 AI...",
                  thinking: "AI 正在思考...",
                  merging: "正在处理内容...",
                  complete: "处理完成！"
                }
                setProgress({
                  stage: event.stage,
                  message: event.message || stageMessages[event.stage] || "处理中..."
                })
              }

              if (event.stage === "error") {
                throw new Error(event.message || "处理失败")
              }

              if (event.stage === "complete" && event.result) {
                finalResult = event.result as ProcessingResult
              }
            } catch (e) {
              console.warn("解析 SSE 事件失败:", e)
            }
          }
        }
      }

      if (finalResult) {
        setResult(finalResult)
        onProcessingComplete?.(finalResult)
      } else {
        throw new Error("未收到处理结果")
      }
    } catch (err: any) {
      console.error("单页处理失败:", err)
      onProcessingError?.(err.message || "单页处理失败，请重试")
    } finally {
      setIsProcessing(false)
      setProgress(null)
    }
  }, [selectedAction, pageData, pptFile, source, customPrompt, onProcessingStart, onProcessingComplete, onProcessingError])

  // 应用结果
  const handleApply = useCallback(() => {
    if (result) {
      onApplyResult?.(result)
      // 重置状态
      setResult(null)
      setSelectedAction(null)
      setCustomPrompt("")
    }
  }, [result, onApplyResult])

  // 取消并关闭
  const handleCancel = useCallback(() => {
    setResult(null)
    setSelectedAction(null)
    setCustomPrompt("")
    setProgress(null)
    onCancel?.()
  }, [onCancel])

  // 如果没有选中页面，不显示
  if (!pageData) {
    return (
      <div className="bg-gray-50 border rounded-lg p-6 text-center">
        <p className="text-gray-500 text-sm">请在左侧预览区选择一个页面</p>
      </div>
    )
  }

  return (
    <div className="bg-white border rounded-lg overflow-hidden">
      {/* 头部：页面信息 */}
      <div className="px-4 py-3 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-900">
            单页处理：{source} 第 {pageData.index + 1} 页
          </h3>
          <span className="text-xs text-gray-500">
            {pageData.title || "无标题"}
          </span>
        </div>
      </div>

      {/* 处理中状态 */}
      {processing && (
        <div className="p-6 text-center">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-600">{progress?.message || "处理中..."}</p>
        </div>
      )}

      {/* 结果预览 */}
      {!processing && result && (
        <div className="p-4 space-y-4">
          {/* 结果标题 */}
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-green-700 flex items-center gap-2">
              <span className="text-lg">{ACTION_CONFIG[result.action].icon}</span>
              {ACTION_CONFIG[result.action].label}完成
            </h4>
            <button
              onClick={() => setResult(null)}
              className="text-xs text-gray-500 hover:text-gray-700"
            >
              重新处理
            </button>
          </div>

          {/* 对比显示 */}
          <div className="space-y-3">
            {/* 原标题 */}
            <div className="text-xs text-gray-500">原标题：{pageData.title || "无标题"}</div>

            {/* 新标题 */}
            <div className="bg-green-50 border border-green-200 rounded p-3">
              <div className="text-xs text-green-600 font-medium mb-1">处理后标题</div>
              <div className="text-sm text-gray-900 font-medium">{result.new_content.title}</div>
            </div>

            {/* 内容对比 */}
            {result.new_content.main_points.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <div className="text-xs text-blue-600 font-medium mb-2">主要要点</div>
                <ul className="space-y-1">
                  {result.new_content.main_points.map((point, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-blue-500 mt-0.5">•</span>
                      {point}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* 扩展内容 */}
            {result.new_content.additional_content && (
              <div className="bg-amber-50 border border-amber-200 rounded p-3">
                <div className="text-xs text-amber-600 font-medium mb-1">扩展内容</div>
                <div className="text-sm text-gray-700">{result.new_content.additional_content}</div>
              </div>
            )}

            {/* 修改说明 */}
            {result.changes.length > 0 && (
              <div className="text-xs text-gray-500">
                <span className="font-medium">修改说明：</span>
                {result.changes.join("；")}
              </div>
            )}
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 pt-2">
            <Button
              onClick={handleApply}
              className="flex-1"
              size="sm"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              应用结果
            </Button>
            <Button
              variant="outline"
              onClick={handleCancel}
              size="sm"
            >
              取消
            </Button>
          </div>
        </div>
      )}

      {/* 操作选择 */}
      {!processing && !result && (
        <div className="p-4 space-y-4">
          {/* 动作选择 */}
          <div>
            <label className="text-xs font-medium text-gray-700 mb-2 block">选择操作</label>
            <div className="grid grid-cols-2 gap-2">
              {(Object.keys(ACTION_CONFIG) as SinglePageAction[]).map((action) => (
                <button
                  key={action}
                  onClick={() => setSelectedAction(action)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    selectedAction === action
                      ? "border-indigo-500 bg-indigo-50 ring-1 ring-indigo-200"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg">{ACTION_CONFIG[action].icon}</span>
                    <span className={`font-medium text-sm ${
                      selectedAction === action ? "text-indigo-700" : "text-gray-900"
                    }`}>
                      {ACTION_CONFIG[action].label}
                    </span>
                  </div>
                  <p className={`text-xs ${
                    selectedAction === action ? "text-indigo-600" : "text-gray-500"
                  }`}>
                    {ACTION_CONFIG[action].description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* 自定义提示语 */}
          <div>
            <label className="text-xs font-medium text-gray-700 mb-2 block">
              处理要求（可选）
            </label>
            <Textarea
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              placeholder="例如：请用更通俗易懂的语言表达..."
              className="min-h-[60px] text-sm"
            />
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2">
            <Button
              onClick={handleProcess}
              disabled={!selectedAction}
              className="flex-1"
              size="sm"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              {selectedAction ? `开始${ACTION_CONFIG[selectedAction].label}` : "选择操作"}
            </Button>
            <Button
              variant="outline"
              onClick={handleCancel}
              size="sm"
            >
              取消
            </Button>
          </div>

          {/* 当前页面预览 */}
          <div className="border-t pt-4">
            <label className="text-xs font-medium text-gray-500 mb-2 block">当前页面内容</label>
            <div className="bg-gray-50 rounded p-3 text-xs text-gray-600 space-y-1 max-h-32 overflow-y-auto">
              <div className="font-medium">{pageData.title || "无标题"}</div>
              {pageData.content.slice(0, 5).map((text, idx) => (
                <div key={idx} className="truncate">{text}</div>
              ))}
              {pageData.content.length > 5 && (
                <div className="text-gray-400">...还有 {pageData.content.length - 5} 条内容</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SinglePageProcessor
