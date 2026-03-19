# PPT 中间数据结构文档

## 概述

本文档描述 PPTX 文件解析后生成的中间数据结构，供 AI 内容融合引擎消费。

## 设计原则

1. **语义优先**：提取对 AI 有意义的内容，忽略渲染细节
2. **类型明确**：每种元素有明确的类型标识
3. **位置信息**：保留元素的相对位置，便于重建布局
4. **教学语义**：识别页面在教学场景中的角色

---

## python-pptx 原始解析能力

### 实测验证结果

基于 `uploads/generated/晋升答辩_大龙猫.pptx` 文件的实测结果：

#### 文件信息
- 总页数：22
- 幻灯片尺寸：10.0 x 5.6 英寸

#### 解析统计

| 元素类型 | 数量 | 说明 |
|----------|------|------|
| shape | 14 | 自动形状、自由形状、占位符等 |
| text_body | 55 | 正文文本 |
| title | 8 | 标题文本 |
| image | 12 | 图片 |
| table | 3 | 表格 |
| subtitle | 1 | 副标题 |
| list_item | 15 | 列表项 |

#### 可解析的原始属性

##### Shape 类型枚举 (MSO_SHAPE_TYPE)

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

##### Shape 属性

```python
shape.left          # 左边距 (EMU)
shape.top           # 上边距 (EMU)
shape.width         # 宽度 (EMU)
shape.height        # 高度 (EMU)
shape.shape_type    # 类型枚举
shape.name          # 形状名称
```

##### 文本属性

```python
shape.text_frame.text           # 完整文本
shape.text_frame.paragraphs     # 段落列表
para.text                       # 段落文本
para.alignment                  # 对齐方式 (LEFT, CENTER, RIGHT, DISTRIBUTE)

# 字体属性
run.font.name                   # 字体名称
run.font.size                   # 字体大小 (Pt)
run.font.bold                   # 是否粗体
run.font.italic                 # 是否斜体
run.font.underline              # 是否下划线
run.font.color.rgb              # 字体颜色 (RGBColor)
```

##### 图片属性

```python
shape.image.blob                # 图片二进制数据
shape.image.ext                 # 图片格式 (png, jpeg, etc.)
shape.image.content_type        # MIME 类型
```

##### 表格属性

```python
shape.table.rows                # 行集合
shape.table.columns             # 列集合
cell.text                       # 单元格文本
```

##### 幻灯片属性

```python
prs.slide_width                 # 幻灯片宽度 (EMU)
prs.slide_height                # 幻灯片高度 (EMU)
slide.shapes                    # 形状集合
```

#### 单位转换

```python
# EMU (English Metric Unit) 转换
inches = emu / 914400
points = emu / 12700
pixels = emu / 9525  # 假设 96 DPI
```

---

## 中间数据结构定义

### python-pptx 解析能力验证

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

### 复杂元素处理策略

当检测到以下元素类型时，标记为"复杂元素"，AI 无法进行内容级合并：

- `CHART` - 图表
- `DIAGRAM` - SmartArt
- `EMBEDDED_OLE_OBJECT` - 嵌入对象
- `MEDIA` - 音视频

**处理方式**：
1. 在 `complex_elements_detected` 字段标记
2. 在 `complex_element_slides` 记录页码
3. 提示用户这些页面只能整页保留

---

## 中间数据结构定义

### 顶层结构

```json
{
  "document_id": "uuid",
  "source_file": "教学PPT.pptx",
  "total_slides": 10,
  "subject": null,
  "grade": null,
  "complex_elements_detected": false,
  "complex_element_slides": [],
  "slides": [...]
}
```

### 幻灯片结构 (SlideData)

```json
{
  "slide_index": 0,
  "slide_type": "title_slide",
  "teaching_role": "cover",
  "layout_width": 10.0,
  "layout_height": 5.625,
  "elements": [...],
  "teaching_content": {...}
}
```

#### slide_type 枚举

| 值 | 说明 |
|----|------|
| `title_slide` | 封面页 |
| `outline_slide` | 目录页 |
| `content_slide` | 内容页 |
| `section_slide` | 章节页 |
| `end_slide` | 结束页 |

#### teaching_role 枚举

| 值 | 说明 |
|----|------|
| `cover` | 封面 |
| `outline` | 目录 |
| `concept` | 概念讲解 |
| `example` | 例题讲解 |
| `exercise` | 练习 |
| `summary` | 总结 |
| `homework` | 作业 |

### 元素结构 (ElementData)

#### 文本元素

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
  "paragraphs": [
    {
      "text": "分数加法",
      "style": {
        "font_name": "微软雅黑",
        "font_size": 44.0,
        "bold": true,
        "color": "#000000"
      }
    }
  ],
  "style": {
    "font_name": "微软雅黑",
    "font_size": 44.0,
    "bold": true
  }
}
```

#### 图片元素

```json
{
  "element_id": "elem_002",
  "type": "image",
  "position": {
    "x_pct": 60.0,
    "y_pct": 30.0,
    "width_pct": 35.0,
    "height_pct": 50.0
  },
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
  "image_format": "png"
}
```

#### 表格元素

```json
{
  "element_id": "elem_003",
  "type": "table",
  "position": {
    "x_pct": 10.0,
    "y_pct": 40.0,
    "width_pct": 80.0,
    "height_pct": 40.0
  },
  "table_data": [
    ["分数", "小数", "百分数"],
    ["1/2", "0.5", "50%"],
    ["1/4", "0.25", "25%"]
  ],
  "table_headers": ["分数", "小数", "百分数"]
}
```

### 位置信息 (Position)

所有位置信息使用**百分比**表示，相对于幻灯片尺寸：

```json
{
  "x_pct": 10.5,      // 左边距百分比
  "y_pct": 5.2,       // 上边距百分比
  "width_pct": 79.0,  // 宽度百分比
  "height_pct": 15.0  // 高度百分比
}
```

**优点**：
- 不依赖具体像素值
- 便于在不同尺寸下重建布局
- AI 更容易理解相对位置

### 样式信息 (Style)

```json
{
  "font_name": "微软雅黑",
  "font_size": 24.0,
  "bold": true,
  "italic": false,
  "underline": false,
  "color": "#FF0000"
}
```

### 教学语义 (TeachingContent)

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

---

## API 接口

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

## 使用示例

### Python 调用

```python
from pathlib import Path
from backend.app.services.ppt_content_parser import parse_pptx_to_structure

# 解析 PPT
result = parse_pptx_to_structure(Path("教学PPT.pptx"))

# 获取第一页内容
slide_0 = result["slides"][0]
print(f"页面类型: {slide_0['slide_type']}")
print(f"教学角色: {slide_0['teaching_role']}")
print(f"元素数量: {len(slide_0['elements'])}")

# 遍历元素
for elem in slide_0["elements"]:
    if elem["type"] == "title":
        print(f"标题: {elem['text']}")
    elif elem["type"] == "image":
        print(f"图片: {elem['image_format']}")
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-03-09 | 初始版本，支持文本、图片、表格解析 |