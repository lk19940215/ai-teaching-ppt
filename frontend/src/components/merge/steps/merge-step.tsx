"use client"

import { Button } from "@/components/ui/button"
import type { useMergePage } from '@/hooks/useMergePage'
import { SlidePoolPanel } from '@/components/merge/panels/slide-pool-panel'
import { FinalSelectionBar } from '@/components/merge/panels/final-selection-bar'
import { MergeMainArea } from './merge-main-area'

export interface MergeStepProps {
  pptA: File | null
  pptB: File | null
  session: ReturnType<typeof useMergePage>['session']
  activeSlide: ReturnType<typeof useMergePage>['activeSlide']
  activeVersion: ReturnType<typeof useMergePage>['activeVersion']
  isInFinalSelection: boolean
  finalSelectionDetails: ReturnType<typeof useMergePage>['finalSelectionDetails']
  globalPrompt: string
  showTemplates: boolean
  subject: string
  grade: string
  alwaysPrompt: string
  onAlwaysPromptChange: (prompt: string) => void
  onSlideClick: (slideId: string) => void
  onSwitchVersion: (versionId: string) => void
  onProcess: (action: any, prompt?: string) => Promise<void>
  onAddToFinal: () => void
  onRemoveFromFinal: () => void
  addToFinal: (versionId: string) => void
  removeFromFinal: (versionId: string) => void
  onMergeSelected: (slideIds: string[]) => Promise<void>
  onGenerateFinal: () => Promise<void>
  onPromptChange: (prompt: string) => void
  onToggleTemplates: () => void
  onSubjectChange: (subject: string) => void
  onGradeChange: (grade: string) => void
  onStepBack: () => void
  onReset: () => void
  reorderFinal: (from: number, to: number) => void
}

export function MergeStep({
  pptA,
  pptB,
  session,
  activeSlide,
  activeVersion,
  isInFinalSelection,
  finalSelectionDetails,
  globalPrompt,
  showTemplates,
  subject,
  grade,
  alwaysPrompt,
  onAlwaysPromptChange,
  onSlideClick,
  onSwitchVersion,
  onProcess,
  onAddToFinal,
  onRemoveFromFinal,
  addToFinal,
  removeFromFinal,
  onMergeSelected,
  onGenerateFinal,
  onPromptChange,
  onToggleTemplates,
  onSubjectChange,
  onGradeChange,
  onStepBack,
  onReset,
  reorderFinal,
}: MergeStepProps) {
  return (
    <div className="space-y-4">
      {/* 顶部控制栏 */}
      <div className="flex items-center justify-between bg-white border rounded-lg px-4 py-3">
        <div className="flex items-center gap-4">
          <Button variant="outline" onClick={onStepBack} size="sm">
            ← 返回上传
          </Button>
          <span className="text-sm text-gray-500">
            {pptA?.name} + {pptB?.name}
          </span>
        </div>
        <Button onClick={onReset} variant="outline" size="sm">
          重置
        </Button>
      </div>

      {/* 顶部：水平幻灯片池 */}
      <SlidePoolPanel
        slidePool={session.slide_pool}
        activeSlideId={session.active_slide_id}
        finalSelection={session.final_selection}
        onSlideClick={onSlideClick}
        isProcessing={session.is_processing}
        isMerging={session.active_operation === 'merge'}
        onMergeSelected={onMergeSelected}
        fileA={session.ppt_a_file}
        fileB={session.ppt_b_file}
        layout="horizontal"
      />

      {/* 最终选择栏（幻灯片池下方） */}
      <FinalSelectionBar
        items={finalSelectionDetails}
        onReorder={reorderFinal}
        onRemove={(versionId) => removeFromFinal(versionId)}
        onDropFromPool={(versionId) => addToFinal(versionId)}
        onGenerate={onGenerateFinal}
        isGenerating={session.is_processing}
      />

      {/* 中部：预览 + 操作 */}
      <MergeMainArea
        activeSlide={activeSlide}
        activeVersion={activeVersion}
        isInFinalSelection={isInFinalSelection}
        isProcessing={session.is_processing}
        currentAction={session.active_operation}
        progressInfo={session.progress_info}
        globalPrompt={globalPrompt}
        showTemplates={showTemplates}
        subject={subject}
        grade={grade}
        fileA={session.ppt_a_file}
        fileB={session.ppt_b_file}
        finalCount={session.final_selection.length}
        alwaysPrompt={alwaysPrompt}
        onAlwaysPromptChange={onAlwaysPromptChange}
        onSwitchVersion={onSwitchVersion}
        onProcess={onProcess}
        onPromptChange={onPromptChange}
        onToggleTemplates={onToggleTemplates}
        onSubjectChange={onSubjectChange}
        onGradeChange={onGradeChange}
        onAddToFinal={onAddToFinal}
        onRemoveFromFinal={onRemoveFromFinal}
      />
    </div>
  )
}
