/**
 * 提示词模板面板组件
 * 提供预设的合并策略模板
 */

"use client"

import { Textarea } from "@/components/ui/textarea"

// 提示词模板定义
export const PROMPT_TEMPLATES = [
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

export interface PromptTemplatesPanelProps {
  globalPrompt: string
  onPromptChange: (prompt: string) => void
  showTemplates?: boolean
  onToggleTemplates?: () => void
}

export function PromptTemplatesPanel({
  globalPrompt,
  onPromptChange,
  showTemplates = false,
  onToggleTemplates,
}: PromptTemplatesPanelProps) {
  return (
    <div className="bg-white border rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-900">合并策略</h4>
        <button
          onClick={onToggleTemplates}
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
              onClick={() => onPromptChange(template.prompt)}
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
        onChange={(e) => onPromptChange(e.target.value)}
        placeholder="输入合并策略或选择上方模板..."
        className="min-h-[80px] text-sm"
      />
      <p className="mt-1 text-xs text-gray-400">{globalPrompt.length} 字</p>
    </div>
  )
}