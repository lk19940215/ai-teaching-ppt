/**
 * PPT 智能合并页面 - 重构版
 * feat-171: 基于虚拟幻灯片池的新架构
 *
 * 三栏布局：
 * - 左侧：幻灯片池面板（PPT A/B + 融合结果分组）
 * - 中间：幻灯片预览面板（大图预览 + 版本切换 + 操作按钮）
 * - 右侧：操作面板（最终选择 + 生成按钮）
 *
 * 底部：最终选择栏（拖拽排序）
 */

"use client"

import * as React from "react"
import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { apiBaseUrl } from '@/lib/api'
import { useMergeSession } from '@/hooks/useMergeSession'
import { SlidePoolPanel } from '@/components/slide-pool-panel'
import { SlidePreviewPanel } from '@/components/slide-preview-panel'
import { FinalSelectionBar } from '@/components/final-selection-bar'
import type { SlideAction } from '@/types/merge-session'

// 步骤类型
type Step = 'upload' | 'merge' | 'confirm'

// 提示词模板
const PROMPT_TEMPLATES = [
  {
    id: 'keep-a-structure',
    name: '保留 A 结构',
    icon: '🏗️',
    prompt: '以 PPT A 的课程结构为主框架，将 PPT B 中的补充内容、例题和素材按知识点融入到 A 对应的位置。保持 A 的整体逻辑和教学流程不变。'
  },
  {
    id: 'keep-b-structure',
    name: '保留 B 结构',
    icon: '🔄',
    prompt: '以 PPT B 的课程结构为主框架，将 PPT A 中的补充内容和素材按知识点融入到 B 对应的位置。保持 B 的整体逻辑和教学流程不变。'
  },
  {
    id: 'merge-best',
    name: '取精华合并',
    icon: '⭐',
    prompt: '分析 PPT A 和 PPT B 的内容质量，从两者中选取最优质的部分进行合并：优先保留更详细的知识点讲解、更丰富的例题、更清晰的图表。去除重复和冗余内容。'
  },
  {
    id: 'sequential',
    name: '顺序拼接',
    icon: '📋',
    prompt: '将 PPT A 的所有页面排在前面，PPT B 的页面排在后面。如果发现两者有重复或高度相似的页面，只保留内容更完整的版本。'
  },
]

/**
 * PPT 上传区域组件
 */
function PptUploadArea({
  label,
  description,
  file,
  onFileSelect,
  disabled,
}: {
  label: string
  description: string
  file: File | null
  onFileSelect: (file: File | null) => void
  disabled?: boolean
}) {
  const [isDragging, setIsDragging] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && selectedFile.name.toLowerCase().endsWith('.pptx')) {
      onFileSelect(selectedFile)
    } else if (selectedFile) {
      alert('请选择 .pptx 格式的文件')
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile && droppedFile.name.toLowerCase().endsWith('.pptx')) {
      onFileSelect(droppedFile)
    }
  }

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
            onClick={() => onFileSelect(null)}
            disabled={disabled}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 transition-all cursor-pointer ${
        isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
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
        <p className="text-xs text-gray-500">{description}</p>
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
 * 步骤指示器
 */
function StepIndicator({
  currentStep,
  onStepClick,
}: {
  currentStep: Step
  onStepClick?: (step: Step) => void
}) {
  const steps: { key: Step; label: string }[] = [
    { key: 'upload', label: '上传 PPT' },
    { key: 'merge', label: '合并设置' },
    { key: 'confirm', label: '完成下载' },
  ]

  const getStepStatus = (stepKey: Step) => {
    const order = ['upload', 'merge', 'confirm']
    const current = order.indexOf(currentStep)
    const step = order.indexOf(stepKey)
    if (step < current) return 'completed'
    if (step === current) return 'current'
    return 'pending'
  }

  return (
    <div className="bg-white border rounded-lg p-4 mb-6">
      <div className="flex items-center justify-center gap-4">
        {steps.map((step, index) => {
          const status = getStepStatus(step.key)
          return (
            <React.Fragment key={step.key}>
              <button
                type="button"
                onClick={() => status === 'completed' && onStepClick?.(step.key)}
                disabled={status === 'pending'}
                className={`flex items-center gap-2 ${
                  status === 'completed' ? 'cursor-pointer' : status === 'pending' ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <span
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    status === 'current'
                      ? 'bg-indigo-600 text-white'
                      : status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {status === 'completed' ? '✓' : index + 1}
                </span>
                <span
                  className={`text-sm ${
                    status === 'current' ? 'text-indigo-600 font-medium' : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </button>
              {index < steps.length - 1 && (
                <div className="w-8 h-px bg-gray-200" />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}

/**
 * 下载完成页面
 */
function DownloadComplete({
  fileName,
  downloadUrl,
  onDownload,
  onBack,
  onRestart,
}: {
  fileName: string | null
  downloadUrl: string | null
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
          您的 PPT 已成功生成，点击下方按钮下载文件
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
 * PPT 智能合并页面
 */
export default function MergePage() {
  // 步骤状态
  const [currentStep, setCurrentStep] = useState<Step>('upload')
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)

  // 上传文件状态
  const [pptA, setPptA] = useState<File | null>(null)
  const [pptB, setPptB] = useState<File | null>(null)
  const [isInitializing, setIsInitializing] = useState(false)

  // 全局提示语状态
  const [globalPrompt, setGlobalPrompt] = useState('')
  const [showTemplates, setShowTemplates] = useState(false)

  // 使用新的 Hook
  const {
    session,
    activeSlide,
    activeVersion,
    finalSelectionDetails,
    initSession,
    processSlide,
    mergeSlides,
    selectVersion,
    setActiveSlide,
    addToFinal,
    removeFromFinal,
    reorderFinal,
    generateFinal,
    resetSession,
  } = useMergeSession()

  // 初始化会话
  useEffect(() => {
    if (pptA && pptB && !session.session_id && !isInitializing) {
      setIsInitializing(true)
      setError(null)

      initSession(pptA, pptB)
        .then(() => {
          setCurrentStep('merge')
        })
        .catch((err) => {
          console.error('初始化会话失败:', err)
          setError(err.message || '初始化失败，请重试')
        })
        .finally(() => {
          setIsInitializing(false)
        })
    }
  }, [pptA, pptB, session.session_id, isInitializing, initSession])

  // 处理幻灯片点击
  const handleSlideClick = useCallback((slideId: string) => {
    setActiveSlide(slideId)
  }, [setActiveSlide])

  // 处理版本切换
  const handleSwitchVersion = useCallback((versionId: string) => {
    if (activeSlide) {
      selectVersion(activeSlide.slide_id, versionId)
    }
  }, [activeSlide, selectVersion])

  // 处理幻灯片操作
  const handleProcess = useCallback(async (action: SlideAction, prompt?: string) => {
    if (!activeSlide) return

    // 合并全局提示语和局部提示语
    const finalPrompt = prompt || globalPrompt || undefined

    const result = await processSlide(activeSlide.slide_id, action, finalPrompt)
    if (!result.success) {
      setError(result.error || '处理失败')
    }
  }, [activeSlide, processSlide, globalPrompt])

  // 添加到最终选择
  const handleAddToFinal = useCallback(() => {
    if (activeVersion) {
      addToFinal(activeVersion.version_id)
    }
  }, [activeVersion, addToFinal])

  // 从最终选择移除
  const handleRemoveFromFinal = useCallback(() => {
    if (activeVersion) {
      removeFromFinal(activeVersion.version_id)
    }
  }, [activeVersion, removeFromFinal])

  // 处理跨 PPT 融合
  const handleMergeSelected = useCallback(async (slideIds: string[]) => {
    if (slideIds.length < 2) {
      setError('请选择至少两个幻灯片进行融合')
      return
    }

    const result = await mergeSlides(slideIds, globalPrompt)
    if (!result.success) {
      setError(result.error || '融合失败')
    }
  }, [mergeSlides, globalPrompt])

  // 生成最终 PPT
  const handleGenerateFinal = useCallback(async () => {
    if (session.final_selection.length === 0) {
      setError('请至少选择一个幻灯片')
      return
    }

    try {
      const result = await generateFinal(globalPrompt)
      setDownloadUrl(result.download_url)
      setFileName(result.file_name)
      setCurrentStep('confirm')
    } catch (err: any) {
      console.error('生成最终 PPT 失败:', err)
      setError(err.message || '生成失败')
    }
  }, [session.final_selection, generateFinal, globalPrompt])

  // 下载处理
  const handleDownload = useCallback(async () => {
    if (!downloadUrl) return

    try {
      const response = await fetch(downloadUrl)
      if (!response.ok) throw new Error(`下载失败: HTTP ${response.status}`)

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
  }, [downloadUrl, fileName])

  // 重置状态
  const handleReset = useCallback(() => {
    setPptA(null)
    setPptB(null)
    setError(null)
    setDownloadUrl(null)
    setFileName(null)
    resetSession()
    setCurrentStep('upload')
  }, [resetSession])

  // 步骤回退
  const handleStepClick = useCallback((step: Step) => {
    if (step === 'upload') {
      handleReset()
    } else if (step === 'merge') {
      setCurrentStep('merge')
    }
  }, [handleReset])

  // 检查当前幻灯片是否在最终选择中
  const isInFinalSelection = activeVersion
    ? session.final_selection.includes(activeVersion.version_id)
    : false

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* 页面标题 */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PPT 智能合并</h1>
        <p className="text-gray-600">上传两个 PPT 文件，灵活处理每个页面，自由组合生成新的教学课件</p>
      </div>

      {/* 步骤指示器 */}
      <StepIndicator currentStep={currentStep} onStepClick={handleStepClick} />

      {/* 错误提示 */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <p className="text-red-800 text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Step 1: 上传 PPT */}
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

            {/* 加载状态 */}
            {isInitializing && (
              <div className="text-center py-4">
                <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm text-gray-600">正在解析 PPT 文件...</p>
              </div>
            )}

            {/* 文件信息 */}
            {pptA && pptB && !isInitializing && (
              <div className="text-center text-sm text-gray-500">
                <p>{pptA.name} ({(pptA.size / 1024 / 1024).toFixed(1)} MB) + {pptB.name} ({(pptB.size / 1024 / 1024).toFixed(1)} MB)</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 2: 合并设置 */}
      {currentStep === 'merge' && (
        <div className="space-y-4">
          {/* 顶部控制栏 */}
          <div className="flex items-center justify-between bg-white border rounded-lg px-4 py-3">
            <div className="flex items-center gap-4">
              <Button variant="outline" onClick={() => handleStepClick('upload')} size="sm">
                ← 返回上传
              </Button>
              <span className="text-sm text-gray-500">
                {pptA?.name} + {pptB?.name}
              </span>
            </div>
            <Button onClick={handleReset} variant="outline" size="sm">
              重置
            </Button>
          </div>

          {/* 三栏布局 */}
          <div className="grid grid-cols-12 gap-4">
            {/* 左侧：幻灯片池面板 */}
            <div className="col-span-3">
              <SlidePoolPanel
                slidePool={session.slide_pool}
                activeSlideId={session.active_slide_id}
                finalSelection={session.final_selection}
                onSlideClick={handleSlideClick}
                isProcessing={session.is_processing}
                isMerging={session.active_operation === 'merge'}
                onMergeSelected={handleMergeSelected}
                fileA={session.ppt_a_file}
                fileB={session.ppt_b_file}
              />
            </div>

            {/* 中间：幻灯片预览面板 */}
            <div className="col-span-6">
              <SlidePreviewPanel
                slide={activeSlide}
                version={activeVersion}
                isInFinalSelection={isInFinalSelection}
                isProcessing={session.is_processing}
                currentAction={session.active_operation}
                progressInfo={session.progress_info}
                globalPrompt={globalPrompt}
                fileA={session.ppt_a_file}
                fileB={session.ppt_b_file}
                onSwitchVersion={handleSwitchVersion}
                onProcess={handleProcess}
                onInjectPrompt={setGlobalPrompt}
                onAddToFinal={handleAddToFinal}
                onRemoveFromFinal={handleRemoveFromFinal}
                className="min-h-[600px]"
              />
            </div>

            {/* 右侧：操作面板 */}
            <div className="col-span-3 space-y-4">
              {/* 全局提示语 */}
              <div className="bg-white border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-900">合并策略</h4>
                  <button
                    onClick={() => setShowTemplates(!showTemplates)}
                    className="text-xs text-indigo-600 hover:text-indigo-800"
                  >
                    {showTemplates ? '收起' : '展开模板'}
                  </button>
                </div>

                {/* 模板列表 */}
                {showTemplates && (
                  <div className="space-y-2 mb-3">
                    {PROMPT_TEMPLATES.map(template => (
                      <button
                        key={template.id}
                        onClick={() => setGlobalPrompt(template.prompt)}
                        className={`w-full flex items-center gap-2 p-2 rounded-lg border text-left text-xs transition-all ${
                          globalPrompt === template.prompt
                            ? 'border-indigo-300 bg-indigo-50'
                            : 'border-gray-200 hover:border-indigo-200 hover:bg-gray-50'
                        }`}
                      >
                        <span className="text-base">{template.icon}</span>
                        <span className="font-medium text-gray-900">{template.name}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* 提示语输入 */}
                <Textarea
                  value={globalPrompt}
                  onChange={(e) => setGlobalPrompt(e.target.value)}
                  placeholder="输入合并策略或选择上方模板..."
                  className="min-h-[80px] text-sm"
                />
                <p className="mt-1 text-xs text-gray-400">{globalPrompt.length} 字</p>
              </div>

              {/* 最终选择统计 */}
              <div className="bg-white border rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-3">最终 PPT</h4>
                <div className="text-center py-4">
                  <div className="text-3xl font-bold text-indigo-600 mb-1">
                    {session.final_selection.length}
                  </div>
                  <div className="text-sm text-gray-500">页已选中</div>
                </div>
              </div>

              {/* 使用说明 */}
              <div className="bg-gray-50 border rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">使用说明</h4>
                <ul className="text-xs text-gray-600 space-y-1">
                  <li>1. 点击左侧幻灯片选择</li>
                  <li>2. 在中间面板选择操作类型</li>
                  <li>3. 点击"执行"按钮处理当前页</li>
                  <li>4. 点击"添加到最终选择"</li>
                  <li>5. 底部点击"生成最终 PPT"</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 底部：最终选择栏 */}
          <FinalSelectionBar
            items={finalSelectionDetails}
            onReorder={reorderFinal}
            onRemove={removeFromFinal}
            onGenerate={handleGenerateFinal}
            isGenerating={session.is_processing}
          />
        </div>
      )}

      {/* Step 3: 完成下载 */}
      {currentStep === 'confirm' && (
        <DownloadComplete
          fileName={fileName}
          downloadUrl={downloadUrl}
          onDownload={handleDownload}
          onBack={() => setCurrentStep('merge')}
          onRestart={handleReset}
        />
      )}
    </div>
  )
}