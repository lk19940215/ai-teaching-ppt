/**
 * PPT 智能合并页面 - 重构版
 * feat-218: 提取子组件和简化代码
 *
 * 三栏布局：
 * - 左侧：幻灯片池面板（PPT A/B + 融合结果分组）
 * - 中间：幻灯片预览面板（大图预览 + 版本切换 + 操作按钮）
 * - 右侧：操作面板（最终选择 + 生成按钮）
 *
 * 底部：最终选择栏（拖拽排序）
 */

"use client"

import { Button } from "@/components/ui/button"
import { useMergePage } from '@/hooks/useMergePage'
import { SlidePoolPanel } from '@/components/merge/panels/slide-pool-panel'
import { SlidePreviewPanel } from '@/components/merge/panels/slide-preview-panel'
import { FinalSelectionBar } from '@/components/merge/panels/final-selection-bar'
import { MonitorPanel } from '@/components/merge/panels/monitor-panel'
import { PptUploadArea } from '@/components/merge/upload/ppt-upload-area'
import { StepIndicator } from '@/components/merge/controls/step-indicator'
import { DownloadComplete } from '@/components/merge/controls/download-complete'
import { PromptTemplatesPanel } from '@/components/merge/controls/prompt-templates-panel'

/**
 * 上传步骤组件
 */
function UploadStep({
  pptA,
  pptB,
  isInitializing,
  onSetPptA,
  onSetPptB,
}: {
  pptA: File | null
  pptB: File | null
  isInitializing: boolean
  onSetPptA: (file: File | null) => void
  onSetPptB: (file: File | null) => void
}) {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border rounded-lg p-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">上传 PPT 文件</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <PptUploadArea
            label="PPT A（基础课件）"
            description="上传主要教学内容的 PPT"
            file={pptA}
            onFileSelect={onSetPptA}
          />
          <PptUploadArea
            label="PPT B（补充内容）"
            description="上传补充例题或扩展内容的 PPT"
            file={pptB}
            onFileSelect={onSetPptB}
          />
        </div>

        {/* 加载状态 */}
        {isInitializing && (
          <div className="text-center py-4">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-600">正在解析 PPT 文件...</p>
          </div>
        )}

        {/* 文件信息 */}
        {pptA && pptB && !isInitializing && (
          <div className="text-center text-sm text-gray-500">
            <p>{pptA.name} ({(pptA.size / 1024 / 1024).toFixed(1)} MB) + {pptB.name} ({(pptB.size / 1024 / 1024).toFixed(1)} MB)</p>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * 合并步骤组件
 */
function MergeStep({
  pptA,
  pptB,
  session,
  activeSlide,
  activeVersion,
  isInFinalSelection,
  finalSelectionDetails,
  globalPrompt,
  showTemplates,
  onSlideClick,
  onSwitchVersion,
  onProcess,
  onAddToFinal,
  onRemoveFromFinal,
  onMergeSelected,
  onGenerateFinal,
  onPromptChange,
  onToggleTemplates,
  onStepBack,
  onReset,
  reorderFinal,
}: {
  pptA: File | null
  pptB: File | null
  session: ReturnType<typeof useMergePage>['session']
  activeSlide: ReturnType<typeof useMergePage>['activeSlide']
  activeVersion: ReturnType<typeof useMergePage>['activeVersion']
  isInFinalSelection: boolean
  finalSelectionDetails: ReturnType<typeof useMergePage>['finalSelectionDetails']
  globalPrompt: string
  showTemplates: boolean
  onSlideClick: (slideId: string) => void
  onSwitchVersion: (versionId: string) => void
  onProcess: (action: any, prompt?: string) => Promise<void>
  onAddToFinal: () => void
  onRemoveFromFinal: () => void
  onMergeSelected: (slideIds: string[]) => Promise<void>
  onGenerateFinal: () => Promise<void>
  onPromptChange: (prompt: string) => void
  onToggleTemplates: () => void
  onStepBack: () => void
  onReset: () => void
  reorderFinal: (from: number, to: number) => void
}) {
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

      {/* 三栏布局 */}
      <div className="grid grid-cols-12 gap-4">
        {/* 左侧：幻灯片池面板 */}
        <div className="col-span-3">
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
          />
        </div>

        {/* 中间：幻灯片预览面板 */}
        <div className="col-span-6">
          <SlidePreviewPanel
            slide={activeSlide}
            version={activeVersion}
            isInFinalSelection={isInFinalSelection}
            isProcessing={session.is_processing}
            currentAction={session.active_operation}
            progressInfo={session.progress_info}
            globalPrompt={globalPrompt}
            fileA={session.ppt_a_file}
            fileB={session.ppt_b_file}
            onSwitchVersion={onSwitchVersion}
            onProcess={onProcess}
            onInjectPrompt={onPromptChange}
            onAddToFinal={onAddToFinal}
            onRemoveFromFinal={onRemoveFromFinal}
            className="min-h-[600px]"
          />
        </div>

        {/* 右侧：操作面板 */}
        <div className="col-span-3 space-y-4">
          {/* 全局提示语 */}
          <PromptTemplatesPanel
            globalPrompt={globalPrompt}
            onPromptChange={onPromptChange}
            showTemplates={showTemplates}
            onToggleTemplates={onToggleTemplates}
          />

          {/* 最终选择统计 */}
          <div className="bg-white border rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">最终 PPT</h4>
            <div className="text-center py-4">
              <div className="text-3xl font-bold text-indigo-600 mb-1">
                {session.final_selection.length}
              </div>
              <div className="text-sm text-gray-500">页已选中</div>
            </div>
          </div>

          {/* 使用说明 */}
          <div className="bg-gray-50 border rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">使用说明</h4>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>1. 点击左侧幻灯片选择</li>
              <li>2. 在中间面板选择操作类型</li>
              <li>3. 点击"执行"按钮处理当前页</li>
              <li>4. 点击"添加到最终选择"</li>
              <li>5. 底部点击"生成最终 PPT"</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 底部：最终选择栏 */}
      <FinalSelectionBar
        items={finalSelectionDetails}
        onReorder={reorderFinal}
        onRemove={(versionId) => {
          // removeFromFinal 需要从 useMergePage 获取
        }}
        onGenerate={onGenerateFinal}
        isGenerating={session.is_processing}
      />
    </div>
  )
}

/**
 * PPT 智能合并页面
 */
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
    handleMergeSelected,
    handleGenerateFinal,
    handleDownload,
    handleReset,
    handleStepClick,
    reorderFinal,
  } = useMergePage()

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* 页面标题 */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PPT 智能合并</h1>
        <p className="text-gray-600">上传两个 PPT 文件，灵活处理每个页面，自由组合生成新的教学课件</p>
      </div>

      {/* 步骤指示器 */}
      <StepIndicator currentStep={currentStep} onStepClick={handleStepClick} />

      {/* 错误提示 */}
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

      {/* Step 1: 上传 PPT */}
      {currentStep === 'upload' && (
        <UploadStep
          pptA={pptA}
          pptB={pptB}
          isInitializing={isInitializing}
          onSetPptA={setPptA}
          onSetPptB={setPptB}
        />
      )}

      {/* Step 2: 合并设置 */}
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
          onSlideClick={handleSlideClick}
          onSwitchVersion={handleSwitchVersion}
          onProcess={handleProcess}
          onAddToFinal={handleAddToFinal}
          onRemoveFromFinal={handleRemoveFromFinal}
          onMergeSelected={handleMergeSelected}
          onGenerateFinal={handleGenerateFinal}
          onPromptChange={setGlobalPrompt}
          onToggleTemplates={() => setShowTemplates(!showTemplates)}
          onStepBack={() => handleStepClick('upload')}
          onReset={handleReset}
          reorderFinal={reorderFinal}
        />
      )}

      {/* Step 3: 完成下载 */}
      {currentStep === 'confirm' && (
        <DownloadComplete
          fileName={fileName}
          downloadUrl={downloadUrl}
          onDownload={handleDownload}
          onBack={() => handleStepClick('merge')}
          onRestart={handleReset}
        />
      )}

      {/* feat-204: 监控面板 */}
      <MonitorPanel />
    </div>
  )
}