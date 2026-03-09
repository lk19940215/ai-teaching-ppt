/**
 * PPT 版本化管理 API 调用函数
 *
 * 相关后端 API：
 * - GET /api/v1/ppt/session/{session_id} - 获取会话详情
 * - GET /api/v1/ppt/session/{session_id}/history - 获取版本历史
 * - POST /api/v1/ppt/version/create - 创建新版本
 * - POST /api/v1/ppt/version/restore - 恢复历史版本
 * - POST /api/v1/ppt/slide/toggle - 删除/恢复页面
 * - POST /api/v1/ppt/session/create - 创建会话
 */

import { apiBaseUrl } from './api'

// ============ 类型定义 ============

/** 幻灯片版本 */
export interface SlideVersion {
  version: string  // v1, v2, v3...
  image_url: string
  created_at: string  // HH:MM:SS
  operation: string  // 原始上传，AI 润色，AI 扩展，etc.
  prompt?: string  // AI 操作提示语
}

/** 页面状态 */
export type SlideStatus = 'active' | 'deleted'

/** 幻灯片状态 */
export interface SlideState {
  current_version: string | null  // 当前版本 v1/v2/...，deleted 时为 null
  status: SlideStatus
  versions: SlideVersion[]
}

/** 文档状态 */
export interface DocumentState {
  source_file: string
  slides: Record<number, SlideState>  // slide_index -> SlideState
}

/** 会话数据 */
export interface SessionData {
  session_id: string
  documents: Record<string, DocumentState>  // document_id (ppt_a/ppt_b) -> DocumentState
  created_at: string
  last_updated: string
}

/** 创建会话请求 */
export interface CreateSessionRequest {
  files: Record<string, File>  // { ppt_a: File, ppt_b: File }
}

/** 创建会话响应 */
export interface CreateSessionResponse {
  session_id: string
  documents: Record<string, {
    source_file: string
    total_slides: number
  }>
}

/** 创建版本请求 */
export interface CreateVersionRequest {
  session_id: string
  document_id: string  // ppt_a, ppt_b
  slide_index: number  // 0-indexed
  operation: string  // ai_polish, ai_expand, ai_rewrite, ai_extract
  prompt?: string
  new_pptx?: string  // 新 PPTX 路径
}

/** 创建版本响应 */
export interface CreateVersionResponse {
  version: string
  image_url: string
  created_at: string
  operation: string
  prompt?: string
}

/** 恢复版本请求 */
export interface RestoreVersionRequest {
  session_id: string
  document_id: string
  slide_index: number
  target_version: string  // v1, v2, ...
}

/** 切换页面状态请求 */
export interface ToggleSlideRequest {
  session_id: string
  document_id: string
  slide_index: number
  action: 'delete' | 'restore'
}

// ============ API 调用函数 ============

/**
 * 创建会话
 */
export async function createSession(
  files: Record<string, File>
): Promise<CreateSessionResponse> {
  const formData = new FormData()

  // 构建 files 对象格式：{ ppt_a: File, ppt_b: File }
  const filesObject: Record<string, any> = {}
  for (const [key, file] of Object.entries(files)) {
    filesObject[key] = file
  }

  // 使用 Blob 包装 JSON 数据
  formData.append('files', new Blob([JSON.stringify(filesObject)]))

  // 实际上传文件
  for (const [key, file] of Object.entries(files)) {
    formData.append(key, file)
  }

  const response = await fetch(`${apiBaseUrl}/api/v1/session/create`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '创建会话失败' }))
    throw new Error(error.detail || '创建会话失败')
  }

  return response.json()
}

/**
 * 获取会话详情
 */
export async function getSession(sessionId: string): Promise<SessionData> {
  const response = await fetch(`${apiBaseUrl}/api/v1/session/${sessionId}`, {
    method: 'GET',
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '获取会话失败' }))
    throw new Error(error.detail || '获取会话失败')
  }

  return response.json()
}

/**
 * 获取版本历史
 */
export async function getVersionHistory(
  sessionId: string,
  documentId: string,
  slideIndex: number
): Promise<SlideVersion[]> {
  const params = new URLSearchParams({
    document_id: documentId,
    slide_index: slideIndex.toString(),
  })

  const response = await fetch(
    `${apiBaseUrl}/api/v1/session/${sessionId}/history?${params}`,
    { method: 'GET' }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '获取版本历史失败' }))
    throw new Error(error.detail || '获取版本历史失败')
  }

  const data = await response.json()
  return data.versions || []
}

/**
 * 创建新版本
 */
export async function createVersion(
  request: CreateVersionRequest
): Promise<CreateVersionResponse> {
  const response = await fetch(`${apiBaseUrl}/api/v1/version/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '创建版本失败' }))
    throw new Error(error.detail || '创建版本失败')
  }

  return response.json()
}

/**
 * 恢复历史版本
 */
export async function restoreVersion(
  request: RestoreVersionRequest
): Promise<{ success: boolean; current_version: string }> {
  const response = await fetch(`${apiBaseUrl}/api/v1/version/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '恢复版本失败' }))
    throw new Error(error.detail || '恢复版本失败')
  }

  return response.json()
}

/**
 * 切换页面状态（删除/恢复）
 */
export async function toggleSlide(
  request: ToggleSlideRequest
): Promise<{ status: SlideStatus }> {
  const response = await fetch(`${apiBaseUrl}/api/v1/slide/toggle`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '操作失败' }))
    throw new Error(error.detail || '操作失败')
  }

  return response.json()
}
