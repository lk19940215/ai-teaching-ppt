# AI Teaching PPT Generator

## WHAT

AI 教学 PPT 生成器：教师输入教学内容（文字/图片/PDF），AI 自动生成交互式教学课件。

- **前端**: Next.js 15 + TypeScript + Tailwind CSS (`frontend/`)
- **后端**: FastAPI + python-pptx + OOXML (`backend/`)
- **数据库**: SQLite（历史记录）
- **核心流程**: 内容输入 → LLM 生成结构化教学内容 → python-pptx 生成 PPTX → 动画/交互注入

## WHY

- PPT 生成必须在后端（python-pptx + OOXML），因为前端库（PptxGenJS）不支持动画和交互
- 使用 SSE 推送生成进度，因为 LLM 生成耗时 60-180 秒
- API Key 存在前端 localStorage 而非后端，因为这是单用户桌面应用

## HOW

### 开发命令

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && pnpm install && pnpm dev

# 类型检查
cd frontend && pnpm tsc --noEmit

# 后端检查
cd backend && python -m py_compile app/main.py
```

### 测试

```bash
# Playwright E2E（需要前后端运行中）
cd frontend && pnpm exec playwright test

# 后端 API 健康检查
curl http://localhost:8000/health
```

### 关键路径

| 功能 | 前端文件 | 后端文件 |
|------|---------|---------|
| 上传/生成页 | `frontend/src/app/upload/page.tsx` | - |
| PPT 生成 API | - | `backend/app/api/v1/generate.py` |
| LLM 内容生成 | - | `backend/app/services/content_generator.py` |
| PPTX 文件生成 | - | `backend/app/services/ppt_generator.py` |
| 动画注入 | - | `backend/app/services/pptx_animator.py` |
| 历史记录 | `frontend/src/app/history/page.tsx` | `backend/app/api/v1/history.py` |
| 设置页 | `frontend/src/app/settings/page.tsx` | - |

### 规则

- 修改前端代码后运行 `pnpm tsc --noEmit` 检查类型
- 修改后端代码后运行 `python -m py_compile` 检查语法
- 不要修改 `requirements.md`（用户需求输入）
- 不要修改 `.claude-coder/playwright-auth.json`（测试凭证）
- 提交前确保 linter 无错误
- 中文用户界面，代码注释用中文
- 测试规则详见 `.claude/rules/testing.md`
- Token 预算控制详见 `.claude-coder/token-budget-rules.md`

### MCP 工具

- **Playwright MCP**: 已配置，使用 `--storage-state` 注入 API Key
- 配置文件: `.mcp.json`
- 认证状态: `.claude-coder/playwright-auth.json`
