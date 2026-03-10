"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { apiBaseUrl } from '@/lib/api'

// 历史记录数据类型
interface HistoryRecord {
  id: number
  session_id: string
  title: string
  grade: string
  subject: string
  style: string
  slide_count: number | null
  chapter: string | null
  file_name: string
  file_path: string
  created_at: string
  download_url?: string
  is_deleted?: boolean
  deleted_at?: string | null
}

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

// 页面类型图标
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

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchKeyword, setSearchKeyword] = useState("")
  const [selectedGrade, setSelectedGrade] = useState("")
  const [selectedSubject, setSelectedSubject] = useState("")
  const [total, setTotal] = useState(0)
  const [limit] = useState(20)
  const [offset, setOffset] = useState(0)
  const [regeneratingId, setRegeneratingId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<"active" | "deleted">("active")
  const [restoringId, setRestoringId] = useState<number | null>(null)

  // 生成 session ID（使用 localStorage 持久化）
  const getSessionId = () => {
    let sessionId = localStorage.getItem("session_id")
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
      localStorage.setItem("session_id", sessionId)
    }
    return sessionId
  }

  // 加载历史记录
  const loadHistory = async () => {
    setLoading(true)
    setError(null)
    const sessionId = getSessionId()

    try {
      let url: string

      if (activeTab === "deleted") {
        // 获取已删除记录
        url = `${apiBaseUrl}/api/v1/history/deleted?session_id=${sessionId}&limit=${limit}&offset=${offset}`
      } else {
        // 构建搜索参数（正常记录）
        const params = new URLSearchParams({
          session_id: sessionId,
          limit: limit.toString(),
          offset: offset.toString(),
        })

        if (searchKeyword) params.append("keyword", searchKeyword)
        if (selectedGrade) params.append("grade", selectedGrade)
        if (selectedSubject) params.append("subject", selectedSubject)

        url = `${apiBaseUrl}/api/v1/history/search?${params}`
      }

      const response = await fetch(url)

      if (!response.ok) {
        throw new Error("加载历史记录失败")
      }

      const result = await response.json()
      setHistory(result.data || [])
      setTotal(result.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [offset, searchKeyword, selectedGrade, selectedSubject, activeTab])

  // 处理下载
  const handleDownload = (record: HistoryRecord) => {
    const downloadUrl = `${apiBaseUrl}/api/v1/ppt/download/${record.file_name}`
    window.open(downloadUrl, "_blank")
  }

  // 处理删除（软删除）
  const handleDelete = async (recordId: number) => {
    if (!confirm("确定要删除这条历史记录吗？\n删除后可到「回收站」恢复。")) return

    const sessionId = getSessionId()

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/history/${recordId}?session_id=${sessionId}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        throw new Error("删除失败")
      }

      // 重新加载列表
      loadHistory()
    } catch (err) {
      alert(err instanceof Error ? err.message : "删除失败")
    }
  }

  // 处理恢复
  const handleRestore = async (recordId: number) => {
    const sessionId = getSessionId()
    setRestoringId(recordId)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/history/${recordId}/restore?session_id=${sessionId}`, {
        method: "POST",
      })

      if (!response.ok) {
        throw new Error("恢复失败")
      }

      // 重新加载列表
      loadHistory()
    } catch (err) {
      alert(err instanceof Error ? err.message : "恢复失败")
    } finally {
      setRestoringId(null)
    }
  }

  // 处理重新生成
  const handleRegenerate = async (record: HistoryRecord) => {
    const sessionId = getSessionId()

    // 获取 LLM 配置
    const savedConfig = localStorage.getItem("llm_config")
    if (!savedConfig) {
      alert("请先在设置页面配置 LLM API Key")
      return
    }

    const llmConfig = JSON.parse(savedConfig)
    if (!llmConfig.apiKey) {
      alert("请先在设置页面配置 LLM API Key")
      return
    }

    setRegeneratingId(record.id)

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/history/${record.id}/regenerate?session_id=${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: llmConfig.apiKey,
          provider: llmConfig.provider || "deepseek",
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "重新生成失败")
      }

      const result = await response.json()
      alert(`重新生成成功！文件名：${result.data?.file_name || "未知"}`)

      // 跳转到上传页面查看结果
      window.location.href = "/upload"
    } catch (err) {
      alert(err instanceof Error ? err.message : "重新生成失败")
    } finally {
      setRegeneratingId(null)
    }
  }

  // 获取年级显示文本
  const getGradeLabel = (grade: string) => {
    const gradeObj = GRADE_OPTIONS.find(g => g.value === grade)
    return gradeObj?.label || `年级${grade}`
  }

  // 获取学科显示文本
  const getSubjectLabel = (subject: string) => {
    const subjectObj = SUBJECT_OPTIONS.find(s => s.value === subject)
    return subjectObj?.label || subject
  }

  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        生成历史记录
      </h1>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 text-red-800 p-4 rounded-lg mb-6">
          {error}
        </div>
      )}

      {/* 标签切换 */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => {
            setActiveTab("active")
            setOffset(0)
          }}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            activeTab === "active"
              ? "bg-indigo-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          全部记录
        </button>
        <button
          onClick={() => {
            setActiveTab("deleted")
            setOffset(0)
          }}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            activeTab === "deleted"
              ? "bg-red-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          回收站
        </button>
      </div>

      {/* 搜索和筛选 - 只在正常记录页显示 */}
      {activeTab === "active" && (
        <div className="bg-white rounded-xl border p-6 shadow-sm mb-6">
          <h2 className="text-lg font-semibold mb-4">搜索与筛选</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* 关键词搜索 */}
            <div className="md:col-span-2">
              <Label htmlFor="search" className="block mb-2">
                搜索关键词
              </Label>
              <Input
                id="search"
                type="text"
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="搜索 PPT 标题或章节名称..."
                className="w-full"
              />
            </div>

            {/* 年级筛选 */}
            <div>
              <Label htmlFor="grade-filter" className="block mb-2">
                年级筛选
              </Label>
              <Select
                id="grade-filter"
                value={selectedGrade}
                onChange={(e) => {
                  setSelectedGrade(e.target.value)
                  setOffset(0)
                }}
              >
                <option value="">全部年级</option>
                {GRADE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {/* 学科筛选 */}
            <div>
              <Label htmlFor="subject-filter" className="block mb-2">
                学科筛选
              </Label>
              <Select
                id="subject-filter"
                value={selectedSubject}
                onChange={(e) => {
                  setSelectedSubject(e.target.value)
                  setOffset(0)
                }}
              >
                <option value="">全部学科</option>
                {SUBJECT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
            <span>共 {total} 条记录</span>
            {offset > 0 && (
              <button
                onClick={() => setOffset(0)}
                className="text-indigo-600 hover:text-indigo-800"
              >
                重置筛选
              </button>
            )}
          </div>
        </div>
      )}

      {/* 历史记录列表 */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">
          加载中...
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          {activeTab === "deleted" ? (
            <>
              🗑️ 回收站为空
              <div className="mt-2 text-sm">
                删除的记录会保留在这里，可随时恢复
              </div>
            </>
          ) : (
            <>
              📭 暂无历史记录
              <div className="mt-2 text-sm">
                去 <a href="/upload" className="text-indigo-600 hover:underline">生成 PPT</a> 创建第一条记录吧！
              </div>
            </>
          )}
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {history.map((record) => (
              <div
                key={record.id}
                className={`rounded-xl border p-6 shadow-sm transition ${
                  record.is_deleted
                    ? "bg-gray-50 border-gray-200"
                    : "bg-white hover:shadow-md"
                }`}
              >
                <div className="flex items-start justify-between">
                  {/* 左侧：PPT 信息 */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">📖</span>
                      <h3 className={`text-xl font-semibold ${
                        record.is_deleted ? "text-gray-500" : "text-gray-900"
                      }`}>
                        {record.title}
                      </h3>
                      {record.is_deleted && (
                        <span className="bg-red-100 text-red-700 px-2 py-1 rounded text-sm">
                          已删除
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-4 mb-3 text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded ${
                        record.is_deleted
                          ? "bg-gray-100 text-gray-500"
                          : "bg-indigo-100 text-indigo-700"
                      }`}>
                        {getGradeLabel(record.grade)}
                      </span>
                      <span className={`px-2 py-1 rounded ${
                        record.is_deleted
                          ? "bg-gray-100 text-gray-500"
                          : "bg-emerald-100 text-emerald-700"
                      }`}>
                        {getSubjectLabel(record.subject)}
                      </span>
                      <span className={`px-2 py-1 rounded ${
                        record.is_deleted
                          ? "bg-gray-100 text-gray-500"
                          : "bg-amber-100 text-amber-700"
                      }`}>
                        {record.slide_count || "--"}页
                      </span>
                      {record.chapter && (
                        <span className="text-gray-400">
                          📑 {record.chapter}
                        </span>
                      )}
                    </div>

                    <div className="text-sm text-gray-400">
                      {record.is_deleted && record.deleted_at ? (
                        <span>🗑️ 删除于 {formatDate(record.deleted_at)}</span>
                      ) : (
                        <span>🕐 {formatDate(record.created_at)}</span>
                      )}
                    </div>
                  </div>

                  {/* 右侧：操作按钮 */}
                  <div className="flex flex-col gap-2">
                    {record.is_deleted ? (
                      <>
                        <Button
                          onClick={() => handleRestore(record.id)}
                          disabled={restoringId === record.id}
                          className="bg-emerald-600 hover:bg-emerald-700"
                        >
                          {restoringId === record.id ? "恢复中..." : "↩️ 恢复"}
                        </Button>
                        <Button
                          variant="outline"
                          disabled
                          className="text-gray-400"
                        >
                          下载 PPT
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          onClick={() => handleDownload(record)}
                          className="bg-indigo-600 hover:bg-indigo-700"
                        >
                          下载 PPT
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleRegenerate(record)}
                          disabled={regeneratingId === record.id}
                        >
                          {regeneratingId === record.id ? "生成中..." : "重新生成"}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleDelete(record.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          删除
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 分页 */}
          {total > limit && (
            <div className="flex items-center justify-between mt-6">
              <Button
                variant="outline"
                onClick={() => setOffset(prev => Math.max(0, prev - limit))}
                disabled={offset === 0}
              >
                ← 上一页
              </Button>

              <span className="text-gray-500">
                {Math.floor(offset / limit) + 1} / {Math.ceil(total / limit)}
              </span>

              <Button
                variant="outline"
                onClick={() => setOffset(prev => prev + limit)}
                disabled={offset + limit >= total}
              >
                下一页 →
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
