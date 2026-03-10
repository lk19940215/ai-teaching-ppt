# 单页实时预览方案设计

> 创建时间：2026-03-10
> 状态：待实现

---

## 一、需求背景

### 1.1 当前问题

用户期望的单页处理流程：
```
上传 PPT → 逐页 AI 处理（润色/扩展/改写）→ 【实时预览效果】→ 确认应用 → 继续下一页 → 全部完成后生成最终 PPT
```

当前实现的问题：
1. **缺少实时 PPT 预览** - AI 处理后只显示文字对比，看不到真实 PPT 效果
2. **缺少累积状态** - 处理完一页后没有进度显示
3. **缺少最终生成逻辑** - 没有把所有修改应用到最终 PPT 的入口

### 1.2 目标

- AI 处理单页后，用户能立即看到**真实的 PPT 效果预览**
- 显示**处理进度**（如：已处理 3/10 页）
- 支持**逐页累积修改**，最后统一生成

---

## 二、技术方案

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端交互层                               │
├─────────────────────────────────────────────────────────────────┤
│  PptCanvasPreview    SinglePageProcessor    ProcessingProgress  │
│  (预览组件)           (处理面板)             (进度显示)           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                         后端服务层                               │
├─────────────────────────────────────────────────────────────────┤
│  /ai-merge (single)   /version/create   /generate-final         │
│  (单页 AI 处理)        (创建新版本)       (生成最终 PPT)          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                         数据存储层                               │
├─────────────────────────────────────────────────────────────────┤
│  SessionData          SlideVersion           临时 PPTX          │
│  (会话状态)            (版本历史)             (生成的预览文件)     │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心流程

#### 流程 1：单页处理 + 实时预览

```
1. 用户点击第 N 页
   ↓
2. 选择操作（润色/扩展/改写/提取）
   ↓
3. 调用 /ai-merge (merge_type=single)
   - 后端返回 AI 修改后的内容结构 (content_snapshot)
   ↓
4. 调用 /version/create
   - 传入 content_snapshot
   - 后端生成临时 PPTX（仅第 N 页）
   - 后端调用 LibreOffice 转换为 PNG
   - 返回新的 image_url
   ↓
5. 前端更新预览图片
   - 显示处理后的真实 PPT 效果
   - 版本标记更新为 v2
   ↓
6. 更新累积状态
   - processedPages["A-2"] = { action: "polish", version: "v2" }
   - 进度显示：已处理 1/22 页
```

#### 流程 2：逐页累积 + 最终生成

```
1. 用户依次处理多个页面
   - 第 1 页：润色 → v2
   - 第 3 页：扩展 → v2
   - 第 5 页：改写 → v2
   ↓
2. 前端维护 processedPages 状态
   {
     "A-0": { action: "polish", version: "v2" },
     "A-2": { action: "expand", version: "v2" },
     "A-4": { action: "rewrite", version: "v2" }
   }
   ↓
3. 用户点击"生成最终 PPT"
   ↓
4. 调用 /generate-final
   - 传入 session_id 和 version_map
   - 后端合并所有修改
   - 生成最终 PPTX 文件
   ↓
5. 返回下载链接
```

---

## 三、数据结构

### 3.1 前端状态

```typescript
// 已处理页面状态
interface ProcessedPage {
  pageIndex: number
  source: 'A' | 'B'
  action: 'polish' | 'expand' | 'rewrite' | 'extract'
  version: string  // "v2", "v3" 等
  imageUrl: string // 处理后的预览图
  contentSnapshot: object // AI 修改的内容快照
}

// 组件状态
const [processedPages, setProcessedPages] = useState<Record<string, ProcessedPage>>({})
// 例：{ "A-0": { pageIndex: 0, source: "A", action: "polish", ... } }

// 处理进度
const processingProgress = {
  total: pptAPages.length + pptBPages.length,
  processed: Object.keys(processedPages).length
}
```

### 3.2 后端 API 扩展

#### /version/create 增强请求

```json
{
  "session_id": "abc123",
  "document_id": "ppt_a",
  "slide_index": 0,
  "operation": "ai_polish",
  "prompt": "润色文字表达",
  "content_snapshot": {
    "title": "润色后的标题",
    "main_points": ["要点1", "要点2"],
    "additional_content": "扩展内容"
  },
  "generate_preview": true  // 新增：是否生成预览图片
}
```

#### /version/create 增强响应

```json
{
  "version": "v2",
  "image_url": "http://localhost:8000/uploads/versions/abc123/ppt_a_slide0_v2.png",
  "created_at": "10:05:00",
  "has_preview": true  // 新增：是否有预览图
}
```

---

## 四、UI 设计

### 4.1 页面布局调整

```
┌─────────────────────────────────────────────────────────────┐
│  步骤指示器                                                  │
├─────────────────────────────────────────────────────────────┤
│  顶部控制条                                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 处理进度：已处理 3/22 页  [生成最终 PPT]              │  │
│  └───────────────────────────────────────────────────────┘  │
├────────────────────────────┬────────────────────────────────┤
│  左侧：PPT 预览区           │  右侧：处理面板              │
│                            │                                │
│  ┌──────────────────┐      │  ┌─ SinglePageProcessor ────┐ │
│  │ 第 1 页 [v2] ✓   │      │  │ • 操作选择               │ │
│  │ 第 2 页 [v1]     │      │  │ • 处理中... / 结果预览   │ │
│  │ 第 3 页 [v2] ✓   │      │  │ • 应用/取消              │ │
│  │ ...              │      │  └───────────────────────────┘ │
│  └──────────────────┘      │                                │
└────────────────────────────┴────────────────────────────────┘
```

### 4.2 处理进度组件

```tsx
function ProcessingProgress({ processed, total }: { processed: number; total: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2">
        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-600 transition-all"
            style={{ width: `${(processed / total) * 100}%` }}
          />
        </div>
        <span className="text-sm text-gray-600">
          已处理 {processed}/{total} 页
        </span>
      </div>
      {processed > 0 && (
        <Button size="sm" variant="default">
          生成最终 PPT
        </Button>
      )}
    </div>
  )
}
```

### 4.3 已处理页面标记

```tsx
// 在缩略图上显示处理状态
<div className="relative">
  <img src={page.imageUrl} />
  {processedPages[`${source}-${index}`] && (
    <>
      <Badge className="absolute top-1 right-1">v{processedPages[key].version}</Badge>
      <div className="absolute bottom-1 left-1 text-green-600 text-xs">✓ 已处理</div>
    </>
  )}
</div>
```

---

## 五、实现步骤

### Phase 1：后端预览生成（优先级 P0）

| 任务 | 描述 | 文件 |
|------|------|------|
| 1.1 | /version/create 支持 generate_preview 参数 | backend/app/api/ppt.py |
| 1.2 | 生成单页临时 PPTX | backend/app/services/ppt_generator.py |
| 1.3 | 调用 LibreOffice 转换为 PNG | backend/app/services/ppt_to_image.py |
| 1.4 | 返回预览图 URL | backend/app/services/version_manager.py |

### Phase 2：前端实时预览（优先级 P0）

| 任务 | 描述 | 文件 |
|------|------|------|
| 2.1 | 处理完成后刷新预览图片 | frontend/src/app/merge/page.tsx |
| 2.2 | 显示处理中 loading 状态 | frontend/src/components/single-page-processor.tsx |
| 2.3 | 已处理页面标记 v2 徽章 | frontend/src/components/ppt-canvas-preview.tsx |

### Phase 3：累积状态与进度（优先级 P1）

| 任务 | 描述 | 文件 |
|------|------|------|
| 3.1 | 添加 processedPages 状态 | frontend/src/app/merge/page.tsx |
| 3.2 | 创建 ProcessingProgress 组件 | frontend/src/components/processing-progress.tsx |
| 3.3 | 已处理页面显示 ✓ 标记 | frontend/src/components/ppt-canvas-preview.tsx |

### Phase 4：最终生成（优先级 P0）

| 任务 | 描述 | 文件 |
|------|------|------|
| 4.1 | 收集 version_map 调用 /generate-final | frontend/src/app/merge/page.tsx |
| 4.2 | 后端合并所有修改生成最终 PPT | backend/app/services/ppt_generator.py |
| 4.3 | 下载验证 | E2E 测试 |

---

## 六、验收标准

| 功能 | 验收标准 |
|------|----------|
| 实时预览 | AI 处理后预览图片立即更新，显示真实 PPT 效果 |
| 版本标记 | 已处理页面显示 v2 徽章 |
| 处理进度 | 显示"已处理 N/M 页"进度条 |
| 累积修改 | 处理多个页面后状态正确累积 |
| 最终生成 | 点击"生成最终 PPT"后下载的文件包含所有修改 |

---

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LibreOffice 转换慢 | 用户体验差 | 显示 loading 动画，异步处理 |
| 临时文件堆积 | 磁盘空间 | 定时清理 session 目录 |
| 版本冲突 | 数据不一致 | 使用乐观锁，冲突时提示用户 |