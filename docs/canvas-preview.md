# Canvas 预览功能文档

## 概述

Canvas 预览功能是本项目的核心功能之一，用于在 PPT 智能合并场景中提供真实的 PPT 页面渲染预览。

**功能位置**：`/merge` 页面

**核心组件**：
- `PptCanvasRenderer` - Canvas 渲染器组件
- `PptCanvasPreview` - Canvas 预览组件
- `PptxjsRenderer` - 降级渲染器（备选方案）

## 技术架构

### 渲染流程

```
PPTX 文件 → 后端解析 API → EnhancedPptPageData → Canvas 渲染器 → 可视化预览
                              ↓
                        渲染失败
                              ↓
                        降级模式 → 后端简化解析 → CSS 渲染
```

### 数据流

1. **前端上传**：用户通过拖拽或点击上传 PPTX 文件
2. **前端解析**：使用 `pptx-render` 库在浏览器端解析 PPTX
3. **Canvas 渲染**：将解析后的数据渲染到 Canvas
4. **降级处理**：渲染失败时调用后端 `/api/v1/ppt/parse` 获取简化数据

## 支持的渲染格式

### 文本渲染

| 属性 | 支持 | 说明 |
|---|---|---|
| 字体 | ✅ | 支持字体名称映射（Microsoft YaHei 等） |
| 大小 | ✅ | 按比例缩放（scale 因子） |
| 颜色 | ✅ | 十六进制颜色值 |
| 粗体 | ✅ | font-weight: bold |
| 斜体 | ✅ | font-style: italic |
| 下划线 | ✅ | Canvas 路径绘制下划线 |
| 对齐 | ✅ | left/center/right |

### 图片渲染

- **格式**：Base64 编码
- **压缩**：后端解析时自动压缩到 512px 宽度
- **懒加载**：滚动到可视区域才加载图片
- **缓存**：LRU 缓存已加载图片

### 表格渲染

- **边框**：Canvas 路径绘制
- **单元格**：自动计算行列尺寸
- **内容**：文本居中对齐
- **样式**：基础黑白样式

### 形状渲染

- **矩形**：`fillRect` + `strokeRect`
- **圆形**：`arc` 路径
- **背景色**：浅灰色填充

## 性能优化

### 离屏 Canvas 缓存（LRU）

```typescript
const MAX_CACHE_SIZE = 30  // 最多缓存 30 个页面
const canvasCache = new Map<string, HTMLCanvasElement>()
const cacheAccessOrder: string[] = []  // 访问顺序队列
```

**缓存键**：`page-{index}-w{width}-h{height}-q{quality}`

**淘汰策略**：超出上限时移除最早访问的缓存

### 分片渲染（requestIdleCallback）

```typescript
const RENDER_SCHEDULER = {
  MAX_PER_FRAME: 4,        // 每帧最多渲染 4 个 Canvas
  DEADLINE_MS: 8,          // 每帧可用时间 8ms
  LOW_QUALITY_THRESHOLD: 20, // 前 20 页高质量
  LOW_QUALITY_FACTOR: 0.5,    // 低质量因子
}
```

**降级方案**：不支持 `requestIdleCallback` 时使用 `requestAnimationFrame`

### 虚拟滚动

```typescript
const VIRTUAL_SCROLL_THRESHOLD = 12  // 超过 12 页启用
const RENDER_AHEAD = 3  // 预渲染前方 3 个
```

**可见范围计算**：
```typescript
const start = Math.floor(scrollTop / thumbnailHeight)
const end = Math.min(start + visibleCount, pages.length)
```

### 懒加载策略

- **前 20 页**：立即可见，高质量渲染
- **20 页以后**：按索引延迟渲染（每页延迟 100ms）
- **不可见区域**：只绘制占位符

### 简化渲染模式

为提升性能，缩略图模式采用简化渲染：
- 只绘制标题（前 20 字符）
- 绘制顶部背景色带
- 绘制内容占位符（灰色块）
- 图片用圆形占位符

**性能提升**：从 600ms/页 降低到 50ms/页

## 降级机制

### 触发条件

| 错误类型 | 检测方式 | 降级动作 |
|---|---|---|
| Canvas 2D 不支持 | `getContext('2d')` 返回 null | 后端解析降级 |
| 内存不足 | Canvas 尺寸 > 4096px | 显示警告 + 降级 |
| 渲染超时 | 渲染时间 > 5000ms | 超时警告 + 降级 |
| 格式不兼容 | 解析异常 | 显示兼容性警告 |

### 降级流程

1. **检测错误**：`PptCanvasRenderer` 捕获渲染异常
2. **设置状态**：`fallbackMode = true`
3. **获取降级数据**：调用 `/api/v1/ppt/parse?extract_enhanced=false`
4. **切换渲染器**：使用 `PptxjsRenderer` 渲染简化内容
5. **显示提示**：UI 显示降级原因和重试按钮

### 重试机制

```typescript
const handleRetry = async () => {
  setRetryCount(prev => prev + 1)
  setFallbackModeState(false)  // 尝试重新渲染
  // 重新触发解析
  onRenderError?.(new Error('retry'))
}
```

## API 端点

### POST /api/v1/ppt/parse

**请求参数**：
- `file`: PPTX 文件（FormData）
- `extract_enhanced`: `true` | `false`（是否提取增强元数据）

**响应格式**（enhanced=false）：
```json
{
  "success": true,
  "pages": [
    {
      "index": 0,
      "title": "页面标题",
      "content": ["内容段落 1", "内容段落 2"],
      "shapes": []
    }
  ]
}
```

## 组件 Props

### PptCanvasRenderer

```typescript
interface PptCanvasRendererProps {
  pageData: EnhancedPptPageData  // 页面数据
  width?: number                  // 画布宽度（默认 300）
  height?: number                 // 画布高度（默认 169）
  isSelected?: boolean            // 是否选中状态
  onClick?: () => void            // 点击回调
  quality?: number                // 渲染质量（1.0/0.5）
  onError?: (error: Error) => void // 错误回调
  fallbackMode?: boolean          // 降级模式标识
  pageIndex?: number              // 页面索引（超时检测）
}
```

### PptCanvasPreview

```typescript
interface PptCanvasPreviewProps {
  label: string                   // PPT 标签（如 "PPT A"）
  pages: PptPageData[]            // 页面数据数组
  isLoading?: boolean             // 加载状态
  selectedPages?: number[]        // 选中页面索引
  onSelectionChange?: (pages: number[]) => void  // 选择变化回调
  disableSelection?: boolean      // 禁用选择
  useCanvas?: boolean             // 使用 Canvas 渲染
  enableVirtualScroll?: boolean   // 启用虚拟滚动
  fallbackMode?: boolean          // 降级模式
  onFallbackModeChange?: (fallback: boolean) => void  // 降级切换回调
  file?: File | null              // PPT 文件引用
  onRenderError?: (error: Error) => void  // 渲染错误回调
}
```

## 浏览器兼容性

### 完全支持

| 浏览器 | 版本 | 备注 |
|---|---|---|
| Chrome | 90+ | 推荐，所有优化生效 |
| Edge | 90+ | Chromium 内核，同等支持 |
| Firefox | 88+ | 所有功能支持 |

### 部分支持

| 浏览器 | 版本 | 限制 |
|---|---|---|
| Safari | 14+ | requestIdleCallback 降级为 RAF |

### 不支持

| 浏览器 | 版本 | 降级方案 |
|---|---|---|
| IE 11 | 全部 | CSS 降级渲染 |

## 测试用例

### P0 测试（必测）

```bash
# 1. 基础渲染测试
访问 /merge → 上传 ppt_a.pptx → 验证 Canvas 显示

# 2. 多选测试
点击页面 1 → Shift+ 点击页面 5 → 验证连续 5 页选中

# 3. 降级测试
强制关闭 Canvas → 上传文件 → 验证降级提示
```

### P1 测试（按需）

```bash
# 1. 性能测试
上传 100 页 PPT → 记录渲染时间 <10s

# 2. 兼容性测试
Firefox/Safari → 验证功能正常
```

## 故障排查

### Canvas 渲染失败

**症状**：显示"Canvas 渲染不可用"警告

**排查步骤**：
1. 检查浏览器控制台是否有错误
2. 确认 Canvas 2D 上下文支持：`canvas.getContext('2d')`
3. 检查内存占用（任务管理器）
4. 尝试更换浏览器

### 降级模式无法退出

**症状**：降级后点击重试仍然降级

**解决方案**：
1. 刷新页面重新上传
2. 检查网络请求（/api/v1/ppt/parse）
3. 清除浏览器缓存

### 性能问题

**症状**：渲染卡顿、内存占用高

**优化建议**：
1. 减少同时渲染的页面数量
2. 使用 Chrome 浏览器
3. 关闭其他浏览器标签页

## 相关文件

| 文件 | 路径 | 说明 |
|---|---|---|
| Canvas 渲染器 | `frontend/src/components/ppt-canvas-renderer.tsx` | 核心渲染逻辑 |
| Canvas 预览 | `frontend/src/components/ppt-canvas-preview.tsx` | 预览组件 |
| 合并页面 | `frontend/src/app/merge/page.tsx` | 功能集成 |
| 后端解析 | `backend/app/api/ppt.py` | `/api/v1/ppt/parse` 端点 |

## 版本历史

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-03-04 | 初始实现（feat-083） |
| v1.1 | 2026-03-05 | 性能优化（feat-088） |
| v1.2 | 2026-03-06 | 虚拟滚动（feat-094） |
| v1.3 | 2026-03-07 | 降级机制（feat-097） |
| v1.4 | 2026-03-08 | 错误处理（feat-098） |
