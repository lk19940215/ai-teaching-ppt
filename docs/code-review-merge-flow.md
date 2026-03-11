# Merge 流程代码复审文档

> 日期：2026-03-11
> 范围：`/merge` 页面端到端流程（上传 → AI 处理 → 预览渲染 → 生成最终 PPT）

---

## 一、整体架构

```
用户上传 PPT A + PPT B
    ↓
[前端] initSession()
    ├── parsePptFile(A) → POST /api/v1/ppt/parse
    ├── parsePptFile(B) → POST /api/v1/ppt/parse
    └── createBackendSession(A, B) → POST /api/v1/session/create
    ↓
构建 slide_pool（每页一个 SlidePoolItem）
    ↓
三栏布局展示
    ├── SlidePoolPanel（左：幻灯片池）
    ├── SlidePreviewPanel（中：预览 + 操作）
    └── 右侧面板（提示词 + 说明）
    ↓
AI 处理
    ├── 单页：processSlide() → POST /api/v1/ppt/ai-merge (merge_type=single)
    └── 多页：mergeSlides() → POST /api/v1/ppt/ai-merge (merge_type=partial)
    ↓
SSE 流式响应 → 创建新版本/融合幻灯片
    ↓
FinalSelectionBar（底部：最终选择 + 拖拽排序）
    ↓
generateFinal() → POST /api/v1/ppt/generate-final
    ↓
下载最终 PPT
```

### 关键文件

| 文件 | 职责 |
|------|------|
| `frontend/src/app/merge/page.tsx` | 页面入口，三栏布局，事件分发 |
| `frontend/src/hooks/useMergeSession.ts` | 核心业务逻辑 Hook |
| `frontend/src/types/merge-session.ts` | 类型定义 + 工具函数 |
| `frontend/src/components/slide-pool-panel.tsx` | 左侧幻灯片池 |
| `frontend/src/components/slide-preview-panel.tsx` | 中间预览面板 |
| `frontend/src/components/final-selection-bar.tsx` | 底部最终选择栏 |
| `frontend/src/components/ppt-canvas-renderer.tsx` | Canvas 渲染器 |
| `backend/app/api/ppt.py` | 所有 PPT 相关 API 端点 |
| `backend/app/services/ppt_generator.py` | PPT 生成服务 |
| `backend/app/services/ppt_to_image.py` | PPT 转图片服务 |
| `backend/app/services/version_manager.py` | 版本管理服务 |

---

## 二、严重 BUG（阻断功能）

### BUG-1：`_add_slide_from_snapshot` 与 AI 返回的 content_snapshot 格式不兼容

**严重程度**：P0 — 导致 v2+ 版本生成的最终 PPT 页面为空白

**位置**：`backend/app/services/ppt_generator.py:524-573`

**问题分析**：

`_add_slide_from_snapshot` 方法期望的数据格式：
```python
snapshot = {
    "title": "标题",
    "main_points": ["要点1", "要点2"],
    "elements": [{"type": "text_body", "content": "内容"}]
}
```

但后端版本管理中存储的 `content_snapshot` 实际格式为嵌套结构：
```python
# polish 操作存储的格式
snapshot = {
    "action": "polish",
    "polished_content": {
        "title": "标题",
        "main_points": ["要点1", "要点2"]
    }
}
```

`_add_slide_from_snapshot` 直接取 `snapshot.get("title")` 和 `snapshot.get("main_points")`，得到的全是空值。

**讽刺的是**，同一个类中已经有 `_extract_content_from_snapshot` 方法可以正确提取嵌套内容（在 `generate_single_slide_pptx` 中使用），但 `_add_slide_from_snapshot` 没有调用它。

**修复方案**：在 `_add_slide_from_snapshot` 开头加入格式适配逻辑。

---

### BUG-2：融合幻灯片在 generate-final 中为占位实现

**严重程度**：P0 — 融合页面在最终 PPT 中内容完全错误

**位置**：`backend/app/api/ppt.py` 约 2679-2693 行

**问题分析**：

代码中有明确的 TODO 注释：
```python
# TODO: 后续需要存储融合幻灯片的独立内容
```

对 `merged_N` 类型的幻灯片，直接从 ppt_a 取第一页，完全未使用 AI 融合产生的内容。

前端 `mergeSlides()` 在 `useMergeSession.ts:606-613` 中正确创建了含融合内容的 `SlidePoolItem`，但 `generate-final` 后端无法获取这些前端状态。

**修复方案**：generate-final 请求中附带融合页的 `content`，后端用 `_add_slide_from_snapshot` 重建。

---

### BUG-3：`local_` 会话调用 generate-final 必失败

**严重程度**：P1 — 后端会话创建失败时，后续所有后端操作均不可用

**位置**：`frontend/src/hooks/useMergeSession.ts:255-258`

**问题分析**：

```typescript
// 后端创建会话失败时降级
return { session_id: `local_${Date.now()}`, slide_image_urls: { ppt_a: emptyUrls, ppt_b: emptyUrls } }
```

使用 `local_` 前缀的虚拟 session_id，但：
- 后端 `version_manager` 中无此会话
- 调用 `generate-final` 时后端返回 404
- AI 处理（processSlide/mergeSlides）不依赖 session_id，可以正常工作
- 但最终生成 PPT 环节必定失败

**修复方案**：
- 方案一：`local_` 模式下禁用"生成最终 PPT"按钮，提示用户检查后端连接
- 方案二：在 generateFinal 中检测 `local_` 前缀，走纯前端生成路径

---

### BUG-4：SSE 解析异常被空 catch 吞噬

**严重程度**：P1 — 后端返回异常数据时用户无法感知

**位置**：
- `useMergeSession.ts:422-424`（processSlide 中）
- `useMergeSession.ts:583-585`（mergeSlides 中）

**问题分析**：

```typescript
try {
  const event = JSON.parse(dataStr)
  if (event.stage === 'error') {
    throw new Error(event.message || '处理失败')  // (A)
  }
  // ...
} catch (e) {
  // 忽略解析错误  ← 空 catch，(A) 处抛出的错误也被吞噬
}
```

当 `event.stage === 'error'` 时，throw 被同一层的 catch 捕获并静默丢弃，导致错误不会传播到外层 try-catch，用户看不到错误信息，`finalResult` 为 null，最终只显示"未收到处理结果"而非后端返回的具体错误消息。

**修复方案**：将 error 判断移到 JSON.parse 的 try 块之外。

---

## 三、中等问题

### ISSUE-5：颜色格式缺少 `#` 前缀

**位置**：`frontend/src/components/ppt-canvas-preview.tsx:184`

```typescript
font: { size: 18, color: '000000' }  // 应为 '#000000'
```

Canvas 的 `fillStyle` 接受 CSS 颜色值，`'000000'` 不是合法的 CSS 颜色，实际会被忽略使用默认黑色（碰巧正确），但如果是其他颜色如 `'FF0000'` 则会渲染失败。

---

### ISSUE-6：convert-to-images URL 路径拼接错误

**位置**：`backend/app/services/ppt_to_image.py`

- `session_id = self.output_dir.name` → 当 `output_dir = uploads/versions` 时，`session_id = "versions"`
- 生成 URL：`http://localhost:8000/public/versions/versions/{filename}.png`（重复 "versions"）
- 且 `/public` 挂载的是 `public/` 目录，而图片文件存储在 `uploads/versions/`

这导致通过 `/api/v1/ppt/convert-to-images` 返回的图片 URL 无法访问。

---

### ISSUE-7：FinalSelectionBar 未使用 version.preview_url

**位置**：`frontend/src/components/final-selection-bar.tsx:123-136`

```tsx
{imageUrl ? (
  <img src={imageUrl} ... />
) : (
  <PptCanvasRenderer ... />
)}
```

`imageUrl` 来源于 `slideImageUrls?.[slide_id]`，但 `page.tsx` 传入的 `slideImageUrls` 可能为空。即使 version 对象上有 `preview_url` 字段，也未被使用。

**修复**：`const imageUrl = slideImageUrls?.[item.slide_item.slide_id] ?? item.version.preview_url`

---

### ISSUE-8：Canvas 段落居中/右对齐逻辑错误

**位置**：`frontend/src/components/ppt-canvas-renderer.tsx:357-378`

```typescript
for (const run of paragraph.runs) {
  renderTextRun(ctx, run, currentX, currentY, maxWidth)
  const textWidth = ctx.measureText(run.text).width
  currentX += textWidth  // 每个 run 累加 X
}
```

当 `textAlign` 为 `center` 或 `right` 时，应先计算整段总宽度，再确定起始 X 坐标。当前逻辑会导致多 run 段落的居中/右对齐完全错位。

---

## 四、代码重复与冗余

### 4.1 `versionToPageData` 重复定义三次

| 位置 | layout 尺寸 | 差异 |
|------|------------|------|
| `slide-pool-panel.tsx:57-81` | 240×135 | 缩略图版，字号 10 |
| `slide-preview-panel.tsx:114-138` | 960×540 | 预览版，字号 18，名为 `contentToPageData` |
| `final-selection-bar.tsx:51-74` | 180×100 | 选择栏版，字号 8，截断 20 字 |

三处功能相同（SlideVersion/SlideContent → EnhancedPptPageData），只是尺寸/字号不同。应提取为公共函数，通过参数控制尺寸。

### 4.2 `getSourceLabel` 重复定义

- `merge-session.ts` 中已 export 了 `getSourceLabel`
- `slide-pool-panel.tsx` 和 `page.tsx` 中也各自定义了类似的来源标签映射
- `sourceColor` 映射也在多处重复

### 4.3 三套渲染组件共存

| 组件 | 状态 | 建议 |
|------|------|------|
| `PptCanvasRenderer` | 正在使用（简化模式） | 保留并优化 |
| `PptxjsRenderer` | 未使用 | 删除或归档 |
| `PptxViewJSRenderer` | 未使用 | 修复后接入 |
| `PptxViewJSPreview` | 未使用 | 修复后接入或删除 |

### 4.4 后端重复导入

**位置**：`backend/app/api/ppt.py:2-3`

```python
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile  # 重复
```

### 4.5 死代码

- `backend/app/services/ppt_content_parser.py:409` — `_extract_teaching_content` 方法未被调用
- `ppt-canvas-renderer.tsx` — `renderImageShape` 和 `renderAutoShape` 定义了但在 `executeRender` 中未调用

---

## 五、数据流断裂分析

整个 AI 合并 → 渲染 → 生成 PPT 的链路存在多处数据格式不一致：

```
[前端] processSlide()
    ↓ POST /api/v1/ppt/ai-merge (merge_type=single)
[后端] AI 返回: { new_content: { title, main_points } }
    ↓ SSE 传回前端
[前端] createNewVersion(content = { title, main_points })
    ↓ version.content = SlideContent
[前端] 渲染: contentToPageData(version.content) → PptCanvasRenderer
    ↓ ⚠️ 渲染效果极差（见文档二）
[前端] generateFinal() → POST /api/v1/ppt/generate-final
    ↓ 发送 final_selection: ["ppt_a_0_v2"]
[后端] 解析 version_id → 获取 doc_state 中的 content_snapshot
    ↓ ⚠️ content_snapshot 格式为 {action, polished_content: {...}}
[后端] _add_slide_from_snapshot(snapshot)
    ↓ ⚠️ 直接取 snapshot.get("title") → 空值！
[结果] 生成的 PPT 页面为空白
```

**关键断裂点**：
1. 前端 `SlideContent` 是扁平的 `{title, main_points}`
2. 后端 `content_snapshot` 是嵌套的 `{action, polished_content: {title, main_points}}`
3. `_add_slide_from_snapshot` 按扁平格式读取，读不到嵌套内容

---

## 六、改造建议（实现文档二方案需要的代码修改）

### 6.1 新增文件

| 文件 | 说明 |
|------|------|
| `frontend/src/components/slide-content-renderer.tsx` | AI 内容美观渲染组件（React 模板） |
| `frontend/src/lib/slide-utils.ts` | 公共工具函数（versionToPageData、sourceLabel 等） |

### 6.2 修改文件

| 文件 | 修改内容 |
|------|---------|
| `slide-preview-panel.tsx` | 主预览区：有 action 的版本用 `SlideContentRenderer`，原始版本保留 Canvas |
| `slide-pool-panel.tsx` | 缩略图：删除本地 `versionToPageData`，改用 `slide-utils.ts` 或 `SlideContentRenderer` |
| `final-selection-bar.tsx` | 同上 |
| `useMergeSession.ts` | 修复 BUG-4（SSE 错误处理），完善 local_ 模式提示 |
| `ppt-canvas-renderer.tsx` | 修复颜色格式、段落对齐、启用图片/形状渲染 |
| `ppt-canvas-preview.tsx` | 修复颜色格式 `'000000'` → `'#000000'` |
| `ppt_generator.py` | 修复 BUG-1（_add_slide_from_snapshot 调用 _extract_content_from_snapshot） |
| `ppt.py` | 修复 BUG-2（merged_N 占位实现），删除重复导入 |
| `merge-session.ts` | SlideContent 类型增加 `elements` 字段 |

### 6.3 改造优先级

| 优先级 | 任务 | 依赖 |
|--------|------|------|
| P0 | 修复 BUG-1 (_add_slide_from_snapshot 格式) | 无 |
| P0 | 修复 BUG-4 (SSE 错误吞噬) | 无 |
| P1 | 修复 BUG-3 (local_ 模式提示) | 无 |
| P1 | 修复 ISSUE-5 (颜色格式) | 无 |
| P1 | 修复 ISSUE-7 (FinalSelectionBar preview_url) | 无 |
| P2 | 新建 SlideContentRenderer | 文档二方案确认后 |
| P2 | 提取 slide-utils.ts 公共函数 | 无 |
| P2 | 接入 PptxViewJSRenderer | 文档一方案确认后 |
| P3 | 修复 ISSUE-8 (段落对齐) | 无 |
| P3 | 清理死代码和未使用组件 | 无 |

---

## 七、测试验证清单

### 端到端测试

- [ ] 上传两个简单 PPT → 预览正常显示
- [ ] 选中一页 → 点击润色 → AI 返回后预览更新
- [ ] 切换版本 v1/v2 → 预览正确切换
- [ ] Ctrl 多选两页 → 融合 → 融合结果显示在幻灯片池
- [ ] 添加多页到最终选择 → 拖拽排序 → 生成最终 PPT → 下载成功
- [ ] 检查生成的 PPT 中 v2+ 版本页面内容正确（非空白）
- [ ] 检查融合页在最终 PPT 中内容正确（非 ppt_a 第一页）

### 边界情况

- [ ] 后端不可用时的降级（local_ 模式提示）
- [ ] 无 LibreOffice 时的预览效果
- [ ] 空内容幻灯片的渲染
- [ ] 超长标题/要点的截断展示
