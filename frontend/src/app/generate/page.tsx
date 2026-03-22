"use client"

import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { apiBaseUrl } from "@/lib/api"
import { getLLMConfig } from "@/lib/llmConfig"

interface SlideOutline {
  title: string
  content: string[]
  notes: string
}

interface Outline {
  title: string
  slides: SlideOutline[]
}

type Stage = "input" | "outline" | "generating" | "done"

export default function GeneratePage() {
  const [content, setContent] = useState("")
  const [subject, setSubject] = useState("")
  const [grade, setGrade] = useState("")
  const [stage, setStage] = useState<Stage>("input")
  const [outline, setOutline] = useState<Outline | null>(null)
  const [downloadUrl, setDownloadUrl] = useState("")
  const [fileName, setFileName] = useState("")
  const [slideCount, setSlideCount] = useState(0)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleGenerateOutline = useCallback(async () => {
    if (content.trim().length < 10) {
      setError("请输入至少 10 个字符的课文内容")
      return
    }
    setError("")
    setIsLoading(true)

    try {
      const llmConfig = await getLLMConfig()
      if (!llmConfig?.apiKey) {
        setError("请先在设置页面配置 LLM API Key")
        return
      }

      const res = await fetch(`${apiBaseUrl}/api/v1/generate/outline`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: content.trim(),
          subject: subject || undefined,
          grade: grade || undefined,
          provider: llmConfig.provider,
          api_key: llmConfig.apiKey,
          base_url: llmConfig.baseUrl || undefined,
          model: llmConfig.model || undefined,
          temperature: llmConfig.temperature ?? 0.3,
          max_tokens: llmConfig.maxOutputTokens ?? 4000,
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `请求失败: ${res.status}`)
      }

      const data: Outline = await res.json()
      setOutline(data)
      setStage("outline")
    } catch (e: any) {
      setError(e.message || "生成大纲失败")
    } finally {
      setIsLoading(false)
    }
  }, [content, subject, grade])

  const handleUpdateSlide = useCallback((index: number, field: keyof SlideOutline, value: any) => {
    if (!outline) return
    const updated = { ...outline }
    updated.slides = [...updated.slides]
    updated.slides[index] = { ...updated.slides[index], [field]: value }
    setOutline(updated)
  }, [outline])

  const handleRemoveSlide = useCallback((index: number) => {
    if (!outline) return
    const updated = { ...outline }
    updated.slides = updated.slides.filter((_, i) => i !== index)
    setOutline(updated)
  }, [outline])

  const handleAddSlide = useCallback(() => {
    if (!outline) return
    const updated = { ...outline }
    updated.slides = [...updated.slides, { title: "新幻灯片", content: ["要点"], notes: "" }]
    setOutline(updated)
  }, [outline])

  const handleGeneratePpt = useCallback(async () => {
    if (!outline) return
    setError("")
    setStage("generating")

    try {
      const res = await fetch(`${apiBaseUrl}/api/v1/generate/ppt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: outline.title,
          slides: outline.slides,
          subject: subject || undefined,
          grade: grade || undefined,
        }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `请求失败: ${res.status}`)
      }

      const data = await res.json()
      if (!data.success) throw new Error(data.error || "生成失败")

      setDownloadUrl(`${apiBaseUrl}${data.download_url}`)
      setFileName(data.file_name)
      setSlideCount(data.slide_count)
      setStage("done")
    } catch (e: any) {
      setError(e.message || "生成 PPT 失败")
      setStage("outline")
    }
  }, [outline, subject, grade])

  const handleReset = useCallback(() => {
    setStage("input")
    setOutline(null)
    setDownloadUrl("")
    setFileName("")
    setError("")
  }, [])

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900">课文生成 PPT</h1>
        <p className="text-gray-500 mt-1">
          输入课文内容，AI 自动生成教学大纲和 PPT 课件
        </p>
      </div>

      {/* 步骤指示 */}
      <div className="flex items-center justify-center gap-4 mb-8">
        {[
          { key: "input", label: "输入课文" },
          { key: "outline", label: "编辑大纲" },
          { key: "done", label: "下载 PPT" },
        ].map((step, i) => {
          const isActive = stage === step.key || (stage === "generating" && step.key === "done")
          const isPast =
            (step.key === "input" && stage !== "input") ||
            (step.key === "outline" && (stage === "generating" || stage === "done"))
          return (
            <div key={step.key} className="flex items-center gap-2">
              {i > 0 && <div className={`w-8 h-0.5 ${isPast ? "bg-indigo-500" : "bg-gray-300"}`} />}
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
                isActive ? "bg-indigo-100 text-indigo-700" :
                isPast ? "bg-indigo-500 text-white" :
                "bg-gray-100 text-gray-500"
              }`}>
                <span>{isPast ? "✓" : i + 1}</span>
                <span>{step.label}</span>
              </div>
            </div>
          )
        })}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
          <button onClick={() => setError("")} className="ml-2 underline">关闭</button>
        </div>
      )}

      {/* Stage 1: 输入课文 */}
      {stage === "input" && (
        <div className="bg-white border rounded-lg p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">学科（可选）</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="如：英语、数学、语文"
                className="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">年级（可选）</label>
              <input
                type="text"
                value={grade}
                onChange={(e) => setGrade(e.target.value)}
                placeholder="如：八年级、高一"
                className="w-full text-sm border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 mb-1 block">
              课文内容 <span className="text-gray-400 font-normal">（粘贴课文全文或核心段落）</span>
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="请在此粘贴课文内容...\n\n例如：\nUnit 2 Stay Healthy\nIn this unit, you will:\n1. Talk about health problems and physical conditions.\n2. Give advice to people who are not feeling well..."
              className="w-full h-64 text-sm border border-gray-300 rounded-md px-3 py-2 resize-y focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <p className="text-xs text-gray-400 mt-1">{content.length} 字</p>
          </div>

          <Button
            onClick={handleGenerateOutline}
            disabled={isLoading || content.trim().length < 10}
            className="w-full"
            size="lg"
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                AI 正在生成大纲...
              </>
            ) : (
              "生成教学大纲"
            )}
          </Button>
        </div>
      )}

      {/* Stage 2: 编辑大纲 */}
      {stage === "outline" && outline && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <label className="text-sm font-medium text-gray-700 mb-1 block">课件标题</label>
            <input
              type="text"
              value={outline.title}
              onChange={(e) => setOutline({ ...outline, title: e.target.value })}
              className="w-full text-lg font-bold border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {outline.slides.map((slide, idx) => (
            <div key={idx} className="bg-white border rounded-lg p-4 relative group">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-gray-400">第 {idx + 1} 页</span>
                <button
                  onClick={() => handleRemoveSlide(idx)}
                  className="text-xs text-red-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  删除
                </button>
              </div>

              <input
                type="text"
                value={slide.title}
                onChange={(e) => handleUpdateSlide(idx, "title", e.target.value)}
                className="w-full text-sm font-semibold border border-gray-200 rounded-md px-3 py-1.5 mb-2 focus:ring-1 focus:ring-indigo-500"
                placeholder="幻灯片标题"
              />

              <textarea
                value={slide.content.join("\n")}
                onChange={(e) => handleUpdateSlide(idx, "content", e.target.value.split("\n").filter(Boolean))}
                className="w-full text-sm border border-gray-200 rounded-md px-3 py-1.5 resize-y focus:ring-1 focus:ring-indigo-500"
                rows={Math.max(2, slide.content.length)}
                placeholder="要点（每行一个）"
              />
            </div>
          ))}

          <button
            onClick={handleAddSlide}
            className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors"
          >
            + 添加幻灯片
          </button>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStage("input")} className="flex-1">
              返回修改课文
            </Button>
            <Button onClick={handleGeneratePpt} className="flex-[2]" size="lg">
              生成 PPT ({outline.slides.length + 1} 页)
            </Button>
          </div>
        </div>
      )}

      {/* Stage 3: 生成中 */}
      {stage === "generating" && (
        <div className="bg-white border rounded-lg p-12 text-center">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-700">正在生成 PPT 课件...</p>
          <p className="text-sm text-gray-400 mt-1">请稍候，通常需要几秒钟</p>
        </div>
      )}

      {/* Stage 4: 完成 */}
      {stage === "done" && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-8 text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900">PPT 生成成功!</h2>
            <p className="text-gray-500">
              {fileName} - 共 {slideCount} 页
            </p>
            <div className="flex gap-3 justify-center">
              <a
                href={downloadUrl}
                download={fileName}
                className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                下载 PPT
              </a>
              <Button variant="outline" onClick={handleReset} size="lg">
                重新生成
              </Button>
            </div>
          </div>

          {/* 引导到 /merge 优化 */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-5">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-indigo-900 mb-1">
                  想要更精美的课件？用 AI 逐页优化
                </h3>
                <p className="text-xs text-indigo-700 mb-3">
                  下载生成的 PPT 后，前往「合并」页面上传，可以对每页进行 AI 润色、扩展、改写，
                  还能与其他 PPT 融合，打造专业级教学课件。
                </p>
                <a
                  href="/merge"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 transition-colors"
                >
                  前往 AI 优化
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
