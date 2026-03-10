"use client"

import * as React from "react"
import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { apiBaseUrl } from '@/lib/api'
import PptCanvasPreview, { type PptPageData } from '@/components/ppt-canvas-preview'
import MergeModeSelector, { type MergeMode } from '@/components/merge-mode-selector'
import MergePlanPanel from '@/components/merge-plan-panel'
import MergeResultPreview from '@/components/merge-result-preview'
import SinglePageProcessor from '@/components/single-page-processor'
import PromptEditor, { type StructuredPagePrompt } from '@/components/prompt-editor'
import ModeGuidePanel from '@/components/mode-guide-panel'
import type { MergePlan } from '@/types/merge-plan'
import { createSession } from '@/lib/version-api'

// 步骤类型定义
type Step = 'upload' | 'merge' | 'confirm'

// PPT 文件上传区域属性
interface PptUploadAreaProps {
  label: string
  description: string
  file: File | null
  onFileSelect: (file: File | null) => void
  disabled?: boolean
}

// 降级模式数据结构
interface FallbackPageData {
  index: number
  title: string
  content: string[]
  shapes?: any[]
}

// 复杂元素数据结构
interface ComplexElementWarning {
  has_complex_elements: boolean
  complex_element_types?: string[]
}

interface PptPageDataWithComplex extends PptPageData {
  has_complex_elements?: boolean
  complex_element_types?: string[]
}

/**
 * 步骤指示器组件
 * feat-151: 分步骤向导式交互
 */
function StepIndicator({
  currentStep,
  onStepClick
}: {
  currentStep: Step
  onStepClick?: (step: Step) => void
}) {
  const steps: { key: Step; label: string; description: string }[] = [
    { key: 'upload', label: '① 上传 PPT', description: '上传两个 PPT 文件' },
    { key: 'merge', label: '② 合并设置', description: '配置 AI 融合方式' },
    { key: 'confirm', label: '③ 完成下载', description: '下载合并结果' },
  ]

  const getStepStatus = (stepKey: Step) => {
    const stepOrder = ['upload', 'merge', 'confirm']
    const currentIndex = stepOrder.indexOf(currentStep)
    const stepIndex = stepOrder.indexOf(stepKey)

    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'current'
    return 'pending'
  }

  return (
    <div className="bg-white border rounded-lg p-4 mb-6">
      <div className="flex items-center justify-center">
        {steps.map((step, index) => {
          const status = getStepStatus(step.key)
          const isLast = index === steps.length - 1

          return (
            <React.Fragment key={step.key}>
              {/* 步骤节点 */}
              <button
                type="button"
                onClick={() => status === 'completed' && onStepClick?.(step.key)}
                disabled={status === 'pending'}
                className={`flex flex-col items-center gap-1 transition-all ${
                  status === 'completed' ? 'cursor-pointer hover:opacity-80' : ''
                } ${status === 'pending' ? 'cursor-not-allowed opacity-50' : ''}`}
              >
                <span
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    status === 'current'
                      ? 'bg-indigo-600 text-white'
                      : status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {status === 'completed' ? '✓' : step.label.split(' ')[0]}
                </span>
                <span
                  className={`text-xs ${
                    status === 'current' ? 'text-indigo-600 font-medium' : 'text-gray-500'
                  }`}
                >
                  {step.label.split(' ')[1]}
                </span>
              </button>

              {/* 连接线 */}
              {!isLast && (
                <div className="w-16 h-px mx-2 relative">
                  <div
                    className={`absolute inset-0 transition-colors ${
                      status === 'completed' ? 'bg-green-400' : 'bg-gray-200'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

/**
 * PPT 上传区域组件（feat-151 增强版）
 * 支持拖拽上传和文件信息展示
 */
function PptUploadArea({ label, description, file, onFileSelect, disabled = false }: PptUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      // 验证文件类型
      if (!selectedFile.name.toLowerCase().endsWith('.pptx')) {
        alert('请选择 .pptx 格式的文件')
        return
      }
      onFileSelect(selectedFile)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      if (!droppedFile.name.toLowerCase().endsWith('.pptx')) {
        alert('请选择 .pptx 格式的文件')
        return
      }
      onFileSelect(droppedFile)
    }
  }

  const handleRemove = () => {
    onFileSelect(null)
  }

  // 已上传状态：显示文件信息卡片
  if (file) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1)
    return (
      <div className="border rounded-lg p-4 bg-green-50 border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
              <p className="text-xs text-gray-500">{sizeMB} MB</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            disabled={disabled}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors disabled:opacity-50"
            title="移除文件"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    )
  }

  // 未上传状态：显示上传区域
  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 transition-all ${
        isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => !disabled && document.getElementById(`file-input-${label}`)?.click()}
    >
      <div className="text-center">
        <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="text-sm font-medium text-gray-900 mb-1">{label}</p>
        <p className="text-xs text-gray-500 mb-3">{description}</p>
        <p className="text-xs text-gray-400">点击或拖拽上传 .pptx 文件</p>
        <p className="text-xs text-gray-400">最大 20MB</p>
      </div>
      <input
        id={`file-input-${label}`}
        type="file"
        accept=".pptx"
        className="hidden"
        onChange={handleFileChange}
        disabled={disabled}
      />
    </div>
  )
}

/**
 * 顶部控制条组件（feat-151）
 * 包含 AI 融合方式选择、操作按钮和 AI 合并方案
 * 注：提示语编辑功能已移至右侧 PromptEditor 组件
 */
function TopControlBar({
  mergeMode,
  onMergeModeChange,
  onAiMerge,
  onReset,
  isAiMerging,
  disabled,
  mergePlan,
  adjustedPlan,
  progressInfo,
  onConfirmPlan,
  onCancelPlan,
  onDeletePage,
  onEditPage,
  onReorder,
  onRegeneratePage,
  isRegenerating
}: {
  mergeMode: MergeMode
  onMergeModeChange: (mode: MergeMode) => void
  onAiMerge: () => void
  onReset: () => void
  isAiMerging: boolean
  disabled: boolean
  mergePlan: MergePlan | null
  adjustedPlan?: MergePlan | null
  progressInfo?: { stage: string; message: string; percentage: number }
  onConfirmPlan: () => void
  onCancelPlan: () => void
  onDeletePage?: (index: number) => void
  onEditPage?: (index: number, newContent: string) => void
  onReorder?: (fromIndex: number, toIndex: number) => void
  onRegeneratePage?: (index: number, prompt: string) => void
  isRegenerating?: boolean
}) {
  return (
    <div className="bg-white border rounded-lg p-4 space-y-4">
      {/* 上层：融合方式选择 */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 mb-2">AI 融合方式</h3>
        <MergeModeSelector
          value={mergeMode}
          onChange={onMergeModeChange}
          disabled={isAiMerging || disabled}
        />
      </div>

      {/* 下层：操作按钮 */}
      <div className="flex gap-3">
        <Button
          onClick={onAiMerge}
          disabled={disabled || isAiMerging}
          className="flex-1"
        >
          {isAiMerging ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              AI 融合中...
            </>
          ) : (
            '开始 AI 融合'
          )}
        </Button>
        <Button
          variant="outline"
          onClick={onReset}
          disabled={isAiMerging}
        >
          重置
        </Button>
      </div>

      {/* AI 合并方案面板 */}
      {(mergePlan || isAiMerging) && (
        <div className="pt-4 border-t">
          <h3 className="text-sm font-medium text-gray-900 mb-3">AI 合并方案</h3>
          <MergePlanPanel
            plan={mergePlan}
            adjustedPlan={adjustedPlan || undefined}
            isLoading={isAiMerging}
            progressInfo={progressInfo}
            onConfirm={() => onConfirmPlan()}
            onCancel={onCancelPlan}
            onDeletePage={onDeletePage}
            onEditPage={onEditPage}
            onReorder={onReorder}
            onRegeneratePage={onRegeneratePage}
            isRegenerating={isRegenerating}
          />
        </div>
      )}
    </div>
  )
}

/**
 * 完成下载页面组件（feat-151 Step 3）
 */
function DownloadComplete({
  fileName,
  onDownload,
  onBack,
  onRestart
}: {
  fileName: string | null
  onDownload: () => void
  onBack: () => void
  onRestart: () => void
}) {
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
          您的 PPT 已成功合并，点击下方按钮下载文件
        </p>

        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <p className="text-xs text-gray-500 mb-1">文件名</p>
          <p className="text-sm font-medium text-gray-900">{fileName || '智能合并课件.pptx'}</p>
        </div>

        <div className="space-y-3">
          <Button onClick={onDownload} className="w-full">
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

/**
 * 智能合并页面 - 分步骤向导式交互
 * feat-151: 页面布局重构
 */
export default function MergePage() {
  // ===== 步骤状态 =====
  const [currentStep, setCurrentStep] = useState<Step>('upload')

  // ===== Step 1: 上传状态 =====
  const [pptA, setPptA] = useState<File | null>(null)
  const [pptB, setPptB] = useState<File | null>(null)

  // ===== Step 2: PPT 页面数据和加载状态 =====
  const [pptAPages, setPptAPages] = useState<PptPageDataWithComplex[]>([])
  const [pptBPages, setPptBPages] = useState<PptPageDataWithComplex[]>([])
  const [isLoadingA, setIsLoadingA] = useState(false)
  const [isLoadingB, setIsLoadingB] = useState(false)

  // ===== 降级模式状态 =====
  const [fallbackModeA, setFallbackModeA] = useState(false)
  const [fallbackModeB, setFallbackModeB] = useState(false)
  const [fallbackDataA, setFallbackDataA] = useState<FallbackPageData[]>([])
  const [fallbackDataB, setFallbackDataB] = useState<FallbackPageData[]>([])

  // ===== 复杂元素警告状态 =====
  const [complexElementSlidesA, setComplexElementSlidesA] = useState<number[]>([])
  const [complexElementSlidesB, setComplexElementSlidesB] = useState<number[]>([])
  const [skippedComplexSlidesA, setSkippedComplexSlidesA] = useState<number[]>([])
  const [skippedComplexSlidesB, setSkippedComplexSlidesB] = useState<number[]>([])

  // ===== 页面选择状态 =====
  const [selectedPagesA, setSelectedPagesA] = useState<number[]>([])
  const [selectedPagesB, setSelectedPagesB] = useState<number[]>([])

  // ===== AI 融合相关状态 =====
  const [mergeMode, setMergeMode] = useState<MergeMode>('full')
  const [globalPrompt, setGlobalPrompt] = useState('')
  const [pagePrompts, setPagePrompts] = useState<Record<string, StructuredPagePrompt>>({})
  const [mergePlan, setMergePlan] = useState<MergePlan | null>(null)
  const [adjustedPlan, setAdjustedPlan] = useState<MergePlan | null>(null)
  const [isAiMerging, setIsAiMerging] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [aiMergeProgress, setAiMergeProgress] = useState<{
    stage: string
    message: string
    percentage: number
  } | null>(null)

  // ===== feat-166: 预览图片 URL 状态 =====
  const [slideImageUrlsA, setSlideImageUrlsA] = useState<Record<number, string>>({})
  const [slideImageUrlsB, setSlideImageUrlsB] = useState<Record<number, string>>({})

  // ===== feat-166: 已处理页面版本状态 =====
  const [processedVersionsA, setProcessedVersionsA] = useState<Record<number, string>>({})
  const [processedVersionsB, setProcessedVersionsB] = useState<Record<number, string>>({})

  // ===== feat-162: 重新生成页面状态 =====
  const [isRegenerating, setIsRegenerating] = useState(false)

  // ===== feat-160: 模式切换联动 =====
  // 切换模式时清除不相关的选择状态
  const handleMergeModeChange = useCallback((newMode: MergeMode) => {
    const prevMode = mergeMode
    setMergeMode(newMode)

    // 模式切换时清除选择状态和单页处理面板
    if (prevMode !== newMode) {
      setSelectedPagesA([])
      setSelectedPagesB([])
      setShowSinglePageProcessor(false)
      setSinglePageData(null)
      setSinglePageSource(null)
      setMergePlan(null)
      setAdjustedPlan(null)
    }
  }, [mergeMode])

  // ===== Step 3: 完成状态 =====
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)

  // ===== 解析 PPT 文件获取页面数据 =====
  const parsePptFile = async (file: File): Promise<PptPageDataWithComplex[]> => {
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

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(`文件 "${file.name}" 无法访问或不存在`)
        }
        if (response.status === 415) {
          throw new Error(`文件格式不支持："${file.name}"，仅支持 .pptx 格式`)
        }
        if (response.status === 400) {
          const errorData = await response.json().catch(() => ({ detail: '文件损坏或格式错误' }))
          throw new Error(`文件损坏或无法解析：${errorData.detail || '请检查文件是否完整'}`)
        }
        if (response.status >= 500) {
          throw new Error(`服务器错误（${response.status}）：PPT 解析服务暂时不可用，请稍后重试`)
        }
        throw new Error(`PPT 解析失败（HTTP ${response.status}）：${response.statusText}`)
      }

      const result = await response.json()

      if (!result.pages || !Array.isArray(result.pages)) {
        throw new Error('PPT 解析返回数据格式错误，无法读取页面内容')
      }

      if (result.pages.length === 0) {
        throw new Error(`PPT 文件 "${file.name}" 中没有检测到页面内容`)
      }

      // 提取复杂元素信息
      const complexSlides = result.complex_element_slides || []
      const complexPagesSet = new Set(complexSlides)

      const pagesWithComplex = result.pages.map((page: PptPageData) => ({
        ...page,
        has_complex_elements: complexPagesSet.has(page.index),
        complex_element_types: complexPagesSet.has(page.index) ? ['chart', 'diagram'] : undefined
      }))

      return pagesWithComplex
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw new Error('PPT 解析超时（30 秒），文件可能过大或网络连接不稳定，请重试')
      }
      throw err
    }
  }

  // 获取降级数据
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

  // Canvas 渲染失败回调
  const handleRenderError = async (source: 'A' | 'B', file: File | null, errorMsg: string) => {
    if (!file) return

    console.warn(`${source} PPT Canvas 渲染失败，切换到降级模式：`, errorMsg)

    const isTimeout = errorMsg.includes('超时') || errorMsg.includes('timeout')
    const isMemoryLow = errorMsg.includes('内存') || errorMsg.includes('memory')

    let message = ''
    if (isTimeout) {
      message = `渲染超时（5 秒），PPT 页面内容过多或浏览器性能不足，已切换到简化渲染模式。`
    } else if (isMemoryLow) {
      message = `内存不足，无法渲染此 PPT 页面。建议：关闭其他浏览器标签页释放内存。`
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
      setComplexElementSlidesA([])
      return
    }

    const loadPptA = async () => {
      setIsLoadingA(true)
      try {
        const pages = await parsePptFile(pptA)
        setPptAPages(pages)
        const complexSlides = pages
          .filter(p => p.has_complex_elements)
          .map(p => p.index - 1)
        setComplexElementSlidesA(complexSlides)
        setSelectedPagesA([])
      } catch (err: any) {
        console.error('解析 PPT A 失败:', err)
        setError(err.message || '解析 PPT A 失败，请重试')
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
      setComplexElementSlidesB([])
      return
    }

    const loadPptB = async () => {
      setIsLoadingB(true)
      try {
        const pages = await parsePptFile(pptB)
        setPptBPages(pages)
        const complexSlides = pages
          .filter(p => p.has_complex_elements)
          .map(p => p.index - 1)
        setComplexElementSlidesB(complexSlides)
        setSelectedPagesB([])
      } catch (err: any) {
        console.error('解析 PPT B 失败:', err)
        setError(err.message || '解析 PPT B 失败，请重试')
      } finally {
        setIsLoadingB(false)
      }
    }

    loadPptB()
  }, [pptB])

  // 当两个 PPT 都上传后，创建会话获取图片预览
  useEffect(() => {
    if (!pptA || !pptB || sessionId) return

    const initSession = async () => {
      try {
        console.log('[feat-150] 创建会话...')
        const result = await createSession({ ppt_a: pptA, ppt_b: pptB })
        console.log('[feat-150] 会话创建成功:', result.session_id)
        setSessionId(result.session_id)
      } catch (err) {
        console.error('[feat-150] 创建会话失败:', err)
      }
    }

    initSession()
  }, [pptA, pptB, sessionId])

  // ===== feat-156: 单页处理相关状态 =====
  const [singlePageData, setSinglePageData] = useState<PptPageDataWithComplex | null>(null)
  const [singlePageSource, setSinglePageSource] = useState<'A' | 'B' | null>(null)
  const [isProcessingSingle, setIsProcessingSingle] = useState(false)
  const [showSinglePageProcessor, setShowSinglePageProcessor] = useState(false)

  // upload → merge: 两个 PPT 都上传成功后自动切换
  useEffect(() => {
    if (pptA && pptB && pptAPages.length > 0 && pptBPages.length > 0 && currentStep === 'upload') {
      setCurrentStep('merge')
    }
  }, [pptA, pptB, pptAPages.length, pptBPages.length, currentStep])

  // ===== AI 融合处理 =====
  const handleAiMerge = async () => {
    if (!pptA || !pptB) {
      setError('请上传 A/B 两个 PPT 文件')
      return
    }

    const llmConfigStr = localStorage.getItem('llm_config')
    if (!llmConfigStr) {
      setError('请先在设置页配置 LLM API Key')
      return
    }

    const llmConfig = JSON.parse(llmConfigStr)
    if (!llmConfig.apiKey) {
      setError('LLM API Key 未配置')
      return
    }

    setIsAiMerging(true)
    setError(null)
    setMergePlan(null)
    setAdjustedPlan(null)
    setAiMergeProgress({
      stage: 'parsing',
      message: '正在解析 PPT 内容...',
      percentage: 10
    })

    const formData = new FormData()
    formData.append('file_a', pptA)
    formData.append('file_b', pptB)
    formData.append('merge_type', mergeMode)
    formData.append('provider', llmConfig.provider || 'deepseek')
    formData.append('api_key', llmConfig.apiKey)
    formData.append('temperature', '0.3')
    formData.append('max_tokens', '3000')

    if (mergeMode === 'partial') {
      formData.append('selected_pages_a', selectedPagesA.join(','))
      formData.append('selected_pages_b', selectedPagesB.join(','))
      if (!selectedPagesA.length && !selectedPagesB.length) {
        setError('选择页面融合模式需要至少选择一个页面')
        setIsAiMerging(false)
        setAiMergeProgress(null)
        return
      }
    } else if (mergeMode === 'single') {
      const singlePage = selectedPagesA[0] !== undefined ? selectedPagesA[0] : selectedPagesB[0]
      if (singlePage === undefined) {
        setError('单页处理模式需要选择一个页面')
        setIsAiMerging(false)
        setAiMergeProgress(null)
        return
      }
      formData.append('single_page_index', singlePage.toString())
      formData.append('single_page_action', 'polish')
      formData.append('source_doc', selectedPagesA[0] !== undefined ? 'A' : 'B')
    }

    if (globalPrompt) {
      formData.append('custom_prompt', globalPrompt)
    }

    // 添加页面级提示语（转换为后端格式）
    if (Object.keys(pagePrompts).length > 0) {
      const backendPagePrompts: { a_pages: Record<string, StructuredPagePrompt>; b_pages: Record<string, StructuredPagePrompt> } = {
        a_pages: {},
        b_pages: {}
      }

      Object.entries(pagePrompts).forEach(([key, prompt]) => {
        const [source, pageNum] = key.split('-')
        if (source === 'A') {
          backendPagePrompts.a_pages[pageNum] = prompt
        } else if (source === 'B') {
          backendPagePrompts.b_pages[pageNum] = prompt
        }
      })

      formData.append('page_prompts', JSON.stringify(backendPagePrompts))
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/ai-merge`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const event = JSON.parse(dataStr)

              if (event.type === 'heartbeat') continue

              if (event.stage) {
                const stageProgress: Record<string, number> = {
                  'parsing': 15,
                  'calling_llm': 30,
                  'thinking': 50,
                  'merging': 75,
                  'complete': 100
                }
                setAiMergeProgress({
                  stage: event.stage,
                  message: event.message || getStageMessage(event.stage),
                  percentage: stageProgress[event.stage] || event.progress || 0
                })
              }

              if (event.stage === 'error') {
                setError(event.message || 'AI 融合失败')
                setIsAiMerging(false)
                setAiMergeProgress(null)
                return
              }

              if (event.stage === 'complete' && event.result) {
                setMergePlan(event.result)
                setIsAiMerging(false)
                setAiMergeProgress(null)
              }
            } catch (e) {
              console.warn('解析 SSE 事件失败:', e)
            }
          }
        }
      }
    } catch (err: any) {
      console.error('AI 融合失败:', err)
      setError(err.message || 'AI 融合失败，请重试')
      setIsAiMerging(false)
      setAiMergeProgress(null)
    }
  }

  const getStageMessage = (stage: string): string => {
    const messages: Record<string, string> = {
      'parsing': '📚 正在解析 PPT 内容...',
      'calling_llm': '🤖 AI 正在分析内容并生成合并策略...',
      'thinking': '🧠 AI 正在深度分析...',
      'merging': '🔧 正在执行智能合并...',
      'complete': '✅ 合并完成！'
    }
    return messages[stage] || '处理中...'
  }

  // ===== 确认合并计划 =====
  const handleConfirmPlan = async () => {
    const finalPlan = adjustedPlan || mergePlan
    if (!finalPlan) return

    // TODO: 调用 generate-final API 生成最终 PPT
    // 当前模拟成功状态
    setFileName(`智能合并课件_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.pptx`)
    setCurrentStep('confirm')
  }

  // ===== 下载处理 =====
  const handleDownload = async () => {
    if (!downloadUrl) return

    try {
      const response = await fetch(downloadUrl)
      if (!response.ok) {
        throw new Error(`下载失败: HTTP ${response.status}`)
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fileName || `merged_${Date.now()}.pptx`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('下载失败:', err)
      setError(`下载失败: ${err.message}`)
    }
  }

  // ===== 重置状态 =====
  const handleReset = () => {
    setPptA(null)
    setPptB(null)
    setPptAPages([])
    setPptBPages([])
    setSelectedPagesA([])
    setSelectedPagesB([])
    setGlobalPrompt('')
    setError(null)
    setDownloadUrl(null)
    setFileName(null)
    setFallbackModeA(false)
    setFallbackModeB(false)
    setFallbackDataA([])
    setFallbackDataB([])
    setMergeMode('full')
    setMergePlan(null)
    setAdjustedPlan(null)
    setIsAiMerging(false)
    setSessionId(null)
    setCurrentStep('upload')
  }

  // ===== 步骤回退 =====
  const handleStepClick = (step: Step) => {
    if (step === 'upload') {
      // 回退到上传步骤
      setMergePlan(null)
      setAdjustedPlan(null)
      setCurrentStep('upload')
    } else if (step === 'merge') {
      // 回退到合并设置步骤
      setCurrentStep('merge')
    }
  }

  // ===== 页面选择处理 =====
  const handleSelectionChangeA = (selected: number[]) => {
    setSelectedPagesA(selected)
    // feat-160: 只在单页处理模式下自动显示 SinglePageProcessor
    if (mergeMode === 'single' && selected.length === 1) {
      const pageIndex = selected[0]
      const pageData = pptAPages.find(p => p.index === pageIndex)
      if (pageData) {
        setSinglePageData(pageData)
        setSinglePageSource('A')
        setShowSinglePageProcessor(true)
      }
    } else {
      // 非 single 模式或多选/无选时关闭单页处理面板
      if (singlePageSource === 'A') {
        setShowSinglePageProcessor(false)
        setSinglePageData(null)
        setSinglePageSource(null)
      }
    }
  }

  const handleSelectionChangeB = (selected: number[]) => {
    setSelectedPagesB(selected)
    // feat-160: 只在单页处理模式下自动显示 SinglePageProcessor
    if (mergeMode === 'single' && selected.length === 1) {
      const pageIndex = selected[0]
      const pageData = pptBPages.find(p => p.index === pageIndex)
      if (pageData) {
        setSinglePageData(pageData)
        setSinglePageSource('B')
        setShowSinglePageProcessor(true)
      }
    } else {
      // 非 single 模式或多选/无选时关闭单页处理面板
      if (singlePageSource === 'B') {
        setShowSinglePageProcessor(false)
        setSinglePageData(null)
        setSinglePageSource(null)
      }
    }
  }

  // ===== 合并方案调整 =====
  const handleDeletePage = (index: number) => {
    if (!mergePlan) return
    const updatedPlan: MergePlan = {
      ...mergePlan,
      slide_plan: mergePlan.slide_plan.filter((_, idx) => idx !== index)
    }
    setAdjustedPlan(updatedPlan)
  }

  const handleEditPage = (index: number, newContent: string) => {
    if (!mergePlan) return
    const updatedPlan: MergePlan = {
      ...mergePlan,
      slide_plan: mergePlan.slide_plan.map((item, idx) =>
        idx === index ? { ...item, new_content: newContent } : item
      )
    }
    setAdjustedPlan(updatedPlan)
  }

  const handleReorder = (fromIndex: number, toIndex: number) => {
    if (!mergePlan) return
    const updatedPlan: MergePlan = {
      ...mergePlan,
      slide_plan: [...mergePlan.slide_plan]
    }
    const [removed] = updatedPlan.slide_plan.splice(fromIndex, 1)
    updatedPlan.slide_plan.splice(toIndex, 0, removed)
    setAdjustedPlan(updatedPlan)
  }

  // ===== feat-162: 重新生成页面 =====
  const handleRegeneratePage = async (index: number, prompt: string) => {
    if (!pptA || !pptB || !mergePlan) return

    const llmConfigStr = localStorage.getItem('llm_config')
    if (!llmConfigStr) {
      setError('请先在设置页配置 LLM API Key')
      return
    }

    const llmConfig = JSON.parse(llmConfigStr)
    if (!llmConfig.apiKey) {
      setError('LLM API Key 未配置')
      return
    }

    setIsRegenerating(true)
    setError(null)

    const formData = new FormData()
    formData.append('file_a', pptA)
    formData.append('file_b', pptB)
    formData.append('slide_index', index.toString())
    formData.append('prompt', prompt)
    formData.append('provider', llmConfig.provider || 'deepseek')
    formData.append('api_key', llmConfig.apiKey)
    formData.append('temperature', '0.3')
    formData.append('max_tokens', '2000')

    // 获取当前页的计划信息
    const currentItem = (adjustedPlan || mergePlan).slide_plan[index]
    formData.append('current_action', currentItem?.action || 'keep')
    formData.append('current_content', currentItem?.new_content || '')
    if (currentItem?.source) {
      formData.append('source_doc', currentItem.source)
      formData.append('source_slide_index', (currentItem.slide_index ?? 0).toString())
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/regenerate-slide`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()

      // 更新计划中的对应页面
      const updatedPlan: MergePlan = {
        ...(adjustedPlan || mergePlan),
        slide_plan: (adjustedPlan || mergePlan).slide_plan.map((item, idx) =>
          idx === index ? { ...item, ...result.new_slide } : item
        )
      }
      setAdjustedPlan(updatedPlan)
      console.log('[feat-162] 重新生成成功:', result)
    } catch (err: any) {
      console.error('[feat-162] 重新生成失败:', err)
      setError(err.message || '重新生成失败，请重试')
    } finally {
      setIsRegenerating(false)
    }
  }

  const handleCancelPlan = () => {
    setMergePlan(null)
    setAdjustedPlan(null)
  }

  // ===== feat-156: 单页处理回调 =====
  const handleSinglePageProcessingStart = () => {
    setIsProcessingSingle(true)
  }

  const handleSinglePageProcessingComplete = (result: any) => {
    setIsProcessingSingle(false)
    console.log('[feat-156] 单页处理完成:', result)
  }

  const handleSinglePageProcessingError = (error: string) => {
    setIsProcessingSingle(false)
    setError(error)
  }

  const handleSinglePageApplyResult = async (result: any) => {
    // 应用单页处理结果 - 创建新版本
    if (!sessionId || !singlePageSource || !singlePageData) return

    setIsProcessingSingle(true)
    try {
      const documentId = singlePageSource === 'A' ? 'ppt_a' : 'ppt_b'

      // 调用版本创建 API
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/version/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          document_id: documentId,
          slide_index: singlePageData.index,
          operation: `single_${result.action}`,
          prompt: result.changes?.join('; ') || '单页处理',
          content_snapshot: result.new_content
        })
      })

      if (!response.ok) {
        throw new Error('创建版本失败')
      }

      const versionResult = await response.json()
      console.log('[feat-156] 版本创建成功:', versionResult)

      // feat-166: 更新预览图片 URL 和版本状态
      if (versionResult.image_url) {
        const slideIndex = singlePageData.index
        if (singlePageSource === 'A') {
          setSlideImageUrlsA(prev => ({ ...prev, [slideIndex]: versionResult.image_url }))
          if (versionResult.version) {
            setProcessedVersionsA(prev => ({ ...prev, [slideIndex]: versionResult.version }))
          }
        } else {
          setSlideImageUrlsB(prev => ({ ...prev, [slideIndex]: versionResult.image_url }))
          if (versionResult.version) {
            setProcessedVersionsB(prev => ({ ...prev, [slideIndex]: versionResult.version }))
          }
        }
        console.log(`[feat-166] 已更新 ${singlePageSource} 第 ${slideIndex + 1} 页预览图:`, versionResult.image_url)
      }

      // 重置单页处理状态
      setShowSinglePageProcessor(false)
      setSinglePageData(null)
      setSinglePageSource(null)
      setSelectedPagesA([])
      setSelectedPagesB([])

      // 显示成功提示
      setError(null)
    } catch (err: any) {
      console.error('[feat-156] 应用单页处理结果失败:', err)
      setError(err.message || '应用处理结果失败')
    } finally {
      setIsProcessingSingle(false)
    }
  }

  const handleSinglePageCancel = () => {
    setShowSinglePageProcessor(false)
    setSinglePageData(null)
    setSinglePageSource(null)
    setSelectedPagesA([])
    setSelectedPagesB([])
  }

  // ===== 多页融合处理（feat-155） =====
  const handleMergeSelectedA = (pages: number[]) => {
    // 设置融合模式为 partial 并开始融合
    setMergeMode('partial')
    // 将选中页面设置到 selectedPagesA
    setSelectedPagesA(pages)
    // 如果 B 也有选中页面，一起融合
    handleAiMergeWithPages(pages, selectedPagesB)
  }

  const handleMergeSelectedB = (pages: number[]) => {
    // 设置融合模式为 partial 并开始融合
    setMergeMode('partial')
    // 将选中页面设置到 selectedPagesB
    setSelectedPagesB(pages)
    // 如果 A 也有选中页面，一起融合
    handleAiMergeWithPages(selectedPagesA, pages)
  }

  // 多页融合的统一处理函数
  const handleAiMergeWithPages = async (pagesA: number[], pagesB: number[]) => {
    if (!pptA || !pptB) {
      setError('请上传 A/B 两个 PPT 文件')
      return
    }

    const llmConfigStr = localStorage.getItem('llm_config')
    if (!llmConfigStr) {
      setError('请先在设置页配置 LLM API Key')
      return
    }

    const llmConfig = JSON.parse(llmConfigStr)
    if (!llmConfig.apiKey) {
      setError('LLM API Key 未配置')
      return
    }

    // 检查是否至少选择了一页
    if (pagesA.length === 0 && pagesB.length === 0) {
      setError('请至少选择一个页面进行融合')
      return
    }

    setIsAiMerging(true)
    setError(null)
    setMergePlan(null)
    setAdjustedPlan(null)
    setAiMergeProgress({
      stage: 'parsing',
      message: '正在准备多页融合...',
      percentage: 10
    })

    const formData = new FormData()
    formData.append('file_a', pptA)
    formData.append('file_b', pptB)
    formData.append('merge_type', 'partial')
    formData.append('provider', llmConfig.provider || 'deepseek')
    formData.append('api_key', llmConfig.apiKey)
    formData.append('temperature', '0.3')
    formData.append('max_tokens', '3000')
    formData.append('selected_pages_a', pagesA.join(','))
    formData.append('selected_pages_b', pagesB.join(','))

    if (globalPrompt) {
      formData.append('custom_prompt', globalPrompt)
    }

    // 添加页面级提示语（转换为后端格式）
    if (Object.keys(pagePrompts).length > 0) {
      const backendPagePrompts: { a_pages: Record<string, StructuredPagePrompt>; b_pages: Record<string, StructuredPagePrompt> } = {
        a_pages: {},
        b_pages: {}
      }

      Object.entries(pagePrompts).forEach(([key, prompt]) => {
        const [source, pageNum] = key.split('-')
        if (source === 'A') {
          backendPagePrompts.a_pages[pageNum] = prompt
        } else if (source === 'B') {
          backendPagePrompts.b_pages[pageNum] = prompt
        }
      })

      formData.append('page_prompts', JSON.stringify(backendPagePrompts))
    }

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/ai-merge`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应流')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const event = JSON.parse(dataStr)

              if (event.type === 'heartbeat') continue

              if (event.stage) {
                const stageProgress: Record<string, number> = {
                  'parsing': 15,
                  'calling_llm': 30,
                  'thinking': 50,
                  'merging': 75,
                  'complete': 100
                }
                setAiMergeProgress({
                  stage: event.stage,
                  message: event.message || getStageMessage(event.stage),
                  percentage: stageProgress[event.stage] || event.progress || 0
                })
              }

              if (event.stage === 'error') {
                setError(event.message || '多页融合失败')
                setIsAiMerging(false)
                setAiMergeProgress(null)
                return
              }

              if (event.stage === 'complete' && event.result) {
                // 构建 MergePlan 格式
                const result = event.result
                const mergePlanData: MergePlan = {
                  merge_strategy: result.merge_strategy || '多页融合',
                  summary: result.content_relationship || `融合 PPT A 的 ${pagesA.length} 页和 PPT B 的 ${pagesB.length} 页`,
                  knowledge_points: result.preserved_from_a?.concat(result.preserved_from_b || []) || [],
                  slide_plan: [{
                    action: 'merge',
                    source: pagesA.length > 0 ? 'A' : 'B',
                    slide_index: pagesA[0] || pagesB[0],
                    sources: [
                      ...pagesA.map(p => ({ source: 'A' as const, slide: p })),
                      ...pagesB.map(p => ({ source: 'B' as const, slide: p }))
                    ],
                    new_content: JSON.stringify(result.new_slide),
                    instruction: '多页融合生成',
                    reason: result.merge_strategy
                  }]
                }
                setMergePlan(mergePlanData)
                setIsAiMerging(false)
                setAiMergeProgress(null)
              }
            } catch (e) {
              console.warn('解析 SSE 事件失败:', e)
            }
          }
        }
      }
    } catch (err: any) {
      console.error('多页融合失败:', err)
      setError(err.message || '多页融合失败，请重试')
      setIsAiMerging(false)
      setAiMergeProgress(null)
    }
  }
  const handleToggleSkipComplexSlide = (source: 'A' | 'B', slideIndex: number) => {
    if (source === 'A') {
      setSkippedComplexSlidesA(prev =>
        prev.includes(slideIndex)
          ? prev.filter(i => i !== slideIndex)
          : [...prev, slideIndex]
      )
    } else {
      setSkippedComplexSlidesB(prev =>
        prev.includes(slideIndex)
          ? prev.filter(i => i !== slideIndex)
          : [...prev, slideIndex]
      )
    }
  }

  // ===== 渲染 =====
  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* 页面标题 */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PPT 智能合并</h1>
        <p className="text-gray-600">上传两个 PPT 文件，通过 AI 提示语指导，智能合并生成新的教学课件</p>
      </div>

      {/* 步骤指示器 */}
      <StepIndicator currentStep={currentStep} onStepClick={handleStepClick} />

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* ===== Step 1: 上传 PPT ===== */}
      {currentStep === 'upload' && (
        <div className="max-w-2xl mx-auto">
          <div className="bg-white border rounded-lg p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">上传 PPT 文件</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <PptUploadArea
                label="PPT A（基础课件）"
                description="上传主要教学内容的 PPT"
                file={pptA}
                onFileSelect={setPptA}
              />
              <PptUploadArea
                label="PPT B（补充内容）"
                description="上传补充例题或扩展内容的 PPT"
                file={pptB}
                onFileSelect={setPptB}
              />
            </div>

            {/* 上传进度和提示 */}
            {(isLoadingA || isLoadingB) && (
              <div className="text-center py-4">
                <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm text-gray-600">
                  {isLoadingA && isLoadingB ? '正在解析两个 PPT...' :
                   isLoadingA ? '正在解析 PPT A...' : '正在解析 PPT B...'}
                </p>
              </div>
            )}

            {pptA && pptB && !isLoadingA && !isLoadingB && (
              <div className="text-center">
                <Button onClick={() => setCurrentStep('merge')} className="px-8">
                  下一步：合并设置 →
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ===== Step 2: 合并设置 + 预览 + 方案 ===== */}
      {currentStep === 'merge' && (
        <div className="space-y-6">
          {/* 返回按钮 */}
          <div className="flex items-center justify-between">
            <Button variant="outline" onClick={() => handleStepClick('upload')} size="sm">
              ← 返回上传
            </Button>
            <span className="text-sm text-gray-500">
              {pptA?.name} + {pptB?.name}
            </span>
          </div>

          {/* 顶部控制条 */}
          <TopControlBar
            mergeMode={mergeMode}
            onMergeModeChange={handleMergeModeChange}
            onAiMerge={handleAiMerge}
            onReset={handleReset}
            isAiMerging={isAiMerging}
            disabled={!pptA || !pptB}
            mergePlan={mergePlan}
            adjustedPlan={adjustedPlan}
            progressInfo={aiMergeProgress || undefined}
            onConfirmPlan={handleConfirmPlan}
            onCancelPlan={handleCancelPlan}
            onDeletePage={handleDeletePage}
            onEditPage={handleEditPage}
            onReorder={handleReorder}
            onRegeneratePage={handleRegeneratePage}
            isRegenerating={isRegenerating}
          />

          {/* 主内容区域：左右布局 */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 左侧：PPT 预览区域 */}
            <div className="lg:col-span-2 space-y-4">
              {/* 复杂元素警告 */}
              {complexElementSlidesA.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-amber-900 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    PPT A 包含复杂元素页面
                  </h4>
                  <p className="text-xs text-amber-700 mb-2">
                    以下页面包含图表或 SmartArt，无法进行 AI 内容级合并，只能整页保留或跳过：
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {complexElementSlidesA.map(slideIndex => {
                      const pageNum = slideIndex + 1
                      const isSkipped = skippedComplexSlidesA.includes(slideIndex)
                      return (
                        <button
                          key={slideIndex}
                          onClick={() => handleToggleSkipComplexSlide('A', slideIndex)}
                          className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                            isSkipped
                              ? 'bg-gray-300 text-gray-700 line-through'
                              : 'bg-amber-200 text-amber-900 hover:bg-amber-300'
                          }`}
                          title={isSkipped ? '点击恢复保留' : '点击跳过此页'}
                        >
                          第{pageNum}页 {isSkipped ? '×' : '✓'}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {complexElementSlidesB.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-amber-900 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    PPT B 包含复杂元素页面
                  </h4>
                  <p className="text-xs text-amber-700 mb-2">
                    以下页面包含图表或 SmartArt，无法进行 AI 内容级合并，只能整页保留或跳过：
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {complexElementSlidesB.map(slideIndex => {
                      const pageNum = slideIndex + 1
                      const isSkipped = skippedComplexSlidesB.includes(slideIndex)
                      return (
                        <button
                          key={slideIndex}
                          onClick={() => handleToggleSkipComplexSlide('B', slideIndex)}
                          className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                            isSkipped
                              ? 'bg-gray-300 text-gray-700 line-through'
                              : 'bg-amber-200 text-amber-900 hover:bg-amber-300'
                          }`}
                          title={isSkipped ? '点击恢复保留' : '点击跳过此页'}
                        >
                          第{pageNum}页 {isSkipped ? '×' : '✓'}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* PPT A 预览 */}
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
                onRenderError={(error) => handleRenderError('A', pptA, error.message)}
                sessionId={sessionId || undefined}
                documentId="ppt_a"
                enableVersioning={!!sessionId}
                // feat-155: 多页融合功能
                onMergeSelected={handleMergeSelectedA}
                isMerging={isAiMerging}
                partnerSelectedPages={selectedPagesB}
                partnerLabel="PPT B"
              />

              {/* PPT B 预览 */}
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
                onRenderError={(error) => handleRenderError('B', pptB, error.message)}
                sessionId={sessionId || undefined}
                documentId="ppt_b"
                enableVersioning={!!sessionId}
                // feat-155: 多页融合功能
                onMergeSelected={handleMergeSelectedB}
                isMerging={isAiMerging}
                partnerSelectedPages={selectedPagesA}
                partnerLabel="PPT A"
              />
            </div>

            {/* 右侧：AI 方案面板 / 单页处理面板 */}
            <div className="lg:col-span-1 space-y-4">
              {/* feat-160: 模式引导面板（非单页处理时显示） */}
              {!showSinglePageProcessor && (
                <ModeGuidePanel
                  mode={mergeMode}
                  selectedPagesA={selectedPagesA}
                  selectedPagesB={selectedPagesB}
                />
              )}

              {/* feat-156: 单页处理面板 */}
              {showSinglePageProcessor && singlePageData && singlePageSource && (
                <SinglePageProcessor
                  pageData={singlePageData}
                  source={singlePageSource}
                  sessionId={sessionId}
                  documentId={singlePageSource === 'A' ? 'ppt_a' : 'ppt_b'}
                  pptFile={singlePageSource === 'A' ? pptA : pptB}
                  isProcessing={isProcessingSingle}
                  onProcessingStart={handleSinglePageProcessingStart}
                  onProcessingComplete={handleSinglePageProcessingComplete}
                  onProcessingError={handleSinglePageProcessingError}
                  onApplyResult={handleSinglePageApplyResult}
                  onCancel={handleSinglePageCancel}
                />
              )}

              {/* 页面级提示语编辑器 */}
              <div className="bg-white border rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">提示语设置</h3>
                <PromptEditor
                  pagesA={pptAPages}
                  pagesB={pptBPages}
                  selectedPagesA={selectedPagesA}
                  selectedPagesB={selectedPagesB}
                  pagePrompts={pagePrompts}
                  onPagePromptsChange={setPagePrompts}
                  globalPrompt={globalPrompt}
                  onGlobalPromptChange={setGlobalPrompt}
                  disabled={isAiMerging}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===== Step 3: 合并结果预览 ===== */}
      {currentStep === 'confirm' && (
        <MergeResultPreview
          mergePlan={adjustedPlan || mergePlan}
          pptAPages={pptAPages}
          pptBPages={pptBPages}
          pptAImageUrls={slideImageUrlsA}
          pptBImageUrls={slideImageUrlsB}
          fileName={fileName}
          downloadUrl={downloadUrl}
          onDownload={handleDownload}
          onRegenerate={handleAiMerge}
          onReorder={(newPlan) => setAdjustedPlan(newPlan)}
          onBack={() => handleStepClick('merge')}
          onRestart={handleReset}
        />
      )}
    </div>
  )
}
