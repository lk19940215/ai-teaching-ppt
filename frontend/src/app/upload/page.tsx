"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { apiBaseUrl, createApiUrl } from '@/lib/api'

// 年级选项
const GRADE_OPTIONS = [
  { value: "1", label: "小学一年级" },
  { value: "2", label: "小学二年级" },
  { value: "3", label: "小学三年级" },
  { value: "4", label: "小学四年级" },
  { value: "5", label: "小学五年级" },
  { value: "6", label: "小学六年级" },
  { value: "7", label: "初中一年级" },
  { value: "8", label: "初中二年级" },
  { value: "9", label: "初中三年级" },
  { value: "10", label: "高中一年级" },
  { value: "11", label: "高中二年级" },
  { value: "12", label: "高中三年级" },
]

// 学科选项
const SUBJECT_OPTIONS = [
  { value: "chinese", label: "语文" },
  { value: "math", label: "数学" },
  { value: "english", label: "英语" },
  { value: "science", label: "科学" },
  { value: "physics", label: "物理" },
  { value: "chemistry", label: "化学" },
  { value: "biology", label: "生物" },
  { value: "history", label: "历史" },
  { value: "politics", label: "政治" },
  { value: "geography", label: "地理" },
  { value: "general", label: "通用" },
]

// PPT 风格选项
const STYLE_OPTIONS = [
  { value: "fun", label: "活泼趣味（适合低年级）" },
  { value: "simple", label: "简约清晰（适合高年级）" },
  { value: "theme", label: "学科主题（根据学科自动配色）" },
]

// 教学层次选项（差异化教学支持 feat-040）
const DIFFICULTY_OPTIONS = [
  { value: "unified", label: "统一（混合难度）" },
  { value: "basic", label: "基础版（1 星）" },
  { value: "intermediate", label: "提高版（2 星）" },
  { value: "advanced", label: "拓展版（3 星）" },
]

// localStorage key 常量（feat-064 文本草稿自动保存）
const STORAGE_KEY = "ppt_draft_content"

interface TeachingConfig {
  grade: string
  subject: string
  style: string
  slideCount: number
  chapter: string
  difficultyLevel: string
}

// PPT 内容类型
interface PPTContent {
  title: string
  slides: Array<{
    page_type: string
    title: string
    content: string[]
    interaction?: string
    exercise?: string
    mnemonic?: string
  }>
  summary: string
  key_points: string[]
}

export default function UploadPage() {
  const [config, setConfig] = useState<TeachingConfig>({
    grade: "5",      // 默认小学五年级（更常用）
    subject: "math",
    style: "fun",    // 默认活泼趣味（更直观）
    slideCount: 15,
    chapter: "",
    difficultyLevel: "unified",
  })

  const [uploadType, setUploadType] = useState<"image" | "pdf" | "text">("text")
  const [textContent, setTextContent] = useState("")
  const [imageFiles, setImageFiles] = useState<File[]>([])
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedContent, setGeneratedContent] = useState<PPTContent | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [currentPreviewSlide, setCurrentPreviewSlide] = useState(0)
  const [llmConfig, setLlmConfig] = useState<any>(null)
  const [progress, setProgress] = useState(0) // 生成进度 0-100
  const [showResult, setShowResult] = useState(false) // 控制结果展示的渐入动画
  const [progressStatus, setProgressStatus] = useState("") // 当前进度状态描述
  const [showPreviewModal, setShowPreviewModal] = useState(false) // 放大预览模态框
  // 进度反馈增强（feat-052）
  const [stageStartTime, setStageStartTime] = useState<number | null>(null) // 当前阶段开始时间（毫秒）
  const [elapsedTime, setElapsedTime] = useState(0) // 已用时间（秒）
  const [estimatedRemaining, setEstimatedRemaining] = useState<number | null>(null) // 预计剩余时间（秒）
  const [currentStageDetail, setCurrentStageDetail] = useState("") // 当前阶段详细说明
  const [nextStageText, setNextStageText] = useState("") // 下一步说明
  // 智能风格推荐（feat-053）
  const [hasManuallyChangedStyle, setHasManuallyChangedStyle] = useState(false) // 用户是否手动修改过风格
  const [styleRecommendationTip, setStyleRecommendationTip] = useState("") // 风格推荐提示

  // 【feat-064 文本草稿自动保存】组件挂载时恢复草稿
  useEffect(() => {
    const savedDraft = localStorage.getItem(STORAGE_KEY)
    if (savedDraft && !textContent) {
      setTextContent(savedDraft)
    }
  }, [])

  // 【feat-064 文本草稿自动保存】监听 textContent 变化，防抖 500ms 后保存
  useEffect(() => {
    const timer = setTimeout(() => {
      if (textContent) {
        localStorage.setItem(STORAGE_KEY, textContent)
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [textContent])

  // 从后端加载 LLM 配置
  useEffect(() => {
    const loadLLMConfig = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/config/providers/default`)
        const result = await response.json()
        if (result.success && result.data) {
          // 从 localStorage 获取完整的 API Key（兼容旧版）
          const localConfig = localStorage.getItem("llm_config")
          if (localConfig) {
            const parsed = JSON.parse(localConfig)
            if (parsed.provider === result.data.provider) {
              setLlmConfig({ ...result.data, apiKey: parsed.apiKey })
              return
            }
          }
          // 否则提示用户去设置页面配置
          setLlmConfig(result.data)
        }
      } catch (error) {
        console.error("加载 LLM 配置失败:", error)
      }
    }
    loadLLMConfig()
  }, [])

  // 【feat-066 放大预览模态框】监听键盘事件（左右箭头翻页、ESC 关闭）
  useEffect(() => {
    if (!showPreviewModal || !generatedContent) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowPreviewModal(false)
      } else if (e.key === 'ArrowLeft') {
        setCurrentPreviewSlide(prev => Math.max(0, prev - 1))
      } else if (e.key === 'ArrowRight') {
        setCurrentPreviewSlide(prev => Math.min(generatedContent.slides.length + 1, prev + 1))
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [showPreviewModal, generatedContent])

  // 从 localStorage 加载 LLM 配置（兼容旧版）
  const getLLMConfig = () => {
    const savedConfig = localStorage.getItem("llm_config")
    if (savedConfig) {
      return JSON.parse(savedConfig)
    }
    return llmConfig
  }

  // 阶段配置：预计耗时（秒）和详细说明（feat-052）
  const STAGE_CONFIG: Record<string, {
    duration: number
    description: string
    detail: string
    nextStage: string
  }> = {
    analyzing_content: {
      duration: 5,
      description: '正在分析教材内容...',
      detail: '提取知识点和教学重难点',
      nextStage: '生成 PPT 大纲'
    },
    generating_outline: {
      duration: 60,
      description: '正在调用 AI 生成 PPT 大纲...',
      detail: '根据年级和学科设计教学结构',
      nextStage: '构建幻灯片页面'
    },
    building_slides: {
      duration: 30,
      description: '正在构建幻灯片页面...',
      detail: '生成每页内容和布局',
      nextStage: '添加动画效果'
    },
    adding_animations: {
      duration: 15,
      description: '正在添加动画效果...',
      detail: '注入页面切换和元素动画',
      nextStage: '完成'
    }
  }

  // 智能风格推荐：根据年级自动推荐风格（feat-053）
  const recommendStyleByGrade = (grade: string): string => {
    const gradeNum = parseInt(grade)
    if (gradeNum >= 1 && gradeNum <= 3) {
      return 'fun' // 小学低年级 → 活泼趣味
    } else if (gradeNum >= 4 && gradeNum <= 6) {
      return 'simple' // 小学高年级 → 简约清晰
    } else {
      return 'theme' // 初中/高中 → 学科主题
    }
  }

  // 获取风格中文名称（feat-053）
  const getStyleLabel = (value: string): string => {
    const style = STYLE_OPTIONS.find(s => s.value === value)
    return style ? style.label.split('（')[0] : value
  }

  // 监听年级变化，自动推荐风格（feat-053）
  useEffect(() => {
    if (hasManuallyChangedStyle) return // 用户手动修改过则不再自动推荐

    const recommendedStyle = recommendStyleByGrade(config.grade)

    // 如果当前风格与推荐的不一致，则更新
    if (config.style !== recommendedStyle) {
      setConfig({ ...config, style: recommendedStyle })
      setStyleRecommendationTip(`已为您推荐"${getStyleLabel(recommendedStyle)}"风格`)

      // 3 秒后清除提示
      const timer = setTimeout(() => {
        setStyleRecommendationTip("")
      }, 3000)

      return () => clearTimeout(timer)
    }
  }, [config.grade])

  // 格式化时间显示（feat-052）
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}秒`
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}分${secs}秒`
  }

  // 动态更新已用时间（feat-052）
  useEffect(() => {
    if (!isGenerating || !stageStartTime) return

    const timer = setInterval(() => {
      const elapsed = (Date.now() - stageStartTime) / 1000
      setElapsedTime(elapsed)

      // 根据当前进度阶段计算预计剩余时间
      const currentStage = Object.keys(STAGE_CONFIG).find((stage, index, arr) => {
        const stageProgress = [10, 30, 60, 85][index]
        const nextProgress = index < arr.length - 1 ? [10, 30, 60, 85][index + 1] : 100
        return progress >= stageProgress && progress < nextProgress
      })

      if (currentStage && currentStage in STAGE_CONFIG) {
        const config = STAGE_CONFIG[currentStage]
        const stageProgress = progress >= 10 ? progress : 10
        const stageStart = [10, 30, 60, 85].find((p, i) =>
          Object.keys(STAGE_CONFIG)[i] === currentStage
        ) || 10
        const stageEnd = [30, 60, 85, 100].find((p, i) =>
          Object.keys(STAGE_CONFIG)[i] === currentStage
        ) || 100

        // 计算当前阶段的完成比例
        const stageProgressRatio = (stageProgress - stageStart) / (stageEnd - stageStart)

        // 动态估算剩余时间
        if (stageProgressRatio > 0.1 && elapsedTime > 0) {
          const estimatedTotal = elapsedTime / stageProgressRatio
          const remaining = estimatedTotal - elapsedTime
          setEstimatedRemaining(Math.max(0, remaining))
        }
      }
    }, 500)

    return () => clearInterval(timer)
  }, [isGenerating, stageStartTime, progress])

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

    const files = Array.from(e.dataTransfer.files)

    if (uploadType === "image") {
      const validFiles = files.filter(f => f.type.startsWith("image/"))
      setImageFiles(prev => [...prev, ...validFiles])
    } else if (uploadType === "pdf") {
      const validFile = files.find(f => f.type === "application/pdf")
      if (validFile) setPdfFile(validFile)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])

    if (uploadType === "image") {
      setImageFiles(prev => [...prev, ...files])
    } else if (uploadType === "pdf" && files[0]) {
      setPdfFile(files[0])
    }
  }

  // 上传并处理图片，返回提取的文本
  const uploadAndProcessImage = async (files: File[]): Promise<string> => {
    const formData = new FormData()
    files.forEach(file => formData.append('files', file))

    // 1. 上传图片
    const uploadResponse = await fetch(`${apiBaseUrl}/api/v1/upload/image`, {
      method: "POST",
      body: formData,
    })

    if (!uploadResponse.ok) {
      const errorData = await uploadResponse.json()
      throw new Error(`图片上传失败：${errorData.detail || '未知错误'}`)
    }

    const uploadResult = await uploadResponse.json()
    if (!uploadResult.saved_files || uploadResult.saved_files.length === 0) {
      throw new Error('图片上传失败：未返回保存的文件信息')
    }

    // 2. 对每张图片进行 OCR 识别
    const extractedTexts: string[] = []
    for (const file of uploadResult.saved_files) {
      const ocrResponse = await fetch(`${apiBaseUrl}/api/v1/process/ocr`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: file.saved_path,
          language: "ch",
        }),
      })

      if (!ocrResponse.ok) {
        const errorData = await ocrResponse.json()
        throw new Error(`OCR 识别失败：${errorData.detail || '未知错误'}`)
      }

      const ocrResult = await ocrResponse.json()
      if (ocrResult.cleaned_text) {
        extractedTexts.push(ocrResult.cleaned_text)
      }
    }

    // 合并所有提取的文本
    return extractedTexts.join('\n\n')
  }

  // 上传并处理 PDF，返回提取的文本
  const uploadAndProcessPdf = async (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('file', file)

    // 1. 上传 PDF
    const uploadResponse = await fetch(`${apiBaseUrl}/api/v1/upload/pdf`, {
      method: "POST",
      body: formData,
    })

    if (!uploadResponse.ok) {
      const errorData = await uploadResponse.json()
      throw new Error(`PDF 上传失败：${errorData.detail || '未知错误'}`)
    }

    const uploadResult = await uploadResponse.json()
    if (!uploadResult.saved_path) {
      throw new Error('PDF 上传失败：未返回保存的文件路径')
    }

    // 2. 解析 PDF
    const pdfResponse = await fetch(`${apiBaseUrl}/api/v1/process/pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_path: uploadResult.saved_path,
        language: "ch",
      }),
    })

    if (!pdfResponse.ok) {
      const errorData = await pdfResponse.json()
      throw new Error(`PDF 解析失败：${errorData.detail || '未知错误'}`)
    }

    const pdfResult = await pdfResponse.json()
    return pdfResult.full_text || ''
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    setError(null)
    setGeneratedContent(null)
    setDownloadUrl(null)
    setFileName(null)
    setProgress(0)
    setShowResult(false)
    setProgressStatus('')
    setStageStartTime(null)
    setElapsedTime(0)
    setEstimatedRemaining(null)
    setCurrentStageDetail('')
    setNextStageText('')

    let eventSource: EventSource | null = null

    try {
      // 获取 LLM 配置
      const llmConfig = getLLMConfig()
      if (!llmConfig) {
        setError('请先在设置页面配置 LLM API Key')
        setIsGenerating(false)
        return
      }
      if (!llmConfig.apiKey) {
        setError('API Key 未配置，请前往设置页面配置')
        setIsGenerating(false)
        return
      }

      // 根据上传类型处理内容提取
      let finalTextContent = textContent

      if (uploadType === 'image' && imageFiles.length > 0) {
        setProgressStatus(`正在上传 ${imageFiles.length} 张图片...`)
        setProgress(10)
        finalTextContent = await uploadAndProcessImage(imageFiles)
        if (!finalTextContent) {
          setError('图片 OCR 识别失败：未提取到有效文本')
          setIsGenerating(false)
          return
        }
        setProgressStatus('图片文字识别完成，正在生成 PPT...')
        setProgress(40)
      } else if (uploadType === 'pdf' && pdfFile) {
        setProgressStatus(`正在上传 PDF 文件...`)
        setProgress(10)
        finalTextContent = await uploadAndProcessPdf(pdfFile)
        if (!finalTextContent) {
          setError('PDF 解析失败：未提取到有效文本')
          setIsGenerating(false)
          return
        }
        setProgressStatus('PDF 内容提取完成，正在生成 PPT...')
        setProgress(40)
      } else if (uploadType === 'text') {
        setProgressStatus('正在分析文本内容...')
        setProgress(20)
      }

      // 验证文本内容
      if (!finalTextContent || finalTextContent.trim().length === 0) {
        setError('未检测到有效内容：请确保图片/PDF 包含可识别的文字')
        setIsGenerating(false)
        return
      }

      // 超长内容检查（feat-049）
      const MAX_CONTENT_LENGTH = 10000 // 约 8000 token 的字数上限
      if (finalTextContent.length > MAX_CONTENT_LENGTH) {
        setError(`内容过长（${finalTextContent.length}字），请控制在${MAX_CONTENT_LENGTH}字以内`)
        setIsGenerating(false)
        return
      }

      // 使用 SSE 流式生成 PPT
      setProgressStatus('正在连接生成服务...')

      const params = new URLSearchParams({
        text_content: finalTextContent,
        grade: config.grade,
        subject: config.subject,
        slide_count: config.slideCount.toString(),
        chapter: config.chapter || '',
        provider: llmConfig.provider,
        api_key: llmConfig.apiKey,
        style: config.style,
        difficulty_level: config.difficultyLevel,
      })

      const sseUrl = `${apiBaseUrl}/api/v1/ppt/generate-stream?${params.toString()}`
      eventSource = new EventSource(sseUrl)

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.stage === 'error') {
          setError(data.message)
          setIsGenerating(false)
          setProgressStatus('')
    setStageStartTime(null)
    setElapsedTime(0)
    setEstimatedRemaining(null)
    setCurrentStageDetail('')
    setNextStageText('')
          setStageStartTime(null)
          setEstimatedRemaining(null)
          eventSource?.close()
          return
        }

        setProgress(data.progress)
        setProgressStatus(data.message)

        // 记录阶段开始时间（feat-052）
        if (data.stage && data.stage !== 'complete' && !stageStartTime) {
          setStageStartTime(Date.now())
        }

        // 更新详细阶段信息（feat-052）
        if (data.stage && data.stage in STAGE_CONFIG) {
          const config = STAGE_CONFIG[data.stage]
          setCurrentStageDetail(config.detail)
          setNextStageText(config.nextStage)
        }

        if (data.stage === 'complete') {
          const result = data.result
          setGeneratedContent(result.content)
          setDownloadUrl(`${apiBaseUrl}${result.download_url}`)
          setFileName(result.file_name)

          // 【feat-064】生成成功后清除草稿
          localStorage.removeItem(STORAGE_KEY)

          setTimeout(() => {
            setIsGenerating(false)
            setShowResult(true)
            setProgressStatus('')
    setStageStartTime(null)
    setElapsedTime(0)
    setEstimatedRemaining(null)
    setCurrentStageDetail('')
    setNextStageText('')
            setStageStartTime(null)
            setEstimatedRemaining(null)
            setCurrentStageDetail('')
            setNextStageText('')
          }, 500)

          eventSource?.close()
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE 连接错误:', error)
        setError('生成连接中断，请稍后重试')
        setIsGenerating(false)
        setProgressStatus('')
    setStageStartTime(null)
    setElapsedTime(0)
    setEstimatedRemaining(null)
    setCurrentStageDetail('')
    setNextStageText('')
        setStageStartTime(null)
        setEstimatedRemaining(null)
        setCurrentStageDetail('')
        setNextStageText('')
        eventSource?.close()
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败，请稍后重试')
      setIsGenerating(false)
      setProgressStatus('')
    setStageStartTime(null)
    setElapsedTime(0)
    setEstimatedRemaining(null)
    setCurrentStageDetail('')
    setNextStageText('')
      setStageStartTime(null)
      setEstimatedRemaining(null)
      setCurrentStageDetail('')
      setNextStageText('')
      eventSource?.close()
    }
  }

  const handleDownload = () => {
    if (downloadUrl && fileName) {
      window.open(downloadUrl, "_blank")
    }
  }

  const handleReset = () => {
    setGeneratedContent(null)
    setError(null)
    setTextContent("")
    setImageFiles([])
    setPdfFile(null)
    setCurrentPreviewSlide(0)
  }

  // 获取页面类型的图标
  const getPageTypeIcon = (pageType: string) => {
    const icons: Record<string, string> = {
      "封面页": "📖",
      "目录页": "📑",
      "知识点讲解页": "📚",
      "互动问答页": "💬",
      "课堂练习页": "✍️",
      "总结回顾页": "✅",
      "单词学习页": "🔤",
      "语法讲解页": "📝",
      "情景对话页": "💭",
      "课文分析页": "🔍",
    }
    return icons[pageType] || "📄"
  }

  // 获取页面类型的背景色
  const getPageTypeBg = (pageType: string, index: number) => {
    const colors = [
      "bg-gradient-to-br from-indigo-500 to-purple-600",
      "bg-gradient-to-br from-emerald-500 to-teal-600",
      "bg-gradient-to-br from-amber-500 to-orange-600",
      "bg-gradient-to-br from-blue-500 to-cyan-600",
      "bg-gradient-to-br from-rose-500 to-pink-600",
      "bg-gradient-to-br from-violet-500 to-purple-600",
    ]
    if (pageType === "封面页") return colors[0]
    if (pageType === "目录页") return colors[1]
    if (pageType === "总结回顾页") return colors[5]
    return colors[index % colors.length]
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        AI 教学 PPT 生成器
      </h1>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-6 animate-fade-in-down">
          {error}
        </div>
      )}

      {/* Loading 状态 - 骨架屏 */}
      {isGenerating && (
        <div className="bg-white rounded-xl border p-6 shadow-sm mb-6 animate-fade-in-up">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            <h2 className="text-xl font-semibold text-gray-700 animate-pulse-slow">AI 正在生成 PPT...</h2>
          </div>

          {/* 进度条 */}
          <div className="mb-6">
            <div className="flex justify-between items-center text-sm text-gray-600 mb-2">
              <span>{progressStatus || "正在处理教材内容..."}</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 transition-all duration-300 ease-out relative overflow-hidden"
                style={{ width: `${progress}%` }}
              >
                <div className="progress-indeterminate"></div>
              </div>
            </div>
          </div>

          {/* 详细进度信息（feat-052） */}
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            {currentStageDetail && (
              <div className="flex items-center gap-2 text-gray-600">
                <span className="text-indigo-500">●</span>
                <span>当前：{currentStageDetail}</span>
              </div>
            )}
            {nextStageText && (
              <div className="flex items-center gap-2 text-gray-600">
                <span className="text-gray-400">○</span>
                <span>下一步：{nextStageText}</span>
              </div>
            )}
            {estimatedRemaining !== null && (
              <div className="col-span-2 text-center text-gray-500 mt-2">
                预计剩余时间：<span className="font-medium text-indigo-600">{formatTime(estimatedRemaining)}</span>
              </div>
            )}
          </div>

          {/* 骨架屏内容 */}
          <div className="space-y-4">
            <div className="skeleton skeleton-title"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="skeleton skeleton-text"></div>
            <div className="flex gap-4 mt-6">
              <div className="skeleton skeleton-card flex-1"></div>
              <div className="skeleton skeleton-card flex-1"></div>
            </div>
          </div>
        </div>
      )}

      {/* 生成结果展示 */}
      {generatedContent && showResult && (
        <div className="bg-white rounded-xl border p-6 shadow-sm mb-6 animate-scale-in">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">生成结果</h2>
            <div className="flex gap-2">
              {downloadUrl && (
                <Button onClick={handleDownload}>
                  下载 PPT
                </Button>
              )}
              <Button variant="outline" onClick={handleReset}>
                重新生成
              </Button>
            </div>
          </div>

          {/* PPT 缩略图轮播预览 */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium">PPT 预览（共 {generatedContent.slides.length + 2} 页）</h3>
              {/* 放大预览按钮（UX 修复） */}
              <Button
                variant="outline"
                onClick={() => setShowPreviewModal(true)}
                className="text-sm"
              >
                🔍 放大查看
              </Button>
            </div>

            {/* 缩略图导航 */}
            <div className="flex gap-2 overflow-x-auto pb-4 mb-4">
              {/* 封面页缩略图 */}
              <button
                onClick={() => setCurrentPreviewSlide(0)}
                className={`flex-shrink-0 w-32 h-20 rounded-lg overflow-hidden border-2 transition ${
                  currentPreviewSlide === 0 ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-gray-200'
                }`}
              >
                <div className="w-full h-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs p-1 text-center">
                  封面
                </div>
              </button>

              {/* 内容页缩略图 */}
              {generatedContent.slides.map((slide, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentPreviewSlide(index + 1)}
                  className={`flex-shrink-0 w-32 h-20 rounded-lg overflow-hidden border-2 transition ${
                    currentPreviewSlide === index + 1 ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-gray-200'
                  }`}
                >
                  <div className={`w-full h-full ${getPageTypeBg(slide.page_type, index)} flex flex-col items-center justify-center text-white text-xs p-1`}>
                    <span className="text-lg">{getPageTypeIcon(slide.page_type)}</span>
                    <span className="truncate w-full text-center px-1">{slide.title.substring(0, 8)}...</span>
                  </div>
                </button>
              ))}

              {/* 总结页缩略图 */}
              <button
                onClick={() => setCurrentPreviewSlide(generatedContent.slides.length + 1)}
                className={`flex-shrink-0 w-32 h-20 rounded-lg overflow-hidden border-2 transition ${
                  currentPreviewSlide === generatedContent.slides.length + 1 ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-gray-200'
                }`}
              >
                <div className="w-full h-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-xs p-1 text-center">
                  总结
                </div>
              </button>
            </div>

            {/* 当前页预览 */}
            <div className="border rounded-xl p-6 bg-gray-50">
              {currentPreviewSlide === 0 ? (
                <div className="text-center py-12">
                  <h1 className="text-3xl font-bold text-indigo-600 mb-4">{generatedContent.title}</h1>
                  <p className="text-gray-500">AI 教学 PPT 生成器</p>
                  {config.chapter && <p className="text-gray-400 mt-2">{config.chapter}</p>}
                </div>
              ) : currentPreviewSlide === generatedContent.slides.length + 1 ? (
                <div>
                  <h3 className="text-xl font-bold text-purple-600 mb-4">总结回顾</h3>
                  <p className="text-gray-700 mb-4">{generatedContent.summary}</p>
                  <div>
                    <h4 className="font-medium mb-2">重点：</h4>
                    <ul className="list-disc list-inside text-gray-600">
                      {generatedContent.key_points.map((point, index) => (
                        <li key={index}>{point}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-2xl">{getPageTypeIcon(generatedContent.slides[currentPreviewSlide - 1].page_type)}</span>
                    <span className="text-sm text-indigo-600 font-medium">
                      第 {currentPreviewSlide} 页 - {generatedContent.slides[currentPreviewSlide - 1].page_type}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold mb-4">{generatedContent.slides[currentPreviewSlide - 1].title}</h3>
                  <ul className="list-disc list-inside text-gray-700 space-y-2 mb-4">
                    {generatedContent.slides[currentPreviewSlide - 1].content.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                  {generatedContent.slides[currentPreviewSlide - 1].interaction && (
                    <div className="bg-green-50 text-green-700 p-3 rounded-lg">
                      💡 <strong>互动环节：</strong>{generatedContent.slides[currentPreviewSlide - 1].interaction}
                    </div>
                  )}
                  {generatedContent.slides[currentPreviewSlide - 1].exercise && (
                    <div className="bg-blue-50 text-blue-700 p-3 rounded-lg">
                      ✍️ <strong>课堂练习：</strong>{generatedContent.slides[currentPreviewSlide - 1].exercise}
                    </div>
                  )}
                  {generatedContent.slides[currentPreviewSlide - 1].mnemonic && (
                    <div className="bg-purple-50 text-purple-700 p-3 rounded-lg">
                      📝 <strong>记忆口诀：</strong>{generatedContent.slides[currentPreviewSlide - 1].mnemonic}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 翻页按钮 */}
            <div className="flex items-center justify-between mt-4">
              <Button
                variant="outline"
                onClick={() => setCurrentPreviewSlide(prev => Math.max(0, prev - 1))}
                disabled={currentPreviewSlide === 0}
              >
                ← 上一页
              </Button>
              <span className="text-gray-500">
                {currentPreviewSlide + 1} / {generatedContent.slides.length + 2}
              </span>
              <Button
                variant="outline"
                onClick={() => setCurrentPreviewSlide(prev => Math.min(generatedContent.slides.length + 1, prev + 1))}
                disabled={currentPreviewSlide === generatedContent.slides.length + 1}
              >
                下一页 →
              </Button>
            </div>
          </div>

          {/* 基本信息 */}
          <div className="border-t pt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">主题</h4>
                <p className="text-gray-900">{generatedContent.title}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-1">重点内容</h4>
                <p className="text-gray-900">{generatedContent.key_points.length} 个知识点</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 左侧：上传区域 */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">上传教材内容</h2>

            {/* 上传方式选择 */}
            <div className="flex gap-2 mb-4">
              {[
                { value: "text" as const, label: "文字输入" },
                { value: "image" as const, label: "图片上传" },
                { value: "pdf" as const, label: "PDF 上传" },
              ].map((option) => (
                <button
                  key={option.value}
                  onClick={() => setUploadType(option.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition btn-click-animate ${
                    uploadType === option.value
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {/* 文字输入 */}
            {uploadType === "text" && (
              <textarea
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="请粘贴课本内容或输入教学要点..."
                className="w-full h-64 p-4 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            )}

            {/* 图片上传 */}
            {uploadType === "image" && (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
                  isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300"
                }`}
              >
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="image-upload"
                />
                <label
                  htmlFor="image-upload"
                  className="cursor-pointer block"
                >
                  <div className="text-gray-500 mb-2">
                    拖拽图片到这里或点击上传
                  </div>
                  <div className="text-sm text-gray-400">
                    支持 JPG、PNG 格式，支持多张图片
                  </div>
                </label>

                {imageFiles.length > 0 && (
                  <div className="mt-4 text-left">
                    <div className="text-sm text-gray-600 mb-2">
                      已选择 {imageFiles.length} 张图片：
                    </div>
                    {imageFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-gray-50 px-3 py-2 rounded mb-1"
                      >
                        <span className="text-sm truncate">{file.name}</span>
                        <button
                          onClick={() => {
                            setImageFiles(prev =>
                              prev.filter((_, i) => i !== index)
                            )
                          }}
                          className="text-red-500 hover:text-red-700 text-sm"
                        >
                          删除
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* PDF 上传 */}
            {uploadType === "pdf" && (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition ${
                  isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-300"
                }`}
              >
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="pdf-upload"
                />
                <label
                  htmlFor="pdf-upload"
                  className="cursor-pointer block"
                >
                  <div className="text-gray-500 mb-2">
                    拖拽 PDF 文件到这里或点击上传
                  </div>
                  <div className="text-sm text-gray-400">
                    支持标准 PDF 格式电子书
                  </div>
                </label>

                {pdfFile && (
                  <div className="mt-4 flex items-center justify-between bg-gray-50 px-3 py-2 rounded">
                    <span className="text-sm truncate">{pdfFile.name}</span>
                    <button
                      onClick={() => setPdfFile(null)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      删除
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 右侧：教学配置 */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">教学参数配置</h2>

            <div className="space-y-4">
              {/* 年级选择 */}
              <div>
                <Label htmlFor="grade" className="block mb-2">
                  年级
                </Label>
                <Select
                  id="grade"
                  value={config.grade}
                  onChange={(e) =>
                    setConfig({ ...config, grade: e.target.value })
                  }
                >
                  {GRADE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>

              {/* 学科选择 */}
              <div>
                <Label htmlFor="subject" className="block mb-2">
                  学科
                </Label>
                <Select
                  id="subject"
                  value={config.subject}
                  onChange={(e) =>
                    setConfig({ ...config, subject: e.target.value })
                  }
                >
                  {SUBJECT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>

              {/* 章节信息 */}
              <div>
                <Label htmlFor="chapter" className="block mb-2">
                  章节名称（可选）
                </Label>
                <Input
                  id="chapter"
                  type="text"
                  value={config.chapter}
                  onChange={(e) =>
                    setConfig({ ...config, chapter: e.target.value })
                  }
                  placeholder="例如：第三章 分数的加减法"
                />
              </div>

              {/* PPT 风格 */}
              <div>
                <Label htmlFor="style" className="block mb-2">
                  PPT 风格
                </Label>
                <Select
                  id="style"
                  value={config.style}
                  onChange={(e) => {
                    setHasManuallyChangedStyle(true) // 标记用户手动修改
                    setConfig({ ...config, style: e.target.value })
                  }}
                >
                  {STYLE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
                {/* 智能推荐提示（feat-053） */}
                {styleRecommendationTip && (
                  <p className="text-xs text-emerald-600 mt-1.5 flex items-center gap-1">
                    <span>✨</span>
                    <span>{styleRecommendationTip}</span>
                  </p>
                )}
              </div>

              {/* 教学层次（差异化教学支持 feat-040） */}
              <div>
                <Label htmlFor="difficultyLevel" className="block mb-2">
                  教学层次
                </Label>
                <Select
                  id="difficultyLevel"
                  value={config.difficultyLevel}
                  onChange={(e) =>
                    setConfig({ ...config, difficultyLevel: e.target.value })
                  }
                >
                  {DIFFICULTY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>

              {/* 幻灯片数量 */}
              <div>
                <Label htmlFor="slideCount" className="block mb-2">
                  幻灯片数量（8-30页）
                </Label>
                <div className="flex items-center gap-4 mb-3">
                  <input
                    type="range"
                    id="slideCount"
                    min="8"
                    max="30"
                    value={config.slideCount}
                    onChange={(e) =>
                      setConfig({ ...config, slideCount: parseInt(e.target.value) })
                    }
                    className="flex-1"
                  />
                  <span className="text-lg font-semibold w-12 text-center">
                    {config.slideCount}页
                  </span>
                </div>
                {/* 快捷选项按钮 */}
                <div className="flex gap-2">
                  {[10, 15, 20, 25].map(num => (
                    <button
                      key={num}
                      onClick={() => setConfig({ ...config, slideCount: num })}
                      className={`px-3 py-1 text-sm rounded border transition ${
                        config.slideCount === num
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400'
                      }`}
                    >
                      {num}页
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 生成按钮 */}
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !textContent && imageFiles.length === 0 && !pdfFile}
              className="w-full mt-6 btn-click-animate"
            >
              {isGenerating ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                  AI 正在备课中...
                </span>
              ) : (
                "生成教学 PPT"
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* 【feat-066】放大预览模态框 */}
      {showPreviewModal && generatedContent && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setShowPreviewModal(false)}
        >
          {/* 模态框内容区域（点击不关闭） */}
          <div
            className="bg-white rounded-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 顶部标题栏 */}
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between rounded-t-xl z-10">
              <div>
                <h2 className="text-xl font-bold text-gray-900">{generatedContent.title}</h2>
                <p className="text-sm text-gray-500 mt-1">
                  第 {currentPreviewSlide + 1} 页 / 共 {generatedContent.slides.length + 2} 页
                </p>
              </div>
              <button
                onClick={() => setShowPreviewModal(false)}
                className="text-gray-400 hover:text-gray-600 transition text-2xl w-8 h-8 flex items-center justify-center"
                title="关闭 (ESC)"
              >
                ✕
              </button>
            </div>

            {/* 幻灯片内容 */}
            <div className="p-8 min-h-[400px]">
              {currentPreviewSlide === 0 ? (
                /* 封面页 */
                <div className="text-center py-16 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl">
                  <h1 className="text-5xl font-bold text-indigo-600 mb-6">{generatedContent.title}</h1>
                  <p className="text-xl text-gray-600">AI 教学 PPT 生成器</p>
                  {config.chapter && (
                    <p className="text-lg text-gray-500 mt-4">{config.chapter}</p>
                  )}
                  <div className="mt-8 flex items-center justify-center gap-4 text-sm text-gray-500">
                    <span>年级：{GRADE_OPTIONS.find(g => g.value === config.grade)?.label}</span>
                    <span>学科：{SUBJECT_OPTIONS.find(s => s.value === config.subject)?.label}</span>
                  </div>
                </div>
              ) : currentPreviewSlide === generatedContent.slides.length + 1 ? (
                /* 总结页 */
                <div className="py-8">
                  <div className="flex items-center gap-3 mb-6">
                    <span className="text-4xl">📚</span>
                    <h3 className="text-3xl font-bold text-purple-600">总结回顾</h3>
                  </div>
                  <p className="text-lg text-gray-700 mb-6 leading-relaxed">{generatedContent.summary}</p>
                  <div className="bg-purple-50 rounded-xl p-6">
                    <h4 className="font-bold text-purple-800 mb-4 text-lg">重点内容</h4>
                    <ul className="space-y-3">
                      {generatedContent.key_points.map((point, index) => (
                        <li key={index} className="flex items-start gap-3">
                          <span className="text-purple-600 font-bold mt-0.5">{index + 1}.</span>
                          <span className="text-gray-700">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ) : (
                /* 内容页 */
                <div className="py-4">
                  <div className="flex items-center gap-3 mb-6">
                    <span className="text-3xl">{getPageTypeIcon(generatedContent.slides[currentPreviewSlide - 1].page_type)}</span>
                    <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                      {generatedContent.slides[currentPreviewSlide - 1].page_type}
                    </span>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-6">
                    {generatedContent.slides[currentPreviewSlide - 1].title}
                  </h3>
                  <ul className="space-y-4 mb-6">
                    {generatedContent.slides[currentPreviewSlide - 1].content.map((item, index) => (
                      <li key={index} className="flex items-start gap-3 text-lg text-gray-700">
                        <span className="text-indigo-600 font-bold mt-1">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                  {generatedContent.slides[currentPreviewSlide - 1].interaction && (
                    <div className="bg-green-50 border border-green-200 text-green-800 p-5 rounded-xl mb-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">💡</span>
                        <div>
                          <strong className="block mb-1">互动环节：</strong>
                          <span>{generatedContent.slides[currentPreviewSlide - 1].interaction}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {generatedContent.slides[currentPreviewSlide - 1].exercise && (
                    <div className="bg-blue-50 border border-blue-200 text-blue-800 p-5 rounded-xl mb-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">✍️</span>
                        <div>
                          <strong className="block mb-1">课堂练习：</strong>
                          <span>{generatedContent.slides[currentPreviewSlide - 1].exercise}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {generatedContent.slides[currentPreviewSlide - 1].mnemonic && (
                    <div className="bg-purple-50 border border-purple-200 text-purple-800 p-5 rounded-xl">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">📝</span>
                        <div>
                          <strong className="block mb-1">记忆口诀：</strong>
                          <span>{generatedContent.slides[currentPreviewSlide - 1].mnemonic}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 底部翻页按钮 */}
            <div className="sticky bottom-0 bg-white border-t px-6 py-4 flex items-center justify-between rounded-b-xl">
              <Button
                variant="outline"
                onClick={() => setCurrentPreviewSlide(prev => Math.max(0, prev - 1))}
                disabled={currentPreviewSlide === 0}
                className="px-6"
              >
                ← 上一页
              </Button>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span>提示：可使用键盘左右箭头翻页</span>
              </div>
              <Button
                variant="outline"
                onClick={() => setCurrentPreviewSlide(prev => Math.min(generatedContent.slides.length + 1, prev + 1))}
                disabled={currentPreviewSlide === generatedContent.slides.length + 1}
                className="px-6"
              >
                下一页 →
              </Button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}