/**
 * LLM 配置工具函数
 *
 * 配置优先级：
 * 1. localStorage 中的用户配置
 * 2. 后端环境变量中的默认配置（LLM_CONFIG 环境变量）
 *
 * feat-003: API Key 不再保存到数据库，由前端 localStorage 管理
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

const LLM_CONFIG_KEY = 'llm_config'

/**
 * 从 localStorage 获取配置
 *
 * @returns localStorage 中的配置，如果不存在或无效则返回 null
 */
export function getLLMConfigFromLocalStorage(): LLMConfig | null {
  try {
    // 检查是否在浏览器环境
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return null
    }

    const configStr = localStorage.getItem(LLM_CONFIG_KEY)
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
 * 保存配置到 localStorage
 *
 * @param config LLM 配置对象
 */
export function saveLLMConfigToLocalStorage(config: LLMConfig): void {
  try {
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      console.warn('[saveLLMConfigToLocalStorage] 非浏览器环境，无法保存配置')
      return
    }

    localStorage.setItem(LLM_CONFIG_KEY, JSON.stringify(config))
    console.log('[saveLLMConfigToLocalStorage] 配置已保存到 localStorage')
  } catch (error) {
    console.error('[saveLLMConfigToLocalStorage] 保存配置失败:', error)
  }
}

/**
 * 清除 localStorage 中的配置
 */
export function clearLLMConfigFromLocalStorage(): void {
  try {
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return
    }

    localStorage.removeItem(LLM_CONFIG_KEY)
    console.log('[clearLLMConfigFromLocalStorage] 配置已清除')
  } catch (error) {
    console.error('[clearLLMConfigFromLocalStorage] 清除配置失败:', error)
  }
}

/**
 * 从后端获取默认配置（环境变量 LLM_CONFIG）
 *
 * 后端返回的字段名是 camelCase 格式（apiKey, baseUrl 等）
 *
 * @returns 默认 LLM 配置，如果未配置则返回 null
 */
export async function getDefaultLLMConfig(): Promise<LLMConfig | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/config/default`)

    if (!response.ok) {
      console.warn('[getDefaultLLMConfig] 后端未配置默认 LLM')
      return null
    }

    const result = await response.json()

    if (!result.success || !result.data) {
      console.warn('[getDefaultLLMConfig] 获取默认配置失败:', result.message)
      return null
    }

    // 后端返回的是 camelCase 格式，直接使用
    const config: LLMConfig = {
      provider: result.data.provider,
      apiKey: result.data.apiKey,
      baseUrl: result.data.baseUrl,
      model: result.data.model,
      temperature: result.data.temperature,
      maxInputTokens: result.data.maxInputTokens,
      maxOutputTokens: result.data.maxOutputTokens,
    }

    console.log('[getDefaultLLMConfig] 成功获取后端默认配置, provider:', config.provider)
    return config
  } catch (error) {
    console.error('[getDefaultLLMConfig] 获取默认配置异常:', error)
    return null
  }
}

/**
 * 获取 LLM 配置（优先 localStorage，其次后端默认）
 *
 * @returns LLM 配置对象，如果未配置则返回 null
 */
export async function getLLMConfig(): Promise<LLMConfig | null> {
  // 1. 优先从 localStorage 获取用户配置
  const localConfig = getLLMConfigFromLocalStorage()
  if (localConfig) {
    console.log('[getLLMConfig] 使用 localStorage 配置, provider:', localConfig.provider)
    return localConfig
  }

  // 2. 从后端获取环境变量默认配置
  const defaultConfig = await getDefaultLLMConfig()
  if (defaultConfig) {
    console.log('[getLLMConfig] 使用后端默认配置, provider:', defaultConfig.provider)
  }

  return defaultConfig
}

/**
 * 检查 LLM 是否已配置
 *
 * @returns 如果已配置返回 true，否则返回 false
 */
export async function isLLMConfigured(): Promise<boolean> {
  const config = await getLLMConfig()
  return config !== null && !!config.apiKey && config.apiKey.trim() !== ''
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
 * @deprecated 请使用 saveLLMConfigToLocalStorage
 * @param config LLM 配置对象
 */
export function updateLocalStorageConfig(config: LLMConfig): void {
  saveLLMConfigToLocalStorage(config)
}