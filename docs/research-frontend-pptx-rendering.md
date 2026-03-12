# 前端解析 PPT 通过 Canvas 渲染 — 调研方案

> 日期：2026-03-11
> 状态：调研完成

## 一、背景与目标

当前项目 `/merge` 页面的 PPT 预览方案：

1. **主方案**：后端 LibreOffice + PyMuPDF 将 PPTX 转 PNG 图片
2. **兜底方案**：前端 `PptCanvasRenderer` 绘制简化占位符（灰色色块 + 截断标题）

**问题**：
- LibreOffice 需安装 ~300MB 系统依赖，部署门槛高
- 兜底 Canvas 渲染效果极差，仅显示标题文字和灰色矩形，无法辨识页面内容
- 对于教学场景（无复杂动画/3D/SmartArt），后端转换属于"杀鸡用牛刀"

**目标**：评估纯前端渲染 PPTX 的可行性，在无 LibreOffice 时提供可用的预览体验。

---

## 二、项目现有前端渲染组件

项目中已存在三套前端渲染方案，但仅一套在 merge 页面使用（且为简化模式）：

### 2.1 PptCanvasRenderer（正在使用）

- **文件**：`frontend/src/components/ppt-canvas-renderer.tsx`
- **原理**：后端解析 PPTX → JSON (`EnhancedPptPageData`) → Canvas 2D 绘制
- **当前状态**：为性能优化（feat-094），采用"简化渲染"，只画标题+灰色占位块
- **已知问题**：
  - 图片仅绘制占位符（灰色矩形 + 🖼 图标），不加载真实图片
  - 段落居中/右对齐逻辑错误（多 run 时 currentX 累加导致错位）
  - AutoShape 有渲染函数但未在 `executeRender` 中调用
  - 颜色格式 `'000000'` 缺少 `#` 前缀

### 2.2 PptxjsRenderer（未使用）

- **文件**：`frontend/src/components/pptxjs-renderer.tsx`
- **原理**：JSZip 解压 PPTX → 解析 slide XML → Canvas 渲染
- **依赖**：`jszip ^3.10.1`（已安装）
- **问题**：
  - 只渲染第一页（`slides: slides[0] || []`）
  - Shape 解析未实现（只有 renderShape 函数体）
  - 图片异步加载未等待
  - 未被任何页面引用

### 2.3 PptxViewJSRenderer（未使用）

- **文件**：`frontend/src/components/pptxviewjs-renderer.tsx`
- **原理**：使用 `pptxviewjs` 库，Canvas 像素级渲染
- **依赖**：`pptxviewjs ^1.1.4` + `chart.js ^4.5.1`（均已安装）
- **问题**：
  - 事件名可能不匹配（代码用 `loaded`，文档为 `loadComplete`）
  - `goToSlide` / `render` 的参数传递需确认
  - 仅被 `pptxviewjs-preview.tsx` 内部引用，未接入任何路由

---

## 三、业界方案调研

### 3.1 pptxviewjs（推荐）

| 属性 | 详情 |
|------|------|
| 官网 | https://gptsci.com/pptxviewjs/ |
| 协议 | MIT 开源 |
| 渲染方式 | Canvas 2D |
| npm | `pptxviewjs ^1.1.4` |
| 周下载量 | ~2K |
| 模块格式 | ESM / CJS / UMD |

**支持的元素**：
- 文本（字体、大小、颜色、粗体、斜体、下划线）
- 图片（嵌入 PNG/JPEG/SVG）
- 表格（含合并单元格、边框、底纹）
- 图表（依赖 Chart.js）
- 形状（矩形、圆形、自由形状等）

**基本用法**：

```javascript
import { PPTXViewer } from 'pptxviewjs'

const viewer = new PPTXViewer({
  canvas: document.getElementById('canvas'),
  slideSizeMode: 'fit',
  backgroundColor: '#ffffff',
})

viewer.on('loadComplete', (slideCount) => {
  console.log(`共 ${slideCount} 页`)
})

const buffer = await file.arrayBuffer()
viewer.loadFile(buffer)
viewer.renderSlide(0) // 渲染第一页
```

**优势**：
- 项目已安装，已有封装组件
- 纯前端，零后端依赖
- Canvas 渲染保真度较高
- 支持 React/Vue/Svelte 框架集成

**劣势**：
- 社区相对较小
- 复杂动画/3D 不支持
- 需确认 API 兼容性

### 3.2 pptx-preview（备选）

| 属性 | 详情 |
|------|------|
| 官网 | https://github.com/501351981/pptx-preview |
| 协议 | npm 免费商用，核心代码不开源 |
| 渲染方式 | HTML DOM |
| npm | `pptx-preview ^1.0.7` |
| 周下载量 | ~8.3K |

**基本用法**：

```javascript
import { init } from 'pptx-preview'

const previewer = init(document.getElementById('container'), {
  width: 960,
  height: 540,
})

const buffer = await file.arrayBuffer()
previewer.preview(buffer)
```

**优势**：
- 活跃维护（2025 年更新）
- HTML 渲染可直接用 CSS 定制样式
- 支持动画效果
- 下载量较大，社区验证充分

**劣势**：
- 核心代码不开源，调试困难
- 依赖 echarts（图表渲染），体积增加 ~500KB
- HTML 渲染在缩略图场景下性能不如 Canvas

### 3.3 @kandiforge/pptx-renderer（参考）

| 属性 | 详情 |
|------|------|
| 协议 | 商业授权 |
| 渲染方式 | Canvas 2D（React 专用） |
| 性能 | <50ms/页 |

**优势**：React 原生、高性能、支持高 DPI、主题色解析
**劣势**：商业授权，不适合开源/教学项目

### 3.4 JSZip + 自研渲染（不推荐）

即项目中 `PptxjsRenderer` 的思路：

- **原理**：用 JSZip 解压 PPTX → 手动解析 XML → Canvas 绘制
- **优势**：完全可控，无第三方依赖
- **劣势**：工作量巨大，需实现完整的 OOXML 渲染引擎
- **评估**：不现实。PPTX 的 XML 结构复杂（`drawingML`, `slideLayout`, `slideMaster`, `theme`），自研渲染投入产出比极低

---

## 四、方案对比

| 维度 | pptxviewjs | pptx-preview | 自研(JSZip) | 现有 Canvas |
|------|-----------|-------------|------------|-------------|
| 渲染保真度 | ★★★★ | ★★★★ | ★★ | ★ |
| 接入成本 | 极低（已安装） | 低（需安装） | 极高 | 已接入 |
| 体积 | ~50KB | ~600KB(含echarts) | ~10KB | 0 |
| 缩略图性能 | 好 | 一般(DOM) | 差 | 好 |
| 开源程度 | MIT | 部分闭源 | 完全自研 | 完全自研 |
| 教学场景适配 | 好 | 好 | 差 | 差 |

---

## 五、推荐方案

### 主方案：pptxviewjs（已安装，优先接入）

适用于：有原始 PPTX 文件的场景（v1 原始版本预览）

### 降级方案：优化 PptCanvasRenderer

适用于：AI 处理后的新版本（无 PPTX 文件，只有 JSON 内容）

### 保留方案：LibreOffice 后端转换

不删除现有代码，有 LibreOffice 时仍优先使用高保真图片预览。

---

## 六、实施路线

### 阶段一：修复 PptxViewJSRenderer（1-2天）

1. 核实 pptxviewjs 实际 API（事件名、方法签名）
2. 修复 `pptxviewjs-renderer.tsx` 中的事件监听和参数传递
3. 编写单元测试验证渲染功能

### 阶段二：接入 merge 页面（1-2天）

1. 在 `SlidePoolPanel` 缩略图中，当有 PPTX 文件引用时，用 `PptxViewJSRenderer` 渲染
2. 在 `SlidePreviewPanel` 主预览区同理
3. 保留 `PptCanvasRenderer` 作为 AI 版本的渲染兜底

### 阶段三：优化 PptCanvasRenderer（1天）

1. 修复颜色格式（补 `#` 前缀）
2. 修复段落对齐逻辑
3. 启用图片真实渲染（异步加载 + 缓存）
4. 启用 AutoShape 渲染

### 阶段四：集成测试（1天）

1. 上传不同复杂度的教学 PPT 测试渲染效果
2. 验证降级链路：pptxviewjs → PptCanvasRenderer → 占位符
3. 性能测试：50 页 PPT 渲染时间 < 5s

---

## 七、渲染优先级决策树

> **实现状态**：✅ 已完成（feat-177）
>
> 实现位置：
> - `frontend/src/components/slide-preview-panel.tsx` (主预览区)
> - `frontend/src/components/slide-pool-panel.tsx` (缩略图)

```
渲染请求
    ↓
有 LibreOffice 图片 URL？
    ├── 是 → 使用 <img> 显示（最高保真）
    └── 否 ↓
有原始 PPTX 文件引用？
    ├── 是 → PptxViewJSRenderer（前端 Canvas 渲染）
    └── 否 ↓
是 AI 版本（有 action）？
    ├── 是 → SlideContentRenderer（React 模板渲染）
    └── 否 ↓
有解析后的 EnhancedPptPageData？
    ├── 是 → PptCanvasRenderer（优化版）
    └── 否 → 占位符（页码 + 灰色背景）
```

**降级链路完整性**：
1. ✅ LibreOffice 图片 → 直接显示
2. ✅ 原始版本（无 action）→ PptxViewJSRenderer
3. ✅ AI 版本（有 action）→ SlideContentRenderer
4. ✅ 兜底 → PptCanvasRenderer / 占位符
