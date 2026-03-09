# PPT AI 内容级合并 - 技术方案设计

## 1. 需求概述

### 1.1 核心场景
```
输入：PPT A（分数加法）+ PPT B（分数减法）
处理：AI 理解内容、融合知识点、生成新结构
输出：新 PPT（分数运算）
```

### 1.2 功能粒度
| 粒度 | 描述 | 示例 |
|------|------|------|
| 整体合并 | 两个 PPT 全部内容融合 | A + B → 完整新课件 |
| 多页融合 | 选中的几页融合 | A 第1页 + B 第2页 → 新页面 |
| 单页处理 | 单页内容润色/改写 | A 第1页 → 润色后的第1页 |

### 1.3 目标用户
- K-12 教师
- 课件特点：文本 + 图片 + 表格为主，SmartArt/图表较少

---

## 2. 数据结构设计

### 2.1 核心问题
**Q: 是直接使用 PPT 原始结构，还是生成新的中间结构？**

**决策：生成新的中间结构**

原因：
1. PPT 原始结构（OOXML）过于复杂，包含大量渲染细节
2. AI 只需要理解"语义内容"，不需要布局细节
3. 中间结构便于 AI 消费和修改

### 2.2 中间结构定义

```json
{
  "document_id": "uuid",
  "source_file": "分数加法.pptx",
  "metadata": {
    "total_slides": 5,
    "subject": "数学",
    "grade": "三年级"
  },
  "slides": [
    {
      "slide_index": 0,
      "slide_type": "title_slide",
      "teaching_role": "封面",
      "elements": [
        {
          "element_id": "elem_001",
          "type": "title",
          "content": "分数加法",
          "style": {
            "font_size": 44,
            "bold": true
          },
          "position": {
            "x_pct": 50,
            "y_pct": 40
          }
        },
        {
          "element_id": "elem_002",
          "type": "subtitle",
          "content": "三年级数学",
          "position": {
            "x_pct": 50,
            "y_pct": 60
          }
        }
      ],
      "teaching_content": {
        "title": "分数加法",
        "main_points": ["同分母分数加法", "异分母分数加法"],
        "has_examples": false
      }
    },
    {
      "slide_index": 1,
      "slide_type": "content_slide",
      "teaching_role": "概念讲解",
      "elements": [
        {
          "element_id": "elem_003",
          "type": "title",
          "content": "同分母分数加法"
        },
        {
          "element_id": "elem_004",
          "type": "text_body",
          "content": "同分母分数相加，分母不变，分子相加。\n例如：1/4 + 2/4 = 3/4",
          "content_type": "definition",
          "paragraphs": [
            {
              "text": "同分母分数相加，分母不变，分子相加。",
              "role": "定义"
            },
            {
              "text": "例如：1/4 + 2/4 = 3/4",
              "role": "例题"
            }
          ]
        },
        {
          "element_id": "elem_005",
          "type": "image",
          "source": "base64...",
          "description": "分数加法示意图",
          "position": {"x_pct": 70, "y_pct": 50}
        }
      ],
      "teaching_content": {
        "title": "同分母分数加法",
        "knowledge_points": ["同分母分数加法规则"],
        "examples": ["1/4 + 2/4 = 3/4"],
        "has_images": true
      }
    }
  ]
}
```

### 2.3 元素类型定义

| 类型 | 说明 | AI 可处理 |
|------|------|-----------|
| `title` | 标题 | ✅ 理解、改写 |
| `subtitle` | 副标题 | ✅ 理解、改写 |
| `text_body` | 正文文本 | ✅ 理解、改写、扩展 |
| `list_item` | 列表项 | ✅ 理解、合并 |
| `image` | 图片 | ✅ 保留、重新布局 |
| `table` | 表格 | ✅ 理解数据、重建 |
| `chart` | 图表 | ⚠️ 有限支持 |
| `smartart` | SmartArt | ❌ 整页保留 |

### 2.4 教学语义提取

AI 需要理解每页的"教学角色"：

```python
TEACHING_ROLES = {
    "title_slide": "封面页",
    "outline_slide": "目录页",
    "concept_slide": "概念讲解",
    "example_slide": "例题讲解",
    "exercise_slide": "练习题",
    "summary_slide": "总结页",
    "homework_slide": "作业页"
}
```

---

## 3. AI 融合策略

### 3.1 整体合并流程

```
Step 1: 解析 PPT A 和 B → 中间结构
        ↓
Step 2: AI 分析两份课件的教学结构
        - 知识点对比
        - 内容重叠度
        - 互补性分析
        ↓
Step 3: AI 生成融合方案
        {
          "merge_strategy": "知识点整合",
          "slide_plan": [
            {"action": "keep", "source": "A", "slide": 0, "reason": "封面保留"},
            {"action": "merge", "sources": ["A:1", "B:1"], "new_content": "..."},
            {"action": "create", "content": "综合练习"},
            {"action": "keep", "source": "B", "slide": 3}
          ]
        }
        ↓
Step 4: 用户可调整方案
        ↓
Step 5: 生成新 PPT
```

### 3.2 单页处理流程

```
用户选中 A 第2页
        ↓
展示当前内容 + AI 操作选项：
  - [润色文字]
  - [扩展内容]
  - [改写风格]
  - [提取知识点]
        ↓
用户选择 [扩展内容]
        ↓
AI 生成扩展版本 → 预览对比 → 用户确认
```

### 3.3 多页融合流程

```
用户选中 A 第1页 + B 第2页
        ↓
AI 分析两页内容关系
        ↓
AI 生成融合方案：
  - 内容合并方式
  - 顺序建议
  - 冲突处理
        ↓
用户确认 → 生成新页面
```

---

## 4. API 设计

### 4.1 PPT 解析 API

```
POST /api/v1/ppt/parse-structured

Request:
{
  "file": <binary>,
  "extract_images": true,
  "extract_teaching_semantic": true
}

Response:
{
  "document_id": "uuid",
  "slides": [...],  // 中间结构
  "metadata": {...}
}
```

### 4.2 PPT 转图片 API

```
POST /api/v1/ppt/convert-to-images

Request:
{
  "file": <binary>,
  "pages": [0, 1, 2],  // 可选，默认全部
  "resolution": "high"  // high/medium/low
}

Response:
{
  "images": [
    {"page": 0, "url": "/static/xxx_0.png", "width": 1920, "height": 1080},
    {"page": 1, "url": "/static/xxx_1.png", ...}
  ]
}
```

### 4.3 AI 融合 API

```
POST /api/v1/ppt/ai-merge

Request:
{
  "document_a_id": "uuid",
  "document_b_id": "uuid",
  "merge_type": "full",  // full / partial / single
  "selected_slides": {   // 仅 partial 时需要
    "a": [0, 1],
    "b": [2]
  },
  "custom_prompt": "合并为分数运算课件",
  "llm_config": {
    "provider": "deepseek",
    "api_key": "xxx"
  }
}

Response (SSE):
{
  "event": "analysis",
  "data": {"status": "正在分析 PPT A 的教学结构..."}
}
{
  "event": "merge_plan",
  "data": {
    "plan": {
      "slide_plan": [...],
      "summary": "将合并为5页课件..."
    }
  }
}
{
  "event": "complete",
  "data": {
    "document_id": "uuid",
    "download_url": "/api/v1/ppt/download/xxx"
  }
}
```

### 4.4 单页处理 API

```
POST /api/v1/ppt/ai-process-page

Request:
{
  "document_id": "uuid",
  "slide_index": 0,
  "action": "polish",  // polish / expand / rewrite / extract
  "custom_prompt": "用更通俗的语言解释"
}

Response:
{
  "new_content": {...},
  "preview_image": "/static/xxx_preview.png"
}
```

---

## 5. 版本化管理设计

### 5.1 设计理念

类似 Git 的版本管理思想：
- 每次操作生成新版本，不删除历史
- 用户可查看和恢复任意历史版本
- 最终合并时基于用户当前选择的版本

### 5.2 版本数据结构

```json
{
  "session_id": "uuid",
  "documents": {
    "ppt_a": {
      "source_file": "分数加法.pptx",
      "slides": {
        "0": {
          "current_version": "v1",
          "status": "active",
          "versions": [
            {
              "version": "v1",
              "image_url": "/static/a_0_v1.png",
              "created_at": "10:00:00",
              "operation": "原始上传"
            }
          ]
        },
        "1": {
          "current_version": "v2",
          "status": "active",
          "versions": [
            {
              "version": "v1",
              "image_url": "/static/a_1_v1.png",
              "created_at": "10:00:00",
              "operation": "原始上传"
            },
            {
              "version": "v2",
              "image_url": "/static/a_1_v2.png",
              "created_at": "10:05:00",
              "operation": "AI润色",
              "prompt": "用更通俗的语言解释"
            }
          ]
        },
        "2": {
          "current_version": null,
          "status": "deleted",
          "versions": [
            {
              "version": "v1",
              "image_url": "/static/a_2_v1.png",
              "created_at": "10:00:00",
              "operation": "原始上传"
            }
          ]
        }
      }
    },
    "ppt_b": { ... }
  }
}
```

### 5.3 版本操作 API

```
POST /api/v1/ppt/version/create

Request:
{
  "session_id": "uuid",
  "document_id": "ppt_a",
  "slide_index": 1,
  "operation": "ai_polish",
  "prompt": "润色这段文字",
  "llm_config": {...}
}

Response:
{
  "version": "v2",
  "image_url": "/static/a_1_v2.png",
  "created_at": "10:05:00"
}
```

```
POST /api/v1/ppt/version/restore

Request:
{
  "session_id": "uuid",
  "document_id": "ppt_a",
  "slide_index": 1,
  "target_version": "v1"
}

Response:
{
  "success": true,
  "current_version": "v1"
}
```

```
POST /api/v1/ppt/slide/toggle

Request:
{
  "session_id": "uuid",
  "document_id": "ppt_a",
  "slide_index": 2,
  "action": "delete"  // 或 "restore"
}

Response:
{
  "success": true,
  "status": "deleted"  // 或 "active"
}
```

### 5.4 版本化预览流程

```
用户上传 PPT
      ↓
创建 session，生成 v1 版本图片
      ↓
用户操作（润色/删除/合并）
      ↓
生成新版本图片，保留旧版本
      ↓
前端显示当前版本，可查看历史
      ↓
用户确认合并
      ↓
基于 current_version 生成最终 PPT
```

### 5.5 存储策略

| 数据类型 | 存储位置 | 生命周期 |
|----------|----------|----------|
| 版本图片 | `/static/versions/{session_id}/` | session 结束后 1 小时清理 |
| 版本元数据 | 内存 / Redis | session 期间 |
| 最终 PPT | `/static/generated/` | 永久（用户可下载） |

### 5.6 前端交互

```
┌─────────────────────────────────────────────────────────────┐
│  PPT A 预览                                                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                       │
│  │  1  │  │  2  │  │  3  │  │  4  │                       │
│  │ ✓   │  │ v2  │  │ ✗   │  │ ✓   │                       │
│  │     │  │ 2版 │  │     │  │     │                       │
│  └─────┘  └─────┘  └─────┘  └─────┘                       │
│                                                             │
│  点击第2页查看历史：                                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 第2页版本历史 (共2个版本)                            │   │
│  │ ┌─────────────────────────────────────────────────┐ │   │
│  │ │ ○ v1 原始上传 10:00               [查看] [选择] │ │   │
│  │ └─────────────────────────────────────────────────┘ │   │
│  │ ┌─────────────────────────────────────────────────┐ │   │
│  │ │ ● v2 AI润色   10:05  [当前]        [查看] [选择]│ │   │
│  │ │     提示语："用更通俗的语言解释"                  │ │   │
│  │ └─────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 5.7 合并生成

```
用户点击"生成新PPT"
      ↓
收集当前选择：
  - PPT A: slide 0(v1), slide 1(v2), slide 3(v1)
  - PPT B: slide 0(v1), slide 2(v1)
      ↓
后端基于选中版本组合：
  - 从 PPT A 源文件提取 slide 0
  - 从 PPT A v2 版本数据重建 slide 1
  - ...
      ↓
生成最终 PPT 文件
```

---

## 6. 前端交互设计

### 6.1 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  PPT 智能合并                                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ PPT A 上传  │  │ PPT B 上传  │                           │
│  │ [选择文件]  │  │ [选择文件]  │                           │
│  └─────────────┘  └─────────────┘                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐  ┌──────────────────────────┐ │
│  │ PPT A 预览               │  │ PPT B 预览               │ │
│  │ ┌───┐┌───┐┌───┐┌───┐    │  │ ┌───┐┌───┐┌───┐┌───┐    │ │
│  │ │ 1 ││ 2 ││ 3 ││ 4 │    │  │ │ 1 ││ 2 ││ 3 ││ 4 │    │ │
│  │ │ ✓ ││v2 ││ ✗ ││ ✓ │    │  │ │ ✓ ││ ✓ ││ ✗ ││ ✓ │    │ │
│  │ └───┘└───┘└───┘└───┘    │  │ └───┘└───┘└───┘└───┘    │ │
│  │                          │  │                          │ │
│  │ [选中] [AI处理] [删除]   │  │ [选中] [AI处理] [删除]   │ │
│  └──────────────────────────┘  └──────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  AI 融合区域                                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 融合方式：[整体合并] [选择页面融合] [单页处理]          │ │
│  │                                                        │ │
│  │ 提示语：[输入您的合并需求...]                          │ │
│  │                                                        │ │
│  │ [开始 AI 融合]                                         │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  融合结果预览                                                │
│  ┌───┐┌───┐┌───┐┌───┐┌───┐                               │
│  │ 1 ││ 2 ││ 3 ││ 4 ││ 5 │  [拖拽调整顺序]               │
│  └───┘└───┘└───┘└───┘└───┘                               │
│                                                            │
│  [重新生成] [下载 PPT]                                     │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 交互流程

```
1. 上传阶段
   - 拖拽或点击上传
   - 自动解析 + 生成预览图 (v1)
   - 显示加载进度

2. 预览阶段
   - 缩略图展示所有页面（带版本标记）
   - 点击查看大图
   - 点击版本标记查看历史版本
   - 多选页面（Ctrl+点击）

3. 操作阶段
   - 选中页面后显示操作按钮
   - 单页：润色/扩展/改写/删除
   - 多页：融合/对比
   - 全部：整体合并
   - 每次操作生成新版本

4. 版本管理
   - 点击页面版本标记
   - 查看历史版本列表
   - 选择/恢复任意版本
   - 恢复已删除页面

5. AI 处理阶段
   - SSE 进度反馈
   - 显示 AI 分析结果
   - 用户可调整，生成新版本

6. 输出阶段
   - 基于当前选择的版本预览
   - 拖拽调整顺序
   - 下载最终 PPT
```

---

## 6. 技术选型

### 6.1 渲染方案

| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| LibreOffice 转 PNG | 100% 还原 | 需安装 200MB | ✅ 采用 |
| Canvas 增强 | 轻量 | 还原度 60-70% | ❌ 不采用 |

### 6.2 解析方案

| 元素 | 解析方式 | 备注 |
|------|----------|------|
| 文本 | python-pptx 直接读取 | ✅ 完整支持 |
| 图片 | 提取为 Base64 | ✅ 完整支持 |
| 表格 | 读取单元格数据 | ✅ 完整支持 |
| SmartArt | 检测后整页标记 | ⚠️ 不做内容解析 |
| 图表 | 检测后整页标记 | ⚠️ 不做内容解析 |

### 6.3 复杂元素处理策略

```python
def detect_complex_elements(slide):
    """
    检测页面是否包含无法 AI 处理的复杂元素
    """
    complex_types = [MSO_SHAPE_TYPE.CHART, MSO_SHAPE_TYPE.DIAGRAM]
    for shape in slide.shapes:
        if shape.shape_type in complex_types:
            return True, shape.shape_type
    return False, None

# 处理策略
if has_complex_elements:
    # 方案 1: 整页保留
    # 方案 2: 提示用户选择
    # 方案 3: 转为图片（丢失编辑能力）
```

---

## 7. 待确认问题

### 7.1 数学公式处理
- 问题：PPT 中的数学公式通常以图片或 OLE 对象存在
- 方案：作为图片保留，不做内容解析
- 后续：可集成 OCR 识别公式

### 7.2 动画效果
- 问题：合并后动画效果如何处理？
- 方案：当前版本暂不支持动画合并，保留静态内容

### 7.3 母版/主题
- 问题：两个 PPT 使用不同主题，合并后如何统一？
- 方案：使用目标 PPT 的主题，或让用户选择

---

## 8. 实施计划

见 `tasks.json` 中的 feat-137 ~ feat-145