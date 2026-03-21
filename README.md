# AI Teaching PPT

一个基于 Web 的 PPT 处理工具，支持 AI 润色/改写/扩展/提取，保留原始格式导出。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.x + FastAPI + uvicorn |
| 前端 | Next.js 15 + React 18 + TypeScript + Tailwind CSS |
| 数据库 | SQLite |
| AI | OpenAI 兼容 API (DeepSeek/GLM/Claude 等) |
| PPTX | python-pptx (读写) + PyMuPDF (预览) |

## 目录结构

```
ai-teaching-ppt/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── main.py         # 入口
│   │   ├── config.py       # 配置
│   │   ├── api/            # HTTP 接口
│   │   ├── core/           # PPTX 解析/写回
│   │   ├── ai/             # LLM 处理
│   │   └── models/         # 数据库模型
│   ├── requirements.txt
│   └── .env                # LLM 配置
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   ├── components/    # React 组件
│   │   └── hooks/         # 自定义 Hooks
│   └── package.json
├── docs/                   # 技术文档
│   ├── technical-spec.md  # 技术规范
│   └── refactor-plan.md   # 重构计划
└── .claude/               # Claude Code 配置
    └── CLAUDE.md          # 项目指令
```

## 快速开始

### 1. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 配置 LLM (编辑 .env)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 前端

```bash
cd frontend
pnpm install
pnpm dev
```

### 3. 访问

- 前端：http://localhost:3000
- 后端 API 文档：http://localhost:8000/docs

## 功能

- 上传 PPTX 文件，解析展示
- 选择页面进行 AI 处理（润色/改写/扩展/提取）
- 预览修改内容，确认后导出
- 保留原始格式（字体、颜色、动画）