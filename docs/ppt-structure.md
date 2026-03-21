# PPT 中间数据结构文档

## 概述

本文档描述 PPTX 文件解析后生成的中间数据结构，以及 AI 处理阶段和渲染阶段的数据流转约定。

## 设计原则

1. **语义优先**：提取对 AI 有意义的内容，忽略渲染细节
2. **类型明确**：每种元素有明确的类型标识
3. **位置信息**：保留元素的相对位置，便于重建布局
4. **教学语义**：识别页面在教学场景中的角色
5. **类型同步**：后端 Pydantic 模型自动生成前端 TypeScript 类型

---

## 1. 三阶段数据流架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   解析阶段    │────▶│  AI处理阶段   │────▶│   渲染阶段    │
│              │     │              │     │              │
│ PPTX 文件    │     │ ContentMerger│     │ PPTGenerator │
│     ↓        │     │     ↓        │     │     ↓        │
│ DocumentData │     │ SlideContent │     │ 新PPTX文件   │
│ SlideData    │     │ MergePlan    │     │              │
│ ElementData  │     │ SingleResult │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## 2. 解析阶段数据结构

### 2.1 核心类型定义

**文件**: `backend/app/models/ppt_structure.py`

#### 元素类型 (ElementType)

| 值 | 说明 |
|----|------|
| `title` | 标题 |
| `subtitle` | 副标题 |
| `text_body` | 正文 |
| `list_item` | 列表项 |
| `image` | 图片 |
| `table` | 表格 |
| `shape` | 形状 |
| `placeholder` | 占位符 |
| `unknown` | 未知类型 |

#### 页面类型 (SlideType)

| 值 | 说明 |
|----|------|
| `title_slide` | 封面页 |
| `outline_slide` | 目录页 |
| `content_slide` | 内容页 |
| `section_slide` | 章节页 |
| `end_slide` | 结束页 |
| `unknown` | 未知类型 |

#### 教学角色 (TeachingRole)

| 值 | 说明 |
|----|------|
| `cover` | 封面 |
| `outline` | 目录 |
| `concept` | 概念讲解 |
| `example` | 例题讲解 |
| `exercise` | 练习 |
| `summary` | 总结 |
| `homework` | 作业 |
| `unknown` | 未知类型 |

#### 页面状态 (SlideStatus)

| 值 | 说明 |
|----|------|
| `active` | 活跃状态 |
| `deleted` | 已删除 |

### 2.2 位置信息 (Position)

所有位置信息使用**百分比**表示，相对于幻灯片尺寸：

```json
{
  "x_pct": 10.5,
  "y_pct": 5.2,
  "width_pct": 79.0,
  "height_pct": 15.0
}
```

**字段说明**：
- `x_pct`: 左边距百分比 (0-100)
- `y_pct`: 上边距百分比 (0-100)
- `width_pct`: 宽度百分比 (0-100)
- `height_pct`: 高度百分比 (0-100)

**转换公式**:
```python
# EMU 转 百分比
x_pct = round(shape.left / 914400 / slide_width * 100, 2)
```

**优点**：
- 不依赖具体像素值
- 便于在不同尺寸下重建布局
- AI 更容易理解相对位置

### 2.3 样式信息 (Style)

```json
{
  "font_name": "微软雅黑",
  "font_size": 24.0,
  "bold": true,
  "italic": false,
  "underline": false,
  "color": "#FF0000",
  "alignment": "left",
  "line_spacing": 1.5,
  "background_color": "#FFFFFF",
  "indent_level": 0
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `font_name` | string | 字体名称 |
| `font_size` | number | 字号 (pt) |
| `bold` | boolean | 是否粗体 |
| `italic` | boolean | 是否斜体 |
| `underline` | boolean | 是否下划线 |
| `color` | string | 颜色 (#RRGGBB 或主题色名称) |
| `alignment` | string | 对齐方式: left/center/right/justify |
| `line_spacing` | number | 行距倍数 (1.0 = 单倍行距) |
| `background_color` | string | 背景色 (#RRGGBB) |
| `indent_level` | number | 缩进级别 (0-8) |

### 2.4 段落结构 (Paragraph)

```json
{
  "text": "同分母分数相加，分母不变，分子相加。",
  "role": "definition",
  "style": {
    "font_name": "微软雅黑",
    "font_size": 18.0
  }
}
```

**字段说明**：
- `text`: 段落文本
- `role`: 段落角色 (definition/example/note)
- `style`: 段落样式

### 2.5 元素数据结构 (ElementData)

```json
{
  "element_id": "elem_001",
  "type": "title",
  "position": {
    "x_pct": 10.5,
    "y_pct": 5.2,
    "width_pct": 79.0,
    "height_pct": 15.0
  },
  "text": "分数加法",
  "paragraphs": [...],
  "style": {...}
}
```

**完整字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `element_id` | string | ✅ | 元素唯一标识 (elem_000) |
| `type` | ElementType | ✅ | 元素类型 |
| `position` | Position | ✅ | 元素位置 |
| `text` | string | ❌ | 文本内容 |
| `paragraphs` | Paragraph[] | ❌ | 段落列表 |
| `style` | Style | ❌ | 文本样式 |
| `image_base64` | string | ❌ | 图片 Base64 编码 |
| `image_format` | string | ❌ | 图片格式 (png/jpeg) |
| `image_description` | string | ❌ | 图片描述 |
| `table_data` | string[][] | ❌ | 表格数据 |
| `table_headers` | string[] | ❌ | 表头 |

### 2.6 教学语义 (TeachingContent)

```json
{
  "title": "同分母分数加法",
  "main_points": [
    "同分母分数相加，分母不变，分子相加",
    "例如：1/4 + 2/4 = 3/4"
  ],
  "knowledge_points": ["同分母分数加法规则"],
  "examples": ["1/4 + 2/4 = 3/4"],
  "has_images": true,
  "has_tables": false
}
```

### 2.7 幻灯片结构 (SlideData)

```json
{
  "slide_index": 0,
  "slide_type": "content_slide",
  "teaching_role": "concept",
  "elements": [...],
  "teaching_content": {...},
  "layout_width": 10.0,
  "layout_height": 5.625
}
```

### 2.8 文档结构 (DocumentData)

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_file": "分数加法.pptx",
  "total_slides": 5,
  "subject": null,
  "grade": null,
  "complex_elements_detected": false,
  "complex_element_slides": [],
  "slides": [...]
}
```

---

## 3. AI 处理阶段数据结构

### 3.1 合并动作类型 (MergeAction)

| 值 | 说明 |
|----|------|
| `keep` | 保留原页 |
| `merge` | 合并多页 |
| `create` | 创建新页 |
| `skip` | 跳过 |
| `polish` | 润色 |
| `expand` | 扩展 |
| `rewrite` | 改写 |
| `extract` | 提取知识点 |

### 3.2 幻灯片内容结构 (SlideContent)

```typescript
interface SlideContent {
  title: string
  main_points: string[]
  additional_content?: string
  elements?: ElementData[]

  // 教学增强字段
  teaching_notes?: string           // 教学笔记
  interaction_prompts?: string[]    // 互动提示
  exercise_questions?: ExerciseItem[] // 练习题
}
```

### 3.3 AI 返回格式约定

| action | 返回字段 | 内容结构 |
|--------|---------|---------|
| `polish` | `polished_content` | `{title, main_points, polished_elements}` |
| `expand` | `expanded_content` | `{title, original_points, expanded_points, new_examples}` |
| `rewrite` | `rewritten_content` | `{title, main_content, style_features}` |
| `extract` | `extracted_knowledge` | `{core_concepts, formulas, methods, common_mistakes}` |

### 3.4 content_snapshot 结构

**content_snapshot 是 AI 修改后的内容快照，用于最终生成 PPT**：

```json
// polish action
{
  "action": "polish",
  "polished_content": {
    "title": "润色后的标题",
    "main_points": ["要点1", "要点2"]
  }
}

// expand action
{
  "action": "expand",
  "expanded_content": {
    "title": "扩展后的标题",
    "original_points": ["原要点"],
    "expanded_points": ["扩展要点"],
    "new_examples": ["新例题"]
  }
}

// extract action
{
  "action": "extract",
  "extracted_knowledge": {
    "core_concepts": [{"concept": "名称", "definition": "定义"}],
    "formulas": [{"name": "公式名", "formula": "公式内容"}],
    "methods": [{"name": "方法名", "steps": ["步骤"]}]
  }
}
```

---

## 4. 渲染阶段数据结构

### 4.1 版本管理模型

#### SlideVersion

```json
{
  "version": "v1",
  "image_url": "/preview/slide_001_v1.png",
  "created_at": "14:30:25",
  "operation": "polish",
  "prompt": "润色这段文字",
  "source_pptx": "/uploads/original.pptx",
  "content_snapshot": {
    "action": "polish",
    "polished_content": {...}
  }
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | string | 版本号 (v1/v2/v3...) |
| `image_url` | string | 预览图 URL |
| `created_at` | string | 创建时间 (HH:MM:SS) |
| `operation` | string | 操作类型 |
| `prompt` | string | AI 操作提示语 |
| `source_pptx` | string | 源 PPTX 路径 |
| `content_snapshot` | object | AI 修改的内容快照 |

#### SlideState

```json
{
  "current_version": "v2",
  "status": "active",
  "versions": [
    {"version": "v1", ...},
    {"version": "v2", ...}
  ]
}
```

### 4.2 两种渲染路径

```python
# 路径1: 保留原页 - 从源 PPTX 复制
def _copy_slide_from_pptx(target_prs, source_pptx_path, slide_index):
    """复制源页面的所有形状到目标 PPT"""

# 路径2: AI 修改 - 从 content_snapshot 重建
def _add_slide_from_snapshot(target_prs, snapshot, font_size):
    """从 AI 返回的内容快照重建页面"""
```

---

## 5. 数据流转约定

### 5.1 必须保留的字段

| 阶段 | 必须保留字段 | 用途 |
|------|-------------|------|
| 解析 | `element_id`, `type`, `position` | 元素标识和布局重建 |
| 解析 | `text`, `paragraphs` | 文本内容 |
| 解析 | `image_base64`, `table_data` | 二进制内容 |
| AI | `action`, `new_content` | 处理指令和结果 |
| AI | `content_snapshot` | 版本历史和最终渲染 |

### 5.2 解析→AI→渲染数据流

```
输入: PPTX 文件
      ↓ PptContentParser.parse()
中间结构: DocumentData
      ↓ ContentMerger.merge_single_slide()
AI结果: SinglePageResult { action, new_content }
      ↓ 保存 content_snapshot 到 SlideVersion
渲染: PPTGenerator.generate_single_slide_pptx()
      ↓
输出: 新 PPTX 文件
```

---

## 6. AI 内容组合策略

### 6.1 覆盖规则

**可以覆盖**:
- 文本内容 (`text`, `main_points`)
- 标题文字 (`title`)
- 列表项 (`list_item`)

**必须保留**:
- 图片二进制数据 (`image_base64`)
- 表格结构 (`table_data`)
- 元素位置 (`position`)
- 复杂元素（图表、SmartArt等）

### 6.2 组合策略矩阵

| 场景 | 策略 | 优先级 |
|------|------|--------|
| 原页保留 | 直接复制 | 最高 |
| 文本润色 | 覆盖文本，保留样式 | 高 |
| 内容扩展 | 追加内容，调整布局 | 中 |
| 多页融合 | 合并内容，重建布局 | 中 |
| 创建新页 | 完全生成 | 低 |

---

## 7. python-pptx 解析能力

### 7.1 Shape 类型枚举 (MSO_SHAPE_TYPE)

```python
AUTO_SHAPE (1)      # 自动形状
FREEFORM (5)        # 自由形状
GROUP (6)           # 组合
PICTURE (13)        # 图片
PLACEHOLDER (14)    # 占位符
TEXT_BOX (17)       # 文本框
TABLE (19)          # 表格
CHART (3)           # 图表
DIAGRAM (21)        # SmartArt
```

### 7.2 解析能力矩阵

| 元素类型 | python-pptx 类型 | 解析能力 | 说明 |
|----------|------------------|----------|------|
| 文本框 | TEXT_BOX (17) | ✅ 完整 | 文本内容、字体样式、对齐方式 |
| 图片 | PICTURE (13) | ✅ 完整 | 图片数据（Base64）、位置、尺寸 |
| 表格 | TABLE (19) | ✅ 完整 | 行列数据、单元格内容 |
| 自动形状 | AUTO_SHAPE (1) | ✅ 部分 | 文本内容可提取，形状样式有限 |
| 自由形状 | FREEFORM (5) | ✅ 部分 | 文本内容可提取 |
| 占位符 | PLACEHOLDER (14) | ✅ 部分 | 文本内容可提取 |
| 组合 | GROUP (6) | ⚠️ 有限 | 可检测，但内部元素需递归解析 |
| 图表 | CHART (3) | ⚠️ 有限 | 可检测，但数据解析复杂 |
| SmartArt | DIAGRAM (21) | ⚠️ 有限 | 可检测，但内部结构不可解析 |
| 嵌入对象 | EMBEDDED_OLE_OBJECT (7) | ❌ 不支持 | 无法解析内容 |
| 音视频 | MEDIA (16) | ❌ 不支持 | 无法解析内容 |

### 7.3 复杂元素处理策略

当检测到以下元素类型时，标记为"复杂元素"，AI 无法进行内容级合并：

- `CHART` - 图表
- `DIAGRAM` - SmartArt
- `EMBEDDED_OLE_OBJECT` - 嵌入对象
- `MEDIA` - 音视频

**处理方式**：
1. 在 `complex_elements_detected` 字段标记
2. 在 `complex_element_slides` 记录页码
3. 提示用户这些页面只能整页保留

### 7.4 单位转换

```python
# EMU (English Metric Unit) 转换
inches = emu / 914400
points = emu / 12700
pixels = emu / 9525  # 假设 96 DPI
```

---

## 8. 完整 JSON 示例

### 8.1 解析结果示例

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_file": "分数加法.pptx",
  "total_slides": 3,
  "subject": "数学",
  "grade": "五年级",
  "complex_elements_detected": false,
  "complex_element_slides": [],
  "slides": [
    {
      "slide_index": 0,
      "slide_type": "title_slide",
      "teaching_role": "cover",
      "layout_width": 10.0,
      "layout_height": 5.625,
      "elements": [
        {
          "element_id": "elem_000",
          "type": "title",
          "position": {"x_pct": 10.0, "y_pct": 35.0, "width_pct": 80.0, "height_pct": 15.0},
          "text": "分数加法",
          "style": {"font_name": "微软雅黑", "font_size": 44.0, "bold": true}
        }
      ],
      "teaching_content": {
        "title": "分数加法",
        "main_points": [],
        "knowledge_points": [],
        "examples": [],
        "has_images": false,
        "has_tables": false
      }
    },
    {
      "slide_index": 1,
      "slide_type": "content_slide",
      "teaching_role": "concept",
      "elements": [
        {
          "element_id": "elem_001",
          "type": "title",
          "position": {"x_pct": 5.0, "y_pct": 5.0, "width_pct": 90.0, "height_pct": 10.0},
          "text": "同分母分数加法"
        },
        {
          "element_id": "elem_002",
          "type": "text_body",
          "position": {"x_pct": 5.0, "y_pct": 20.0, "width_pct": 90.0, "height_pct": 30.0},
          "text": "同分母分数相加，分母不变，分子相加。",
          "paragraphs": [
            {"text": "同分母分数相加，分母不变，分子相加。", "role": "definition"}
          ]
        }
      ],
      "teaching_content": {
        "title": "同分母分数加法",
        "main_points": ["同分母分数相加，分母不变，分子相加"],
        "knowledge_points": ["同分母分数加法规则"],
        "examples": [],
        "has_images": false,
        "has_tables": false
      }
    }
  ]
}
```

### 8.2 AI 处理结果示例

```json
{
  "action": "polish",
  "new_content": {
    "title": "同分母分数加法规则",
    "main_points": [
      "同分母分数相加时，分母保持不变",
      "只需将分子进行相加运算"
    ]
  },
  "success": true
}
```

### 8.3 版本管理示例

```json
{
  "session_id": "session_001",
  "documents": {
    "doc_001": {
      "source_file": "分数加法.pptx",
      "slides": {
        "0": {
          "current_version": "v2",
          "status": "active",
          "versions": [
            {
              "version": "v1",
              "image_url": "/preview/doc_001_0_v1.png",
              "created_at": "14:30:00",
              "operation": "original",
              "source_pptx": "/uploads/分数加法.pptx"
            },
            {
              "version": "v2",
              "image_url": "/preview/doc_001_0_v2.png",
              "created_at": "14:31:25",
              "operation": "polish",
              "prompt": "润色这段文字",
              "content_snapshot": {
                "action": "polish",
                "polished_content": {
                  "title": "同分母分数加法规则",
                  "main_points": ["同分母分数相加时，分母保持不变"]
                }
              }
            }
          ]
        }
      }
    }
  },
  "created_at": "2026-03-21T14:30:00",
  "last_updated": "2026-03-21T14:31:25"
}
```

---

## 9. 类型同步机制

### 9.1 自动生成 TypeScript 类型

后端使用 Pydantic 模型定义数据结构，通过 `backend/scripts/generate_types.py` 自动生成前端 TypeScript 类型。

**生成命令**：
```bash
cd frontend && pnpm generate:types
```

**输出文件**: `frontend/src/types/generated.ts`

### 9.2 类型映射规则

| Python 类型 | TypeScript 类型 |
|-------------|-----------------|
| `str` | `string` |
| `int` | `number` |
| `float` | `number` |
| `bool` | `boolean` |
| `Optional[T]` | `T \| null` |
| `List[T]` | `Array<T>` |
| `Dict[K, V]` | `Record<K, V>` |
| `Enum` | `type = 'value1' \| 'value2'` |

---

## 10. 关键文件路径

| 文件 | 用途 |
|------|------|
| `backend/app/models/ppt_structure.py` | 核心数据结构定义 (Pydantic) |
| `backend/app/services/ppt_content_parser.py` | PPT 解析入口 |
| `backend/app/services/content_merger.py` | AI 内容融合核心逻辑 |
| `backend/app/services/ppt_generator.py` | PPT 渲染核心 |
| `backend/scripts/generate_types.py` | TypeScript 类型生成脚本 |
| `frontend/src/types/generated.ts` | 自动生成的 TypeScript 类型 |

---

## 11. API 接口

### POST /api/v1/ppt/parse

解析上传的 PPTX 文件，返回结构化的幻灯片数据。

**请求**：
```
Content-Type: multipart/form-data

file: <PPTX 文件>
```

**响应**：
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

---

## 12. 验证方式

1. **解析验证**: 上传测试 PPTX，检查 DocumentData 结构完整性
2. **AI 处理验证**: 执行 polish/expand/rewrite/extract，验证 content_snapshot 格式
3. **渲染验证**: 从 content_snapshot 生成新 PPTX，对比原文件内容
4. **类型同步验证**: 运行 `pnpm generate:types` 后 `pnpm tsc --noEmit` 无错误

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-03-09 | 初始版本，支持文本、图片、表格解析 |
| 2.0 | 2026-03-21 | feat-246: 整合方案文档，添加 AI 处理和渲染阶段数据结构 |