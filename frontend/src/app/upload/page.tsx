"use client"

import * as React from "react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"

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

interface TeachingConfig {
  grade: string
  subject: string
  style: string
  slideCount: number
  chapter: string
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
    grade: "3",
    subject: "math",
    style: "simple",
    slideCount: 15,
    chapter: "",
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

  // 从 localStorage 加载 LLM 配置
  const getLLMConfig = () => {
    const savedConfig = localStorage.getItem("llm_config")
    if (savedConfig) {
      return JSON.parse(savedConfig)
    }
    return null
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

  const handleGenerate = async () => {
    setIsGenerating(true)
    setError(null)
    setGeneratedContent(null)
    setDownloadUrl(null)
    setFileName(null)

    try {
      // 获取 LLM 配置
      const llmConfig = getLLMConfig()
      if (!llmConfig || !llmConfig.apiKey) {
        setError("请先在设置页面配置 LLM API Key")
        return
      }

      // 调用后端 API 完整生成 PPT（内容 + 文件）
      const response = await fetch("http://localhost:8000/api/v1/ppt/generate-full", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text_content: textContent,
          grade: config.grade,
          subject: config.subject,
          slideCount: config.slideCount,
          chapter: config.chapter || undefined,
          provider: llmConfig.provider,
          api_key: llmConfig.apiKey,
          style: config.style,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "生成失败")
      }

      const result = await response.json()
      setGeneratedContent(result.content)
      setDownloadUrl(`http://localhost:8000${result.download_url}`)
      setFileName(result.file_name)
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败，请稍后重试")
    } finally {
      setIsGenerating(false)
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
        <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* 生成结果展示 */}
      {generatedContent && (
        <div className="bg-white rounded-xl border p-6 shadow-sm mb-6">
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
            <h3 className="text-lg font-medium mb-4">PPT 预览（共 {generatedContent.slides.length + 2} 页）</h3>

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
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
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
                  onChange={(e) =>
                    setConfig({ ...config, style: e.target.value })
                  }
                >
                  {STYLE_OPTIONS.map((option) => (
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
                <div className="flex items-center gap-4">
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
                  <span className="text-lg font-semibold w-8 text-center">
                    {config.slideCount}
                  </span>
                </div>
              </div>
            </div>

            {/* 生成按钮 */}
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !textContent && imageFiles.length === 0 && !pdfFile}
              className="w-full mt-6"
            >
              {isGenerating ? "AI 正在备课中..." : "生成教学 PPT"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}