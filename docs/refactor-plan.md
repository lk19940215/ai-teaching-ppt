# AI Teaching PPT — 重构实施文档

> 本文档定义代码重构的具体执行计划，包括新建、删除、改动的文件清单和实施顺序。
> 技术细节参见 [技术文档](./technical-spec.md)。

---

## 一、重构范围

### 1.1 目标

将当前分散的后端代码重构为清晰的三层管道架构：

```
core/ (解析 + 提取 + 写回)  →  ai/ (LLM 处理)  →  api/ (HTTP 接口)
```

### 1.2 前端

布局不变，仅调整 `useMergeSession.ts` 中的 API 调用以适配新后端。

---

## 二、新目录结构

```
backend/app/
├── main.py                     # 入口（改动：更新 router 导入）
├── config.py                   # 配置（保留）
│
├── core/                       # 【新建】核心 PPT 处理管道
│   ├── __init__.py
│   ├── models.py               # 统一数据模型
│   ├── pptx_reader.py          # PPTX 解析器
│   ├── pptx_writer.py          # PPTX 写回器
│   └── content_extractor.py    # 内容提取器
│
├── ai/                         # 【新建】AI 处理层
│   ├── __init__.py
│   ├── llm_client.py           # LLM 客户端
│   ├── processor.py            # AI 处理编排
│   └── prompts.py              # 提示词模板
│
├── api/                        # 【重写】HTTP 接口
│   ├── __init__.py
│   ├── routes.py               # 4 个核心端点
│   ├── schemas.py              # 请求/响应模型
│   └── config.py               # LLM 配置端点（保留）
│
├── services/                   # 【精简】辅助服务
│   └── ppt_to_image.py         # 保留
│
└── models/                     # 【保留】数据库
    ├── database.py
    ├── llm_config.py
    └── llm_config_crud.py
```

---

## 三、文件变更清单

### 3.1 新建文件（7 个）

| 文件 | 职责 | 依赖 |
|------|------|------|
| `core/__init__.py` | 模块导出 | - |
| `core/models.py` | 数据模型 (TextRun, Paragraph, SlideElement, ParsedPresentation, SlideContent, ProcessingResult 等) | pydantic |
| `core/pptx_reader.py` | 解析 PPTX → ParsedPresentation | python-pptx, core/models |
| `core/pptx_writer.py` | 修改指令 → 新 PPTX | python-pptx, core/models |
| `core/content_extractor.py` | ParsedPresentation → SlideContent | core/models |
| `ai/__init__.py` | 模块导出 | - |
| `ai/llm_client.py` | OpenAI 兼容 LLM 客户端 | openai SDK |
| `ai/processor.py` | AI 内容处理编排 | ai/llm_client, ai/prompts, core/models |
| `ai/prompts.py` | 提示词模板 | - |

### 3.2 重写文件（2 个）

| 文件 | 说明 |
|------|------|
| `api/routes.py` | 替代 `api/ppt.py`（1000+行 → ~300 行，4 个端点） |
| `api/schemas.py` | 新建，请求/响应 Pydantic 模型 |

### 3.3 改动文件（2 个）

| 文件 | 改动内容 |
|------|----------|
| `main.py` | 更新 router 导入路径 |
| `frontend/src/hooks/useMergeSession.ts` | API 调用适配新端点 |

### 3.4 保留不动的文件

| 文件 | 理由 |
|------|------|
| `config.py` | 路径配置仍需要 |
| `services/ppt_to_image.py` | 预览图生成逻辑独立可用 |
| `models/database.py` | SQLite 配置 |
| `models/llm_config.py` | LLM 配置 CRUD |
| `models/llm_config_crud.py` | LLM 配置 CRUD |
| `api/config.py` | LLM 配置 HTTP 端点 |

### 3.5 删除文件（16 个，约 12000+ 行）

| 文件 | 行数（约） | 删除理由 |
|------|-----------|----------|
| `services/ppt_generator.py` | 7000+ | 硬编码 PPT 布局，新方案不重建 PPT |
| `services/content_merger.py` | 1500+ | 被 ai/processor.py 替代 |
| `services/content_merger_utils.py` | 400+ | 辅助函数，不再需要 |
| `services/ppt_content_parser.py` | 600+ | 被 core/pptx_reader.py 替代 |
| `services/teaching_semantic_extractor.py` | 300+ | 教学语义分析，AI 直接处理即可 |
| `services/content_generator.py` | 200+ | 生成逻辑，不再需要 |
| `services/content_quality_evaluator.py` | 200+ | 质量评估，不再需要 |
| `services/version_manager.py` | 200+ | 版本管理，简化为内存缓存 |
| `services/attention_optimizer.py` | 150+ | 注意力优化，不再需要 |
| `services/pptx_animator.py` | 200+ | 动画编排，原地修改保留原动画 |
| `services/pptx_interactive.py` | 200+ | 互动触发器，不再需要 |
| `services/ppt_enhancer/enhancer.py` | 300+ | 增强器，不再需要 |
| `services/ppt_enhancer/layout_engine.py` | 400+ | 布局引擎，不再需要 |
| `services/ppt_enhancer/template_manager.py` | 300+ | 模板管理，不再需要 |
| `services/ppt_enhancer/theme_manager.py` | 300+ | 主题管理，不再需要 |
| `services/ppt_enhancer/animation_orchestrator.py` | 300+ | 动画编排，不再需要 |
| `services/prompts/merge_prompts.py` | 500+ | 被 ai/prompts.py 替代 |
| `api/ppt.py` | 1000+ | 被 api/routes.py 替代 |
| `models/ppt_structure.py` | 340+ | 被 core/models.py 替代 |

---

## 四、可复用代码

从旧文件中提取复用的逻辑：

| 来源 | 复用内容 | 目标 |
|------|----------|------|
| `services/llm.py` | `_extract_json_from_response()`, `_fix_json()` | `ai/llm_client.py` |
| `services/llm.py` | Provider 默认配置、Timeout 设置 | `ai/llm_client.py` |
| `services/ppt_content_parser.py` | `_is_placeholder_text()` 占位符文本列表 | `core/pptx_reader.py` |
| `services/ppt_content_parser.py` | `_compress_image()` 图片压缩逻辑 | `core/pptx_reader.py` |
| `services/ppt_content_parser.py` | `_extract_style()` 样式提取逻辑 | `core/pptx_reader.py` |

---

## 五、实施顺序

### Phase 1：核心管道

**目标**：用一个真实 PPTX 文件跑通「解析 → 提取 → 手动修改 → 写回」

| 步骤 | 文件 | 产出 |
|------|------|------|
| 1.1 | `core/models.py` | 全部数据模型定义 |
| 1.2 | `core/pptx_reader.py` | 解析任意 PPTX → ParsedPresentation |
| 1.3 | `core/content_extractor.py` | 提取 AI 友好文本 |
| 1.4 | `core/pptx_writer.py` | Run 级别写回 |
| 1.5 | 手动测试脚本 | 验证管道完整性 |

### Phase 2：AI 处理层

**目标**：接入 LLM，跑通「解析 → AI 润色 → 写回」

| 步骤 | 文件 | 产出 |
|------|------|------|
| 2.1 | `ai/llm_client.py` | LLM 调用 + JSON 解析 |
| 2.2 | `ai/prompts.py` | 4 种 action 的提示词 |
| 2.3 | `ai/processor.py` | AI 处理编排 |

### Phase 3：API 层

**目标**：HTTP 端点可用，Swagger 可测

| 步骤 | 文件 | 产出 |
|------|------|------|
| 3.1 | `api/schemas.py` | 请求/响应模型 |
| 3.2 | `api/routes.py` | 4 个端点实现 |
| 3.3 | `main.py` | 更新路由注册 |

### Phase 4：前端适配

**目标**：Web 界面端到端可用

| 步骤 | 文件 | 产出 |
|------|------|------|
| 4.1 | `useMergeSession.ts` | API 调用适配 |
| 4.2 | 端到端测试 | 上传 → 预览 → AI 处理 → 下载 |

### Phase 5：清理

**目标**：删除旧代码，更新依赖

| 步骤 | 操作 |
|------|------|
| 5.1 | 按 §3.5 清单删除旧文件 |
| 5.2 | 从 requirements.txt 移除 jieba |
| 5.3 | 更新 README.md |

---

## 六、验收标准

### Phase 1 完成标准（已完成 2026-03-21）
- [x] 任意 PPTX 文件可被解析为 ParsedPresentation JSON
- [x] ParsedPresentation 包含所有文本、表格、图片元素
- [x] 手动构造 TextModification 可成功写回新 PPTX
- [x] 写回后的 PPTX 用 PowerPoint/WPS 打开，格式与原文件一致
- [x] 真实 PPT（test_大龙猫.pptx）解析验证通过：2页、文本+表格+图片

### Phase 2 完成标准（代码已完成 2026-03-21）
- [x] LLM 客户端支持 deepseek/openai/claude/glm/自定义 Provider
- [x] 4 种 action 提示词模板就绪（polish/expand/rewrite/extract）
- [x] ProcessingResult 中的 shape_index 与原始内容正确映射
- [ ] 端到端 AI 调用验证（待接入真实 API Key 测试）

### Phase 3 完成标准（已完成 2026-03-21）
- [x] Swagger UI 可访问 6 个端点（upload/process/compose/versions/download/session）
- [x] POST /upload 可上传 PPTX 并返回解析结果 + 预览图
- [x] POST /process 可调用 AI 处理并立即生成新版本 PPTX
- [x] POST /compose 可从多 PPT 选页组合新 PPT
- [x] GET /versions 可获取版本历史
- [x] GET /download 可下载指定版本或最新版本
- [x] API 端到端测试通过（上传→解析→预览→版本→下载）

### Phase 4 完成标准（进行中）
- [ ] 前端 useMergeSession.ts 对接新 API 端点
- [ ] Web 界面上传 PPTX 后显示预览图 + 幻灯片列表
- [ ] 选择页面并执行 AI 润色后版本历史更新
- [ ] 可下载任意版本的 PPTX
- [ ] Playwright 浏览器端到端测试通过

### Phase 5 完成标准（进行中）
- [ ] 旧文件全部删除（~20 个文件，12000+ 行）
- [ ] api/config.py 迁移至新 LLM 客户端
- [ ] 无孤立导入/未使用的依赖
- [ ] 后端启动无报错
- [ ] 前端构建无报错

### Phase 6 完成标准 — 提示词架构重构（已完成 2026-03-22）
- [x] prompt_template.md 重写为通用 PPT 协议（非教学专用）
- [x] 多槽位注入架构：{{domain_context}} + {{operation_guide}} + {{custom_instructions}}
- [x] 领域预设目录 ai/domains/：_default.md + english_teaching.md
- [x] 操作预设目录 ai/operations/：polish.md / expand.md / rewrite.md / extract.md
- [x] 输出 Schema 扩展：style_hints (可选) + animation_hints (可选)
- [x] 可插拔插件：StyleApplicator (样式应用) + AnimationApplicator (动画应用)
- [x] PPTXWriter 集成插件，支持样式写入
- [x] API 层支持 domain 参数传递
- [x] 基于 LLM 注意力研究优化 prompt 布局（U形注意力 → TOP/BOTTOM 放关键约束）
- [x] 15 项自动化测试通过，0 linter 错误
- [x] PROJECT.md / technical-spec.md / refactor-plan.md 文档同步更新
