/**
 * 合并会话状态管理 Hook
 * feat-171: 基于虚拟幻灯片池的状态管理
 *
 * 功能：
 * - 初始化会话（上传PPT后自动创建幻灯片池）
 * - 单页处理（润色/扩展/改写/提取）
 * - 多页融合（跨PPT页面融合）
 * - 版本管理（切换版本、查看历史）
 * - 最终选择（添加/移除/重排序）
 * - 生成最终PPT
 */

import { useState, useCallback, useMemo } from 'react'
import { apiBaseUrl } from '@/lib/api'
import { requireLLMConfig } from '@/lib/llmConfig'
import {
  type MergeSession,
  type SlidePoolItem,
  type SlideVersion,
  type SlideAction,
  type OriginalSlideData,
  type ProcessingResult,
  createInitialSlidePoolItem,
  createMergedSlidePoolItem,
  createNewVersion,
  getCurrentVersion,
} from '@/types/merge-session'
import type { SlideContent } from '@/types/merge-plan'

/** 初始会话状态 */
const initialSession: MergeSession = {
  session_id: '',
  created_at: 0,
  ppt_a_file: null,
  ppt_b_file: null,
  ppt_a_pages: [],
  ppt_b_pages: [],
  slide_pool: {},
  final_selection: [],
  active_slide_id: null,
  active_operation: null,
  is_processing: false,
}

/** Hook 返回类型 */
export interface UseMergeSessionReturn {
  // 状态
  session: MergeSession
  /** 幻灯片池项列表（按分组） */
  slidePoolItems: SlidePoolItem[]
  /** 最终选择的详情列表 */
  finalSelectionDetails: Array<{
    version_id: string
    slide_item: SlidePoolItem
    version: SlideVersion
  }>
  /** 当前活动的幻灯片 */
  activeSlide: SlidePoolItem | null
  /** 当前活动的版本 */
  activeVersion: SlideVersion | null

  // 操作
  /** 初始化会话 */
  initSession: (pptA: File, pptB: File) => Promise<void>
  /** 处理单页 */
  processSlide: (slideId: string, action: SlideAction, prompt?: string, domain?: string) => Promise<ProcessingResult>
  /** 融合多个幻灯片（AI 内容级融合） */
  mergeSlides: (slideIds: string[], prompt?: string, domain?: string) => Promise<ProcessingResult>
  /** 切换版本 */
  selectVersion: (slideId: string, versionId: string) => void
  /** 设置活动幻灯片 */
  setActiveSlide: (slideId: string | null) => void
  /** 添加到最终选择 */
  addToFinal: (versionId: string) => void
  /** 从最终选择移除 */
  removeFromFinal: (versionId: string) => void
  /** 重排最终选择 */
  reorderFinal: (fromIndex: number, toIndex: number) => void
  /** 切换最终选择（添加或移除） */
  toggleFinalSelection: (versionId: string) => void
  /** 生成最终PPT */
  generateFinal: (globalPrompt?: string) => Promise<{ download_url: string; file_name: string }>
  /** 重置会话 */
  resetSession: () => void
}

/**
 * 上传 PPT 文件并创建会话（新 API v2）
 * 一次调用完成上传、解析、预览图生成
 */
async function uploadAndCreateSession(pptA: File, pptB?: File | null): Promise<{
  session_id: string
  parsed: Record<string, any>
  preview_images: Array<{ slide_index: number; url: string; source: string }>
}> {
  const formData = new FormData()
  formData.append('file_a', pptA)
  if (pptB) {
    formData.append('file_b', pptB)
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/ppt/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
    throw new Error(err.detail || `上传失败: ${response.status}`)
  }

  return response.json()
}

/**
 * 将后端 ParsedPresentation 的 slides 转换为前端 OriginalSlideData 格式
 */
function mapParsedToOriginalSlides(
  parsed: any,
  previewImages: Array<{ slide_index: number; url: string; source: string }>,
  sourceKey: string,
): { pages: OriginalSlideData[]; imageUrls: Record<number, string> } {
  const slides = parsed.slides || []
  const slideWidth = parsed.slide_width || 9144000
  const slideHeight = parsed.slide_height || 5143500

  const imageUrls: Record<number, string> = {}
  for (const img of previewImages) {
    if (img.source === sourceKey) {
      const url = img.url.startsWith('http') ? img.url : `${apiBaseUrl}${img.url}`
      imageUrls[img.slide_index] = url
    }
  }

  const pages: OriginalSlideData[] = slides.map((slide: any) => {
    const elements = slide.elements || []
    const titleElem = elements.find((e: any) => e.is_title && e.plain_text)
    const textElems = elements.filter((e: any) => e.plain_text)
    const complexTypes: string[] = []
    if (slide.has_animations) complexTypes.push('animation')
    if (slide.has_media) complexTypes.push('media')

    const shapes = elements.map((e: any) => ({
      type: e.element_type || 'text_box',
      name: e.name || '',
      position: {
        x: e.position?.left || 0,
        y: e.position?.top || 0,
        width: e.position?.width || 0,
        height: e.position?.height || 0,
      },
      image_base64: e.image_base64 || undefined,
      table_data: e.table_data
        ? e.table_data.map((row: any[]) => row.map((cell: any) => cell.text || ''))
        : undefined,
      text_content: (e.paragraphs || []).map((para: any) => ({
        runs: (para.runs || []).map((run: any) => ({
          text: run.text || '',
          font: {
            name: run.font_name || undefined,
            size: run.font_size || undefined,
            color: run.font_color || undefined,
            bold: run.bold || undefined,
            italic: run.italic || undefined,
            underline: run.underline || undefined,
          },
        })),
        alignment: para.alignment || undefined,
      })),
    }))

    return {
      index: slide.slide_index,
      title: titleElem?.plain_text || '',
      content: textElems.map((e: any) => e.plain_text || ''),
      shapes,
      layout: { width: slideWidth, height: slideHeight },
      has_complex_elements: complexTypes.length > 0,
      complex_element_types: complexTypes,
    }
  })

  return { pages, imageUrls }
}

/**
 * 合并会话状态管理 Hook
 */
export function useMergeSession(): UseMergeSessionReturn {
  const [session, setSession] = useState<MergeSession>(initialSession)

  // 计算属性
  const slidePoolItems = useMemo(() => {
    return Object.values(session.slide_pool)
  }, [session.slide_pool])

  const finalSelectionDetails = useMemo(() => {
    const result: Array<{
      version_id: string
      slide_item: SlidePoolItem
      version: SlideVersion
    }> = []

    for (const versionId of session.final_selection) {
      const match = versionId.match(/^(.*)_v\d+$/)
      if (!match) continue

      const slideId = match[1]
      const slideItem = session.slide_pool[slideId]
      if (!slideItem) continue

      const version = slideItem.versions.find(v => v.version_id === versionId)
      if (!version) continue

      result.push({
        version_id: versionId,
        slide_item: slideItem,
        version,
      })
    }

    return result
  }, [session.slide_pool, session.final_selection])

  const activeSlide = useMemo(() => {
    if (!session.active_slide_id) return null
    return session.slide_pool[session.active_slide_id] || null
  }, [session.slide_pool, session.active_slide_id])

  const activeVersion = useMemo(() => {
    if (!activeSlide) return null
    return getCurrentVersion(activeSlide) || null
  }, [activeSlide])

  // 初始化会话：一次上传完成解析+预览
  const initSession = useCallback(async (pptA: File, pptB: File) => {
    const startTime = Date.now()

    setSession(prev => ({
      ...prev,
      is_processing: true,
      progress_info: {
        stage: 'uploading',
        message: '正在上传并解析 PPT 文件...',
        percentage: 10,
      },
    }))

    try {
      const uploadResult = await uploadAndCreateSession(pptA, pptB)
      const { session_id, parsed, preview_images } = uploadResult

      const slidePool: Record<string, SlidePoolItem> = {}
      let pagesA: OriginalSlideData[] = []
      let pagesB: OriginalSlideData[] = []

      if (parsed.ppt_a) {
        const resultA = mapParsedToOriginalSlides(parsed.ppt_a, preview_images || [], 'ppt_a')
        pagesA = resultA.pages
        for (let i = 0; i < pagesA.length; i++) {
          const slideId = `ppt_a_${i}`
          const item = createInitialSlidePoolItem('ppt_a', i, pagesA[i])
          if (resultA.imageUrls[i]) {
            item.versions[0].preview_url = resultA.imageUrls[i]
          }
          slidePool[slideId] = item
        }
      }

      if (parsed.ppt_b) {
        const resultB = mapParsedToOriginalSlides(parsed.ppt_b, preview_images || [], 'ppt_b')
        pagesB = resultB.pages
        for (let i = 0; i < pagesB.length; i++) {
          const slideId = `ppt_b_${i}`
          const item = createInitialSlidePoolItem('ppt_b', i, pagesB[i])
          if (resultB.imageUrls[i]) {
            item.versions[0].preview_url = resultB.imageUrls[i]
          }
          slidePool[slideId] = item
        }
      }

      setSession({
        session_id,
        created_at: Date.now(),
        ppt_a_file: pptA,
        ppt_b_file: pptB,
        ppt_a_pages: pagesA,
        ppt_b_pages: pagesB,
        slide_pool: slidePool,
        final_selection: [],
        active_slide_id: Object.keys(slidePool)[0] || null,
        active_operation: null,
        is_processing: false,
        progress_info: undefined,
      })

      console.log('[initSession]', `耗时 ${Date.now() - startTime}ms`)
    } catch (err: any) {
      console.error('初始化会话失败:', err)
      setSession(prev => ({
        ...prev,
        is_processing: false,
        progress_info: undefined,
      }))
      throw err
    }
  }, [])

  // 处理单页
  // feat-252: 优化数据流，直接传递已解析的内容，无需传文件
  const processSlide = useCallback(async (
    slideId: string,
    action: SlideAction,
    prompt?: string,
    domain?: string
  ): Promise<ProcessingResult> => {
    // feat-205: 性能监控点
    const startTime = Date.now()

    const slideItem = session.slide_pool[slideId]
    if (!slideItem) {
      return { success: false, error: '幻灯片不存在' }
    }

    // 获取当前版本的内容
    const currentVersion = getCurrentVersion(slideItem)
    if (!currentVersion) {
      return { success: false, error: '幻灯片版本不存在' }
    }

    // 设置处理状态
    setSession(prev => ({
      ...prev,
      active_operation: action,
      is_processing: true,
      progress_info: {
        stage: 'processing',
        message: `正在${getActionLabel(action)}...`,
        percentage: 20,
      },
    }))

    try {
      // feat-240: 从后端获取 LLM 配置，避免 localStorage 配置丢失
      const llmConfig = await requireLLMConfig()

      // 更新进度
      setSession(prev => ({
        ...prev,
        progress_info: {
          stage: 'ai_processing',
          message: '正在调用 AI 处理...',
          percentage: 40,
        },
      }))

      const requestBody = {
        session_id: session.session_id,
        slide_indices: [slideItem.original_index],
        action: action,
        custom_prompt: prompt || undefined,
        domain: domain || undefined,
        provider: llmConfig.provider || 'deepseek',
        api_key: llmConfig.apiKey,
        base_url: llmConfig.baseUrl || undefined,
        model: llmConfig.model || undefined,
        temperature: 0.3,
        max_tokens: 3000,
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      // feat-202: 增强 fetch 错误处理，记录完整错误详情和 URL
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: `HTTP ${response.status}`,
          url: response.url
        }))
        console.error('[processSlide] API 请求失败:', {
          status: response.status,
          statusText: response.statusText,
          url: response.url,
          error: errorData
        })
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      // 解析 JSON 响应
      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || '处理失败')
      }

      // 更新进度到完成阶段
      setSession(prev => ({
        ...prev,
        progress_info: {
          stage: 'complete',
          message: '处理完成',
          percentage: 90,
        },
      }))

      // 从新 API 返回的 result 和 version 提取内容
      const serverVersion = result.version
      const processResult = result.result

      // 从修改指令中提取新内容，构建 SlideContent
      const newContent: SlideContent = {
        title: currentVersion.content.title || '',
        main_points: [...(currentVersion.content.main_points || [])],
      }

      // 如果有文本修改，用修改后的文本更新 main_points
      if (processResult?.modifications) {
        for (const mod of processResult.modifications) {
          const newTexts = (mod.text_modifications || []).map((tm: any) => tm.new_text)
          if (newTexts.length > 0) {
            newContent.main_points = newTexts
          }
        }
      }

      if (processResult?.modifications?.[0]?.ai_summary) {
        newContent.title = newContent.title || processResult.modifications[0].ai_summary
      }

      const newVersion = createNewVersion(slideItem, action, newContent, prompt)

      // 附加服务端版本的预览图（按修改页面的索引取对应预览图）
      if (serverVersion?.preview_images?.length > 0) {
        const pageIdx = slideItem.original_index
        const pUrl = serverVersion.preview_images[pageIdx] || serverVersion.preview_images[0]
        newVersion.preview_url = pUrl.startsWith('http') ? pUrl : `${apiBaseUrl}${pUrl}`
      }

      // 更新幻灯片池
      setSession(prev => {
        const updatedPool = { ...prev.slide_pool }
        updatedPool[slideId] = {
          ...slideItem,
          versions: [...slideItem.versions, newVersion],
          current_version: newVersion.version_id,
          display_title: newContent.title || slideItem.display_title,
        }

        return {
          ...prev,
          slide_pool: updatedPool,
          active_operation: null,
          is_processing: false,
          progress_info: undefined,
        }
      })

      console.log(`[processSlide_${action}]`, `耗时 ${Date.now() - startTime}ms`)

      return {
        success: true,
        new_version: newVersion,
      }
    } catch (err: any) {
      console.error('处理幻灯片失败:', err)
      setSession(prev => ({
        ...prev,
        active_operation: null,
        is_processing: false,
        progress_info: undefined,
      }))
      return {
        success: false,
        error: err.message || '处理失败',
      }
    }
  }, [session.slide_pool])

  // 融合多个幻灯片（通过 AI 内容级融合）
  const mergeSlides = useCallback(async (
    slideIds: string[],
    prompt?: string,
    domain?: string
  ): Promise<ProcessingResult> => {
    if (slideIds.length < 2) {
      return { success: false, error: '需要选择至少两个幻灯片进行融合' }
    }

    setSession(prev => ({
      ...prev,
      active_operation: 'merge',
      is_processing: true,
      progress_info: {
        stage: 'merging',
        message: '正在 AI 融合幻灯片...',
        percentage: 20,
      },
    }))

    try {
      const llmConfig = await requireLLMConfig()

      const selections = slideIds.map(slideId => {
        const item = session.slide_pool[slideId]
        return {
          source: item?.original_source as string,
          slide_index: item?.original_index || 0,
        }
      }).filter(s => s.source === 'ppt_a' || s.source === 'ppt_b')

      const requestBody = {
        session_id: session.session_id,
        action: 'fuse',
        selections,
        custom_prompt: prompt || undefined,
        domain: domain || undefined,
        provider: llmConfig.provider || 'deepseek',
        api_key: llmConfig.apiKey,
        base_url: llmConfig.baseUrl || undefined,
        model: llmConfig.model || undefined,
        temperature: 0.3,
        max_tokens: 4000,
      }

      setSession(prev => ({
        ...prev,
        progress_info: {
          stage: 'ai_processing',
          message: '正在调用 AI 融合内容...',
          percentage: 40,
        },
      }))

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || '融合失败')
      }

      const mergedIndex = Object.values(session.slide_pool)
        .filter(item => item.original_source === 'merge').length

      const sources = slideIds.map(slideId => {
        const item = session.slide_pool[slideId]
        return {
          source: item?.original_source as 'ppt_a' | 'ppt_b',
          slide_index: item?.original_index || 0,
        }
      })

      const serverVersion = result.version
      const processResult = result.result

      const newSlide = createMergedSlidePoolItem(
        mergedIndex,
        sources,
        {
          title: processResult?.modifications?.[0]?.ai_summary || serverVersion?.description || 'AI 融合结果',
          main_points: [`从 ${selections.length} 页 AI 融合而成`],
        }
      )

      if (serverVersion?.preview_images?.length > 0) {
        const pUrl = serverVersion.preview_images[0]
        newSlide.versions[0].preview_url = pUrl.startsWith('http') ? pUrl : `${apiBaseUrl}${pUrl}`
      }

      setSession(prev => {
        const updatedPool = { ...prev.slide_pool }
        updatedPool[newSlide.slide_id] = newSlide

        return {
          ...prev,
          slide_pool: updatedPool,
          active_slide_id: newSlide.slide_id,
          active_operation: null,
          is_processing: false,
          progress_info: undefined,
        }
      })

      return {
        success: true,
        new_version: newSlide.versions[0],
      }
    } catch (err: any) {
      console.error('融合幻灯片失败:', err)
      setSession(prev => ({
        ...prev,
        active_operation: null,
        is_processing: false,
        progress_info: undefined,
      }))
      return {
        success: false,
        error: err.message || '融合失败',
      }
    }
  }, [session.slide_pool])

  // 切换版本
  const selectVersion = useCallback((slideId: string, versionId: string) => {
    setSession(prev => {
      const slideItem = prev.slide_pool[slideId]
      if (!slideItem) return prev

      const version = slideItem.versions.find(v => v.version_id === versionId)
      if (!version) return prev

      const updatedPool = { ...prev.slide_pool }
      updatedPool[slideId] = {
        ...slideItem,
        current_version: versionId,
      }

      return {
        ...prev,
        slide_pool: updatedPool,
      }
    })
  }, [])

  // 设置活动幻灯片
  const setActiveSlide = useCallback((slideId: string | null) => {
    setSession(prev => ({
      ...prev,
      active_slide_id: slideId,
    }))
  }, [])

  // 添加到最终选择
  const addToFinal = useCallback((versionId: string) => {
    setSession(prev => {
      if (prev.final_selection.includes(versionId)) return prev
      return {
        ...prev,
        final_selection: [...prev.final_selection, versionId],
      }
    })
  }, [])

  // 从最终选择移除
  const removeFromFinal = useCallback((versionId: string) => {
    setSession(prev => ({
      ...prev,
      final_selection: prev.final_selection.filter(id => id !== versionId),
    }))
  }, [])

  // 重排最终选择
  const reorderFinal = useCallback((fromIndex: number, toIndex: number) => {
    setSession(prev => {
      const newSelection = [...prev.final_selection]
      const [removed] = newSelection.splice(fromIndex, 1)
      newSelection.splice(toIndex, 0, removed)
      return {
        ...prev,
        final_selection: newSelection,
      }
    })
  }, [])

  // 切换最终选择
  const toggleFinalSelection = useCallback((versionId: string) => {
    setSession(prev => {
      const isSelected = prev.final_selection.includes(versionId)
      return {
        ...prev,
        final_selection: isSelected
          ? prev.final_selection.filter(id => id !== versionId)
          : [...prev.final_selection, versionId],
      }
    })
  }, [])

  // 生成最终PPT
  const generateFinal = useCallback(async (globalPrompt?: string): Promise<{ download_url: string; file_name: string }> => {
    if (!session.session_id) {
      throw new Error('会话不存在')
    }

    if (session.session_id.startsWith('local_')) {
      throw new Error('后端会话创建失败，无法生成最终 PPT。请检查后端服务是否正常运行，然后重新上传文件。')
    }

    setSession(prev => ({
      ...prev,
      is_processing: true,
      progress_info: {
        stage: 'generating',
        message: '正在生成最终 PPT...',
        percentage: 20,
      },
    }))

    try {
      // 从 final_selection 中的 version_id 提取 source + slide_index
      const selections: Array<{ source: string; slide_index: number }> = []
      for (const versionId of session.final_selection) {
        const match = versionId.match(/^(.*)_v\d+$/)
        if (!match) continue
        const slideId = match[1]
        const item = session.slide_pool[slideId]
        if (!item) continue
        selections.push({
          source: item.original_source === 'merge' ? 'latest' : item.original_source,
          slide_index: item.original_index,
        })
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/compose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          selections,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '生成失败' }))
        throw new Error(errorData.detail || '生成失败')
      }

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || '组合失败')
      }

      setSession(prev => ({
        ...prev,
        is_processing: false,
        progress_info: undefined,
      }))

      const versionId = result.version?.version_id || ''
      return {
        download_url: `${apiBaseUrl}/api/v1/ppt/download/${session.session_id}/${versionId}`,
        file_name: `final_${session.session_id}.pptx`,
      }
    } catch (err: any) {
      console.error('生成最终 PPT 失败:', err)
      setSession(prev => ({
        ...prev,
        is_processing: false,
        progress_info: undefined,
      }))
      throw err
    }
  }, [session.session_id, session.final_selection])

  // 重置会话
  const resetSession = useCallback(() => {
    setSession(initialSession)
  }, [])

  return {
    session,
    slidePoolItems,
    finalSelectionDetails,
    activeSlide,
    activeVersion,
    initSession,
    processSlide,
    mergeSlides,
    selectVersion,
    setActiveSlide,
    addToFinal,
    removeFromFinal,
    reorderFinal,
    toggleFinalSelection,
    generateFinal,
    resetSession,
  }
}

/**
 * 获取动作的中文标签
 */
function getActionLabel(action: SlideAction): string {
  const labels: Record<SlideAction, string> = {
    polish: '润色',
    expand: '扩展',
    rewrite: '改写',
    extract: '提取',
    merge: '融合',
    create: '创建',
  }
  return labels[action] || action
}

export default useMergeSession