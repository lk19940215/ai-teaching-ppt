/**
 * LLM 配置工具函数
 *
 * 从后端获取 LLM 服务商配置，避免前端 localStorage 配置丢失问题。
 * feat-240: 修复 LLM API Key 配置逻辑和同步机制
 */

import { apiBaseUrl } from './api'

/**
 * LLM 配置类型定义
 */
export interface LLMConfig {
  provider: string
  apiKey: string
  baseUrl?: string
  model?: string
  temperature?: number
  maxInputTokens?: number
  maxOutputTokens?: number
}

/**
 * 从后端获取默认服务商的完整配置
 *
 * 此函数从后端 API 获取配置，确保 API Key 不丢失。
 * 优先使用后端配置，如果后端没有配置则返回 null。
 *
 * @returns LLM 配置对象，如果未配置则返回 null
 */
export async function getLLMConfig(): Promise<LLMConfig | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/config/providers/default/active`)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: '请求失败' }))
      console.warn('[getLLMConfig] 获取配置失败:', errorData.message)
      return null
    }

    const result = await response.json()

    if (!result.success || !result.data) {
      console.warn('[getLLMConfig] 未配置 LLM:', result.message)
      return null
    }

    // 转换后端字段名到前端格式
    const config: LLMConfig = {
      provider: result.data.provider,
      apiKey: result.data.api_key,
      baseUrl: result.data.base_url,
      model: result.data.model,
      temperature: result.data.temperature,
      maxInputTokens: result.data.max_input_tokens,
      maxOutputTokens: result.data.max_output_tokens,
    }

    return config
  } catch (error) {
    console.error('[getLLMConfig] 获取配置异常:', error)
    return null
  }
}

/**
 * 同步获取 LLM 配置（使用 localStorage 缓存）
 *
 * 此函数首先尝试从 localStorage 获取配置，如果不存在或 API Key 为空，
 * 则需要调用 getLLMConfig() 从后端获取。
 *
 * 注意：此函数不进行网络请求，仅检查 localStorage。
 * 对于需要确保配置正确的场景，请使用 getLLMConfig()。
 *
 * @returns localStorage 中的配置，如果不存在或无效则返回 null
 */
export function getLLMConfigFromLocalStorage(): LLMConfig | null {
  try {
    const configStr = localStorage.getItem('llm_config')
    if (!configStr) {
      return null
    }

    const config = JSON.parse(configStr) as LLMConfig

    // 检查 API Key 是否有效
    if (!config.apiKey || config.apiKey.trim() === '') {
      return null
    }

    return config
  } catch (error) {
    console.error('[getLLMConfigFromLocalStorage] 解析配置失败:', error)
    return null
  }
}

/**
 * 检查 LLM 是否已配置
 *
 * @returns 如果已配置返回 true，否则返回 false
 */
export async function isLLMConfigured(): Promise<boolean> {
  const config = await getLLMConfig()
  return config !== null && !!config.apiKey
}

/**
 * 获取 LLM 配置或抛出错误
 *
 * 用于需要确保配置存在的场景，如果未配置则抛出友好的错误信息。
 *
 * @throws Error 如果未配置 LLM API Key
 * @returns LLM 配置对象
 */
export async function requireLLMConfig(): Promise<LLMConfig> {
  const config = await getLLMConfig()

  if (!config) {
    throw new Error('请先在设置页面配置 LLM API Key')
  }

  if (!config.apiKey || config.apiKey.trim() === '') {
    throw new Error('LLM API Key 未配置，请在设置页面重新配置')
  }

  return config
}

/**
 * 更新 localStorage 中的 LLM 配置
 *
 * 注意：此函数仅用于向后兼容，新代码应该使用后端 API 获取配置。
 *
 * @param config LLM 配置对象
 */
export function updateLocalStorageConfig(config: LLMConfig): void {
  try {
    localStorage.setItem('llm_config', JSON.stringify(config))
  } catch (error) {
    console.error('[updateLocalStorageConfig] 更新 localStorage 失败:', error)
  }
}