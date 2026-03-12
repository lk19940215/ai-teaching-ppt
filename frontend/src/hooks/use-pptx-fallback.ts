/**
 * PptxViewJS 渲染器降级 hook
 * feat-185: PptxViewJSRenderer 降级到 PptCanvasRenderer 的自动切换
 *
 * 功能：
 * - 管理降级状态
 * - 提供错误处理回调
 * - 自动重置降级状态
 */

import { useState, useCallback, useEffect } from "react"

export interface UsePptxFallbackOptions {
  /** 用于重置降级状态的依赖项（如文件、幻灯片 ID） */
  resetDeps?: unknown[]
}

export interface UsePptxFallbackReturn {
  /** 是否处于降级模式 */
  fallbackMode: boolean
  /** PptxViewJSRenderer 错误处理回调 */
  handlePptxViewJSError: (error: Error) => void
  /** 手动重置降级状态 */
  resetFallback: () => void
}

/**
 * 获取 PPT 文件的工具函数
 * @param original_source 幻灯片来源 ('ppt_a' | 'ppt_b' | 'merge' 等)
 * @param fileA PPT A 文件
 * @param fileB PPT B 文件
 * @returns 对应的 File 或 null
 */
export function getPptFile(
  original_source: string | undefined,
  fileA?: File | null,
  fileB?: File | null
): File | null {
  if (original_source === 'ppt_a') return fileA ?? null
  if (original_source === 'ppt_b') return fileB ?? null
  return null
}

/**
 * PptxViewJS 渲染器降级 hook
 *
 * @example
 * ```tsx
 * const { fallbackMode, handlePptxViewJSError } = usePptxFallback({
 *   resetDeps: [pptFile, slide?.slide_id]
 * })
 * ```
 */
export function usePptxFallback(options: UsePptxFallbackOptions = {}): UsePptxFallbackReturn {
  const { resetDeps = [] } = options

  const [fallbackMode, setFallbackMode] = useState(false)

  const handlePptxViewJSError = useCallback((error: Error) => {
    console.warn('[usePptxFallback] PptxViewJSRenderer 渲染失败，降级到 PptCanvasRenderer:', error.message)
    setFallbackMode(true)
  }, [])

  const resetFallback = useCallback(() => {
    setFallbackMode(false)
  }, [])

  // 当依赖项变化时重置降级状态
  useEffect(() => {
    setFallbackMode(false)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, resetDeps)

  return {
    fallbackMode,
    handlePptxViewJSError,
    resetFallback,
  }
}