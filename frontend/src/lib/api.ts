/**
 * API 工具模块
 *
 * 统一管理 API 基础地址，支持环境变量配置
 *
 * 开发环境：使用相对路径（空字符串），通过 Next.js rewrite 代理到后端
 * 生产环境：使用 NEXT_PUBLIC_API_URL 环境变量配置完整 URL
 *
 * 使用方法：
 * import { apiBaseUrl, createApiUrl } from '@/lib/api'
 *
 * // 方式 1：手动拼接 URL
 * const response = await fetch(`${apiBaseUrl}/api/v1/config/providers`)
 *
 * // 方式 2：使用 helper 函数
 * const response = await fetch(createApiUrl('/api/v1/config/providers'))
 */

/**
 * API 基础地址
 *
 * - 开发环境 (.env.development): 设置 NEXT_PUBLIC_API_URL= 空值，使用相对路径
 * - 生产环境 (.env.production): 设置 NEXT_PUBLIC_API_URL=https://your-api-server
 *
 * 开发环境通过 Next.js rewrites (next.config.js) 代理到后端，避免 CORS 问题
 */
export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || ''

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
