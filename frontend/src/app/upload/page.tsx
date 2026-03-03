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

    try {
      // 获取 LLM 配置
      const llmConfig = getLLMConfig()
      if (!llmConfig || !llmConfig.apiKey) {
        setError("请先在设置页面配置 LLM API Key")
        return
      }

      // 调用后端 API 生成 PPT 内容
      const response = await fetch("http://localhost:8000/api/v1/generate/ppt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: textContent,
          grade: config.grade,
          subject: config.subject,
          slideCount: config.slideCount,
          chapter: config.chapter || undefined,
          provider: llmConfig.provider,
          api_key: llmConfig.apiKey,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "生成失败")
      }

      const result = await response.json()
      setGeneratedContent(result.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败，请稍后重试")
    } finally {
      setIsGenerating(false)
    }
  }

  const handleReset = () => {
    setGeneratedContent(null)
    setError(null)
    setTextContent("")
    setImageFiles([])
    setPdfFile(null)
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
            <Button variant="outline" onClick={handleReset}>
              重新生成
            </Button>
          </div>

          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-medium mb-2">{generatedContent.title}</h3>
              <p className="text-gray-600">{generatedContent.summary}</p>
            </div>

            <div>
              <h4 className="font-medium mb-2">重点：</h4>
              <ul className="list-disc list-inside text-gray-600">
                {generatedContent.key_points.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">幻灯片内容：</h4>
              <div className="space-y-4">
                {generatedContent.slides.map((slide, index) => (
                  <div key={index} className="border p-4 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-indigo-600 font-medium">
                        第 {index + 1} 页 - {slide.page_type}
                      </span>
                    </div>
                    <h5 className="font-medium">{slide.title}</h5>
                    <ul className="list-disc list-inside text-sm text-gray-600 mt-2">
                      {slide.content.map((item, i) => (
                        <li key={i}>{item}</li>
                      ))}
                    </ul>
                    {slide.interaction && (
                      <div className="mt-2 text-sm text-green-600">
                        互动：{slide.interaction}
                      </div>
                    )}
                    {slide.exercise && (
                      <div className="mt-2 text-sm text-blue-600">
                        练习：{slide.exercise}
                      </div>
                    )}
                    {slide.mnemonic && (
                      <div className="mt-2 text-sm text-purple-600">
                        口诀：{slide.mnemonic}
                      </div>
                    )}
                  </div>
                ))}
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