/**
 * MergePage 页面状态管理 Hook
 * 管理步骤状态、文件上传、全局提示语、下载状态等页面级状态
 */

import { useState, useCallback, useEffect } from 'react'
import { useMergeSession } from '@/hooks/useMergeSession'
import type { SlideAction } from '@/types/merge-session'

// 步骤类型
export type Step = 'upload' | 'merge' | 'confirm'

/** 学科选项 */
export const SUBJECT_OPTIONS = [
  { value: '_default', label: '通用' },
  { value: 'english_teaching', label: '英语' },
] as const

/** 年级选项 */
export const GRADE_OPTIONS = [
  { value: '', label: '不限' },
  { value: '一年级', label: '一年级' },
  { value: '二年级', label: '二年级' },
  { value: '三年级', label: '三年级' },
  { value: '四年级', label: '四年级' },
  { value: '五年级', label: '五年级' },
  { value: '六年级', label: '六年级' },
  { value: '七年级', label: '七年级' },
  { value: '八年级', label: '八年级' },
  { value: '九年级', label: '九年级' },
  { value: '高一', label: '高一' },
  { value: '高二', label: '高二' },
  { value: '高三', label: '高三' },
] as const

export interface UseMergePageReturn {
  // 步骤状态
  currentStep: Step
  setCurrentStep: (step: Step) => void

  // 文件状态
  pptA: File | null
  pptB: File | null
  setPptA: (file: File | null) => void
  setPptB: (file: File | null) => void
  isInitializing: boolean

  // 错误状态
  error: string | null
  setError: (error: string | null) => void

  // 全局提示语
  globalPrompt: string
  setGlobalPrompt: (prompt: string) => void
  showTemplates: boolean
  setShowTemplates: (show: boolean) => void

  // 学科/年级
  subject: string
  setSubject: (subject: string) => void
  grade: string
  setGrade: (grade: string) => void

  // 下载状态
  downloadUrl: string | null
  fileName: string | null

  // 会话状态（来自 useMergeSession）
  session: ReturnType<typeof useMergeSession>['session']
  activeSlide: ReturnType<typeof useMergeSession>['activeSlide']
  activeVersion: ReturnType<typeof useMergeSession>['activeVersion']
  finalSelectionDetails: ReturnType<typeof useMergeSession>['finalSelectionDetails']
  isInFinalSelection: boolean

  // 操作方法
  handleSlideClick: (slideId: string) => void
  handleSwitchVersion: (versionId: string) => void
  handleProcess: (action: SlideAction, prompt?: string) => Promise<void>
  handleBatchProcess: (slideIds: string[], action: SlideAction) => Promise<void>
  handleAddToFinal: () => void
  handleRemoveFromFinal: () => void
  addToFinal: (versionId: string) => void
  removeFromFinal: (versionId: string) => void
  handleMergeSelected: (slideIds: string[]) => Promise<void>
  handleGenerateFinal: () => Promise<void>
  handleDownload: () => Promise<void>
  handleReset: () => void
  handleStepClick: (step: Step) => void
  reorderFinal: (fromIndex: number, toIndex: number) => void
}

export function useMergePage(): UseMergePageReturn {
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

  // 学科/年级
  const [subject, setSubject] = useState('_default')
  const [grade, setGrade] = useState('')

  // 使用会话 Hook
  const {
    session,
    activeSlide,
    activeVersion,
    finalSelectionDetails,
    initSession,
    processSlide,
    batchProcessSlides,
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
    let finalPrompt = prompt || globalPrompt || undefined

    // 注入年级上下文
    if (grade && finalPrompt) {
      finalPrompt = `当前年级：${grade}。${finalPrompt}`
    } else if (grade) {
      finalPrompt = `当前年级：${grade}`
    }

    const domain = subject === '_default' ? undefined : subject
    const result = await processSlide(activeSlide.slide_id, action, finalPrompt, domain)
    if (!result.success) {
      setError(result.error || '处理失败')
    }
  }, [activeSlide, processSlide, globalPrompt, subject, grade])

  // 批量处理多个幻灯片
  const handleBatchProcess = useCallback(async (slideIds: string[], action: SlideAction) => {
    const actionTemplates: Record<string, string> = {
      polish: '请优化这段内容的文字表达，使语言更加流畅自然、通俗易懂，同时保持教学内容的准确性和完整性。',
      expand: '请在保持原有内容基础上，适当增加细节、例子或解释说明，使教学内容更加丰富和完整。',
      rewrite: '请调整这段内容的语言风格，使其更符合目标学生的认知水平，保持专业性的同时增强可读性。',
      extract: '请提取这段内容的核心知识点，以简洁清晰的方式呈现关键信息，去除冗余内容。',
    }

    let finalPrompt = globalPrompt || actionTemplates[action] || ''
    if (grade && finalPrompt) {
      finalPrompt = `当前年级：${grade}。${finalPrompt}`
    } else if (grade) {
      finalPrompt = `当前年级：${grade}`
    }

    const domain = subject === '_default' ? undefined : subject
    const result = await batchProcessSlides(slideIds, action, finalPrompt, domain)
    if (result.failed > 0) {
      setError(`批量处理完成: ${result.succeeded}/${result.total} 成功, ${result.failed} 失败`)
    }
  }, [batchProcessSlides, globalPrompt, subject, grade])

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

  // 处理跨 PPT 融合（AI 内容级融合）
  const handleMergeSelected = useCallback(async (slideIds: string[]) => {
    if (slideIds.length < 2) {
      setError('请选择至少两个幻灯片进行融合')
      return
    }

    let finalPrompt = globalPrompt || undefined
    if (grade && finalPrompt) {
      finalPrompt = `当前年级：${grade}。${finalPrompt}`
    } else if (grade) {
      finalPrompt = `当前年级：${grade}`
    }

    const domain = subject === '_default' ? undefined : subject
    const result = await mergeSlides(slideIds, finalPrompt, domain)
    if (!result.success) {
      setError(result.error || '融合失败')
    }
  }, [mergeSlides, globalPrompt, subject, grade])

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

  return {
    // 步骤状态
    currentStep,
    setCurrentStep,

    // 文件状态
    pptA,
    pptB,
    setPptA,
    setPptB,
    isInitializing,

    // 错误状态
    error,
    setError,

    // 全局提示语
    globalPrompt,
    setGlobalPrompt,
    showTemplates,
    setShowTemplates,

    // 学科/年级
    subject,
    setSubject,
    grade,
    setGrade,

    // 下载状态
    downloadUrl,
    fileName,

    // 会话状态
    session,
    activeSlide,
    activeVersion,
    finalSelectionDetails,
    isInFinalSelection,

    // 操作方法
    handleSlideClick,
    handleSwitchVersion,
    handleProcess,
    handleBatchProcess,
    handleAddToFinal,
    handleRemoveFromFinal,
    addToFinal,
    removeFromFinal,
    handleMergeSelected,
    handleGenerateFinal,
    handleDownload,
    handleReset,
    handleStepClick,
    reorderFinal,
  }
}