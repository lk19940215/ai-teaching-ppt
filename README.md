# AI 教学 PPT 智能合并工具

> **Built with [Claude Coder](https://github.com/lk19940215/claude-coder)** — 纯 AI Agent 驱动开发

将多个教学 PPT 智能合并，支持页面级润色、扩展、改写、知识点提取，生成可编辑的 .pptx 文件。

## 功能特点

- **PPT 智能合并**：上传两个 PPT，AI 分析内容后智能合并
- **单页处理**：润色、扩展、改写、知识点提取
- **多页融合**：合并多个页面内容为一张新幻灯片
- **Canvas 预览**：真实的 PPT 页面 Canvas 渲染
- **版本管理**：每个幻灯片支持多版本预览和切换
- **标准格式输出**：生成 .pptx 文件，WPS / PowerPoint 均可编辑
- **多 AI 模型**：支持 DeepSeek / OpenAI / Claude / 智谱 GLM

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 15 + TypeScript + Tailwind CSS |
| 后端 | Python FastAPI + SQLite |
| PPT 生成 | python-pptx + OOXML |
| Canvas 预览 | 原生 Canvas 2D + LRU 缓存 |
| 测试 | Playwright E2E |

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.11+ | 后端服务 |
| Node.js | 20+ | 前端服务 |
| pnpm | latest | 前端包管理 |

### 开发环境启动

```bash
git clone https://github.com/lk19940215/ai-teaching-ppt.git
cd ai-teaching-ppt

# 后端
cd backend && python -m venv ../.venv
# Windows
..\..venv\Scripts\activate
# Linux/macOS
source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd ../frontend && pnpm install && pnpm dev
```

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

## 使用指南

### 1. 配置 LLM

访问 `/settings` 页面，配置 AI 模型的 API Key：

- DeepSeek（推荐，性价比高）
- OpenAI
- Claude
- 智谱 GLM

### 2. 上传 PPT

访问 `/merge` 页面，上传两个 PPTX 文件。系统会自动解析并显示预览。

### 3. 处理幻灯片

选中幻灯片后可进行以下操作：

| 操作 | 说明 |
|---|---|
| 润色 | 优化文字表达，保持原意 |
| 扩展 | 补充更多细节和示例 |
| 改写 | 以不同风格重写内容 |
| 提取 | 提取知识点和关键信息 |

### 4. 合并页面

选中多个幻灯片后点击「合并」，AI 会智能融合内容为一张新幻灯片。

### 5. 生成最终 PPT

将处理好的幻灯片添加到最终选择栏，点击「生成最终 PPT」下载。

## Canvas 预览

Canvas 预览功能使用原生 Canvas 2D 渲染 PPT 页面：

| 元素 | 支持程度 |
|---|---|
| 文本 | ✅ 完全支持（字体、颜色、对齐） |
| 图片 | ✅ 完全支持 |
| 表格 | ✅ 完全支持 |
| 形状 | ✅ 支持 |

详细文档：[docs/canvas-preview.md](docs/canvas-preview.md)

## 项目结构

```
ai-teaching-ppt/
├── backend/
│   ├── app/api/          # API 路由
│   └── app/services/     # 业务逻辑
├── frontend/
│   ├── src/app/          # 页面路由
│   └── src/components/   # UI 组件
├── docs/                 # 技术文档
└── requirements.md       # 需求文档
```

## 文档

- [用户指南](docs/user-guide.md) - 详细使用教程
- [Canvas 预览功能](docs/canvas-preview.md) - Canvas 渲染技术文档
- [PPT 数据结构](docs/ppt-structure.md) - 中间数据结构定义

## License

MIT