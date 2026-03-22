/**
 * PPT 智能合并页面
 *
 * 布局：
 * - 顶部：水平幻灯片池（PPT A / PPT B / 融合结果，各一行，可左右滚动）
 * - 中部：预览面板(8) + 操作面板(4) 两栏
 * - 最终选择栏（幻灯片池下方，拖拽排序）
 */

"use client"

import { useState } from "react"
import { useMergePage } from '@/hooks/useMergePage'
import { StepIndicator } from '@/components/merge/controls/step-indicator'
import { DownloadComplete } from '@/components/merge/controls/download-complete'
import { UploadStep } from '@/components/merge/steps/upload-step'
import { MergeStep } from '@/components/merge/steps/merge-step'

export default function MergePage() {
  const {
    currentStep,
    pptA,
    pptB,
    isInitializing,
    error,
    setError,
    globalPrompt,
    setGlobalPrompt,
    showTemplates,
    setShowTemplates,
    subject,
    setSubject,
    grade,
    setGrade,
    downloadUrl,
    fileName,
    session,
    activeSlide,
    activeVersion,
    finalSelectionDetails,
    isInFinalSelection,
    setPptA,
    setPptB,
    handleSlideClick,
    handleSwitchVersion,
    handleProcess,
    handleAddToFinal,
    handleRemoveFromFinal,
    addToFinal,
    removeFromFinal,
    handleMergeSelected,
    handleGenerateFinal,
    handleDownload,
    handleReset,
    handleStepClick,
    reorderFinal,
  } = useMergePage()

  const [alwaysPrompt, setAlwaysPrompt] = useState('')

  return (
    <div className="w-full px-4 py-6">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PPT 智能合并</h1>
        <p className="text-gray-600">上传两个 PPT 文件，灵活处理每个页面，自由组合生成新的教学课件</p>
      </div>

      <StepIndicator currentStep={currentStep} onStepClick={handleStepClick} />

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <p className="text-red-800 text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {currentStep === 'upload' && (
        <UploadStep
          pptA={pptA}
          pptB={pptB}
          isInitializing={isInitializing}
          onSetPptA={setPptA}
          onSetPptB={setPptB}
        />
      )}

      {currentStep === 'merge' && (
        <MergeStep
          pptA={pptA}
          pptB={pptB}
          session={session}
          activeSlide={activeSlide}
          activeVersion={activeVersion}
          isInFinalSelection={isInFinalSelection}
          finalSelectionDetails={finalSelectionDetails}
          globalPrompt={globalPrompt}
          showTemplates={showTemplates}
          subject={subject}
          grade={grade}
          alwaysPrompt={alwaysPrompt}
          onAlwaysPromptChange={setAlwaysPrompt}
          onSlideClick={handleSlideClick}
          onSwitchVersion={handleSwitchVersion}
          onProcess={handleProcess}
          onAddToFinal={handleAddToFinal}
          onRemoveFromFinal={handleRemoveFromFinal}
          addToFinal={addToFinal}
          removeFromFinal={removeFromFinal}
          onMergeSelected={handleMergeSelected}
          onGenerateFinal={handleGenerateFinal}
          onPromptChange={setGlobalPrompt}
          onToggleTemplates={() => setShowTemplates(!showTemplates)}
          onSubjectChange={setSubject}
          onGradeChange={setGrade}
          onStepBack={() => handleStepClick('upload')}
          onReset={handleReset}
          reorderFinal={reorderFinal}
        />
      )}

      {currentStep === 'confirm' && (
        <DownloadComplete
          fileName={fileName}
          downloadUrl={downloadUrl}
          onDownload={handleDownload}
          onBack={() => handleStepClick('merge')}
          onRestart={handleReset}
        />
      )}
    </div>
  )
}
