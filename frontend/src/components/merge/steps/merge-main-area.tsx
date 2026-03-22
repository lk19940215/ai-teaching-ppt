"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { SUBJECT_OPTIONS, GRADE_OPTIONS } from '@/hooks/useMergePage'
import { SlidePreviewPanel } from '@/components/merge/panels/slide-preview-panel'
import { PromptTemplatesPanel } from '@/components/merge/controls/prompt-templates-panel'
import type { SlidePoolItem, SlideVersion, SlideAction } from "@/types/merge-session"
import { ACTION_CONFIG } from "@/types/merge-session"

const MAIN_ACTIONS = ['polish', 'expand', 'rewrite', 'extract'] as const
type ActionKey = (typeof MAIN_ACTIONS)[number]

export interface MergeMainAreaProps {
  activeSlide: SlidePoolItem | null
  activeVersion: SlideVersion | null
  isInFinalSelection: boolean
  isProcessing: boolean
  currentAction: any
  progressInfo: any
  globalPrompt: string
  showTemplates: boolean
  subject: string
  grade: string
  fileA?: File | null
  fileB?: File | null
  finalCount: number
  alwaysPrompt: string
  onAlwaysPromptChange: (prompt: string) => void
  onSwitchVersion: (versionId: string) => void
  onProcess: (action: any, prompt?: string) => Promise<void>
  onPromptChange: (prompt: string) => void
  onToggleTemplates: () => void
  onSubjectChange: (subject: string) => void
  onGradeChange: (grade: string) => void
  onAddToFinal: () => void
  onRemoveFromFinal: () => void
  multiSelectedIds?: string[]
  onBatchProcess?: (slideIds: string[], action: SlideAction) => Promise<void>
  onMergeSelected?: (slideIds: string[]) => Promise<void>
  isMerging?: boolean
  batchProgress?: { current: number; total: number } | null
  onClearMultiSelect?: () => void
}

export function MergeMainArea({
  activeSlide,
  activeVersion,
  isInFinalSelection,
  isProcessing,
  currentAction,
  progressInfo,
  globalPrompt,
  showTemplates,
  subject,
  grade,
  fileA,
  fileB,
  finalCount,
  alwaysPrompt,
  onAlwaysPromptChange,
  onSwitchVersion,
  onProcess,
  onPromptChange,
  onToggleTemplates,
  onSubjectChange,
  onGradeChange,
  onAddToFinal,
  onRemoveFromFinal,
  multiSelectedIds = [],
  onBatchProcess,
  onMergeSelected,
  isMerging,
  batchProgress,
  onClearMultiSelect,
}: MergeMainAreaProps) {
  const [selectedAction, setSelectedAction] = useState<ActionKey | null>(null)

  const isBatchMode = multiSelectedIds.length > 0

  const handleActionClick = (action: ActionKey) => {
    setSelectedAction(action)
    const template = ACTION_CONFIG[action].template
    if (template) onPromptChange(template)
  }

  const handleExecute = () => {
    if (selectedAction) {
      const combinedPrompt = [alwaysPrompt, globalPrompt].filter(Boolean).join('\n')
      onProcess(selectedAction, combinedPrompt || undefined)
    }
  }

  const handleBatchExecute = () => {
    if (!selectedAction || !onBatchProcess || multiSelectedIds.length === 0) return
    const label = ACTION_CONFIG[selectedAction].label
    const confirmed = window.confirm(
      `确认对选中的 ${multiSelectedIds.length} 页执行「${label}」操作？\n\n将逐页调用 AI 处理，可能需要较长时间。`
    )
    if (confirmed) {
      const ids = [...multiSelectedIds]
      onClearMultiSelect?.()
      onBatchProcess(ids, selectedAction)
    }
  }

  const handleMerge = () => {
    if (!onMergeSelected || multiSelectedIds.length < 2) return
    const ids = [...multiSelectedIds]
    onClearMultiSelect?.()
    onMergeSelected(ids)
  }

  return (
    <div className="grid grid-cols-12 gap-4">
      {/* 左侧：预览 */}
      <div className="col-span-8">
        <SlidePreviewPanel
          slide={activeSlide}
          version={activeVersion}
          isInFinalSelection={isInFinalSelection}
          isProcessing={isProcessing}
          currentAction={currentAction}
          progressInfo={progressInfo}
          globalPrompt={globalPrompt}
          fileA={fileA}
          fileB={fileB}
          onSwitchVersion={onSwitchVersion}
          onProcess={onProcess}
          onInjectPrompt={onPromptChange}
          onAddToFinal={onAddToFinal}
          onRemoveFromFinal={onRemoveFromFinal}
          className="min-h-[400px]"
        />
      </div>

      {/* 右侧：操作面板 */}
      <div className="col-span-4 space-y-3">
        {/* 学科/年级 */}
        <div className="bg-white border rounded-lg p-3">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">学科</label>
              <select
                value={subject || '_default'}
                onChange={(e) => onSubjectChange(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-md px-2 py-1.5 bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {SUBJECT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">年级</label>
              <select
                value={grade || ''}
                onChange={(e) => onGradeChange(e.target.value)}
                className="w-full text-xs border border-gray-300 rounded-md px-2 py-1.5 bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {GRADE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* 操作类型 */}
        <div className="bg-white border rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-500">选择操作类型</p>
            {isBatchMode && (
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full">
                  已选 {multiSelectedIds.length} 页
                </span>
                {multiSelectedIds.length >= 2 && onMergeSelected && (
                  <button
                    onClick={handleMerge}
                    disabled={isMerging}
                    className="text-[10px] px-2 py-0.5 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
                  >
                    {isMerging ? '融合中...' : '融合'}
                  </button>
                )}
                <button
                  onClick={onClearMultiSelect}
                  className="text-[10px] text-purple-500 hover:text-purple-700 underline"
                >
                  取消
                </button>
              </div>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2">
            {MAIN_ACTIONS.map((action) => (
              <Button
                key={action}
                variant={selectedAction === action ? "default" : "outline"}
                size="sm"
                onClick={() => handleActionClick(action)}
                disabled={isProcessing}
                className={cn(
                  "flex flex-col items-center gap-0.5 h-auto py-2",
                  selectedAction === action && "ring-2 ring-indigo-300"
                )}
              >
                <span className="text-lg">{ACTION_CONFIG[action].icon}</span>
                <span className="text-xs">{ACTION_CONFIG[action].label}</span>
              </Button>
            ))}
          </div>

          {selectedAction && globalPrompt && !isBatchMode && (
            <Button
              onClick={handleExecute}
              disabled={isProcessing}
              className="w-full mt-2"
              size="sm"
            >
              {isProcessing ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />
                  {ACTION_CONFIG[selectedAction]?.label}中...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  执行{ACTION_CONFIG[selectedAction]?.label}
                </>
              )}
            </Button>
          )}

          {selectedAction && isBatchMode && (
            <Button
              onClick={handleBatchExecute}
              disabled={isProcessing}
              className="w-full mt-2 bg-purple-600 hover:bg-purple-700"
              size="sm"
            >
              {isProcessing ? (
                <>
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />
                  批量{ACTION_CONFIG[selectedAction]?.label}中...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  批量{ACTION_CONFIG[selectedAction]?.label} ({multiSelectedIds.length} 页)
                </>
              )}
            </Button>
          )}

          {batchProgress && (
            <div className="mt-2 p-2 bg-amber-50 border border-amber-200 rounded-md">
              <div className="flex items-center gap-2 text-xs text-amber-700">
                <span className="w-3 h-3 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
                <span className="font-medium">
                  批量处理中... ({batchProgress.current}/{batchProgress.total})
                </span>
              </div>
              <div className="mt-1.5 w-full bg-amber-200 rounded-full h-1.5">
                <div
                  className="bg-amber-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${Math.round((batchProgress.current / batchProgress.total) * 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* 已选统计 */}
        <div className="bg-white border rounded-lg p-3 text-center">
          <span className="text-2xl font-bold text-indigo-600">{finalCount}</span>
          <span className="text-xs text-gray-500 ml-1">页已选中</span>
        </div>

        {/* 总是注入的提示语 */}
        <div className="bg-white border rounded-lg p-3">
          <h4 className="text-xs font-medium text-gray-700 mb-1.5">总是注入的提示语</h4>
          <textarea
            value={alwaysPrompt}
            onChange={(e) => onAlwaysPromptChange(e.target.value)}
            placeholder="每次 AI 操作时自动附加的提示语..."
            className="w-full text-xs border border-gray-300 rounded-md px-2 py-1.5 bg-gray-50 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
            rows={2}
          />
          <p className="text-[10px] text-gray-400 mt-1">此内容会自动拼接到每次操作的提示词中</p>
        </div>

        {/* 合并策略 */}
        <PromptTemplatesPanel
          globalPrompt={globalPrompt}
          onPromptChange={onPromptChange}
          showTemplates={showTemplates}
          onToggleTemplates={onToggleTemplates}
        />
      </div>
    </div>
  )
}
