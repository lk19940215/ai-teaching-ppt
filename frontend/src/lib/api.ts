/**
 * API 工具模块
 *
 * 统一管理 API 基础地址，支持环境变量配置。
 * 使用方法：import { apiBaseUrl } from '@/lib/api'
 */

export const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || ''
