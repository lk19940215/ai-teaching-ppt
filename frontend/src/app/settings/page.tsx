"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"

// 配置类型
interface LLMConfig {
  provider: string
  apiKey: string
  baseUrl: string
  model: string
  temperature: number
  maxInputTokens: number
  maxOutputTokens: number
  isDefault?: boolean
  isActive?: boolean
}

// 服务商配置（后端返回的格式）
interface ServerProviderConfig {
  id?: number
  provider: string
  api_key_masked?: string
  base_url?: string
  model?: string
  temperature?: number
  max_input_tokens?: number
  max_output_tokens?: number
  is_default?: boolean
  is_active?: boolean
}

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
  maxInputTokens: 4096,
  maxOutputTokens: 2000,
}

export default function SettingsPage() {
  const [config, setConfig] = useState<LLMConfig>(DEFAULT_CONFIG)
  const [savedConfigs, setSavedConfigs] = useState<ServerProviderConfig[]>([])
  const [defaultProvider, setDefaultProvider] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const API_BASE = "http://localhost:8000/api/v1"

  // 加载已保存的配置
  useEffect(() => {
    loadSavedConfigs()
  }, [])

  const loadSavedConfigs = async () => {
    try {
      const response = await fetch(`${API_BASE}/config/providers`)
      const result = await response.json()
      if (result.success) {
        setSavedConfigs(result.data || [])
        // 查找默认服务商
        const defaultConfig = (result.data || []).find((c: ServerProviderConfig) => c.is_default)
        if (defaultConfig) {
          setDefaultProvider(defaultConfig.provider)
          setConfig({
            provider: defaultConfig.provider,
            apiKey: "", // 不加载完整 API Key
            baseUrl: defaultConfig.base_url || "",
            model: defaultConfig.model || "",
            temperature: defaultConfig.temperature ?? 0.7,
            maxInputTokens: defaultConfig.max_input_tokens ?? 4096,
            maxOutputTokens: defaultConfig.max_output_tokens ?? 2000,
          })
        }
      }
    } catch (error) {
      console.error("加载配置失败:", error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    if (!config.apiKey) {
      setTestResult({ success: false, message: "API Key 不能为空" })
      return
    }

    setIsSaving(true)
    setTestResult(null)

    try {
      const response = await fetch(`${API_BASE}/config/providers/${config.provider}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: config.apiKey,
          base_url: config.baseUrl || undefined,
          model: config.model || undefined,
          is_default: true, // 保存时设为默认
          temperature: config.temperature,
          max_input_tokens: config.maxInputTokens,
          max_output_tokens: config.maxOutputTokens,
        }),
      })

      const result = await response.json()
      if (result.success) {
        setTestResult({ success: true, message: "配置保存成功" })
        // 重新加载配置列表
        await loadSavedConfigs()
        // 同时也保存到 localStorage（兼容旧版）
        localStorage.setItem("llm_config", JSON.stringify(config))
      } else {
        setTestResult({ success: false, message: result.message || "保存失败" })
      }
    } catch (error) {
      setTestResult({ success: false, message: "保存失败" })
    } finally {
      setIsSaving(false)
      setTimeout(() => setTestResult(null), 3000)
    }
  }

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

  const handleSetDefault = async (provider: string) => {
    try {
      const response = await fetch(`${API_BASE}/config/providers/${provider}/set-default`, {
        method: "POST",
      })
      const result = await response.json()
      if (result.success) {
        setDefaultProvider(provider)
        await loadSavedConfigs()
      }
    } catch (error) {
      console.error("设置默认服务商失败:", error)
    }
  }

  const handleProviderChange = (provider: string) => {
    const providerConfig = PROVIDER_OPTIONS.find(p => p.provider === provider)
    const savedConfig = savedConfigs.find((c: ServerProviderConfig) => c.provider === provider)

    if (providerConfig) {
      setConfig({
        provider,
        apiKey: "",
        baseUrl: savedConfig?.base_url || providerConfig.baseUrl,
        model: savedConfig?.model || providerConfig.model,
        temperature: savedConfig?.temperature ?? 0.7,
        maxInputTokens: savedConfig?.max_input_tokens ?? 4096,
        maxOutputTokens: savedConfig?.max_output_tokens ?? 2000,
      })
    }
  }

  const isConfigured = (provider: string) => {
    return savedConfigs.some((c: ServerProviderConfig) => c.provider === provider && c.is_active)
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">设置</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* 左侧：服务商列表 */}
        <div className="md:col-span-1">
          <div className="bg-white rounded-xl border p-4 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">已配置的服务商</h2>
            {isLoading ? (
              <p className="text-gray-500">加载中...</p>
            ) : savedConfigs.length === 0 ? (
              <p className="text-gray-500 text-sm">暂无已配置的服务商</p>
            ) : (
              <ul className="space-y-2">
                {savedConfigs.map((c: ServerProviderConfig) => (
                  <li
                    key={c.provider}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      c.provider === config.provider
                        ? "bg-indigo-50 border-indigo-200"
                        : "bg-white hover:bg-gray-50"
                    }`}
                    onClick={() => handleProviderChange(c.provider)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{c.provider}</p>
                        <p className="text-xs text-gray-500">{c.api_key_masked || "未配置 API Key"}</p>
                      </div>
                      {c.is_default && (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">默认</span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* 右侧：配置表单 */}
        <div className="md:col-span-2">
          <div className="bg-white rounded-xl border p-6 shadow-sm">
            <h2 className="text-xl font-semibold mb-4">LLM 服务商配置</h2>

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
                      {option.name} {isConfigured(option.provider) && "✓"}
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
                  您的 API Key 将加密存储在服务器数据库中。
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

              {/* 温度参数 */}
              <div>
                <Label htmlFor="temperature">温度（Temperature）: {config.temperature.toFixed(1)}</Label>
                <input
                  id="temperature"
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0（确定）</span>
                  <span>1（平衡）</span>
                  <span>2（随机）</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  控制输出的随机性：较低值使输出更确定，较高值使输出更富创造性。
                </p>
              </div>

              {/* 最大输入 Token */}
              <div>
                <Label htmlFor="maxInputTokens">最大输入 Token 数</Label>
                <Input
                  id="maxInputTokens"
                  type="number"
                  value={config.maxInputTokens}
                  onChange={(e) => setConfig({ ...config, maxInputTokens: parseInt(e.target.value) || 4096 })}
                  placeholder="4096"
                />
                <p className="text-xs text-gray-500 mt-1">
                  限制发送给 LLM 的最大输入 token 数量（包含提示词和上下文）。
                </p>
              </div>

              {/* 最大输出 Token */}
              <div>
                <Label htmlFor="maxOutputTokens">最大输出 Token 数</Label>
                <Input
                  id="maxOutputTokens"
                  type="number"
                  value={config.maxOutputTokens}
                  onChange={(e) => setConfig({ ...config, maxOutputTokens: parseInt(e.target.value) || 2000 })}
                  placeholder="2000"
                />
                <p className="text-xs text-gray-500 mt-1">
                  限制 LLM 返回的最大输出 token 数量。
                </p>
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
          </div>
        </div>
      </div>

      {/* 关于说明 */}
      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-4">关于</h2>
        <p className="text-gray-600">
          AI 教学 PPT 生成器使用 LLM 服务来生成教学内容。
          您可以配置自己的 API Key 来使用支持的 LLM 服务商。
        </p>
        <p className="text-gray-600 mt-2">
          支持的服务商：DeepSeek、OpenAI、Claude、智谱 GLM
        </p>
        <p className="text-gray-600 mt-2 text-sm">
          配置保存后会在所有页面中使用，无需重复配置。
        </p>
      </div>
    </div>
  )
}
