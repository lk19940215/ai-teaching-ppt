# Claude Coding Agent Guide

## Project

AI Teaching PPT Generator: converts teaching materials (text/image/PDF) into interactive PPTX slides.

Stack:

* Frontend: Next.js 15 + TypeScript + Tailwind (`frontend/`)
* Backend: FastAPI + python-pptx + OOXML (`backend/`)
* DB: SQLite (history)

Pipeline:
input → LLM structured content → python-pptx PPTX → animation/interaction injection.

Important constraints:

* PPT generation MUST run in backend (python-pptx supports animations; frontend libraries do not).
* Long generation (60–180s) uses SSE progress streaming.
* API keys are stored in frontend localStorage (single-user desktop app).

---

## Repository Navigation

Explore in this order:

1. `glob` → understand structure
2. `grep` → locate symbols
3. read only necessary files

Key paths:

* Upload / generate page
  `frontend/src/app/upload/page.tsx`

* History UI
  `frontend/src/app/history/page.tsx`

* Settings
  `frontend/src/app/settings/page.tsx`

* Generate API
  `backend/app/api/v1/generate.py`

* Content generation
  `backend/app/services/content_generator.py`

* PPTX generation
  `backend/app/services/ppt_generator.py`

* Animation injection
  `backend/app/services/pptx_animator.py`

* History API
  `backend/app/api/v1/history.py`

* Canvas 预览组件
  `frontend/src/components/ppt-canvas-renderer.tsx`
  `frontend/src/components/ppt-canvas-preview.tsx`

* PPT 合并页面
  `frontend/src/app/merge/page.tsx`

* Canvas 文档
  `docs/canvas-preview.md`

---

## Development Commands

Backend:

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

Frontend:

cd frontend
pnpm install
pnpm dev

---

## Validation

After changes:

Frontend:
pnpm tsc --noEmit

Backend:
python -m py_compile app/main.py

Health check:

curl http://localhost:8000/health

E2E tests:

cd frontend
pnpm exec playwright test

---

## Editing Rules

* Make minimal changes.
* Avoid modifying unrelated files.
* Preserve architecture and API contracts.

Never modify:

* `requirements.md`
* `.claude-coder/playwright-auth.json`

UI language: Chinese.
Code comments: Chinese.

---

## Playwright MCP

Playwright MCP is configured.

Authentication requires:

--isolated
--storage-state

Both flags must be used together or localStorage will not load.

Config:
`.mcp.json`

Auth state:
`.claude-coder/playwright-auth.json`

---

## Execution Strategy

For non-trivial tasks:

1. explore repository
2. create a short plan
3. implement step-by-step
4. validate with type check / compile / tests

Minimize tool calls and avoid reading large files unless required.

---

## Testing Guidelines

### Playwright MCP Waiting Strategy (Multi-stage `browser_wait_for`)

For long-running tasks (SSE streaming, AI generation, file processing), use **multi-stage `browser_wait_for`** instead of single long timeout:

```json
{
  "steps": [
    "【环境】curl http://localhost:8000/health",
    "【P0】browser_navigate http://localhost:3000/merge",
    "【P0】browser_wait_for text='PPT 智能合并' timeout=10000",
    "【P0】browser_file_upload paths=['PPT *.pptx']",
    "【P0】browser_wait_for text='共 5 页' timeout=10000",
    "【P0】browser_file_upload paths=['PPT *.pptx']",
    "【P0】browser_wait_for text='共 5 页' timeout=10000",
    "【P0】browser_click ref=[合并按钮ref]",
    "【P0】browser_wait_for text='📚 正在解析 PPT 内容...' timeout=10000 (阶段1：解析)",
    "【P0】browser_wait_for text='🤖 正在调用 AI 生成合并策略...' timeout=60000 (阶段2：AI)",
    "【P0】browser_wait_for text='🔧 正在执行智能合并...' timeout=60000 (阶段3：合并)",
    "【P0】browser_wait_for text='✅ 合并完成！' timeout=60000 (阶段4：完成)",
    "【P0】browser_snapshot 验证下载链接"
  ]
}
```

**Rationale**:
- `browser_wait_for` has an internal 30s limit, but **multi-stage waiting works around this**
- Each stage has realistic timeout based on actual processing time
- Provides better visibility into where failures occur
- Aligns with SSE progress events (10% → 50% → 75% → 100%)

**Stage-specific timeouts**:
- File upload/parse: 10s
- LLM strategy generation: 60s (API call + response)
- PPT merging: 60s
- Final completion: 60s

**Total**: ~190s coverage vs single 180s timeout

---

## Troubleshooting

### Known Issues

**SSE Progress Stuck at 40%**:
- Symptom: Progress shows "正在连接生成服务..." and hangs
- Root cause: Backend uvicorn process blocked on async queue
- Fix: Restart backend service (`npx kill-port 8000` then restart uvicorn)

**browser_wait_for Timeouts Early**:
- Symptom: Set timeout=180000 but actual wait is ~30s
- Root cause: Playwright MCP internal 30s hard limit
- Workaround: Use multi-stage `browser_wait_for` as shown above
- Alternative: Use `browser_run_code` with custom polling logic

**Downloaded PPT Cannot Open**:
- Symptom: File downloads but PowerPoint shows "文件损坏"
- Root cause: Incorrect Content-Type or corrupted file write
- Fix: Use `fetch + blob` download method instead of direct link