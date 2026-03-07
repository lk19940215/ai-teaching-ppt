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
