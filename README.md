# AI 教学 PPT 生成器

> **Built with [Claude Coder](https://github.com/lk19940215/claude-coder)** — 18 个功能，3 天，由 AI Agent 自主完成 15 个。

教师上传教材内容（拍照 / PDF / 文字），AI 自动生成互动性强、美观的教学 PPT（.pptx），支持 WPS 二次编辑。

## 功能特点

- **多种输入方式**：拍照识别（OCR）、PDF 电子书解析、直接粘贴文字
- **智能内容生成**：AI 根据年级和学科自动调整内容深度和表达方式
- **年级自适应**：小学趣味化、初中体系化，字号配色自动适配
- **英语学科增强**：单词卡、语法图解、情景对话等专属页面类型
- **标准格式输出**：生成 .pptx 文件，WPS / PowerPoint 均可打开编辑
- **多 AI 模型**：支持 DeepSeek / OpenAI / Claude / 智谱 GLM 切换
- **Docker 部署**：前后端容器化，一键启动

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui |
| 后端 | Python FastAPI + SQLite |
| OCR | PaddleOCR |
| PPT 生成 | python-pptx + OOXML |
| 测试 | Playwright E2E |
| 部署 | Docker + docker-compose |

## 开发方式：Claude Coder 自动编码

本项目使用 [Claude Coder](https://github.com/lk19940215/claude-coder)（`npm install -g claude-coder`）进行自主编码开发。

```bash
# 安装
npm install -g @anthropic-ai/claude-agent-sdk
npm install -g claude-coder

# 配置模型
claude-coder setup

# 自动编码（从 requirements.md 驱动）
claude-coder run

# 查看进度
claude-coder status
```

**开发数据**：

| 指标 | 数值 |
|---|---|
| 开发时间 | 3 天（2026.03.02 ~ 03.04） |
| 总功能数 | 18 |
| AI 完成 | 15（83%） |
| 源代码 | 5,729 行（Python 3,700 + TypeScript 2,029） |
| Git commits | 47 |
| E2E 测试 | Playwright 13 用例，10 通过 |

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.11+ | 后端服务 |
| Node.js | 20+ | 前端服务 |
| pnpm | latest | 前端包管理 |
| Git | 2.x+ | 版本控制 |
| Docker | 可选 | 容器化部署 |

### 开发环境启动

```bash
git clone https://github.com/lk19940215/ai-teaching-ppt.git
cd ai-teaching-ppt

# 后端
cd backend && python -m venv ../.venv && source ../.venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd ../frontend && pnpm install && pnpm dev
```

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

### Docker 部署

```bash
docker-compose up -d
```

## 项目结构

```
ai-teaching-ppt/
├── backend/           # Python FastAPI 后端
│   ├── app/
│   │   ├── api/       # API 路由
│   │   ├── services/  # 业务逻辑（OCR、PPT生成、LLM）
│   │   └── models/    # 数据模型
├── frontend/          # Next.js 14 前端
│   ├── app/           # 页面路由
│   └── components/    # UI 组件
├── tests/             # Playwright E2E 测试
├── .claude-coder/     # Claude Coder 运行时数据
└── requirements.md    # 需求文档
```

## License

MIT
