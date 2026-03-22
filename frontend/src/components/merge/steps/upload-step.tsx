"use client"

import { Button } from "@/components/ui/button"
import { PptUploadArea } from '@/components/merge/upload/ppt-upload-area'

export interface UploadStepProps {
  pptA: File | null
  pptB: File | null
  isInitializing: boolean
  onSetPptA: (file: File | null) => void
  onSetPptB: (file: File | null) => void
  onConfirm: () => void
}

export function UploadStep({
  pptA,
  pptB,
  isInitializing,
  onSetPptA,
  onSetPptB,
  onConfirm,
}: UploadStepProps) {
  const canProceed = pptA && !isInitializing

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border rounded-lg p-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 text-center">上传 PPT 文件</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <PptUploadArea
            label="PPT A（主课件）"
            description="上传主要教学内容的 PPT"
            file={pptA}
            onFileSelect={onSetPptA}
          />
          <PptUploadArea
            label="PPT B（可选）"
            description="上传补充内容的 PPT（非必须）"
            file={pptB}
            onFileSelect={onSetPptB}
          />
        </div>

        {!pptB && pptA && (
          <p className="text-xs text-gray-400 text-center mb-4">
            只上传一个 PPT 也可以进行 AI 润色、扩展、改写等操作
          </p>
        )}

        {isInitializing && (
          <div className="text-center py-4">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-600">正在解析 PPT 文件...</p>
          </div>
        )}

        {!isInitializing && (
          <Button
            onClick={onConfirm}
            disabled={!canProceed}
            className="w-full"
            size="lg"
          >
            {pptA && pptB
              ? "上传完毕，开始合并"
              : pptA
              ? "上传完毕，开始处理"
              : "请先上传至少一个 PPT 文件"
            }
          </Button>
        )}
      </div>
    </div>
  )
}
