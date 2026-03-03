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
}

const PROVIDER_OPTIONS = [
  { value: "deepseek", name: "DeepSeek", baseUrl: "https://api.deepseek.com", model: "deepseek-chat" },
  { value: "openai", name: "OpenAI", baseUrl: "https://api.openai.com/v1", model: "gpt-4" },
  { value: "claude", name: "Claude", baseUrl: "https://api.anthropic.com/v1", model: "claude-3-opus-20240229" },
  { value: "glm", name: "智谱 GLM", baseUrl: "https://open.bigmodel.cn/api/paas/v4", model: "glm-4" },
]

const DEFAULT_CONFIG: LLMConfig = {
  provider: "deepseek",
  apiKey: "",
  baseUrl: "",
  model: "",
}

export default function SettingsPage() {
  const [config, setConfig] = useState<LLMConfig>(DEFAULT_CONFIG)
  const [isSaving, setIsSaving] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [isTesting, setIsTesting] = useState(false)

  // 从 localStorage 加载配置
  useEffect(() => {
    const savedConfig = localStorage.getItem("llm_config")
    if (savedConfig) {
      setConfig(JSON.parse(savedConfig))
    }
  }, [])

  const handleSave = () => {
    setIsSaving(true)
    try {
      localStorage.setItem("llm_config", JSON.stringify(config))
      setTestResult({ success: true, message: "配置已保存" })
      setTimeout(() => setTestResult(null), 3000)
    } catch (error) {
      setTestResult({ success: false, message: "保存失败" })
    } finally {
      setIsSaving(false)
    }
  }

  const handleTest = async () => {
    setIsTesting(true)
    setTestResult(null)

    try {
      const response = await fetch("http://localhost:8000/api/v1/generate/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: config.provider,
          apiKey: config.apiKey,
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

  const handleProviderChange = (provider: string) => {
    const providerConfig = PROVIDER_OPTIONS.find(p => p.value === provider)
    if (providerConfig) {
      setConfig({
        provider,
        apiKey: config.apiKey,
        baseUrl: providerConfig.baseUrl,
        model: providerConfig.model,
      })
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">设置</h1>

      <div className="bg-white rounded-xl border p-6 shadow-sm mb-6">
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
                <option key={option.value} value={option.value}>
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
              您的 API Key 将只保存在本地浏览器中，不会发送到其他服务器。
            </p>
          </div>

          {/* Base URL（可选） */}
          <div>
            <Label htmlFor="baseUrl">API Base URL（可选）</Label>
            <Input
              id="baseUrl"
              value={config.baseUrl}
              onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
              placeholder={PROVIDER_OPTIONS.find(p => p.value === config.provider)?.baseUrl}
            />
          </div>

          {/* 模型名称（可选） */}
          <div>
            <Label htmlFor="model">模型名称（可选）</Label>
            <Input
              id="model"
              value={config.model}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              placeholder={PROVIDER_OPTIONS.find(p => p.value === config.provider)?.model}
            />
          </div>

          {/* 按钮组 */}
          <div className="flex gap-4 pt-4">
            <Button
              onClick={handleSave}
              disabled={isSaving}
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

      <div className="bg-white rounded-xl border p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-4">关于</h2>
        <p className="text-gray-600">
          AI 教学 PPT 生成器使用 LLM 服务来生成教学内容。
          您可以配置自己的 API Key 来使用支持的 LLM 服务商。
        </p>
        <p className="text-gray-600 mt-2">
          支持的服务商：DeepSeek、OpenAI、Claude、智谱 GLM
        </p>
      </div>
    </div>
  )
}