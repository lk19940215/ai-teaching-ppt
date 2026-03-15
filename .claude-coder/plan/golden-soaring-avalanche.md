# AI教学PPT合并功能优化方案

## 一、问题概述

### 1.1 现状问题
根据需求文档，`/merge`页面在单页面合并时触发AI合并后存在以下问题：
- **返回的结构数据不明确**：不清楚AI返回的数据格式和字段含义
- **渲染灰色块**：AI返回数据后，前端渲染出现灰色块，视觉效果不佳
- **功能效果不佳**：执行AI润色、合并等操作的效果不理想

### 1.2 根本原因分析
通过代码库探索，发现问题根源：

1. **单页处理的数据流不一致**
   - 后端`/api/ppt/ai-merge`在`merge_type='single'`时，调用`merger.process_single_page()`
   - 但后端返回的`result`结构与前端期望的`MergePlan`结构不同
   - 前端`merge-result-preview.tsx`依赖`MergePlan.slide_plan`来显示预览

2. **数据结构不匹配**
   - 前端期望：`SlidePlanItem.new_content` 可以是`string`或`SlideContent`对象
   - 后端实际：`process_single_page()`返回的`new_content`格式不确定，可能是纯文本或结构化对象

3. **渲染逻辑缺失**
   - `slide-content-renderer.tsx`的模板选择逻辑基于`action`和`content.elements`
   - 但单页处理时，`new_content`可能缺少必要的字段（如`title`、`main_points`）
   - 导致渲染器无法正确识别模板类型，显示默认的灰色背景

## 二、技术方案

### 2.1 整体架构

#### 2.1.1 数据流架构
```
用户操作
  ↓
前端 /merge/page.tsx
  ↓
调用 useMergeSession Hook
  ↓
发起 SSE 请求到 /api/ppt/ai-merge
  ↓
后端 content_merger.process_single_page()
  ↓
返回统一结构化的 JSON 响应
  ↓
前端解析并渲染到 SlideContentRenderer
  ↓
用户可见的预览卡片
```

#### 2.1.2 数据结构定义

**后端统一返回结构（SinglePageResult扩展）：**
```typescript
interface SinglePageMergeResult {
  merge_type: 'single'
  action: MergeAction  // polish | expand | rewrite | extract
  slide_plan: [
    {
      action: MergeAction
      source: 'A' | 'B'
      slide_index: number
      new_content: SlideContent  // 必须是结构化对象
      reason: string
    }
  ]
  success: boolean
  error?: string
}
```

**SlideContent（结构化JSON）：**
```typescript
interface SlideContent {
  title: string  // 必填，标题（用于渲染色带）
  main_points?: string[]  // 要点列表
  additional_content?: string  // 补充说明
  elements?: Array<{  // 融合结果的结构化元素
    type: 'title' | 'subtitle' | 'text_body' | 'list_item'
    content: string
  }>
}
```

### 2.2 后端改造方案

#### 2.2.1 修改 `content_merger.py` 的 `process_single_page` 方法

**目标：** 确保单页处理返回结构化的`SlideContent`对象

```python
def process_single_page(self, slide_data, action, custom_prompt=""):
    """处理单页操作，返回结构化的 SlideContent"""
    # 1. 构建提示词
    prompt = self._build_single_page_prompt(slide_data, action, custom_prompt)

    # 2. 调用 LLM
    response = self._call_llm(prompt)

    # 3. 解析返回结果（确保返回结构化数据）
    parsed = self._parse_single_page_response(response, action)

    return {
        'action': action,
        'new_content': parsed,  # SlideContent 结构
        'original_slide': slide_data,
        'changes': [],  # 可选：记录变化点
        'success': True
    }
```

**新增解析方法：**
```python
def _parse_single_page_response(self, response, action):
    """将 LLM 响应解析为结构化的 SlideContent"""
    # 尝试从响应中提取 JSON
    json_data = self._extract_json(response)

    # 如果解析成功，验证必要字段
    if json_data and 'title' in json_data:
        return {
            'title': json_data['title'],
            'main_points': json_data.get('main_points', []),
            'additional_content': json_data.get('additional_content', ''),
            'elements': json_data.get('elements', [])
        }

    # 如果解析失败，从文本中提取标题和要点
    text = response if isinstance(response, str) else str(response)
    title, main_points = self._extract_title_and_points(text)

    return {
        'title': title or 'AI处理结果',
        'main_points': main_points or [text[:100]],  # 至少保留摘要
        'additional_content': text[100:] if len(text) > 100 else ''
    }
```

#### 2.2.2 修改 `ppt.py` 的 `ai_merge_ppts` 路由

**目标：** 统一返回格式，与前端`MergePlan`接口兼容

```python
# 在 ai_merge_ppts 函数中，处理单页模式
elif merge_type == 'single':
    source_doc_data = doc_a if source_doc == 'A' else doc_b
    slides = source_doc_data.get('slides', [])
    if single_page_index < 0 or single_page_index >= len(slides):
        raise ValueError(f'页码超出范围：{single_page_index}')

    # 调用单页处理
    result = merger.process_single_page(slides[single_page_index], single_page_action, custom_prompt)

    # 统一包装为 MergePlan 格式
    unified_result = {
        'merge_type': 'single',
        'slide_plan': [{
            'action': result['action'],
            'source': source_doc,
            'slide_index': single_page_index,
            'sources': None,
            'new_content': result['new_content'],  # SlideContent 对象
            'instruction': custom_prompt,
            'reason': 'AI单页处理结果'
        }],
        'merge_strategy': f'{single_page_action} 单页',
        'summary': '单页处理完成',
        'knowledge_points': []
    }
```

### 2.3 前端改造方案

#### 2.3.1 确保 SSE 处理逻辑

在`useMergeSession`或相关 hook 中，处理单页合并的 SSE 响应：

```typescript
// 处理 AI 合并的 SSE 响应
const handleAIMergeResponse = (event: MessageEvent) => {
  const data = JSON.parse(event.data)

  if (data.stage === 'complete' && data.result) {
    const result = data.result

    // 统一处理：无论是 full 还是 single，都有 slide_plan
    if (result.slide_plan) {
      // 将 new_content 确保为 SlideContent 格式
      const normalizedPlan: MergePlan = {
        merge_strategy: result.merge_strategy || '单页处理',
        slide_plan: result.slide_plan.map((item: SlidePlanItem) => ({
          ...item,
          // 确保 new_content 是对象格式
          new_content: parseSlideContent(item.new_content)
        })),
        summary: result.summary || '',
        knowledge_points: result.knowledge_points || []
      }

      setMergePlan(normalizedPlan)
      setStatus('complete')
    }
  }
}
```

#### 2.3.2 优化 `slide-content-renderer.tsx`

虽然用户表示"确认数据结构后渲染即可"，但仍建议增加数据验证：

```typescript
export function SlideContentRenderer({
  content,
  action,
  slide,
  size = "preview",
  className,
  animated = false,
}: SlideContentRendererProps) {
  const isThumbnail = size === "thumbnail"

  // 确保 title 存在，避免渲染空白
  const safeContent: SlideContent = {
    title: content.title || '未命名幻灯片',
    main_points: content.main_points || [],
    additional_content: content.additional_content,
    elements: content.elements
  }

  const templateType = selectTemplate(safeContent, action)

  // ... 原有渲染逻辑
}
```

#### 2.3.3 确认 `merge-result-preview.tsx` 的缩略图显示

当前逻辑已正确处理 `new_content` 为空的情况（显示动作图标和描述）：

```typescript
{thumbnailUrl ? (
  <img src={thumbnailUrl} ... />
) : (
  <div className="bg-gradient-to-br from-gray-50 to-gray-100">
    {/* 显示动作标签和内容摘要 */}
    <span className={getActionColor(action)}>
      {getActionIcon(action)}
      {getActionDescription(action)}
    </span>
    {item.new_content && (
      <p>{getNewContentText(item.new_content).slice(0, 50)}...</p>
    )}
  </div>
)}
```

**优化建议：** 确保 `getNewContentText` 正确处理 `SlideContent` 对象：

```typescript
function getNewContentText(newContent: string | any): string {
  if (!newContent) return ''
  if (typeof newContent === 'string') return newContent

  // 处理 SlideContent 对象
  const content = parseSlideContent(newContent)
  const parts: string[] = []

  if (content.title) parts.push(content.title)
  if (content.main_points && content.main_points.length > 0) {
    parts.push(...content.main_points.slice(0, 2))
  }
  if (content.additional_content) {
    parts.push(content.additional_content)
  }

  return parts.join(' | ')
}
```

### 2.4 关键数据结构映射

| 操作类型 | 后端返回字段 | 前端渲染模板 | 关键字段要求 |
|---------|------------|------------|------------|
| `polish` | `new_content: {title, main_points}` | BulletTemplate | title必填 |
| `expand` | `new_content: {title, main_points, additional_content}` | BulletTemplate | title必填 |
| `rewrite` | `new_content: {title, main_points}` | ContentTemplate | title必填 |
| `extract` | `new_content: {title, main_points}` | KnowledgeTemplate | title必填，按关键词分类 |
| `merge` | `new_content: {title, elements}` | MergeTemplate | title必填，elements数组 |

## 三、实施步骤

### 第一阶段：后端改造（预计2小时）

1. **修改 `content_merger.py`**
   - [ ] 实现 `_parse_single_page_response` 方法
   - [ ] 修改 `process_single_page` 返回结构化 `SlideContent`
   - [ ] 确保所有单页操作（polish/expand/rewrite/extract）都返回相同结构

2. **修改 `ppt.py` 的 `ai_merge_ppts` 路由**
   - [ ] 统一 `merge_type='single'` 的返回格式为 `MergePlan` 兼容结构
   - [ ] 确保 `new_content` 字段始终为对象格式

3. **测试验证**
   - [ ] 使用 Postman 测试 `/api/ppt/ai-merge` 的单页模式
   - [ ] 验证返回的 JSON 结构符合预期
   - [ ] 检查所有操作类型（polish/expand/rewrite/extract）的返回

### 第二阶段：前端改造（预计1小时）

1. **验证 SSE 响应处理**
   - [ ] 确认前端接收到的 `new_content` 已是对象格式
   - [ ] 如果需要，添加数据验证和默认值处理

2. **测试渲染效果**
   - [ ] 在 `/merge` 页面测试单页处理
   - [ ] 验证不同操作类型的渲染模板选择正确
   - [ ] 确认不再出现灰色块

3. **优化用户体验**
   - [ ] 添加加载状态提示
   - [ ] 处理错误情况（如 API 调用失败）

### 第三阶段：端到端测试（预计1小时）

1. **功能测试**
   - [ ] 测试 `polish` 操作：润色文字，渲染为 BulletTemplate
   - [ ] 测试 `expand` 操作：扩展内容，渲染为 BulletTemplate
   - [ ] 测试 `rewrite` 操作：改写风格，渲染为 ContentTemplate
   - [ ] 测试 `extract` 操作：提取知识点，渲染为 KnowledgeTemplate

2. **回归测试**
   - [ ] 测试多页合并（`merge_type='full'`）不受影响
   - [ ] 测试部分合并（`merge_type='partial'`）不受影响

3. **性能测试**
   - [ ] 检查 AI 调用响应时间
   - [ ] 验证 SSE 流式传输正常

## 四、验证方案

### 4.1 后端验证

```bash
# 测试单页润色
curl -X POST http://localhost:8000/api/v1/ppt/ai-merge \
  -F "file_a=@test_a.pptx" \
  -F "file_b=@empty.pptx" \
  -F "merge_type=single" \
  -F "single_page_action=polish" \
  -F "single_page_index=0" \
  -F "source_doc=A" \
  -F "provider=deepseek" \
  -F "api_key=your_key"
```

**期望返回：**
```json
{
  "merge_type": "single",
  "slide_plan": [{
    "action": "polish",
    "source": "A",
    "slide_index": 0,
    "new_content": {
      "title": "润色后的标题",
      "main_points": ["要点1", "要点2"],
      "additional_content": "补充说明"
    },
    "reason": "AI单页处理结果"
  }],
  "merge_strategy": "polish 单页",
  "summary": "单页处理完成"
}
```

### 4.2 前端验证

1. **打开浏览器开发者工具**
   - 查看 Network 面板，确认 SSE 响应数据
   - 检查 `new_content` 是否为对象格式

2. **在 `/merge` 页面操作**
   - 上传两个 PPT 文件
   - 选择单页，点击"润色"按钮
   - 观察预览区域是否正确渲染（蓝色色带 + 要点列表）

3. **验证不同操作**
   - 尝试 expand、rewrite、extract 操作
   - 确认每种操作都使用正确的模板渲染

### 4.3 灰色块问题排查

如果仍有灰色块出现，检查：

1. **缩略图 URL 是否存在**
   - 检查 `pptAImageUrls` / `pptBImageUrls` 是否正确填充
   - 如果没有缩略图，应该显示动作图标而不是灰色背景

2. **new_content 是否为空**
   - 在浏览器控制台打印 `item.new_content`
   - 确认不是 `null` 或空字符串

3. **模板选择逻辑**
   - 检查 `selectTemplate` 函数的返回值
   - 确认 `content.title` 存在

## 五、风险评估

### 5.1 技术风险

| 风险项 | 影响 | 缓解措施 |
|-------|-----|---------|
| LLM 返回格式不一致 | 前端解析失败 | 增加 `_parse_single_page_response` 的容错处理 |
| 历史数据兼容性 | 现有代码报错 | 保持向后兼容，支持字符串和对象两种格式 |
| 性能影响 | 响应变慢 | 监控 API 响应时间，优化提示词 |

### 5.2 业务风险

| 风险项 | 影响 | 缓解措施 |
|-------|-----|---------|
| 用户操作体验下降 | 用户流失 | 充分测试，确保所有操作类型正常工作 |
| 渲染效果不符合预期 | 用户不满意 | 参考现有的模板设计，保持一致性 |

## 六、后续优化建议

### 6.1 短期优化（本次迭代后）

1. **增加内容验证**
   - 前端增加 `SlideContent` 的 TypeScript 类型检查
   - 后端增加返回数据的 Schema 验证

2. **优化错误处理**
   - 统一错误返回格式
   - 前端显示友好的错误提示

3. **性能优化**
   - 缓存 AI 处理结果
   - 实现请求去重

### 6.2 中期优化（下一迭代）

1. **模板增强**
   - 为每种操作类型设计专属的视觉风格
   - 增加配色方案配置

2. **内容质量提升**
   - 优化 LLM 提示词，提高返回质量
   - 增加内容审核机制

3. **用户体验优化**
   - 实现实时预览（输入提示语即时预览效果）
   - 增加版本对比功能

## 七、关键文件清单

### 后端文件
- `backend/app/services/content_merger.py` - 核心修改：`process_single_page` 和 `_parse_single_page_response`
- `backend/app/api/ppt.py` - 修改：`ai_merge_ppts` 路由的单页处理逻辑

### 前端文件
- `frontend/src/types/merge-plan.ts` - 已有定义，无需修改
- `frontend/src/components/slide-content-renderer.tsx` - 可选优化：增加默认值处理
- `frontend/src/app/merge/page.tsx` 或相关 hook - 确认 SSE 响应处理逻辑

### 测试文件
- 建议添加单元测试：
  - `backend/tests/test_content_merger.py` - 测试 `process_single_page` 返回格式
  - `frontend/src/__tests__/slide-content-renderer.test.tsx` - 测试渲染逻辑

---

**方案制定日期：** 2026-03-15
**方案状态：** 待批准
**预计实施时间：** 4小时（含测试）
