/**
 * PPT 上传区域组件
 * 支持拖拽上传和点击选择文件
 */

"use client"

import * as React from "react"
import { useState } from "react"

export interface PptUploadAreaProps {
  label: string
  description: string
  file: File | null
  onFileSelect: (file: File | null) => void
  disabled?: boolean
}

export function PptUploadArea({
  label,
  description,
  file,
  onFileSelect,
  disabled,
}: PptUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false)

  const isPptFile = (name: string) => {
    const lower = name.toLowerCase()
    return lower.endsWith('.pptx') || lower.endsWith('.ppt')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile && isPptFile(selectedFile.name)) {
      onFileSelect(selectedFile)
    } else if (selectedFile) {
      alert('请选择 .ppt 或 .pptx 格式的文件')
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile && isPptFile(droppedFile.name)) {
      onFileSelect(droppedFile)
    }
  }

  if (file) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1)
    return (
      <div className="border rounded-lg p-4 bg-green-50 border-green-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{file.name}</p>
              <p className="text-xs text-gray-500">{sizeMB} MB</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => onFileSelect(null)}
            disabled={disabled}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-6 transition-all cursor-pointer ${
        isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => !disabled && document.getElementById(`file-input-${label}`)?.click()}
    >
      <div className="text-center">
        <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-3">
          <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="text-sm font-medium text-gray-900 mb-1">{label}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
      <input
        id={`file-input-${label}`}
        type="file"
        accept=".ppt,.pptx"
        className="hidden"
        onChange={handleFileChange}
        disabled={disabled}
      />
    </div>
  )
}