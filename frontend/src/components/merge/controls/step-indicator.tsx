/**
 * 步骤指示器组件
 * 显示当前步骤状态，支持点击已完成步骤回退
 */

"use client"

import * as React from "react"

export type Step = 'upload' | 'merge' | 'confirm'

export interface StepIndicatorProps {
  currentStep: Step
  onStepClick?: (step: Step) => void
}

export function StepIndicator({
  currentStep,
  onStepClick,
}: StepIndicatorProps) {
  const steps: { key: Step; label: string }[] = [
    { key: 'upload', label: '上传 PPT' },
    { key: 'merge', label: '合并设置' },
    { key: 'confirm', label: '完成下载' },
  ]

  const getStepStatus = (stepKey: Step) => {
    const order: Step[] = ['upload', 'merge', 'confirm']
    const current = order.indexOf(currentStep)
    const step = order.indexOf(stepKey)
    if (step < current) return 'completed'
    if (step === current) return 'current'
    return 'pending'
  }

  return (
    <div className="bg-white border rounded-lg p-4 mb-6">
      <div className="flex items-center justify-center gap-4">
        {steps.map((step, index) => {
          const status = getStepStatus(step.key)
          return (
            <React.Fragment key={step.key}>
              <button
                type="button"
                onClick={() => status === 'completed' && onStepClick?.(step.key)}
                disabled={status === 'pending'}
                className={`flex items-center gap-2 ${
                  status === 'completed' ? 'cursor-pointer' : status === 'pending' ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <span
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    status === 'current'
                      ? 'bg-indigo-600 text-white'
                      : status === 'completed'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {status === 'completed' ? '✓' : index + 1}
                </span>
                <span
                  className={`text-sm ${
                    status === 'current' ? 'text-indigo-600 font-medium' : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </button>
              {index < steps.length - 1 && (
                <div className="w-8 h-px bg-gray-200" />
              )}
            </React.Fragment>
          )
        })}
      </div>
    </div>
  )
}