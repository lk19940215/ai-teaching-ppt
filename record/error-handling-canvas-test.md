# Canvas 预览错误处理策略文档

## 概述

本文档记录了 PPT Canvas 预览组件（feat-098）实现的完整错误处理和用户提示机制。

## 错误类型分类

### P0 级别错误（必须处理）

#### 1. 文件不存在/格式错误

**触发条件**：
- 用户上传非 .pptx 格式文件
- 文件已删除或路径无效
- 文件大小超过 20MB 限制

**错误提示**：
```
文件格式错误："xxx.ppt" 不是 PPTX 格式，请选择 .pptx 文件
文件大小超出限制：25.3MB > 20MB，请上传小于 20MB 的文件
```

**实现位置**：
- `frontend/src/app/merge/page.tsx` - `handleFileChange`, `handleDrop`

---

#### 2. Canvas 不支持（降级提示）

**触发条件**：
- 浏览器不支持 Canvas 2D 上下文
- Canvas 渲染完全失败

**错误提示**：
```
浏览器不支持 Canvas 2D 渲染，已切换到后端解析模式（仅显示文本内容）。
建议使用 Chrome、Firefox、Edge 等现代浏览器。
```

**降级行为**：
- 自动调用 `/api/v1/ppt/parse?extract_enhanced=false`
- 使用简化版文本渲染
- 显示重试按钮

**实现位置**：
- `frontend/src/components/ppt-canvas-renderer.tsx` - `executeRender`
- `frontend/src/components/ppt-canvas-preview.tsx` - `handleRenderError`

---

#### 3. 加载超时（重试机制）

**触发条件**：
- PPT 解析 API 超过 30 秒无响应
- Canvas 单页渲染超过 5 秒

**错误提示**：
```
PPT 解析超时（30 秒），文件可能过大或网络连接不稳定，请重试
渲染超时（5 秒），PPT 页面内容过多或浏览器性能不足
```

**重试机制**：
- 用户可点击"尝试重新渲染"按钮重试
- 重试次数显示在 UI 中
- 重试时清除降级模式状态

**实现位置**：
- `frontend/src/app/merge/page.tsx` - `parsePptFile` (AbortController 30s 超时)
- `frontend/src/components/ppt-canvas-renderer.tsx` - `executeRender` (5s 渲染检测)
- `frontend/src/components/ppt-canvas-preview.tsx` - `handleRetry`

---

### P1 级别错误（按情况处理）

#### 4. 格式不兼容警告

**触发条件**：
- PPT 包含复杂动画、过渡效果
- 特殊字体或嵌入对象
- 非标准形状或图表

**警告提示**：
```
格式兼容性提示
- 此 PPT 包含某些可能无法完全兼容的格式元素
- 复杂动画、过渡效果在预览中不可见
```

**UI 展示**：
- 蓝色警告框（非阻塞）
- 列出具体不兼容项

**实现位置**：
- `frontend/src/components/ppt-canvas-preview.tsx` - `compatibilityWarnings`

---

#### 5. 内存不足（清理建议）

**触发条件**：
- Canvas 尺寸超过 4096px 限制
- 浏览器内存不足导致渲染失败
- 同时渲染过多页面

**错误提示**：
```
内存不足，无法渲染此 PPT 页面。
建议：关闭其他浏览器标签页，或重启浏览器释放内存后重试。
```

**自动优化**：
- 前 20 页高质量渲染，后续页面低质量
- 虚拟滚动：只渲染可见区域
- LRU 缓存：最多缓存 30 个页面

**实现位置**：
- `frontend/src/components/ppt-canvas-renderer.tsx` - `executeRender` (内存检查)
- `RENDER_SCHEDULER.LOW_QUALITY_THRESHOLD = 20`
- `MAX_CACHE_SIZE = 30`

---

## 错误处理流程图

```
用户上传 PPT
    │
    ▼
文件验证 ────────► 格式错误/超限 ──► 显示错误提示
    │
    ▼
调用解析 API ────► 超时/失败 ──────► 显示错误 + 重试按钮
    │
    ▼
Canvas 渲染 ────► 不支持/失败 ─────► 降级模式 + 提示
    │
    ▼
成功显示预览
```

---

## 测试场景

### 场景 1：文件格式错误
1. 访问 `/merge` 页面
2. 上传 `.ppt` 或 `.pdf` 文件
3. 预期：显示"文件格式错误"提示

### 场景 2：文件超大
1. 访问 `/merge` 页面
2. 上传大于 20MB 的 PPTX 文件
3. 预期：显示"文件大小超出限制"提示

### 场景 3：Canvas 不支持
1. 使用不支持 Canvas 的旧浏览器
2. 访问 `/merge` 页面
3. 预期：自动降级，显示文本预览

### 场景 4：渲染超时
1. 上传包含复杂内容的 PPTX（100+ 页）
2. 观察渲染过程
3. 预期：超过 5 秒显示超时提示，提供重试按钮

### 场景 5：内存不足
1. 打开多个浏览器标签页
2. 上传大型 PPTX 文件
3. 预期：显示内存不足提示，建议关闭其他标签页

---

## 代码结构

| 文件 | 职责 |
|------|------|
| `merge/page.tsx` | 文件验证、API 调用超时、错误分类显示 |
| `ppt-canvas-renderer.tsx` | Canvas 渲染、超时检测、内存检查 |
| `ppt-canvas-preview.tsx` | 降级模式、重试机制、兼容性警告 |

---

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RENDER_TIMEOUT` | 5000ms | Canvas 渲染超时阈值 |
| `API_TIMEOUT` | 30000ms | PPT 解析 API 超时阈值 |
| `MAX_CANVAS_SIZE` | 4096px | Canvas 最大边长 |
| `MAX_CACHE_SIZE` | 30 | LRU 缓存页面数量上限 |
| `MAX_FILE_SIZE` | 20MB | 上传文件大小限制 |

---

## 后续优化建议

1. **错误日志上报**：将错误信息发送到后端日志系统
2. **性能监控**：收集渲染时间数据，优化阈值
3. **用户反馈**：添加"报告问题"按钮
4. **浏览器检测**：提前检测浏览器能力，主动提示

---

**文档版本**: v1.0
**创建时间**: 2026-03-08
**关联功能**: feat-098 错误处理和用户提示
