"use client"

import { PptUploadArea } from '@/components/merge/upload/ppt-upload-area'

export interface UploadStepProps {
  pptA: File | null
  pptB: File | null
  isInitializing: boolean
  onSetPptA: (file: File | null) => void
  onSetPptB: (file: File | null) => void
}

export function UploadStep({
  pptA,
  pptB,
  isInitializing,
  onSetPptA,
  onSetPptB,
}: UploadStepProps) {
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

        {isInitializing && (
          <div className="text-center py-4">
            <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-600">正在解析 PPT 文件...</p>
          </div>
        )}

        {pptA && pptB && !isInitializing && (
          <div className="text-center text-sm text-gray-500">
            <p>{pptA.name} ({(pptA.size / 1024 / 1024).toFixed(1)} MB) + {pptB.name} ({(pptB.size / 1024 / 1024).toFixed(1)} MB)</p>
          </div>
        )}
      </div>
    </div>
  )
}
