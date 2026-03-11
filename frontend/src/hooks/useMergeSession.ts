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
  processSlide: (slideId: string, action: SlideAction, prompt?: string) => Promise<ProcessingResult>
  /** 融合多个幻灯片 */
  mergeSlides: (slideIds: string[], prompt?: string) => Promise<ProcessingResult>
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
 * 解析 PPT 文件获取页面数据
 */
async function parsePptFile(file: File): Promise<OriginalSlideData[]> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${apiBaseUrl}/api/v1/ppt/parse`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`PPT 解析失败: ${response.status}`)
  }

  const result = await response.json()

  if (!result.pages || !Array.isArray(result.pages)) {
    throw new Error('PPT 解析返回数据格式错误')
  }

  return result.pages.map((page: any) => ({
    index: page.index,
    title: page.title || '',
    content: page.content || [],
    shapes: page.shapes,
    has_complex_elements: page.has_complex_elements,
    complex_element_types: page.complex_element_types,
  }))
}

/**
 * 创建后端会话并获取预览图
 */
async function createBackendSession(pptA: File, pptB: File): Promise<{
  session_id: string
  slide_image_urls: {
    ppt_a: Record<number, string>
    ppt_b: Record<number, string>
  }
}> {
  const formData = new FormData()
  formData.append('ppt_a', pptA)
  formData.append('ppt_b', pptB)

  // 创建会话
  const createResponse = await fetch(`${apiBaseUrl}/api/v1/session/create`, {
    method: 'POST',
    body: formData,
  })

  if (!createResponse.ok) {
    throw new Error('创建会话失败')
  }

  const createResult = await createResponse.json()
  const sessionId = createResult.session_id

  // 获取完整会话数据（包含图片 URL）
  const sessionResponse = await fetch(`${apiBaseUrl}/api/v1/session/${sessionId}`)

  if (!sessionResponse.ok) {
    // 如果获取失败，返回空 URL，但继续使用 session_id
    console.warn('获取会话详情失败，预览图可能不可用')
    const emptyUrls: Record<number, string> = {}
    return {
      session_id: sessionId,
      slide_image_urls: { ppt_a: emptyUrls, ppt_b: emptyUrls }
    }
  }

  const sessionData = await sessionResponse.json()

  // 提取预览图 URL
  const slide_image_urls: {
    ppt_a: Record<number, string>
    ppt_b: Record<number, string>
  } = { ppt_a: {}, ppt_b: {} }

  // 从返回的 documents 中提取图片 URL
  if (sessionData.documents) {
    for (const [docId, docData] of Object.entries(sessionData.documents)) {
      const typedDoc = docData as { slides?: Record<string, { versions?: Array<{ image_url?: string }> }> }
      if (typedDoc.slides) {
        const targetKey = docId === 'ppt_a' ? 'ppt_a' : 'ppt_b'
        for (const [slideIdx, slideData] of Object.entries(typedDoc.slides)) {
          const typedSlide = slideData as { versions?: Array<{ image_url?: string }> }
          if (typedSlide.versions && typedSlide.versions[0]?.image_url) {
            slide_image_urls[targetKey][parseInt(slideIdx)] = typedSlide.versions[0].image_url
          }
        }
      }
    }
  }

  return {
    session_id: sessionId,
    slide_image_urls,
  }
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

  // 初始化会话
  const initSession = useCallback(async (pptA: File, pptB: File) => {
    setSession(prev => ({
      ...prev,
      is_processing: true,
      progress_info: {
        stage: 'parsing',
        message: '正在解析 PPT 文件...',
        percentage: 10,
      },
    }))

    try {
      // 并行解析两个 PPT 和创建后端会话
      const [pagesA, pagesB, backendResult] = await Promise.all([
        parsePptFile(pptA),
        parsePptFile(pptB),
        createBackendSession(pptA, pptB).catch((err) => {
          console.warn('创建后端会话失败，使用本地模式:', err)
          const emptyUrls: Record<number, string> = {}
          return { session_id: `local_${Date.now()}`, slide_image_urls: { ppt_a: emptyUrls, ppt_b: emptyUrls } }
        }),
      ])

      const { session_id: backendSessionId, slide_image_urls } = backendResult

      // 创建幻灯片池
      const slidePool: Record<string, SlidePoolItem> = {}

      // 添加 PPT A 的幻灯片
      for (let i = 0; i < pagesA.length; i++) {
        const slideId = `ppt_a_${i}`
        const item = createInitialSlidePoolItem('ppt_a', i, pagesA[i])
        // 添加预览图 URL
        const imageUrl = slide_image_urls.ppt_a[i]
        if (imageUrl) {
          item.versions[0].preview_url = imageUrl
        }
        slidePool[slideId] = item
      }

      // 添加 PPT B 的幻灯片
      for (let i = 0; i < pagesB.length; i++) {
        const slideId = `ppt_b_${i}`
        const item = createInitialSlidePoolItem('ppt_b', i, pagesB[i])
        // 添加预览图 URL
        const imageUrl = slide_image_urls.ppt_b[i]
        if (imageUrl) {
          item.versions[0].preview_url = imageUrl
        }
        slidePool[slideId] = item
      }

      setSession({
        session_id: backendSessionId,
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
  const processSlide = useCallback(async (
    slideId: string,
    action: SlideAction,
    prompt?: string
  ): Promise<ProcessingResult> => {
    const slideItem = session.slide_pool[slideId]
    if (!slideItem) {
      return { success: false, error: '幻灯片不存在' }
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
      // 获取 LLM 配置
      const llmConfigStr = localStorage.getItem('llm_config')
      if (!llmConfigStr) {
        throw new Error('请先配置 LLM API Key')
      }
      const llmConfig = JSON.parse(llmConfigStr)

      // 确定来源文档
      const source = slideItem.original_source === 'ppt_a' ? 'A' :
                     slideItem.original_source === 'ppt_b' ? 'B' : 'A'
      const pptFile = source === 'A' ? session.ppt_a_file : session.ppt_b_file

      if (!pptFile) {
        throw new Error('PPT 文件不存在')
      }

      // 调用后端 API
      const formData = new FormData()
      formData.append('file_a', source === 'A' ? pptFile : new File([], 'placeholder'))
      formData.append('file_b', source === 'B' ? pptFile : new File([], 'placeholder'))
      formData.append('merge_type', 'single')
      formData.append('single_page_index', slideItem.original_index.toString())
      formData.append('single_page_action', action)
      formData.append('source_doc', source)
      formData.append('provider', llmConfig.provider || 'deepseek')
      formData.append('api_key', llmConfig.apiKey)
      formData.append('temperature', '0.3')
      formData.append('max_tokens', '3000')
      if (prompt) {
        formData.append('custom_prompt', prompt)
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/ai-merge`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      // 解析 SSE 响应
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let finalResult: any = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const event = JSON.parse(dataStr)
              if (event.type === 'heartbeat') continue
              if (event.stage === 'error') {
                throw new Error(event.message || '处理失败')
              }
              if (event.stage === 'complete' && event.result) {
                finalResult = event.result
              }
              if (event.stage) {
                setSession(prev => ({
                  ...prev,
                  progress_info: {
                    stage: event.stage,
                    message: event.message || '处理中...',
                    percentage: event.progress || 50,
                  },
                }))
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      if (!finalResult || !finalResult.new_content) {
        throw new Error('未收到处理结果')
      }

      // 创建新版本
      const newVersion = createNewVersion(slideItem, action, finalResult.new_content, prompt)

      // 更新幻灯片池
      setSession(prev => {
        const updatedPool = { ...prev.slide_pool }
        updatedPool[slideId] = {
          ...slideItem,
          versions: [...slideItem.versions, newVersion],
          current_version: newVersion.version_id,
          display_title: finalResult.new_content.title || slideItem.display_title,
        }

        return {
          ...prev,
          slide_pool: updatedPool,
          active_operation: null,
          is_processing: false,
          progress_info: undefined,
        }
      })

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
  }, [session.slide_pool, session.ppt_a_file, session.ppt_b_file])

  // 融合多个幻灯片
  const mergeSlides = useCallback(async (
    slideIds: string[],
    prompt?: string
  ): Promise<ProcessingResult> => {
    if (slideIds.length < 2) {
      return { success: false, error: '需要选择至少两个幻灯片进行融合' }
    }

    // 设置处理状态
    setSession(prev => ({
      ...prev,
      active_operation: 'merge',
      is_processing: true,
      progress_info: {
        stage: 'merging',
        message: '正在融合幻灯片...',
        percentage: 20,
      },
    }))

    try {
      // 获取 LLM 配置
      const llmConfigStr = localStorage.getItem('llm_config')
      if (!llmConfigStr) {
        throw new Error('请先配置 LLM API Key')
      }
      const llmConfig = JSON.parse(llmConfigStr)

      // 分离 A/B 来源
      const pagesA: number[] = []
      const pagesB: number[] = []

      for (const slideId of slideIds) {
        const item = session.slide_pool[slideId]
        if (!item) continue

        if (item.original_source === 'ppt_a') {
          pagesA.push(item.original_index)
        } else if (item.original_source === 'ppt_b') {
          pagesB.push(item.original_index)
        }
      }

      // 调用后端 API
      const formData = new FormData()
      formData.append('file_a', session.ppt_a_file || new File([], 'placeholder'))
      formData.append('file_b', session.ppt_b_file || new File([], 'placeholder'))
      formData.append('merge_type', 'partial')
      formData.append('selected_pages_a', pagesA.join(','))
      formData.append('selected_pages_b', pagesB.join(','))
      formData.append('provider', llmConfig.provider || 'deepseek')
      formData.append('api_key', llmConfig.apiKey)
      formData.append('temperature', '0.3')
      formData.append('max_tokens', '3000')
      if (prompt) {
        formData.append('custom_prompt', prompt)
      }

      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/ai-merge`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      // 解析 SSE 响应
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('无法读取响应')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let finalResult: any = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const event = JSON.parse(dataStr)
              if (event.type === 'heartbeat') continue
              if (event.stage === 'error') {
                throw new Error(event.message || '融合失败')
              }
              if (event.stage === 'complete' && event.result) {
                finalResult = event.result
              }
              if (event.stage) {
                setSession(prev => ({
                  ...prev,
                  progress_info: {
                    stage: event.stage,
                    message: event.message || '处理中...',
                    percentage: event.progress || 50,
                  },
                }))
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }

      if (!finalResult || !finalResult.new_slide) {
        throw new Error('未收到融合结果')
      }

      // 创建融合幻灯片
      const mergedIndex = Object.values(session.slide_pool)
        .filter(item => item.original_source === 'merge').length

      const sources = slideIds.map(slideId => {
        const item = session.slide_pool[slideId]
        return {
          source: item?.original_source as 'ppt_a' | 'ppt_b',
          slide_index: item?.original_index || 0,
        }
      })

      const newSlide = createMergedSlidePoolItem(
        mergedIndex,
        sources,
        {
          title: finalResult.new_slide.title,
          main_points: finalResult.new_slide.elements?.map((e: any) => e.content) || [],
        }
      )

      // 更新幻灯片池
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
  }, [session.slide_pool, session.ppt_a_file, session.ppt_b_file])

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
      const response = await fetch(`${apiBaseUrl}/api/v1/ppt/generate-final`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: session.session_id,
          final_selection: session.final_selection,
          title: '智能合并课件',
          grade: '6',
          subject: 'general',
          style: 'simple',
          custom_prompt: globalPrompt || undefined,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '生成失败' }))
        throw new Error(errorData.detail || '生成失败')
      }

      const result = await response.json()

      setSession(prev => ({
        ...prev,
        is_processing: false,
        progress_info: undefined,
      }))

      return {
        download_url: `${apiBaseUrl}${result.download_url}`,
        file_name: result.file_name,
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