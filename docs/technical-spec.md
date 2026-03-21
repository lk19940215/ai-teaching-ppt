# AI Teaching PPT — 技术文档

> 本文档定义项目的核心技术选型、数据模型设计和模块接口规范。
> 作为开发的技术参考手册。

---

## 一、项目定位

一个基于 Web 的 PPT 处理工具：用户上传 PPTX 文件，系统解析内容在浏览器中展示，
用户选择页面进行 AI 润色/改写/扩展/提取，最终导出保留原始格式的 PPTX 文件。

---

## 二、技术栈

### 2.1 后端

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.104.1 | 异步支持、自动 OpenAPI 文档 |
| 数据验证 | Pydantic | 2.5.0 | 类型安全的数据模型 |
| PPTX 读写 | python-pptx | 0.6.23 | 核心依赖，读写 OOXML 格式 |
| LLM 调用 | openai SDK | >=2.24.0 | OpenAI 兼容协议，覆盖多家模型 |
| 图片处理 | Pillow | latest | 图片压缩、格式转换 |
| PDF 渲染 | PyMuPDF | 1.23.8 | PDF 转 PNG（预览图生成） |
| JSON 修复 | json5 | >=0.9.0 | 宽松 JSON 解析，修复 LLM 输出 |
| 异步文件 | aiofiles | 23.2.1 | 异步文件读写 |

### 2.2 前端

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Next.js | 15.x | App Router、SSR/CSR 混合 |
| 语言 | TypeScript | - | 类型安全 |
| 样式 | Tailwind CSS | - | 实用优先 CSS |
| 拖拽 | @dnd-kit | - | 页面排序交互 |
| UI 基础 | Radix UI + shadcn | - | 无障碍组件 |

### 2.3 辅助工具

| 工具 | 用途 |
|------|------|
| LibreOffice (headless) | PPTX → PDF 转换（预览图生成，可选） |
| SQLite | LLM 配置持久化 |

---

## 三、PPTX 文件格式原理

### 3.1 文件结构

PPTX 是 ZIP 压缩包，内部为 OOXML (Office Open XML) 格式：

```
example.pptx (ZIP)
├── [Content_Types].xml
├── _rels/.rels
├── ppt/
│   ├── presentation.xml          # 演示文稿主文件
│   ├── slides/
│   │   ├── slide1.xml            # 第1页内容
│   │   ├── slide2.xml            # 第2页内容
│   │   └── ...
│   ├── slideLayouts/             # 版式定义
│   ├── slideMasters/             # 母版定义
│   ├── theme/                    # 主题（颜色、字体方案）
│   ├── media/                    # 嵌入的图片、音视频
│   └── noteSlides/               # 备注页
└── docProps/                     # 文档属性
```

### 3.2 Slide XML 结构

每页幻灯片的核心结构：

```xml
<p:sld>
  <p:cSld>
    <p:spTree>                          <!-- Shape Tree: 所有形状的容器 -->
      <p:sp>                            <!-- Shape: 一个形状 -->
        <p:nvSpPr>                      <!-- 非可视属性（名称、ID） -->
        <p:spPr>                        <!-- 形状属性（位置、大小、填充） -->
          <a:xfrm>
            <a:off x="457200" y="274638"/>    <!-- 位置 (EMU) -->
            <a:ext cx="8229600" cy="1143000"/><!-- 大小 (EMU) -->
          </a:xfrm>
        </p:spPr>
        <p:txBody>                      <!-- 文本框 -->
          <a:p>                         <!-- 段落 -->
            <a:pPr algn="ctr"/>         <!-- 段落属性（对齐） -->
            <a:r>                       <!-- Run: 最小文本单元 -->
              <a:rPr lang="zh-CN" sz="2800" b="1">  <!-- Run 属性（格式） -->
                <a:solidFill>
                  <a:srgbClr val="FF0000"/>          <!-- 颜色 -->
                </a:solidFill>
              </a:rPr>
              <a:t>这是标题文字</a:t>                 <!-- 实际文本 -->
            </a:r>
            <a:r>                       <!-- 同一段落的另一个 Run（不同格式） -->
              <a:rPr lang="zh-CN" sz="2400"/>
              <a:t>这是副标题</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>
```

### 3.3 关键概念

**EMU (English Metric Units)**：OOXML 使用的长度单位。
- 1 英寸 = 914400 EMU
- 1 厘米 = 360000 EMU
- 1 点 (pt) = 12700 EMU

**Run**：文本的最小格式化单元。一个段落可包含多个 Run，每个 Run 有独立的字体、颜色、大小等属性。

**Shape Index**：每页幻灯片的 `spTree` 中的 Shape 按顺序排列，索引从 0 开始。python-pptx 通过 `slide.shapes[index]` 访问。

### 3.4 原地修改的技术基础

python-pptx 的 `run.text = "新文字"` 只修改 XML 中 `<a:t>` 节点的内容，
`<a:rPr>`（格式属性）节点完全不动。

这意味着：
- 字体名称、大小 → 保留
- 颜色（RGB/主题色） → 保留
- 粗体、斜体、下划线 → 保留
- 位置、大小 → 保留（属于 Shape 级别，不受文本修改影响）
- 动画 → 保留（绑定在 Shape 上，不受文本修改影响）
- 超链接 → 需要注意，替换整个 Run 文本时超链接绑定可能丢失

---

## 四、核心数据模型

### 4.1 模型层次关系

```
第一层: PPTX 解析模型          ← 完整表示 PPTX 结构，用于前端显示 + 写回定位
  │
  ↓ ContentExtractor 提取
  │
第二层: AI 友好内容模型         ← 纯文本 + 源映射，给 LLM 消费
  │
  ↓ AIProcessor 处理
  │
第三层: 修改指令模型            ← 精确描述改什么、改成什么，给 Writer 执行
```

### 4.2 第一层：PPTX 解析模型

```python
class TextRun(BaseModel):
    """文本 Run — python-pptx 中的最小文本单元"""
    text: str
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    font_size: Optional[float] = None       # pt
    font_color: Optional[str] = None        # "#RRGGBB" 或 "theme_accent1"
    font_name: Optional[str] = None


class Paragraph(BaseModel):
    """段落"""
    runs: list[TextRun] = []
    alignment: Optional[str] = None         # left / center / right / justify
    level: int = 0                          # 缩进级别 (0-8)
    line_spacing: Optional[float] = None    # 行距倍数


class Position(BaseModel):
    """元素位置（EMU 原始值）"""
    left: int
    top: int
    width: int
    height: int


class TableCell(BaseModel):
    """表格单元格"""
    text: str
    paragraphs: list[Paragraph] = []
    row_span: int = 1
    col_span: int = 1


class ElementType(str, Enum):
    TEXT_BOX = "text_box"
    TABLE = "table"
    IMAGE = "image"
    PLACEHOLDER = "placeholder"
    SHAPE = "shape"
    GROUP = "group"
    CHART = "chart"
    MEDIA = "media"


class SlideElement(BaseModel):
    """幻灯片元素（对应 PPTX 的一个 Shape）
    
    shape_index 是写回定位的关键字段：
    PPTXWriter 通过 slide.shapes[shape_index] 找到原始 Shape 进行修改
    """
    shape_index: int                        # slide.shapes 中的索引
    element_type: ElementType
    position: Position
    name: Optional[str] = None              # Shape 名称

    # 文本内容
    paragraphs: list[Paragraph] = []
    plain_text: Optional[str] = None        # 纯文本拼接

    # 表格内容
    table_data: Optional[list[list[TableCell]]] = None
    table_rows: int = 0
    table_cols: int = 0

    # 图片内容
    image_base64: Optional[str] = None      # 缩略图（前端预览）
    image_format: Optional[str] = None

    # 语义标记
    is_title: bool = False
    is_placeholder: bool = False
    placeholder_type: Optional[str] = None
    has_hyperlink: bool = False


class ParsedSlide(BaseModel):
    """解析后的单页幻灯片"""
    slide_index: int
    elements: list[SlideElement] = []
    layout_name: Optional[str] = None
    has_notes: bool = False
    notes_text: Optional[str] = None
    has_animations: bool = False
    has_media: bool = False


class ParsedPresentation(BaseModel):
    """解析后的完整演示文稿"""
    filename: str
    slide_count: int
    slide_width: int                        # EMU
    slide_height: int                       # EMU
    slides: list[ParsedSlide] = []
    title: Optional[str] = None
```

### 4.3 第二层：AI 友好内容模型

```python
class TextBlock(BaseModel):
    """可被 AI 处理的文本块"""
    shape_index: int                    # 回溯到 SlideElement
    role: str                           # title / body / subtitle / note
    text: str


class TableBlock(BaseModel):
    """可被 AI 处理的表格"""
    shape_index: int
    headers: list[str] = []
    rows: list[list[str]] = []


class SlideContent(BaseModel):
    """单页的 AI 可处理内容"""
    slide_index: int
    title: Optional[str] = None
    text_blocks: list[TextBlock] = []
    table_blocks: list[TableBlock] = []
    has_images: bool = False
    has_media: bool = False
```

### 4.4 第三层：修改指令模型

```python
class TextModification(BaseModel):
    """文本修改指令"""
    shape_index: int
    original_text: str                  # 校验用
    new_text: str


class TableCellModification(BaseModel):
    """表格单元格修改指令"""
    shape_index: int
    row: int
    col: int
    original_text: str
    new_text: str


class SlideModification(BaseModel):
    """单页修改"""
    slide_index: int
    text_modifications: list[TextModification] = []
    table_modifications: list[TableCellModification] = []
    ai_summary: Optional[str] = None


class ProcessingResult(BaseModel):
    """AI 处理结果"""
    success: bool
    modifications: list[SlideModification] = []
    action: str
    total_changes: int = 0
    error: Optional[str] = None
```

### 4.5 第四层：版本管理与会话模型

```python
class SlideSelector(BaseModel):
    """页面选择器（用于组合新 PPT）"""
    source: str                     # "ppt_a" / "ppt_b" / "latest"
    slide_index: int

class PPTVersion(BaseModel):
    """一次 AI 操作或组合产生的版本"""
    version_id: str
    version_number: int
    created_at: str
    action: str                     # polish / expand / rewrite / extract / compose
    description: str
    output_path: str                # 生成的 PPTX 文件路径
    slide_selection: list[SlideSelector] = []
    modifications: list[SlideModification] = []
    preview_images: list[str] = []
    source_version_id: Optional[str] = None

class PPTSession(BaseModel):
    """完整的 PPT 处理会话"""
    session_id: str
    created_at: str
    original_files: dict[str, str] = {}    # {"ppt_a": "path", "ppt_b": "path"}
    parsed: dict = {}                       # {"ppt_a": ParsedPresentation, ...}
    versions: list[PPTVersion] = []
    current_version_id: Optional[str] = None
```

---

## 五、模块接口规范

### 5.1 PPTXReader

```python
class PPTXReader:
    def __init__(self, max_image_size: int = 512): ...
    def parse(self, file_path: Path) -> ParsedPresentation: ...
```

输入：PPTX 文件路径
输出：`ParsedPresentation`（完整的结构化表示）

解析规则：
- 过滤模板占位符文本（"单击此处添加标题" 等）
- 图片提取为 base64 缩略图（限制 max_image_size）
- 表格保留单元格级别数据
- 位置使用 EMU 原始值（不转换为百分比）
- 检测但不分析动画/音视频（标记 has_animations / has_media）

### 5.2 ContentExtractor

```python
class ContentExtractor:
    def extract_slide(self, slide: ParsedSlide) -> SlideContent: ...
    def extract_all(self, presentation: ParsedPresentation) -> list[SlideContent]: ...
```

输入：`ParsedSlide` 或 `ParsedPresentation`
输出：`SlideContent` 列表（纯文本 + 源映射）

提取规则：
- 自动识别标题元素（`is_title=True` 的 Shape）
- 文本 Run 拼接为纯文本
- 表格提取表头 + 数据行
- 通过 `shape_index` 保持与原始 Shape 的映射

### 5.3 AIProcessor

```python
class AIProcessor:
    def __init__(self, llm_client: LLMClient): ...
    async def process_slide(
        self, content: SlideContent, action: str,
        custom_prompt: Optional[str] = None
    ) -> ProcessingResult: ...
```

输入：`SlideContent` + 操作类型
输出：`ProcessingResult`（含修改指令列表）

支持的 action：
- `polish`：润色文字表达
- `expand`：扩展内容（用户在前端预览后决定是否采用）
- `rewrite`：改写风格
- `extract`：提取知识点

AI 输出格式要求（JSON）：
```json
{
  "text_blocks": [
    {"shape_index": 0, "new_text": "修改后的文字"}
  ],
  "table_cells": [
    {"shape_index": 1, "row": 0, "col": 1, "new_text": "修改后的单元格"}
  ],
  "summary": "修改说明"
}
```

### 5.4 PPTXWriter

```python
class PPTXWriter:
    def apply(
        self, source_path: Path,
        modifications: list[SlideModification],
        output_dir: Path
    ) -> Path: ...
```

输入：原始 PPTX 路径 + 修改指令
输出：新 PPTX 文件路径

写入策略：
- 打开原始 PPTX（Presentation 对象）
- 通过 `shape_index` 定位目标 Shape
- Run 级别文本替换：替换第一个 Run 文本，清空后续 Run
- 表格单元格：同样使用 Run 级别替换
- 校验：检查 `original_text` 是否匹配，不匹配则跳过（安全机制）
- 保存为新文件，不覆盖原始

### 5.5 LLMClient

```python
class LLMClient:
    def __init__(self, provider, api_key, base_url=None, model=None,
                 temperature=0.3, max_tokens=3000, timeout=300): ...
    def chat(self, messages: list[dict], **kwargs) -> str: ...
    def chat_json(self, messages: list[dict], **kwargs) -> dict: ...
```

支持的 Provider：
- `deepseek` → https://api.deepseek.com, deepseek-chat
- `openai` → https://api.openai.com/v1, gpt-4
- `claude` → https://api.anthropic.com/v1, claude-3-opus
- `glm` → https://open.bigmodel.cn/api/paas/v4, glm-4
- 自定义 → 必须提供 base_url

---

## 六、API 接口规范

### 6.1 POST /api/v1/ppt/upload

上传 1-2 个 PPTX 文件，解析并创建会话。

**请求**：`multipart/form-data`
- `file_a`: PPTX 文件（必填）
- `file_b`: PPTX 文件（可选，用于多 PPT 融合场景）

**响应**：
```json
{
  "session_id": "18efdea3a647",
  "parsed": {
    "ppt_a": { "filename": "...", "slide_count": 5, "slides": [...] },
    "ppt_b": { "filename": "...", "slide_count": 3, "slides": [...] }
  },
  "preview_images": [
    {"slide_index": 0, "url": "/public/previews/.../slide_0.png", "source": "ppt_a"},
    {"slide_index": 1, "url": "/public/previews/.../slide_1.png", "source": "ppt_a"}
  ]
}
```

### 6.2 POST /api/v1/ppt/process

AI 处理选定页面，立即写回生成新版本 PPTX。

**请求**：`application/json`
```json
{
  "session_id": "18efdea3a647",
  "slide_indices": [0, 2],
  "action": "polish",
  "custom_prompt": null,
  "provider": "deepseek",
  "api_key": "sk-xxx",
  "base_url": null,
  "model": null,
  "temperature": 0.3,
  "max_tokens": 3000
}
```

**响应**：
```json
{
  "success": true,
  "version": {
    "version_id": "a1b2c3d4",
    "version_number": 1,
    "action": "polish",
    "description": "润色了2页内容",
    "preview_images": ["/public/previews/.../slide_0.png"]
  },
  "result": {
    "success": true,
    "modifications": [...],
    "action": "polish",
    "total_changes": 3
  }
}
```

### 6.3 POST /api/v1/ppt/compose

从多个 PPT 选择页面组合新 PPT。

**请求**：`application/json`
```json
{
  "session_id": "18efdea3a647",
  "selections": [
    {"source": "ppt_a", "slide_index": 0},
    {"source": "ppt_b", "slide_index": 2},
    {"source": "ppt_a", "slide_index": 1}
  ]
}
```

**响应**：
```json
{
  "success": true,
  "version": {
    "version_id": "e5f6g7h8",
    "version_number": 2,
    "action": "compose",
    "description": "从 3 页组合"
  }
}
```

### 6.4 GET /api/v1/ppt/versions/{session_id}

获取版本历史。

**响应**：
```json
{
  "session_id": "18efdea3a647",
  "versions": [
    {"version_id": "a1b2c3d4", "version_number": 1, "action": "polish", "description": "..."},
    {"version_id": "e5f6g7h8", "version_number": 2, "action": "compose", "description": "..."}
  ],
  "current_version_id": "e5f6g7h8"
}
```

### 6.5 GET /api/v1/ppt/download/{session_id}/{version_id}

下载指定版本的 PPTX 文件。

**响应**：`application/vnd.openxmlformats-officedocument.presentationml.presentation`

### 6.6 GET /api/v1/ppt/download/{session_id}

下载最新版本（若无版本则下载原始文件）。

### 6.7 GET /api/v1/ppt/session/{session_id}

获取完整会话信息（含解析数据、版本列表等）。

---

## 七、数据流总览

```
用户上传 1-2 个 .pptx
    │
    ▼
┌───────────────────────────────────────────────────┐
│  POST /ppt/upload                                 │
│  1. 保存文件到 uploads/{session_id}/              │
│  2. PPTXReader.parse() → ParsedPresentation       │
│  3. LibreOffice → PDF → PyMuPDF → 预览图 PNG     │
│  4. 创建 PPTSession（内存缓存）                   │
│  5. 返回 parsed + preview_images                  │
└───────────────────────────────────────────────────┘
    │
    ▼
前端显示预览图 + 解析内容
用户选择页面 + 操作类型（polish/expand/rewrite/extract）
    │
    ├──── AI 处理路线 ────────────────┐
    ▼                                 │
┌───────────────────────────────────┐ │
│  POST /ppt/process                │ │
│  1. 重新解析最新版本 PPTX         │ │
│  2. ContentExtractor → 文本       │ │
│  3. AIProcessor → 修改指令        │ │
│  4. PPTXWriter.apply() → 新 PPTX  │ │
│  5. 创建 PPTVersion（立即可下载） │ │
│  6. 生成新预览图                   │ │
└───────────────────────────────────┘ │
    │                                 │
    ├──── 页面组合路线 ───────────────┘
    ▼
┌───────────────────────────────────┐
│  POST /ppt/compose                │
│  1. 从多个源 PPTX 选页            │
│  2. PPTXWriter.compose() → 新 PPT │
│  3. 创建 PPTVersion               │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│  GET /ppt/versions/{session_id}   │
│  查看版本历史，每个版本可下载     │
└───────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────┐
│  GET /ppt/download/{id}/{ver}     │
│  下载指定版本的 PPTX 文件          │
└───────────────────────────────────┘
```

---

## 八、PPTXWriter 核心算法：Run 级别文本替换

```python
def _replace_text_preserve_format(self, shape, new_text: str):
    """
    策略：将新文本按段落分配到已有段落中，
    在每个段落内替换第一个 Run 的文本、清空后续 Run。
    所有格式属性来自原始 Run，不做修改。
    """
    tf = shape.text_frame
    new_paragraphs = new_text.split("\n")
    old_paragraphs = list(tf.paragraphs)

    for i, new_para_text in enumerate(new_paragraphs):
        if i < len(old_paragraphs):
            para = old_paragraphs[i]
            runs = list(para.runs)
            if runs:
                runs[0].text = new_para_text
                for run in runs[1:]:
                    run.text = ""
            else:
                para.text = new_para_text
        else:
            new_para = tf.add_paragraph()
            new_para.text = new_para_text
            if old_paragraphs:
                self._copy_paragraph_format(old_paragraphs[-1], new_para)

    for i in range(len(new_paragraphs), len(old_paragraphs)):
        for run in old_paragraphs[i].runs:
            run.text = ""
```

**为什么不直接 `shape.text_frame.text = new_text`**：
- 这会删除所有 Run，创建一个新的默认格式 Run
- 所有字体、颜色、大小信息全部丢失
- Run 级别替换只改 `<a:t>` 内容，`<a:rPr>` 格式节点完全不动

---

## 九、错误处理与降级

| 场景 | 处理方式 |
|------|----------|
| LLM 返回非法 JSON | 多级修复：正则提取 → json.loads → _fix_json → json5 |
| shape_index 不匹配 | 校验 original_text，不匹配时跳过该修改 |
| LibreOffice 不可用 | 跳过预览图生成，前端用 canvas 渲染 |
| PPTX 格式损坏 | 返回明确错误信息，不做静默处理 |
| 超链接丢失 | 已知限制：Run 级别替换可能影响超链接绑定，文档中标注 |
