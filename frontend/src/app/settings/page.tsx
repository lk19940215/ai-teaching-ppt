"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import {
  getLLMConfigFromLocalStorage,
  saveLLMConfigToLocalStorage,
  clearLLMConfigFromLocalStorage,
  getDefaultLLMConfig,
  type LLMConfig
} from '@/lib/llmConfig'
import { apiBaseUrl } from '@/lib/api'

// 服务商配置（前端选项格式）
interface ProviderOption {
  provider: string
  name: string
  baseUrl: string
  model: string
}

const PROVIDER_OPTIONS: ProviderOption[] = [
  { provider: "deepseek", name: "DeepSeek", baseUrl: "https://api.deepseek.com", model: "deepseek-chat" },
  { provider: "openai", name: "OpenAI", baseUrl: "https://api.openai.com/v1", model: "gpt-4" },
  { provider: "claude", name: "Claude", baseUrl: "https://api.anthropic.com/v1", model: "claude-3-opus-20240229" },
  { provider: "glm", name: "智谱 GLM", baseUrl: "https://open.bigmodel.cn/api/paas/v4", model: "glm-4" },
]

const DEFAULT_CONFIG: LLMConfig = {
  provider: "deepseek",
  apiKey: "",
  baseUrl: "",
  model: "",
  temperature: 0.7,
  maxInputTokens: 8000,
  maxOutputTokens: 4000,
}

export default function SettingsPage() {
  const [config, setConfig] = useState<LLMConfig>(DEFAULT_CONFIG)
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [hasLocalConfig, setHasLocalConfig] = useState(false)

  const API_BASE = `${apiBaseUrl}/api/v1`

  // 初始化加载配置：优先 localStorage，其次后端默认配置
  useEffect(() => {
    const loadConfig = async () => {
      setIsLoading(true)

      // 1. 优先从 localStorage 获取用户配置
      const localConfig = getLLMConfigFromLocalStorage()
      if (localConfig) {
        setConfig(localConfig)
        setHasLocalConfig(true)
        setIsLoading(false)
        return
      }

      // 2. 从后端获取环境变量默认配置
      const defaultConfig = await getDefaultLLMConfig()
      if (defaultConfig) {
        setConfig(defaultConfig)
        setHasLocalConfig(false)
      }

      setIsLoading(false)
    }

    loadConfig()
  }, [])

  // 保存配置到 localStorage
  const handleSave = async () => {
    if (!config.apiKey) {
      setTestResult({ success: false, message: "API Key 不能为空" })
      return
    }

    setIsSaving(true)
    setTestResult(null)

    try {
      // 保存到 localStorage
      saveLLMConfigToLocalStorage(config)
      setHasLocalConfig(true)
      setTestResult({ success: true, message: "配置保存成功（已保存到浏览器本地存储）" })
    } catch (error) {
      setTestResult({ success: false, message: "保存失败" })
    } finally {
      setIsSaving(false)
      setTimeout(() => setTestResult(null), 3000)
    }
  }

  // 测试连接
  const handleTest = async () => {
    if (!config.apiKey) {
      setTestResult({ success: false, message: "请先输入 API Key" })
      return
    }

    setIsTesting(true)
    setTestResult(null)

    try {
      const response = await fetch(`${API_BASE}/config/test-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: config.provider,
          api_key: config.apiKey,
          base_url: config.baseUrl || undefined,
          model: config.model || undefined,
        }),
      })

      const result = await response.json()
      setTestResult(result)
    } catch (error) {
      setTestResult({ success: false, message: "连接测试失败" })
    } finally {
      setIsTesting(false)
    }
  }

  // 清除配置
  const handleClear = () => {
    clearLLMConfigFromLocalStorage()
    setConfig(DEFAULT_CONFIG)
    setHasLocalConfig(false)
    setTestResult({ success: true, message: "配置已清除" })
    setTimeout(() => setTestResult(null), 3000)
  }

  // 服务商切换
  const handleProviderChange = (provider: string) => {
    const providerConfig = PROVIDER_OPTIONS.find(p => p.provider === provider)

    if (providerConfig) {
      setConfig({
        provider,
        apiKey: "", // 切换服务商时清空 API Key
        baseUrl: providerConfig.baseUrl,
        model: providerConfig.model,
        temperature: 0.7,
        maxInputTokens: 8000,
        maxOutputTokens: 4000,
      })
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">设置</h1>

      {/* 配置状态提示 */}
      {hasLocalConfig && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <p className="text-green-800 text-sm">
            ✓ 已保存配置到浏览器本地存储，服务商：{config.provider}
          </p>
        </div>
      )}

      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-4">LLM 服务商配置</h2>

        {isLoading ? (
          <p className="text-gray-500">加载中...</p>
        ) : (
          <div className="space-y-4">
            {/* 服务商选择 */}
            <div>
              <Label htmlFor="provider">服务商</Label>
              <Select
                id="provider"
                value={config.provider}
                onChange={(e) => handleProviderChange(e.target.value)}
              >
                {PROVIDER_OPTIONS.map((option) => (
                  <option key={option.provider} value={option.provider}>
                    {option.name}
                  </option>
                ))}
              </Select>
            </div>

            {/* API Key */}
            <div>
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                placeholder="请输入 API Key"
              />
              <p className="text-sm text-gray-500 mt-1">
                API Key 仅保存在浏览器本地存储中，不会上传到服务器。
              </p>
            </div>

            {/* Base URL（可选） */}
            <div>
              <Label htmlFor="baseUrl">API Base URL（可选）</Label>
              <Input
                id="baseUrl"
                value={config.baseUrl}
                onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
                placeholder={PROVIDER_OPTIONS.find(p => p.provider === config.provider)?.baseUrl}
              />
            </div>

            {/* 模型名称（可选） */}
            <div>
              <Label htmlFor="model">模型名称（可选）</Label>
              <Input
                id="model"
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
                placeholder={PROVIDER_OPTIONS.find(p => p.provider === config.provider)?.model}
              />
            </div>

            {/* 高级 LLM 参数配置 */}
            <div className="pt-4 border-t">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">高级 LLM 参数配置</h3>

              {/* 温度滑块 */}
              <div className="mb-4">
                <Label htmlFor="temperature">温度（Temperature）: {config.temperature?.toFixed(1)}</Label>
                <input
                  id="temperature"
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature || 0.7}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0（确定）</span>
                  <span>1（平衡）</span>
                  <span>2（随机）</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">温度越低输出越确定，越高越有创造力。建议值：0.5-0.8</p>
              </div>

              {/* 最大输入 Token */}
              <div className="mb-4">
                <Label htmlFor="maxInputTokens">最大输入 Token 数</Label>
                <Input
                  id="maxInputTokens"
                  type="number"
                  min="1000"
                  max="128000"
                  step="1000"
                  value={config.maxInputTokens || 8000}
                  onChange={(e) => setConfig({ ...config, maxInputTokens: parseInt(e.target.value) || 8000 })}
                  placeholder="8000"
                />
                <p className="text-xs text-gray-500 mt-1">限制发送给 LLM 的最大输入 token 数（提示词 + 历史消息）</p>
              </div>

              {/* 最大输出 Token */}
              <div className="mb-4">
                <Label htmlFor="maxOutputTokens">最大输出 Token 数</Label>
                <Input
                  id="maxOutputTokens"
                  type="number"
                  min="100"
                  max="32000"
                  step="100"
                  value={config.maxOutputTokens || 4000}
                  onChange={(e) => setConfig({ ...config, maxOutputTokens: parseInt(e.target.value) || 4000 })}
                  placeholder="4000"
                />
                <p className="text-xs text-gray-500 mt-1">限制 LLM 返回的最大 token 数，较大的值可能生成更长的响应</p>
              </div>
            </div>

            {/* 按钮组 */}
            <div className="flex gap-4 pt-4">
              <Button
                onClick={handleSave}
                disabled={isSaving || !config.apiKey}
                className="flex-1"
              >
                {isSaving ? "保存中..." : "保存配置"}
              </Button>
              <Button
                variant="outline"
                onClick={handleTest}
                disabled={isTesting || !config.apiKey}
                className="flex-1"
              >
                {isTesting ? "测试中..." : "测试连接"}
              </Button>
              {hasLocalConfig && (
                <Button
                  variant="destructive"
                  onClick={handleClear}
                  className="flex-1"
                >
                  清除配置
                </Button>
              )}
            </div>

            {/* 测试结果 */}
            {testResult && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  testResult.success
                    ? "bg-green-50 text-green-800"
                    : "bg-red-50 text-red-800"
                }`}
              >
                {testResult.message}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 关于说明 */}
      <div className="bg-white rounded-xl border p-6 shadow-sm mt-6">
        <h2 className="text-xl font-semibold mb-4">关于</h2>
        <p className="text-gray-600">
          AI 教学 PPT 生成器使用 LLM 服务来生成教学内容。
          您可以配置自己的 API Key 来使用支持的 LLM 服务商。
        </p>
        <p className="text-gray-600 mt-2">
          支持的服务商：DeepSeek、OpenAI、Claude、智谱 GLM
        </p>
        <p className="text-gray-600 mt-2 text-sm">
          配置仅保存在浏览器本地存储中，刷新页面后仍可使用。清除浏览器数据后需要重新配置。
        </p>
      </div>
    </div>
  )
}