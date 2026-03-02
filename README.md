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

### Cursor IDE 模式

在 Cursor 中新建对话，输入需求即可。Agent 会自动读取 `requirements.md` 和工作协议。

### CLI 模式

```bash
bash claude-auto-loop/run.sh
```

详细用法见 `claude-auto-loop/README.md`。

## 项目结构

```
ai-teaching-ppt/
├── backend/          # Python FastAPI 后端
├── frontend/         # Next.js 前端
├── claude-auto-loop/ # 自动化开发工具（不纳入版本控制）
├── requirements.md   # 项目需求文档
└── README.md
```
