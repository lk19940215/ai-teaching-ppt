"use client"

import * as React from "react"
import { useState, useCallback, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { apiBaseUrl } from "@/lib/api"
import { requireLLMConfig } from "@/lib/llmConfig"  // feat-240: 从后端获取 LLM 配置
import { PptCanvasRenderer, type EnhancedPptPageData } from "@/components/merge/renderers/ppt-canvas-renderer"

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

/**
 * 将 AI 返回的 new_content 转换为 EnhancedPptPageData 格式
 * 用于 Canvas 模拟渲染
 */
function convertContentToPageData(
  content: { title: string; main_points: string[]; additional_content?: string },
  pageIndex: number
): EnhancedPptPageData {
  const mainPoints = content.main_points || []
  const additionalContent = content.additional_content || ''

  // 构建文本内容
  const allTexts = [...mainPoints]
  if (additionalContent) {
    allTexts.push(additionalContent)
  }

  return {
    index: pageIndex,
    title: content.title || '',
    content: allTexts.map(text => ({ type: 'text' as const, text })),
    shapes: [{
      type: 'text_box',
      name: 'main_content',
      position: { x: 50, y: 100, width: 860, height: 400 },
      text_content: [{
        runs: mainPoints.map(text => ({
          text: text + '\n',
          font: { size: 18, color: '#333333' }
        }))
      }]
    }],
    layout: { width: 960, height: 540 }
  }
}

/**
 * 将原始 PageData 转换为 EnhancedPptPageData 格式
 */
function convertPageDataToEnhanced(pageData: PageData): EnhancedPptPageData {
  return {
    index: pageData.index,
    title: pageData.title || '',
    content: (pageData.content || []).map(text => ({ type: 'text' as const, text })),
    shapes: [{
      type: 'text_box',
      name: 'original_content',
      position: { x: 50, y: 100, width: 860, height: 400 },
      text_content: [{
        runs: (pageData.content || []).map(text => ({
          text: text + '\n',
          font: { size: 18, color: '#333333' }
        }))
      }]
    }],
    layout: { width: 960, height: 540 }
  }
}

// 组件属性
interface SinglePageProcessorProps {
  // 当前选中的页面（来自 PPT A 或 B）
  pageData: PageData | null
  source: "A" | "B" | null
  sessionId: string | null
  documentId: "ppt_a" | "ppt_b" | null
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
  // feat-252: 优化数据流，直接传递已解析的内容
  const handleProcess = useCallback(async () => {
    if (!selectedAction || !pageData || !source) {
      onProcessingError?.("缺少必要参数")
      return
    }

    setIsProcessing(true)
    setProgress({ stage: "calling", message: "正在调用 AI 处理..." })
    setResult(null)
    onProcessingStart?.()

    try {
      // feat-240: 从后端获取 LLM 配置，避免 localStorage 配置丢失
      const llmConfig = await requireLLMConfig()

      // feat-252: 使用已解析的内容，不再传文件
      const slideContent = {
        title: pageData.title || '',
        content: pageData.content || [],
      }

      const requestBody = {
        slide_content: slideContent,
        action: selectedAction,
        custom_prompt: customPrompt || undefined,
        provider: llmConfig.provider || "deepseek",
        api_key: llmConfig.apiKey,
        base_url: llmConfig.baseUrl || undefined,
        model: llmConfig.model || undefined,
        temperature: 0.3,
        max_tokens: 3000,
      }

      setProgress({ stage: "thinking", message: "AI 正在处理..." })

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/ai-merge-single`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "请求失败" }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || "处理失败")
      }

      // 转换结果格式
      const finalResult: ProcessingResult = {
        action: selectedAction,
        original_summary: pageData.title,
        new_content: result.content,
        changes: []
      }

      setResult(finalResult)
      onProcessingComplete?.(finalResult)
    } catch (err: any) {
      console.error("单页处理失败:", err)
      onProcessingError?.(err.message || "单页处理失败，请重试")
    } finally {
      setIsProcessing(false)
      setProgress(null)
    }
  }, [selectedAction, pageData, source, customPrompt, onProcessingStart, onProcessingComplete, onProcessingError])

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

          {/* 版本对比 UI - Canvas 预览 */}
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-3 py-2 border-b text-xs font-medium text-gray-600">
              版本对比预览
            </div>
            <div className="grid grid-cols-2 gap-0.5 bg-gray-200">
              {/* 原始版本 */}
              <div className="bg-white p-2">
                <div className="text-xs text-gray-500 mb-1 text-center">原始版本</div>
                <div className="flex justify-center">
                  <PptCanvasRenderer
                    pageData={convertPageDataToEnhanced(pageData)}
                    width={280}
                    height={158}
                    quality={0.8}
                  />
                </div>
                <div className="text-xs text-gray-400 mt-1 text-center truncate">
                  {pageData.title || "无标题"}
                </div>
              </div>
              {/* 处理后版本 */}
              <div className="bg-white p-2">
                <div className="text-xs text-green-600 mb-1 text-center font-medium">处理后版本</div>
                <div className="flex justify-center">
                  <PptCanvasRenderer
                    pageData={convertContentToPageData(result.new_content, pageData.index)}
                    width={280}
                    height={158}
                    quality={0.8}
                  />
                </div>
                <div className="text-xs text-green-600 mt-1 text-center truncate font-medium">
                  {result.new_content.title || "新标题"}
                </div>
              </div>
            </div>
          </div>

          {/* 文本对比（折叠显示） */}
          <details className="group">
            <summary className="cursor-pointer text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1">
              <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              查看详细文本对比
            </summary>
            <div className="mt-2 space-y-3">
              {/* 新标题 */}
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <div className="text-xs text-green-600 font-medium mb-1">处理后标题</div>
                <div className="text-sm text-gray-900 font-medium">{result.new_content.title}</div>
              </div>

              {/* 内容对比 */}
              {result.new_content.main_points && result.new_content.main_points.length > 0 && (
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
              {result.changes && result.changes.length > 0 && (
                <div className="text-xs text-gray-500">
                  <span className="font-medium">修改说明：</span>
                  {result.changes.join("；")}
                </div>
              )}
            </div>
          </details>

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
