/**
 * API 工具模块
 *
 * 统一管理 API 基础地址，支持环境变量配置
 *
 * 使用方法：
 * import { apiBaseUrl, createApiUrl } from '@/lib/api'
 *
 * // 方式 1：手动拼接 URL
 * const response = await fetch(`${apiBaseUrl}/api/v1/config/providers`)
 *
 * // 方式 2：使用 helper 函数
 * const response = await fetch(createApiUrl('/api/v1/config/providers'))
 *
 * // 方式 3：直接使用环境变量
 * const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/config/providers`)
 */

// 从环境变量获取 API 基础地址，支持浏览器和 Node.js 环境
export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * 创建完整的 API URL
 * @param path API 路径（如 /api/v1/config/providers）
 * @returns 完整的 URL
 */
export function createApiUrl(path: string): string {
  // 移除路径开头的斜杠，避免拼接后出现双斜杠
  const cleanPath = path.startsWith('/') ? path.slice(1) : path
  return `${apiBaseUrl}/${cleanPath}`
}

/**
 * 创建下载 URL（用于文件下载）
 * @param path 下载路径（如 /api/v1/ppt/download/xxx.pptx）
 * @returns 完整的下载 URL
 */
export function createDownloadUrl(path: string): string {
  return createApiUrl(path)
}
