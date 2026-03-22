# AI 提示词组装流程

## 架构概览

```
用户操作（前端）
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    前端 ACTION_CONFIG                     │
│  merge-session.ts 中定义的操作模板                         │
│  作为 custom_prompt 发送到后端                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                后端 prompts.py → build_prompt()           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │         SYSTEM PROMPT（由模板 + 槽位组装）         │    │
│  │                                                 │    │
│  │  prompt_template.md                             │    │
│  │  ├── 数据映射说明                                │    │
│  │  ├── 输出 JSON 格式定义                          │    │
│  │  ├── 核心约束                                   │    │
│  │  ├── 输入格式说明                                │    │
│  │  ├── 输出示例                                   │    │
│  │  ├── {{domain_context}}   ← domains/*.md        │    │
│  │  ├── {{operation_guide}}  ← operations/*.md     │    │
│  │  └── {{custom_instructions}} ← 前端 template    │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │              USER MESSAGE                        │    │
│  │                                                 │    │
│  │  "**幻灯片内容**：\n{slide_text}\n\n"            │    │
│  │  + user_suffix（根据 action 不同而变化）           │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
                   LLM API
                       │
                       ▼
              JSON 响应 → 解析 → 应用修改
```

## 三层注入槽位

### 1. 领域预设（`{{domain_context}}`）

- 文件位置：`backend/app/ai/domains/*.md`
- 当前可用：
  - `_default.md` — 通用领域（保持原文语言、准确术语）
  - `english_teaching.md` — 英语教学（保留英文内容、音标、对话格式）
- 由前端 `subject` 参数指定，未指定时使用 `_default`

### 2. 操作指导（`{{operation_guide}}`）

- 文件位置：`backend/app/ai/operations/*.md`
- 当前可用操作：
  - `polish.md` — 润色：优化表达，保持原意
  - `expand.md` — 扩展：补充细节、示例、解释
  - `rewrite.md` — 改写：全新表达，句式/结构/视角变化
  - `extract.md` — 提取：提炼核心知识点
  - `fuse.md` — 融合：多页合并为新页面
- 每个操作包含：分析步骤、操作原则、具体策略、教学场景特化、注意事项

### 3. 用户补充要求（`{{custom_instructions}}`）

- 来源：前端 `ACTION_CONFIG.template` + 用户自定义输入
- 前端发送的 `custom_prompt` 会被注入到此槽位
- 默认模板定义在 `frontend/src/types/merge-session.ts` 的 `ACTION_CONFIG` 中

## User Message 中的 action-specific suffix

根据操作类型，user 消息末尾追加不同的指令：

| 操作 | user_suffix |
|------|-------------|
| fuse（融合） | 强制创建新页面，不修改已有页面，每个 body_texts 是独立板块 |
| rewrite/expand | **必须对每个文本框都返回 new_text**，确保修改有明显区别 |
| 其他（polish/extract） | 只返回需要修改的元素 |

## 核心约束的区分

`prompt_template.md` 中的核心约束根据操作类型有所区分：

- **润色/提取**：只返回需要修改的元素，未修改的不列出
- **改写/扩展**：必须对每个文本框都返回修改结果
- **通用约束**：shape_index 必须来自输入、纯文本输出、不修改只读内容

## 提示词调试指南

### 查看实际发送的提示词

后端日志中会记录完整的 SYSTEM PROMPT 和 USER INPUT：

```
[session_logger] SYSTEM PROMPT: ...
[session_logger] USER INPUT: ...
[session_logger] LLM OUTPUT: ...
```

### 添加新操作

1. 在 `backend/app/ai/operations/` 下创建 `{action_name}.md`
2. 在 `frontend/src/types/merge-session.ts` 的 `SlideAction` 类型中添加新操作
3. 在 `ACTION_CONFIG` 中添加对应的 label/icon/template
4. 如果需要特殊的 user_suffix，在 `prompts.py` 中添加分支

### 添加新领域

1. 在 `backend/app/ai/domains/` 下创建 `{domain_name}.md`
2. 在前端 `SUBJECT_OPTIONS` 中添加选项（`useMergePage.ts`）

## 文件清单

| 文件 | 作用 |
|------|------|
| `backend/app/ai/prompt_template.md` | 主模板（309行），定义 JSON Schema、约束、示例 |
| `backend/app/ai/prompts.py` | 提示词组装引擎，填充槽位，构建 messages |
| `backend/app/ai/operations/*.md` | 操作指导预设（5个） |
| `backend/app/ai/domains/*.md` | 领域规则预设（2个） |
| `frontend/src/types/merge-session.ts` | ACTION_CONFIG（前端模板） |
