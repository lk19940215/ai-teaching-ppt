# AI 产出内容后的美观渲染方案

> 日期：2026-03-11
> 状态：调研完成

## 一、问题定义

### 1.1 当前现状

AI 处理（润色/扩展/改写/提取/融合）后返回结构化 JSON：

```typescript
// 单页处理返回
interface SlideContent {
  title: string
  main_points: string[]
  additional_content?: string
}

// 多页融合返回
interface MergedSlide {
  title: string
  elements: Array<{ type: string; content: string }>
}
```

当前渲染方式：`contentToPageData()` 将所有 `main_points` 塞入一个 Canvas text_box → `PptCanvasRenderer` 绘制。

**渲染效果极差**：
- 纯黑色文字堆叠在灰色背景上
- 无字体层级（标题/正文同号）
- 无配色方案
- 无布局变化（永远是上下罗列）
- 无任何视觉吸引力

### 1.2 目标

将 AI 产出的结构化内容渲染为**美观、专业的教学幻灯片预览卡片**，具备：
- 清晰的字体层级和排版
- 教学风格的配色方案
- 根据内容类型自动选择布局模板
- 可选的入场动画

---

## 二、AI 返回数据格式详解

### 2.1 按 action 分类

| action | 返回字段 | 内容特点 |
|--------|---------|---------|
| `polish`（润色） | `title`, `main_points` | 内容精炼，与原文结构相似 |
| `expand`（扩展） | `title`, `main_points`, `additional_content` | 内容增多，有补充说明 |
| `rewrite`（改写） | `title`, `main_points` | 结构可能变化，风格不同 |
| `extract`（提取） | `title`, `main_points` | 知识点条目化，偏结构化 |
| `merge`（融合） | `title`, `elements[]` | 含 `title`/`text_body`/`list_item` 等类型 |

### 2.2 后端 content_snapshot 完整格式（参考）

```json
// polish
{ "action": "polish", "polished_content": { "title": "...", "main_points": [...], "polished_elements": [...] } }

// expand
{ "action": "expand", "expanded_content": { "title": "...", "original_points": [...], "expanded_points": [...], "new_examples": [...], "additional_content": "..." } }

// rewrite
{ "action": "rewrite", "rewritten_content": { "title": "...", "main_content": "...", "style_features": [...] } }

// extract
{ "action": "extract", "extracted_knowledge": { "core_concepts": [...], "formulas": [...], "methods": [...], "common_mistakes": [...], "related_knowledge": [...] } }
```

---

## 三、方案对比

### 方案 A：React 组件模板渲染（推荐）

**原理**：用 React 组件 + Tailwind CSS 将 AI JSON 渲染为美观的"幻灯片卡片"

**技术栈**：
- React 组件（与项目一致）
- Tailwind CSS（项目已使用）
- Framer Motion（可选动画，需安装）

**优势**：
- 完全可控的渲染效果
- 与项目技术栈100%一致，无新依赖
- 可为不同 action 定制专属模板
- 支持响应式，在缩略图和大图预览中自适应
- 后续可导出为图片（html2canvas）

**劣势**：
- 需要设计和实现多套模板
- 非真实 PPT 渲染（是"伪幻灯片"卡片）

### 方案 B：Reveal.js 嵌入

**原理**：将 AI 内容注入 Reveal.js 幻灯片框架，嵌入 iframe 渲染

**优势**：
- 专业幻灯片效果，支持过渡动画
- Markdown 渲染 + 代码高亮 + 数学公式
- 丰富的主题

**劣势**：
- Reveal.js 设计为全屏演示，嵌入预览面板需大量 CSS hack
- iframe 嵌入影响性能
- 与项目 React 生态整合成本高
- 缩略图场景无法使用

### 方案 C：Markdown → HTML 渲染

**原理**：AI 内容转 Markdown，用 `react-markdown` + 自定义主题渲染

**优势**：
- 实现简单
- Markdown 渲染库成熟

**劣势**：
- 排版控制有限（Markdown 无法精确控制布局）
- 无法实现幻灯片卡片式的视觉效果
- 不适合教学场景的展示需求

### 方案 D：Slidev / MARP

**原理**：使用 Slidev（Vue）或 MARP（Markdown）框架渲染

**劣势**：
- Slidev 基于 Vue，与项目 React 技术栈冲突
- MARP 是静态导出工具，不适合动态渲染
- 均设计为全屏演示场景

---

## 四、推荐方案：React 组件模板渲染

### 4.1 架构设计

```
SlideContent (AI JSON)
    ↓
SlideContentRenderer (入口组件)
    ↓
TemplateSelector (根据 action/元素数量/内容特征 选模板)
    ↓
具体模板组件
    ├── TitleTemplate        — 大标题 + 副标题（适合封面/章节）
    ├── BulletTemplate       — 标题 + 要点列表（适合 polish/expand）
    ├── KnowledgeTemplate    — 知识卡片网格（适合 extract）
    ├── CompareTemplate      — 左右/上下对比（适合 rewrite 前后对比）
    ├── ContentTemplate      — 标题 + 段落正文（适合 rewrite）
    └── MergeTemplate        — 融合结果展示（适合 merge 的 elements）
    ↓
Tailwind CSS 样式 + 可选 Framer Motion 动画
```

### 4.2 模板详细设计

#### 模板一：BulletTemplate（要点列表模板）

适用 action：`polish`, `expand`

```
┌────────────────────────────────────────────┐
│  ┌─ 蓝色色带 ─────────────────────────┐   │
│  │  📘  标题文字                       │   │
│  └─────────────────────────────────────┘   │
│                                            │
│  ● 要点一：同分母分数相加规则              │
│                                            │
│  ● 要点二：分母不变，分子相加              │
│                                            │
│  ● 要点三：结果需要化简                    │
│                                            │
│  ┌─ 浅蓝色背景 ───────────────────────┐   │
│  │  💡 补充说明：additional_content    │   │
│  └─────────────────────────────────────┘   │
│                                    P3 v2   │
└────────────────────────────────────────────┘
```

#### 模板二：KnowledgeTemplate（知识卡片模板）

适用 action：`extract`

```
┌────────────────────────────────────────────┐
│  📚  知识点提取                             │
│                                            │
│  ┌──────────┐  ┌──────────┐               │
│  │ 🔑 核心   │  │ 📐 公式   │               │
│  │ 概念1     │  │ 公式1     │               │
│  │ 概念2     │  │ 公式2     │               │
│  └──────────┘  └──────────┘               │
│                                            │
│  ┌──────────┐  ┌──────────┐               │
│  │ 📝 方法   │  │ ⚠️ 易错   │               │
│  │ 方法1     │  │ 错误1     │               │
│  │ 方法2     │  │ 错误2     │               │
│  └──────────┘  └──────────┘               │
└────────────────────────────────────────────┘
```

#### 模板三：MergeTemplate（融合结果模板）

适用 action：`merge`

```
┌────────────────────────────────────────────┐
│  ┌─ 紫色色带 ─────────────────────────┐   │
│  │  🔀  融合后标题                     │   │
│  └─────────────────────────────────────┘   │
│                                            │
│  ▎ 正文内容段落                            │
│  ▎ （type: text_body）                     │
│                                            │
│  • 列表项 1（type: list_item）             │
│  • 列表项 2                                │
│  • 列表项 3                                │
│                                            │
│                          融合自 A:P2 + B:P3 │
└────────────────────────────────────────────┘
```

### 4.3 设计规范

#### 配色方案

```
教学主题色系：
├── 主色：  #3B82F6 (蓝色)    — 标题、强调
├── 辅助1：#10B981 (绿色)    — 正确/要点
├── 辅助2：#F59E0B (琥珀)    — 警告/易错
├── 辅助3：#8B5CF6 (紫色)    — 融合/创意
├── 辅助4：#EF4444 (红色)    — 重要/错误
├── 背景：  #FFFFFF (白色)    — 卡片背景
├── 次背景：#F8FAFC (浅灰蓝) — 次要区域
└── 文字：  #1E293B (深灰蓝) — 正文
```

#### 字体层级

```
标题：    text-xl   font-bold     text-gray-900    (20px)
副标题：  text-base font-semibold text-gray-700    (16px)
正文：    text-sm   font-normal   text-gray-600    (14px)
注释：    text-xs   font-normal   text-gray-400    (12px)
```

#### 间距与圆角

```
卡片：   p-6  rounded-xl  shadow-sm  border
内部区块：p-4  rounded-lg  bg-gray-50
元素间距：space-y-3
卡片宽高比：16:9（aspect-video）
```

### 4.4 组件接口设计

```typescript
interface SlideContentRendererProps {
  content: SlideContent           // AI 返回的内容
  action?: SlideAction            // 操作类型（用于选模板）
  slide?: SlidePoolItem           // 幻灯片信息（来源标记等）
  size?: 'thumbnail' | 'preview'  // 渲染尺寸
  className?: string
  animated?: boolean              // 是否启用动画
}
```

### 4.5 模板选择逻辑

```typescript
function selectTemplate(content: SlideContent, action?: SlideAction): TemplateType {
  // 融合结果
  if (action === 'merge' || content.elements?.length > 0) return 'merge'

  // 知识点提取
  if (action === 'extract') return 'knowledge'

  // 改写（可能有前后对比）
  if (action === 'rewrite') return 'content'

  // 要点少于2条且有大段内容
  if ((content.main_points?.length || 0) <= 1 && content.additional_content) return 'content'

  // 默认：要点列表
  return 'bullet'
}
```

### 4.6 缩略图模式

在 `SlidePoolPanel` 和 `FinalSelectionBar` 中，需要渲染 96x54 的小缩略图：

```typescript
// size='thumbnail' 时的简化策略
- 隐藏补充说明
- 标题截断到 15 字
- 要点最多显示 3 条，每条截断到 20 字
- 字体缩小：标题 text-xs，正文 text-[10px]
- 禁用动画
```

---

## 五、动画方案（可选增强）

### 5.1 Framer Motion 基础动画

```typescript
// 元素依次入场
const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1 } },
}

const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
}
```

### 5.2 动画触发时机

- 版本切换时：新版本内容 fadeIn
- AI 处理完成时：结果卡片 slideUp + 要点逐条出现
- 缩略图模式：禁用动画

### 5.3 依赖评估

- `framer-motion` 约 ~150KB（gzip ~40KB）
- 项目已使用 Next.js + Tailwind，兼容性好
- 可作为第二阶段增强，初期用 CSS `transition` + `@keyframes` 替代

---

## 六、与现有代码的集成

### 6.1 替换 contentToPageData + PptCanvasRenderer

当前 `SlidePreviewPanel` 中：

```tsx
// 现在（效果差）
<PptCanvasRenderer
  pageData={contentToPageData(version.content, slide.original_index)}
  width={800} height={450}
/>

// 改为（效果好）
<SlideContentRenderer
  content={version.content}
  action={version.action}
  slide={slide}
  size="preview"
/>
```

### 6.2 决策逻辑

```
渲染 AI 版本（有 action 字段的 version）
    ↓
SlideContentRenderer (React 模板渲染)

渲染原始版本（v1，无 action 字段）
    ↓
优先 imageUrl → PptxViewJSRenderer → PptCanvasRenderer
```

### 6.3 需要修改的文件

| 文件 | 修改内容 |
|------|---------|
| 新建 `slide-content-renderer.tsx` | 核心组件：模板选择 + 各模板实现 |
| `slide-preview-panel.tsx` | 主预览区用 SlideContentRenderer 替代 Canvas |
| `slide-pool-panel.tsx` | 缩略图用 SlideContentRenderer 的 thumbnail 模式 |
| `final-selection-bar.tsx` | 同上 |
| `merge-session.ts` | 确保 `SlideContent` 类型包含 `elements` 字段 |

---

## 七、后续演进

### Phase 1（当前）：基础模板渲染
- 实现 BulletTemplate / KnowledgeTemplate / MergeTemplate
- 无动画，纯 Tailwind CSS

### Phase 2：动画增强
- 安装 Framer Motion
- 添加入场动画、版本切换过渡

### Phase 3：导出能力
- 使用 `html2canvas` 将 React 渲染结果导出为 PNG
- 可用于生成 PPT 时嵌入预览图

### Phase 4：用户自定义
- 支持切换配色主题（蓝/绿/紫/红）
- 支持选择字体（微软雅黑/思源黑体/楷体）
- 支持调整布局（紧凑/标准/宽松）
