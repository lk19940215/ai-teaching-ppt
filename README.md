# AI 教学 PPT 生成器

教师上传教材内容（拍照 / PDF / 文字），AI 自动生成互动性强、美观的教学 PPT（.pptx），支持 WPS 二次编辑。

## 功能特点

- **多种输入方式**：拍照识别（OCR）、PDF 电子书解析、直接粘贴文字
- **智能内容生成**：AI 根据年级和学科自动调整内容深度和表达方式
- **年级自适应**：小学趣味化、初中体系化，字号配色自动适配
- **英语学科增强**：单词卡、语法图解、情景对话等专属页面类型
- **标准格式输出**：生成 .pptx 文件，WPS / PowerPoint 均可打开编辑
- **多 AI 模型**：支持 DeepSeek / OpenAI / Claude / 智谱 GLM 切换

## 技术栈

- **前端**：Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **后端**：Python FastAPI
- **OCR**：PaddleOCR
- **PPT 生成**：python-pptx
- **数据库**：SQLite

## 开发

本项目使用 [claude-auto-loop](https://github.com/lk19940215/claude-auto-loop) 辅助自动化开发。

**拉取 claude-auto-loop 最新代码：**
```bash
# macOS / Linux
bash claude-auto-loop/update.sh

# Windows (PowerShell / CMD)
claude-auto-loop\loop.bat update
```

### Windows 用户

Windows 用户通过 `loop.bat` 统一入口运行，无需手动配置 bash 环境：

```powershell
claude-auto-loop\loop.bat setup          # 首次配置模型
claude-auto-loop\loop.bat run "你的需求"  # 运行编码循环
claude-auto-loop\loop.bat update         # 更新工具
claude-auto-loop\loop.bat validate       # 校验
```

`loop.bat` 会自动找到 Git Bash 并调用对应的 `.sh` 脚本，所有参数原样透传。


### Cursor IDE 模式

在 Cursor 中新建对话，输入需求即可。Agent 会自动读取 `requirements.md` 和工作协议。

### CLI 模式

```bash
# macOS / Linux
bash claude-auto-loop/run.sh

# Windows (PowerShell / CMD)
claude-auto-loop\loop.bat run
```

详细用法见 `claude-auto-loop/README.md`。

## 项目结构

```
ai-teaching-ppt/
├── backend/          # Python FastAPI 后端
├── frontend/         # Next.js 前端
├── claude-auto-loop/ # 自动化开发工具
├── requirements.md   # 项目需求文档
└── README.md
```

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | 3.11+ | 后端服务 |
| Node.js | 20+ | 前端服务 |
| pnpm | latest | 前端包管理（init.sh 会自动安装） |
| Git | 2.x+ | 版本控制 |
| Docker | 可选 | 容器化部署 |

**Windows 用户：** 安装 [Git for Windows](https://git-scm.com/download/win) 即可，使用 `loop.bat` 运行（自动调用 Git Bash）。详见上方 [Windows 用户](#windows-用户)。

### 开发环境启动

1. **克隆项目**
   ```bash
   git clone <仓库地址>
   cd ai-teaching-ppt
   ```

2. **初始化环境**（由 Agent 自动执行，通常无需手动运行）

3. **启动后端服务**
   ```bash
   cd backend
   # macOS / Linux
   source ../.venv/bin/activate
   # Windows (PowerShell)
   ..\.venv\Scripts\activate
   
   uvicorn app.main:app --reload --port 8000
   ```

4. **启动前端服务**
   ```bash
   cd frontend
   pnpm dev
   ```

5. **访问应用**
   - 前端：http://localhost:3000
   - 后端 API 文档：http://localhost:8000/docs

### Docker 部署

```bash
# 使用 docker-compose 启动完整服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 停止服务
docker-compose down
```

### 项目开发

本项目使用 [claude-auto-loop](https://github.com/lk19940215/claude-auto-loop) 进行自动化开发。任务已分解到 `claude-auto-loop/tasks.json` 中，Agent 将按优先级逐步实现功能。

### 技术栈详情

- **后端**：FastAPI + SQLite + python-pptx + PaddleOCR + PyMuPDF
- **前端**：Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui
- **AI 集成**：支持 DeepSeek / OpenAI / Claude / 智谱 GLM
- **部署**：Docker 容器化，支持独立部署
