"use client"

import * as React from "react"
import { useState, useRef } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { PptPageData } from "@/components/ppt-preview"

export interface StructuredPagePrompt {
  keep?: string
  discard?: string
}

export interface PagePrompt {
  pageIndex: number
  pptSource: 'A' | 'B'
  prompt: string
}

interface PromptEditorProps {
  pagesA: PptPageData[]
  pagesB: PptPageData[]
  selectedPagesA: number[]
  selectedPagesB: number[]
  pagePrompts?: Record<string, StructuredPagePrompt>
  onPagePromptsChange?: (prompts: Record<string, StructuredPagePrompt>) => void
  globalPrompt?: string
  onGlobalPromptChange?: (prompt: string) => void
  disabled?: boolean
  focusPage?: { pptSource: 'A' | 'B'; pageIndex: number } | null
}

const SYSTEM_TEMPLATES = [
  {
    id: 'keep-a-structure',
    name: '保留 A 结构',
    icon: '🏗️',
    description: '以 PPT A 的结构为主，将 B 的内容融入',
    prompt: '以 PPT A 的课程结构为主框架，将 PPT B 中的补充内容、例题和素材按知识点融入到 A 对应的位置。保持 A 的整体逻辑和教学流程不变。'
  },
  {
    id: 'keep-b-structure',
    name: '保留 B 结构',
    icon: '🔄',
    description: '以 PPT B 的结构为主，将 A 的内容融入',
    prompt: '以 PPT B 的课程结构为主框架，将 PPT A 中的补充内容和素材按知识点融入到 B 对应的位置。保持 B 的整体逻辑和教学流程不变。'
  },
  {
    id: 'merge-best',
    name: '取精华合并',
    icon: '⭐',
    description: '从两个 PPT 中各取最好的部分合并',
    prompt: '分析 PPT A 和 PPT B 的内容质量，从两者中选取最优质的部分进行合并：优先保留更详细的知识点讲解、更丰富的例题、更清晰的图表。去除重复和冗余内容。'
  },
  {
    id: 'sequential',
    name: '顺序拼接',
    icon: '📋',
    description: '先 A 后 B 依次排列，去重',
    prompt: '将 PPT A 的所有页面排在前面，PPT B 的页面排在后面。如果发现两者有重复或高度相似的页面，只保留内容更完整的版本。'
  },
  {
    id: 'style-unify',
    name: '风格统一',
    icon: '🎨',
    description: '合并内容并统一视觉风格',
    prompt: '合并两个 PPT 的内容，并统一整体视觉风格：包括字体、字号、配色方案、标题格式等。确保合并后的课件看起来像一套完整的教学材料。'
  },
]

export function PromptEditor({
  pagesA = [],
  pagesB = [],
  selectedPagesA = [],
  selectedPagesB = [],
  pagePrompts = {},
  onPagePromptsChange,
  globalPrompt = "",
  onGlobalPromptChange,
  disabled = false,
  focusPage = null,
}: PromptEditorProps) {
  const [localPagePrompts, setLocalPagePrompts] = useState<Record<string, StructuredPagePrompt>>(pagePrompts)
  const [localGlobalPrompt, setLocalGlobalPrompt] = useState(globalPrompt)
  const [showTemplates, setShowTemplates] = useState(false)
  const inputRefs = useRef<Record<string, HTMLTextAreaElement | null>>({})

  React.useEffect(() => {
    setLocalPagePrompts(pagePrompts)
  }, [pagePrompts])

  React.useEffect(() => {
    setLocalGlobalPrompt(globalPrompt)
  }, [globalPrompt])

  React.useEffect(() => {
    if (!focusPage) return
    const key = `${focusPage.pptSource}-${focusPage.pageIndex}`
    const keepEl = inputRefs.current[`${key}-keep`]
    if (keepEl) {
      keepEl.scrollIntoView({ behavior: 'smooth', block: 'center' })
      keepEl.focus()
    }
  }, [focusPage])

  const getPageTitle = (pptSource: 'A' | 'B', pageIndex: number): string => {
    const pages = pptSource === 'A' ? pagesA : pagesB
    const page = pages.find(p => p.index === pageIndex)
    if (!page) return `P${pageIndex + 1}`
    return page.title.length > 20 ? page.title.substring(0, 20) + "..." : page.title
  }

  const handlePromptChange = (pptSource: 'A' | 'B', pageIndex: number, field: 'keep' | 'discard', value: string) => {
    const key = `${pptSource}-${pageIndex}`
    const current = localPagePrompts[key] || {}
    const updated = { ...current, [field]: value }

    if (!updated.keep?.trim() && !updated.discard?.trim()) {
      const { [key]: _, ...rest } = localPagePrompts
      setLocalPagePrompts(rest)
      onPagePromptsChange?.(rest)
    } else {
      const newPrompts = { ...localPagePrompts, [key]: updated }
      setLocalPagePrompts(newPrompts)
      onPagePromptsChange?.(newPrompts)
    }
  }

  const handleGlobalPromptChange = (value: string) => {
    setLocalGlobalPrompt(value)
    onGlobalPromptChange?.(value)
  }

  const handleClearPagePrompt = (pptSource: 'A' | 'B', pageIndex: number) => {
    const key = `${pptSource}-${pageIndex}`
    const { [key]: _, ...rest } = localPagePrompts
    setLocalPagePrompts(rest)
    onPagePromptsChange?.(rest)
  }

  const handleClearAll = () => {
    setLocalPagePrompts({})
    onPagePromptsChange?.({})
  }

  const applyTemplate = (template: typeof SYSTEM_TEMPLATES[0]) => {
    handleGlobalPromptChange(template.prompt)
    setShowTemplates(false)
  }

  const selectedPagesAWithData = selectedPagesA
    .map(i => pagesA.find(p => p.index === i))
    .filter((p): p is PptPageData => !!p)

  const selectedPagesBWithData = selectedPagesB
    .map(i => pagesB.find(p => p.index === i))
    .filter((p): p is PptPageData => !!p)

  const allSelectedPages = [
    ...selectedPagesA.map(i => ({ pptSource: 'A' as const, pageIndex: i })),
    ...selectedPagesB.map(i => ({ pptSource: 'B' as const, pageIndex: i })),
  ]

  const renderPagePromptCard = (pptSource: 'A' | 'B', page: PptPageData) => {
    const key = `${pptSource}-${page.index}`
    const prompt = localPagePrompts[key] || {}
    const hasContent = !!(prompt.keep?.trim() || prompt.discard?.trim())
    const colorScheme = pptSource === 'A'
      ? { border: 'border-indigo-200', bg: 'bg-indigo-50/50', label: 'text-indigo-600', accent: 'indigo' }
      : { border: 'border-emerald-200', bg: 'bg-emerald-50/50', label: 'text-emerald-600', accent: 'emerald' }

    return (
      <div key={key} className={cn("rounded-lg border p-3 transition-colors", hasContent ? colorScheme.border : "border-gray-200")}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={cn(
              "flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold",
              pptSource === 'A' ? "bg-indigo-100 text-indigo-700" : "bg-emerald-100 text-emerald-700"
            )}>
              {pptSource}-P{page.index + 1}
            </span>
            <span className="text-xs text-gray-500 truncate max-w-[140px]">
              {getPageTitle(pptSource, page.index)}
            </span>
          </div>
          {hasContent && (
            <button
              onClick={() => handleClearPagePrompt(pptSource, page.index)}
              disabled={disabled}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* 保留字段 */}
        <div className="mb-2">
          <label className="text-[10px] font-medium text-green-700 mb-0.5 flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full inline-block" />
            保留（可选）
          </label>
          <textarea
            ref={(el) => { inputRefs.current[`${key}-keep`] = el }}
            value={prompt.keep || ""}
            onChange={(e) => handlePromptChange(pptSource, page.index, 'keep', e.target.value)}
            placeholder="填入需要保留的内容..."
            className="w-full h-12 p-1.5 text-xs border border-green-200 rounded resize-none focus:outline-none focus:ring-1 focus:ring-green-400 focus:border-green-400 bg-green-50/30"
            disabled={disabled}
          />
        </div>

        {/* 废弃字段 */}
        <div>
          <label className="text-[10px] font-medium text-red-600 mb-0.5 flex items-center gap-1">
            <span className="w-2 h-2 bg-red-500 rounded-full inline-block" />
            废弃（可选）
          </label>
          <textarea
            ref={(el) => { inputRefs.current[`${key}-discard`] = el }}
            value={prompt.discard || ""}
            onChange={(e) => handlePromptChange(pptSource, page.index, 'discard', e.target.value)}
            placeholder="填入需要废弃的内容..."
            className="w-full h-12 p-1.5 text-xs border border-red-200 rounded resize-none focus:outline-none focus:ring-1 focus:ring-red-400 focus:border-red-400 bg-red-50/30"
            disabled={disabled}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 系统提示词模板 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="text-sm font-medium text-gray-700">
            合并策略模板
          </Label>
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            className="text-xs text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            {showTemplates ? '收起' : '展开模板'}
          </button>
        </div>

        {showTemplates && (
          <div className="grid grid-cols-1 gap-2 mb-3">
            {SYSTEM_TEMPLATES.map(template => (
              <button
                key={template.id}
                onClick={() => applyTemplate(template)}
                disabled={disabled}
                className={cn(
                  "flex items-start gap-2 p-2 rounded-lg border text-left transition-all hover:shadow-sm",
                  localGlobalPrompt === template.prompt
                    ? "border-indigo-300 bg-indigo-50"
                    : "border-gray-200 bg-white hover:border-indigo-200 hover:bg-indigo-50/30"
                )}
              >
                <span className="text-lg flex-shrink-0 mt-0.5">{template.icon}</span>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-900">{template.name}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{template.description}</p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 总提示语输入区域 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label htmlFor="global-prompt-editor" className="text-sm font-medium text-gray-700">
            总体合并策略
          </Label>
          {localGlobalPrompt.trim().length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handleGlobalPromptChange("")}
              disabled={disabled}
              className="h-6 text-xs text-gray-500 hover:text-red-600"
            >
              清空
            </Button>
          )}
        </div>
        <textarea
          id="global-prompt-editor"
          value={localGlobalPrompt}
          onChange={(e) => handleGlobalPromptChange(e.target.value)}
          placeholder="选择上方模板或自行输入合并策略..."
          className="w-full h-24 p-3 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          disabled={disabled}
        />
        <p className="mt-1 text-xs text-gray-400">
          {localGlobalPrompt.length} 字
        </p>
      </div>

      {/* 页面级提示语 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="text-sm font-medium text-gray-700">
            页面级提示语
          </Label>
          {Object.keys(localPagePrompts).length > 0 && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              disabled={disabled}
              className="h-6 text-xs text-gray-500 hover:text-red-600"
            >
              清空全部
            </Button>
          )}
        </div>

        {allSelectedPages.length === 0 ? (
          <div className="text-center py-4 border-2 border-dashed border-gray-200 rounded-lg">
            <svg className="mx-auto h-6 w-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
            <p className="mt-1 text-xs text-gray-500">在左侧选择页面后，可为每页设置保留/废弃指令</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {selectedPagesAWithData.length > 0 && (
              <div className="space-y-2">
                <p className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider">
                  PPT A（{selectedPagesAWithData.length} 页）
                </p>
                {selectedPagesAWithData.map(page => renderPagePromptCard('A', page))}
              </div>
            )}

            {selectedPagesBWithData.length > 0 && (
              <div className="space-y-2 pt-2 border-t">
                <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">
                  PPT B（{selectedPagesBWithData.length} 页）
                </p>
                {selectedPagesBWithData.map(page => renderPagePromptCard('B', page))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 提示语汇总 */}
      {(Object.keys(localPagePrompts).length > 0 || localGlobalPrompt.trim().length > 0) && (
        <div className="pt-3 border-t">
          <Label className="text-sm font-medium text-gray-700 mb-2 block">
            提示语汇总
          </Label>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 max-h-40 overflow-y-auto text-xs">
            {Object.entries(localPagePrompts).map(([key, prompt]) => {
              if (!prompt.keep?.trim() && !prompt.discard?.trim()) return null
              const [pptSource, pageIndex] = key.split('-')
              const pageNum = parseInt(pageIndex) + 1
              return (
                <div key={key} className="mb-2 last:mb-0">
                  <span className={cn(
                    "font-medium px-1.5 py-0.5 rounded mr-1",
                    pptSource === 'A' ? "bg-indigo-100 text-indigo-700" : "bg-emerald-100 text-emerald-700"
                  )}>
                    {pptSource} P{pageNum}
                  </span>
                  {prompt.keep?.trim() && (
                    <span className="text-green-700">保留: {prompt.keep.trim()}</span>
                  )}
                  {prompt.keep?.trim() && prompt.discard?.trim() && <span className="text-gray-400 mx-1">|</span>}
                  {prompt.discard?.trim() && (
                    <span className="text-red-600">废弃: {prompt.discard.trim()}</span>
                  )}
                </div>
              )
            })}
            {localGlobalPrompt.trim().length > 0 && (
              <div className="pt-2 mt-2 border-t border-gray-200">
                <span className="font-medium bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded mr-1">
                  总体策略
                </span>
                <span className="text-gray-600">{localGlobalPrompt}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default PromptEditor
