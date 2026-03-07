"use client"

import * as React from "react"
import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { PptPageData } from "@/components/ppt-preview"

// 页面级提示语数据结构
export interface PagePrompt {
  // 页面索引（从 0 开始）
  pageIndex: number
  // 所属 PPT（'A' | 'B'）
  pptSource: 'A' | 'B'
  // 提示语内容
  prompt: string
}

// PromptEditor 组件属性
interface PromptEditorProps {
  // PPT A 的页面数据
  pagesA: PptPageData[]
  // PPT B 的页面数据
  pagesB: PptPageData[]
  // 选中的 A 页面索引
  selectedPagesA: number[]
  // 选中的 B 页面索引
  selectedPagesB: number[]
  // 页面级提示语映射（key: `${pptSource}-${pageIndex}`）
  pagePrompts?: Record<string, string>
  // 页面级提示语变化回调
  onPagePromptsChange?: (prompts: Record<string, string>) => void
  // 总提示语
  globalPrompt?: string
  // 总提示语变化回调
  onGlobalPromptChange?: (prompt: string) => void
  // 是否禁用编辑
  disabled?: boolean
}

/**
 * 提示语编辑组件（feat-077）
 *
 * 功能：
 * - 显示已选中页面的列表
 * - 支持为每页添加/编辑提示语
 * - 总提示语输入区域
 * - 实时预览所有提示语汇总
 */
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
}: PromptEditorProps) {
  const [localPagePrompts, setLocalPagePrompts] = useState<Record<string, string>>(pagePrompts)
  const [localGlobalPrompt, setLocalGlobalPrompt] = useState(globalPrompt)

  // 同步外部状态变化
  React.useEffect(() => {
    setLocalPagePrompts(pagePrompts)
  }, [pagePrompts])

  React.useEffect(() => {
    setLocalGlobalPrompt(globalPrompt)
  }, [globalPrompt])

  // 获取页面的标题（截断）
  const getPageTitle = (pptSource: 'A' | 'B', pageIndex: number): string => {
    const pages = pptSource === 'A' ? pagesA : pagesB
    const page = pages.find(p => p.index === pageIndex)
    if (!page) return `P${pageIndex + 1}`
    return page.title.length > 20 ? page.title.substring(0, 20) + "..." : page.title
  }

  // 处理单个页面提示语变化
  const handlePagePromptChange = (pptSource: 'A' | 'B', pageIndex: number, value: string) => {
    const key = `${pptSource}-${pageIndex}`
    const newPrompts = { ...localPagePrompts, [key]: value }
    setLocalPagePrompts(newPrompts)
    onPagePromptsChange?.(newPrompts)
  }

  // 处理总提示语变化
  const handleGlobalPromptChange = (value: string) => {
    setLocalGlobalPrompt(value)
    onGlobalPromptChange?.(value)
  }

  // 清空单个页面提示语
  const handleClearPagePrompt = (pptSource: 'A' | 'B', pageIndex: number) => {
    const key = `${pptSource}-${pageIndex}`
    const { [key]: _, ...rest } = localPagePrompts
    setLocalPagePrompts(rest)
    onPagePromptsChange?.(rest)
  }

  // 清空所有页面提示语
  const handleClearAllPagePrompts = () => {
    setLocalPagePrompts({})
    onPagePromptsChange?.({})
  }

  // 获取所有选中的页面列表
  const allSelectedPages: Array<{ pptSource: 'A' | 'B'; pageIndex: number }> = [
    ...selectedPagesA.map(i => ({ pptSource: 'A' as const, pageIndex: i })),
    ...selectedPagesB.map(i => ({ pptSource: 'B' as const, pageIndex: i })),
  ]

  // 按 PPT 分组显示
  const selectedPagesAWithData = selectedPagesA
    .map(i => pagesA.find(p => p.index === i))
    .filter((p): p is PptPageData => !!p)

  const selectedPagesBWithData = selectedPagesB
    .map(i => pagesB.find(p => p.index === i))
    .filter((p): p is PptPageData => !!p)

  return (
    <div className="space-y-4">
      {/* 页面级提示语区域 */}
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
              onClick={handleClearAllPagePrompts}
              disabled={disabled}
              className="h-6 text-xs text-gray-500 hover:text-red-600"
            >
              清空全部
            </Button>
          )}
        </div>

        {allSelectedPages.length === 0 ? (
          <div className="text-center py-6 border-2 border-dashed border-gray-200 rounded-lg">
            <svg className="mx-auto h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
            </svg>
            <p className="mt-2 text-sm text-gray-500">在左侧选择需要合并的页面</p>
          </div>
        ) : (
          <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
            {/* PPT A 选中页面提示语 */}
            {selectedPagesAWithData.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-indigo-600 uppercase tracking-wide">
                  PPT A（{selectedPagesAWithData.length} 页）
                </p>
                {selectedPagesAWithData.map(page => {
                  const key = `A-${page.index}`
                  const value = localPagePrompts[key] || ""
                  const hasPrompt = value.trim().length > 0

                  return (
                    <div key={key} className="relative">
                      <div className={cn(
                        "flex items-start gap-2 p-2 rounded border transition-colors",
                        hasPrompt
                          ? "border-indigo-300 bg-indigo-50"
                          : "border-gray-200 bg-gray-50"
                      )}>
                        <span className="flex-shrink-0 w-8 h-6 flex items-center justify-center bg-gray-200 text-gray-700 text-xs rounded font-mono">
                          P{page.index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-gray-600 truncate mb-1">
                            {getPageTitle('A', page.index)}
                          </p>
                          <textarea
                            value={value}
                            onChange={(e) => handlePagePromptChange('A', page.index, e.target.value)}
                            placeholder="例如：保留此页，与 B 第 5 页合并..."
                            className="w-full h-16 p-2 text-sm border border-gray-300 rounded resize-none focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-transparent"
                            disabled={disabled}
                          />
                        </div>
                        {hasPrompt && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleClearPagePrompt('A', page.index)}
                            disabled={disabled}
                            className="h-6 w-6 p-0 text-gray-400 hover:text-red-600 flex-shrink-0"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </Button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}

            {/* PPT B 选中页面提示语 */}
            {selectedPagesBWithData.length > 0 && (
              <div className="space-y-2 pt-2 border-t">
                <p className="text-xs font-medium text-emerald-600 uppercase tracking-wide">
                  PPT B（{selectedPagesBWithData.length} 页）
                </p>
                {selectedPagesBWithData.map(page => {
                  const key = `B-${page.index}`
                  const value = localPagePrompts[key] || ""
                  const hasPrompt = value.trim().length > 0

                  return (
                    <div key={key} className="relative">
                      <div className={cn(
                        "flex items-start gap-2 p-2 rounded border transition-colors",
                        hasPrompt
                          ? "border-emerald-300 bg-emerald-50"
                          : "border-gray-200 bg-gray-50"
                      )}>
                        <span className="flex-shrink-0 w-8 h-6 flex items-center justify-center bg-gray-200 text-gray-700 text-xs rounded font-mono">
                          P{page.index + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-gray-600 truncate mb-1">
                            {getPageTitle('B', page.index)}
                          </p>
                          <textarea
                            value={value}
                            onChange={(e) => handlePagePromptChange('B', page.index, e.target.value)}
                            placeholder="例如：将此页内容插入到 A 第 3 页之后..."
                            className="w-full h-16 p-2 text-sm border border-gray-300 rounded resize-none focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-transparent"
                            disabled={disabled}
                          />
                        </div>
                        {hasPrompt && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => handleClearPagePrompt('B', page.index)}
                            disabled={disabled}
                            className="h-6 w-6 p-0 text-gray-400 hover:text-red-600 flex-shrink-0"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </Button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 总提示语输入区域 */}
      <div className="pt-2 border-t">
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
          placeholder="例如：保留 PPT A 的课程结构，将 PPT B 的例题插入到对应知识点后面；注意保持风格统一..."
          className="w-full h-28 p-3 text-sm border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          disabled={disabled}
        />
        <p className="mt-1 text-xs text-gray-500">
          当前字数：{localGlobalPrompt.length}
        </p>
      </div>

      {/* 提示语汇总预览 */}
      {(Object.keys(localPagePrompts).length > 0 || localGlobalPrompt.trim().length > 0) && (
        <div className="pt-3 border-t">
          <Label className="text-sm font-medium text-gray-700 mb-2 block">
            提示语汇总预览
          </Label>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 max-h-48 overflow-y-auto">
            {Object.entries(localPagePrompts).map(([key, prompt]) => {
              if (!prompt.trim()) return null
              const [pptSource, pageIndex] = key.split('-')
              const pageNum = parseInt(pageIndex) + 1
              return (
                <div key={key} className="mb-2 last:mb-0">
                  <span className={cn(
                    "text-xs font-medium px-1.5 py-0.5 rounded mr-2",
                    pptSource === 'A' ? "bg-indigo-100 text-indigo-700" : "bg-emerald-100 text-emerald-700"
                  )}>
                    {pptSource} 第{pageNum}页
                  </span>
                  <span className="text-xs text-gray-600">{prompt}</span>
                </div>
              )
            })}
            {localGlobalPrompt.trim().length > 0 && (
              <div className="pt-2 mt-2 border-t border-gray-200">
                <span className="text-xs font-medium bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded mr-2">
                  总体策略
                </span>
                <span className="text-xs text-gray-600">{localGlobalPrompt}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default PromptEditor
