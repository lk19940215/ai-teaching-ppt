# API 数据流文档

本文档描述 `/api/v1/ppt/ai-merge-single` API 的完整请求/响应格式，供前后端开发参考。

相关文档：
- [PPT 数据结构](./ppt-structure.md) - 完整数据模型定义
- [Canvas 预览](./canvas-preview.md) - 前端渲染实现

---

## 1. API 概述

### 端点信息

| 属性 | 值 |
|------|-----|
| 路径 | `/api/v1/ppt/ai-merge-single` |
| 方法 | `POST` |
| Content-Type | `multipart/form-data` |
| 功能 | 单页 AI 处理 + 实时生成 PPT 图片预览 |

### 处理流程

```
1. 解析原始 PPT 获取页面结构
2. 调用 LLM 进行 AI 处理
3. 生成单页 PPTX 文件
4. 转换为 PNG 预览图
```

---

## 2. 请求格式

### 2.1 FormData 参数

| 参数名 | 类型 | 必需 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `file` | File | ✅ | - | PPTX 文件 |
| `page_index` | int | ✅ | - | 要处理的页码（0-indexed） |
| `action` | string | ✅ | - | 操作类型：`polish`/`expand`/`rewrite`/`extract` |
| `custom_prompt` | string | ❌ | `null` | 自定义提示语 |
| `provider` | string | ❌ | `"deepseek"` | LLM 服务商 |
| `api_key` | string | ✅ | - | API 密钥 |
| `base_url` | string | ❌ | `null` | API Base URL（自定义端点） |
| `model` | string | ❌ | `null` | 模型名称（覆盖默认） |
| `temperature` | float | ❌ | `0.3` | 温度参数 |
| `max_tokens` | int | ❌ | `2000` | 最大输出 token |

### 2.2 TypeScript 类型定义

```typescript
interface AiMergeSingleRequest {
  file: File                  // PPTX 文件（必需）
  page_index: number          // 页码，0-indexed（必需）
  action: 'polish' | 'expand' | 'rewrite' | 'extract'  // 操作类型（必需）
  custom_prompt?: string      // 自定义提示语（可选）
  provider: string            // LLM 服务商（默认 'deepseek'）
  api_key: string             // API 密钥（必需）
  base_url?: string           // API Base URL（可选）
  model?: string              // 模型名称（可选）
  temperature: number         // 温度参数（默认 0.3）
  max_tokens: number          // 最大输出 token（默认 2000）
}
```

### 2.3 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/ppt/ai-merge-single" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@presentation.pptx" \
  -F "page_index=0" \
  -F "action=polish" \
  -F "provider=deepseek" \
  -F "api_key=sk-xxx" \
  -F "temperature=0.3" \
  -F "max_tokens=2000"
```

---

## 3. 响应格式

### 3.1 成功响应

```typescript
interface AiMergeSingleResponse {
  success: boolean              // true
  content: UnifiedSlideContent  // 处理后的内容
  preview_url?: string          // 预览图 URL（如 /public/images/xxx/slide.png）
  image_path?: string           // 图片服务器路径
  degraded: boolean             // 是否降级模式（图片生成失败时为 true）
  error?: string                // 错误信息（仅 degraded=true 时）
}
```

### 3.2 UnifiedSlideContent 结构

```typescript
interface UnifiedSlideContent {
  title: string                    // 页面标题
  main_points: string[]            // 主要要点（最多 6 条）
  additional_content?: string      // 额外内容（例题、易错提醒等）
  elements?: ElementData[]         // 元素列表（可选）
  metadata?: {                     // 元数据
    action: string                 // 操作类型
    additional_content?: string
    [key: string]: any             // action 特有的额外字段
  }
}
```

### 3.3 成功响应示例

```json
{
  "success": true,
  "content": {
    "title": "一元二次方程的概念",
    "main_points": [
      "一元二次方程的定义：只含有一个未知数，且未知数的最高次数为2的整式方程",
      "标准形式：ax² + bx + c = 0（a≠0）",
      "系数含义：a 为二次项系数，b 为一次项系数，c 为常数项"
    ],
    "additional_content": "",
    "elements": [],
    "metadata": {
      "action": "polish",
      "additional_content": ""
    }
  },
  "preview_url": "/public/images/abc123/slide.png",
  "image_path": "/data/images/abc123/slide.png",
  "degraded": false
}
```

---

## 4. 各 Action 返回格式差异

### 4.1 字段映射表

| action | LLM 返回字段 | 标准化后字段 | 说明 |
|--------|-------------|-------------|------|
| `polish` | `polished_content` | `title, main_points` | 润色后的文字 |
| `expand` | `expanded_content` | `title, original_points, expanded_points, new_examples` | 扩展内容 |
| `rewrite` | `rewritten_content` | `title, main_content, style_features` | 改写后的风格 |
| `extract` | `extracted_knowledge` | `core_concepts, formulas, methods, common_mistakes` | 知识点提取 |

### 4.2 各 Action 详细说明

#### polish（润色）

对文字进行优化润色，保持原意但提升表达质量。

```json
{
  "title": "润色后的标题",
  "main_points": ["优化后的要点1", "优化后的要点2"],
  "additional_content": "",
  "metadata": {
    "action": "polish",
    "changes": [
      { "location": "标题", "original": "原标题", "polished": "润色后标题" }
    ]
  }
}
```

#### expand（扩展）

扩展页面内容，增加补充说明和例题。

```json
{
  "title": "扩展后的标题",
  "main_points": ["原要点1", "原要点2", "扩展要点1"],
  "additional_content": "新增例题：例题1内容；例题2内容",
  "metadata": {
    "action": "expand",
    "original_points": ["原要点1", "原要点2"],
    "expanded_points": ["扩展要点1"],
    "new_examples": ["例题1内容", "例题2内容"]
  }
}
```

#### rewrite（改写）

以特定风格重新改写内容。

```json
{
  "title": "改写后的标题",
  "main_points": ["改写后的内容段落1", "改写后的内容段落2"],
  "additional_content": "风格特点：简洁明了、层次清晰",
  "metadata": {
    "action": "rewrite",
    "style_features": ["简洁明了", "层次清晰"]
  }
}
```

#### extract（提取知识点）

从页面中提取核心知识点、公式和方法。

```json
{
  "title": "知识点提取",
  "main_points": [
    "【一元二次方程】只含一个未知数且最高次数为2的整式方程",
    "【求根公式】x = (-b ± √(b²-4ac)) / 2a"
  ],
  "additional_content": "易错提醒：忘记检验根是否满足原方程",
  "metadata": {
    "action": "extract",
    "core_concepts": [
      { "concept": "一元二次方程", "definition": "..." }
    ],
    "formulas": [
      { "name": "求根公式", "formula": "x = (-b ± √(b²-4ac)) / 2a" }
    ],
    "methods": [],
    "common_mistakes": [
      { "mistake": "忘记检验", "correction": "代入原方程验证" }
    ]
  }
}
```

---

## 5. 错误响应格式

### 5.1 HTTP 400 - 参数错误

请求参数无效时返回。

```json
{
  "detail": "页码超出范围：5，有效范围 0-9"
}
```

**常见错误：**

| 错误信息 | 原因 |
|---------|------|
| `上传文件为空` | 未提供 file 参数或文件内容为空 |
| `页码超出范围：X，有效范围 0-Y` | page_index 超出 PPT 页数范围 |
| `无效的操作类型：xxx` | action 不是 polish/expand/rewrite/extract 之一 |
| `缺少必需参数：api_key` | 未提供 API Key |

### 5.2 HTTP 500 - 服务器错误

服务器处理过程中发生异常。

```json
{
  "detail": "单页处理失败: LLM 调用失败: API Key 无效"
}
```

**常见错误：**

| 错误信息 | 原因 |
|---------|------|
| `LLM 调用失败: API Key 无效` | API Key 过期或不正确 |
| `LLM 调用失败: 网络连接超时` | 无法连接到 LLM 服务 |
| `PPT 解析失败` | 文件格式损坏或不支持 |
| `JSON 序列化失败` | LLM 返回格式异常 |

### 5.3 错误排查建议

1. **检查后端终端输出** - 查看 ERROR 级别日志
2. **检查浏览器控制台** - Network 标签查看响应详情
3. **验证 localStorage 配置** - 确认 LLM 配置完整
4. **测试连接** - 在设置页面验证 API Key 有效性

---

## 6. 前端调用示例

### 6.1 TypeScript 实现

```typescript
async function processSlide(
  file: File,
  pageIndex: number,
  action: 'polish' | 'expand' | 'rewrite' | 'extract',
  llmConfig: LLMConfig
): Promise<AiMergeSingleResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('page_index', pageIndex.toString())
  formData.append('action', action)
  formData.append('provider', llmConfig.provider || 'deepseek')
  formData.append('api_key', llmConfig.apiKey)
  formData.append('temperature', '0.3')
  formData.append('max_tokens', '2000')

  if (llmConfig.baseUrl) {
    formData.append('base_url', llmConfig.baseUrl)
  }
  if (llmConfig.model) {
    formData.append('model', llmConfig.model)
  }

  const response = await fetch('/api/v1/ppt/ai-merge-single', {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '处理失败')
  }

  return response.json()
}
```

### 6.2 错误处理

```typescript
try {
  const result = await processSlide(file, 0, 'polish', llmConfig)
  if (result.success) {
    console.log('处理成功:', result.content.title)
    if (result.degraded) {
      console.warn('降级模式:', result.error)
    }
  }
} catch (error) {
  if (error.message.includes('页码超出范围')) {
    // 处理参数错误
  } else if (error.message.includes('API Key')) {
    // 处理认证错误
  } else {
    // 处理其他错误
  }
}
```

---

## 7. 后端实现参考

### 7.1 关键文件

| 文件 | 用途 |
|------|------|
| `backend/app/api/ppt.py` | API 路由定义 |
| `backend/app/services/content_merger.py` | AI 内容融合引擎 |
| `backend/app/services/llm.py` | LLM 服务封装 |
| `backend/app/services/ppt_generator.py` | PPT 生成器 |
| `backend/app/models/ppt_structure.py` | 数据模型定义 |

### 7.2 数据流转

```
请求 → ai_merge_single_page()
     → parse_pptx_to_structure()     # 解析 PPT
     → get_content_merger()          # 创建 AI 处理器
     → process_single_page()         # LLM 处理
     → _extract_content_by_action()  # 标准化输出
     → generate_single_slide_pptx()  # 生成 PPTX
     → convert_single_slide_to_image() # 生成预览图
     → 返回响应
```

---

## 更新日志

| 日期 | 变更 |
|------|------|
| 2026-03-21 | feat-250: 初始版本，基于方案文档创建 |
| 2026-03-21 | feat-241: 统一 UnifiedSlideContent 格式 |
| 2026-03-21 | feat-247: 新增 base_url/model 参数 |
| 2026-03-21 | feat-249: 增强错误日志记录 |