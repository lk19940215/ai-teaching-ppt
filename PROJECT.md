# AI 教学 PPT 生成器 — 项目架构文档

> 本文件是项目的完整技术地图。任何 AI 或开发者读完本文档即可理解架构、代码组成、功能和交互。

---

## 一、项目概述

**目标**：上传 PPTX → 浏览器预览 → AI 润色/改写/扩展/提取 → 保留原始格式导出 PPTX

**核心原则**：**非破坏性原地修改** — AI 只修改文本内容，系统自动保留字体、颜色、动画、图片、布局等所有格式。

**技术栈**：
- 前端：Next.js 15 + React 18 + TailwindCSS + shadcn/ui + pnpm
- 后端：Python FastAPI + python-pptx + OpenAI 兼容 LLM
- 预览图：LibreOffice (headless) + PyMuPDF (PDF→PNG)
- 测试：Playwright MCP（浏览器自动化）

---

## 二、数据流架构

```
┌──────────────────────────────────────────────────────────────┐
│                       Frontend (Next.js :3000)               │
│                                                              │
│  上传PPTX → useMergePage → useMergeSession → API调用        │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │UploadStep│→ │ SlidePoolPanel│→ │ SlidePreviewPanel    │   │
│  │(选文件)  │  │ (44页缩略图) │  │ (大图+AI操作+版本)   │   │
│  └──────────┘  └──────────────┘  └──────────────────────┘   │
│                                   ↕                          │
│                         FinalSelectionBar (拖拽排序→生成PPT)  │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP (直连 :9501，绕过 Next 代理)
┌────────────────────────────▼─────────────────────────────────┐
│                     Backend (FastAPI :9501)                    │
│                                                              │
│  POST /upload → PPTXReader.parse → 生成预览图 → 返回JSON     │
│  POST /process → ContentExtractor → AIProcessor(LLM) →      │
│                  PPTXWriter.apply → 生成预览图 → 返回版本     │
│  POST /compose → PPTXWriter.compose → 生成预览图 → 返回版本  │
│  GET  /download → FileResponse                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 三、目录结构

```
ai-teaching-ppt/
├── PROJECT.md                    ← 本文件：项目架构全貌
├── README.md                     ← 项目简介和运行说明
├── requirements.md               ← 用户需求文档（只读）
├── .gitignore
│
├── docs/
│   ├── technical-spec.md         ← 技术规格：数据模型、API、模块边界
│   └── refactor-plan.md          ← 重构计划和执行状态
│
├── logs/                         ← 运行时会话日志（gitignored）
│
├── backend/                      ← Python 后端
│   ├── requirements.txt          ← Python 依赖
│   ├── Dockerfile                ← 容器构建
│   ├── .env                      ← 本地环境变量（API密钥等）
│   │
│   ├── app/
│   │   ├── main.py               ← FastAPI 入口：CORS、路由注册、静态文件挂载
│   │   ├── config.py             ← Settings：端口(9501)、路径、LLM默认值
│   │   │
│   │   ├── core/                 ← 核心 PPT 处理管道
│   │   │   ├── models.py         ← 四层数据模型（Pydantic）
│   │   │   ├── pptx_reader.py    ← PPTX → ParsedPresentation
│   │   │   ├── content_extractor.py ← ParsedPresentation → SlideContent（AI友好）
│   │   │   ├── pptx_writer.py    ← 修改指令 → 写回PPTX（Run级别保留格式）
│   │   │   └── session_logger.py ← 会话级文件日志
│   │   │
│   │   ├── ai/                   ← AI 处理层
│   │   │   ├── prompt_template.md ← AI协议文档（唯一的提示词模板）
│   │   │   ├── prompts.py        ← 加载模板 + 注入操作指导
│   │   │   ├── processor.py      ← AIProcessor：编排提取→LLM→解析
│   │   │   └── llm_client.py     ← OpenAI兼容LLM客户端
│   │   │
│   │   ├── api/                  ← HTTP 路由层
│   │   │   ├── routes.py         ← PPT路由：upload/process/compose/download
│   │   │   ├── schemas.py        ← 请求/响应 Pydantic 模型
│   │   │   └── config.py         ← LLM配置API（/api/v1/config）
│   │   │
│   │   ├── models/               ← 持久化层（SQLite）
│   │   │   ├── database.py       ← SQLAlchemy引擎和会话
│   │   │   ├── llm_config.py     ← LLM配置ORM模型
│   │   │   └── llm_config_crud.py ← LLM配置CRUD
│   │   │
│   │   └── services/
│   │       └── ppt_to_image.py   ← PPTX→PDF→PNG 预览图生成
│   │
│   └── tests/                    ← 测试脚本
│       ├── test_api_e2e.py       ← API端到端测试
│       ├── test_api_quick.py     ← 快速API测试
│       ├── test_roundtrip_quality.py ← 往返质量测试
│       ├── trace_full_pipeline.py   ← 8阶段管道追踪
│       └── verify_prompt.py      ← 提示词模板验证
│
├── frontend/                     ← Next.js 前端
│   ├── next.config.js            ← API代理、超时、body限制
│   ├── .env.local                ← NEXT_PUBLIC_API_URL=http://localhost:9501
│   ├── package.json              ← 依赖和脚本
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx        ← 根布局
│       │   ├── page.tsx          ← 首页
│       │   ├── merge/page.tsx    ← 合并页面（主功能入口）
│       │   └── settings/page.tsx ← LLM设置页面
│       │
│       ├── hooks/
│       │   ├── useMergeSession.ts ← 核心状态机：上传、AI处理、版本管理、组合
│       │   ├── useMergePage.ts    ← 页面级UI状态（步骤、错误、提示语）
│       │   └── use-pptx-fallback.ts ← 渲染降级策略
│       │
│       ├── components/merge/
│       │   ├── upload/           ← 上传区域组件
│       │   ├── panels/           ← 幻灯片池、预览、最终选择、监控面板
│       │   ├── controls/         ← 操作按钮、进度条、版本切换、步骤指示器
│       │   └── renderers/        ← 幻灯片渲染器（图片/Canvas/PptxViewJS）
│       │
│       ├── lib/
│       │   ├── api.ts            ← apiBaseUrl 和 URL 构建
│       │   ├── llmConfig.ts      ← LLM配置管理（localStorage + 后端默认）
│       │   └── version-api.ts    ← 版本历史API客户端
│       │
│       ├── types/
│       │   ├── merge-session.ts  ← 前端领域类型（SlidePoolItem、SlideVersion等）
│       │   ├── merge-plan.ts     ← 合并计划类型
│       │   └── generated.ts      ← 从后端Pydantic模型生成的类型
│       │
│       └── utils/
│           └── monitor.ts        ← 客户端请求/响应/性能监控
```

---

## 四、四层数据模型

```
层级1: ParsedPresentation        ← PPTX 完整结构
  └── ParsedSlide[]
       └── ParsedShape[]          ← shape_index 精确对应 slide.shapes[N]
            ├── text_content       ← 文本框内容（含Run级别格式）
            ├── table_data         ← 表格内容
            ├── element_type       ← TITLE/TEXT/TABLE/IMAGE/GROUP等
            └── has_animations     ← 动画标记

层级2: SlideContent               ← AI 友好的纯文本视图
  ├── text_blocks[]               ← TextBlock(shape_index, text, role)
  ├── table_blocks[]              ← TableBlock(shape_index, headers, rows)
  ├── has_animations/images/media ← 页面上下文
  └── layout_name, element_count  ← 版式信息

层级3: SlideModification          ← AI 返回的修改指令
  ├── text_modifications[]        ← TextModification(shape_index, new_text)
  ├── table_modifications[]       ← TableCellModification(shape_index, row, col, new_text)
  └── ai_summary                  ← AI 修改说明

层级4: PPTSession + PPTVersion    ← 会话和版本管理
  ├── session_id                  ← 会话标识
  ├── original_files              ← 原始PPTX路径
  ├── versions[]                  ← 每次操作生成一个版本
  └── current_version_id          ← 当前版本指针
```

---

## 五、API 端点

| 端点 | 方法 | 功能 | 关键参数 |
|------|------|------|----------|
| `/api/v1/ppt/upload` | POST | 上传1-2个PPTX，解析+预览 | `file_a`, `file_b`(可选) |
| `/api/v1/ppt/process` | POST | AI处理选定页面 | `session_id`, `slide_indices[]`, `action`, `provider`, `api_key` |
| `/api/v1/ppt/compose` | POST | 多PPT选页组合 | `session_id`, `selections[{source, slide_index}]` |
| `/api/v1/ppt/versions/{id}` | GET | 获取版本历史 | `session_id` |
| `/api/v1/ppt/download/{id}/{ver}` | GET | 下载指定版本 | `session_id`, `version_id` |
| `/api/v1/config/llm/default` | GET | 获取默认LLM配置 | — |
| `/health` | GET | 健康检查 | — |

**AI操作类型** (`action` 参数)：
- `polish` — 润色：优化文字表达
- `expand` — 扩展：补充细节和示例
- `rewrite` — 改写：换用不同表达
- `extract` — 提取：提取核心知识点

---

## 六、核心处理管道

```
PPTX文件
  │
  ├─ PPTXReader.parse()           → ParsedPresentation
  │   └─ 遍历 slide.shapes，记录 shape_index、类型、文本
  │
  ├─ ContentExtractor.extract()   → SlideContent
  │   └─ format_for_ai() 生成带标签的文本：
  │      【页面信息】版式=空白, 共6个元素, 含动画
  │      【标题】第三章 数据结构
  │      【正文·shape_2】学习目标：...
  │      【表格·shape_3】表头: ... | ...
  │
  ├─ AIProcessor.process_slide()
  │   ├─ build_prompt()           → 注入 prompt_template.md + action指导
  │   ├─ LLMClient.chat_json()    → 调用LLM，返回JSON
  │   └─ _parse_response()        → SlideModification
  │
  ├─ PPTXWriter.apply()           → 新PPTX文件
  │   └─ Run级别替换：保留 <a:rPr>，只修改 <a:t>
  │
  └─ ppt_to_image.convert()       → PNG预览图
      └─ LibreOffice → PDF → PyMuPDF → PNG
```

---

## 七、前端交互流程

```
Step 1: 上传
  ├─ 选择 PPT A + PPT B → 自动触发 initSession()
  ├─ 调用 POST /upload → 返回解析数据 + 预览图
  └─ 进入 Step 2

Step 2: 合并设置（三栏布局）
  ├─ 左栏: SlidePoolPanel — PPT A/B 所有页面缩略图
  │   ├─ 单击选择页面 → 中间预览
  │   └─ Ctrl+点击多选 → "融合选中页面"按钮
  │
  ├─ 中栏: SlidePreviewPanel — 大图 + AI操作
  │   ├─ 选择操作类型（润色/扩展/改写/提取）
  │   ├─ 点击"执行" → 调用 POST /process
  │   ├─ 版本切换（v1/v2/v3...）
  │   └─ "添加到最终选择"
  │
  └─ 右栏: 合并策略 + 最终PPT统计 + 使用说明

  底部: FinalSelectionBar — 拖拽排序已选页面

Step 3: 完成下载
  └─ 点击"生成最终PPT" → POST /compose → 下载链接
```

---

## 八、AI 提示词协议

**唯一入口**：`backend/app/ai/prompt_template.md`

**注入机制**：`prompts.py` 加载模板，将 `{{action_instruction}}` 替换为对应操作的指导文本。

**AI 输入格式**：
```
【页面信息】版式=标题幻灯片, 共14个元素, 含入场动画, 含图片
【正文·shape_11】In this unit, you will...
【表格·shape_3】
  表头: 名称 | 类型
  第1行: 数组 | 线性
```

**AI 输出格式**（JSON）：
```json
{
  "text_blocks": [{"shape_index": 11, "new_text": "..."}],
  "table_cells": [{"shape_index": 3, "row": 1, "col": 0, "new_text": "..."}],
  "summary": "修改说明"
}
```

**铁律**：
1. `shape_index` 只能使用输入中出现过的值
2. 只返回需要修改的元素
3. `new_text` 是纯文本，不含 HTML/Markdown

---

## 九、日志系统

**文件位置**：`logs/session_YYYYMMDD.log`

**日志内容**（每个会话）：
```
============================================================
[HH:MM:SS] [session_id] 新会话 - 上传 PPTX
============================================================
[HH:MM:SS] [session_id] ▶ parse (开始)
[HH:MM:SS] [session_id] ✓ parse (2.7s)
[HH:MM:SS] [session_id] ▶ preview
[HH:MM:SS] [session_id] ✓ preview (13.4s)

============================================================
[HH:MM:SS] [session_id] AI 处理 - polish
============================================================
[HH:MM:SS] [session_id] 📄 SYSTEM PROMPT
  （完整的prompt_template.md内容）
[HH:MM:SS] [session_id] 📄 USER INPUT
  （发送给AI的幻灯片文本）
[HH:MM:SS] [session_id] 📄 LLM OUTPUT
  （AI返回的JSON）
[HH:MM:SS] [session_id] ✓ llm_call (17.4s)
```

---

## 十、启动和运行

```bash
# 后端（端口 9501）
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 9501

# 前端（端口 3000）
cd frontend
pnpm install
pnpm dev

# 访问
http://localhost:3000/merge
```

**环境变量**：
- `backend/.env`：`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 等
- `frontend/.env.local`：`NEXT_PUBLIC_API_URL=http://localhost:9501`

**端口统一管理**：
- 后端端口在 `backend/app/config.py` 的 `BACKEND_PORT = 9501` 统一定义
- 前端通过 `next.config.js` 的 `BACKEND_PORT` 环境变量或默认值 `9501` 对齐

---

## 十一、关键技术点

| 技术点 | 说明 |
|--------|------|
| Run 级别文本替换 | 修改 `<a:t>` 保留 `<a:rPr>`，字体/颜色/粗斜体全部保留 |
| shape_index 源映射 | 每个 shape 有唯一索引，AI 输入输出通过此索引精确定位 |
| 组合文本只读 | Group 内嵌套的文本提取为 `group_readonly`，AI 可参考但不修改 |
| 页面上下文注入 | 向 AI 传递版式、元素数、动画/图片/媒体信息，指导生成策略 |
| 预览图即时生成 | 每次 AI 操作后立即生成新的 PNG 预览图 |
| 会话内存管理 | `_sessions` 字典存储，服务重启后丢失 |
| 直连模式 | 前端直连后端 :9501，绕过 Next.js 代理的 body 大小限制 |

---

## 十二、已知限制和改进方向

| 项目 | 当前状态 | 改进方向 |
|------|----------|----------|
| 会话持久化 | 内存字典 | SQLite/Redis 持久化 |
| 预览图生成 | 全量转换（每次22页） | 增量更新（只转换修改页） |
| LibreOffice 依赖 | 系统必须安装 | 添加健康检查和降级方案 |
| AI 内容融合 | 仅物理拷贝页面 | 使用 AI 融合多页内容为一页 |
| 前端渲染 | 静态 PNG 预览 | Canvas 直接渲染 OOXML |
