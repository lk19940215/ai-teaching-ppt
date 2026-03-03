# Claude Auto Loop — 架构概述

> 本文件面向 AI Agent 和开发者，用于快速理解本工具的设计、文件结构和扩展方式。
> 修改工具前请先阅读本文件。

## 定位

一个 **通用的 Claude Code 自动编码 harness**。它将 Claude Code CLI 包装为一个循环引擎：自动扫描项目 → 拆解任务 → 逐个实现 → 校验 → 推送，无需人工干预（可在暂停点确认）。

核心特征：
- **项目无关**：所有项目信息由 Agent 扫描后存入 `project_profile.json`，工具本身不含任何项目特定逻辑
- **可恢复**：通过 `progress.txt` 跨会话记忆，任意 session 可断点续跑
- **可观测**：通过 PreToolUse hook 实时显示 Agent 当前步骤和最近工具调用

## 整体架构

```mermaid
flowchart TB
    subgraph Harness["run.sh (Harness 主控)"]
        direction TB
        scan["run_scan()<br/>首次扫描"]
        coding["run_coding_session()<br/>编码循环"]
        validate["validate.sh<br/>校验"]
        indicator["start_thinking_indicator()<br/>每15秒轮询状态文件"]
    end

    subgraph Claude["Claude Code CLI"]
        agent["Agent<br/>(遵循 CLAUDE.md 协议)"]
        hook_sys["Hooks 系统<br/>PreToolUse 事件"]
    end

    subgraph Files["文件系统"]
        direction TB
        profile["project_profile.json<br/>init.sh<br/>tasks.json"]
        runtime["session_result.json<br/>progress.txt"]
        phase[".phase / .phase_step<br/>.activity_log"]
    end

    subgraph Hook["hooks/phase-signal.py"]
        infer["步骤推断<br/>1~6步"]
        activity["活动日志<br/>工具摘要"]
    end

    scan -->|"--append-system-prompt-file<br/>CLAUDE.md + SCAN_PROTOCOL.md"| agent
    coding -->|"--append-system-prompt-file<br/>CLAUDE.md"| agent
    coding -->|"--settings<br/>hooks-settings.json"| hook_sys

    agent -->|生成| profile
    agent -->|写入| runtime

    hook_sys -->|"stdin JSON<br/>{tool_name, tool_input}"| Hook
    infer -->|写入| phase
    activity -->|追加| phase

    indicator -->|"读取"| phase
    indicator -->|"终端输出"| terminal["终端显示<br/>[INFO] AI 编码中 · 步骤4 · Edit src/app.tsx"]

    validate -->|读取| runtime
    validate -->|"pass → 下一session<br/>fail → rollback"| coding
```

## 执行流程（首次运行 vs 后续运行）

```mermaid
flowchart LR
    start([bash run.sh]) --> check{profile<br/>存在?}

    check -->|否| req["读取<br/>requirements.md"]
    req --> scan["run_scan()"]
    scan --> profile_out["生成<br/>profile + init.sh + tasks.json"]
    profile_out --> loop

    check -->|是| loop

    loop["编码循环"] --> session["run_coding_session(N)"]
    session --> val["validate.sh"]
    val -->|pass| push["git push"]
    push --> done_check{所有任务<br/>done?}
    done_check -->|否| pause_check{每N个session<br/>暂停?}
    pause_check -->|继续| session
    done_check -->|是| finish([完成])

    val -->|fail| rollback["git reset --hard"]
    rollback --> retry_check{连续失败<br/>≥3次?}
    retry_check -->|否| session
    retry_check -->|是| mark_failed["标记 task failed"]
    mark_failed --> session
```

## Hook 数据流（每次工具调用）

```mermaid
sequenceDiagram
    participant CC as Claude Code
    participant Hook as phase-signal.py
    participant FS as 文件系统
    participant Ind as run.sh indicator

    CC->>Hook: PreToolUse stdin JSON<br/>{tool_name: "Edit", tool_input: {path: "src/app.tsx"}, cwd: "/project"}

    Hook->>Hook: _extract_summary()<br/>→ "src/app.tsx"
    Hook->>FS: 追加 .activity_log<br/>"16:05:01|Edit|src/app.tsx"

    Hook->>Hook: 步骤推断<br/>Edit + /src/ → "4-增量实现"
    Hook->>FS: 写入 .phase_step<br/>"4-增量实现"
    Hook->>FS: 写入 .phase<br/>"coding"

    Note over CC,Hook: async=true, 不阻塞 Agent

    loop 每 15 秒
        Ind->>FS: 读取 .phase, .phase_step, .activity_log
        Ind->>Ind: 拼接输出
        Ind-->>Ind: [INFO] AI 编码中 · 步骤4-增量实现 · Edit src/app.tsx 16:05:01
    end
```

## Agent 6 步工作流（单个 Session 内部）

```mermaid
flowchart TB
    s1["Step 1: 恢复上下文<br/>读取 progress.txt + tasks.json + profile"]
    s2["Step 2: 环境检查<br/>运行 init.sh + 健康检查"]
    s3["Step 3: 选择任务<br/>优先 failed → 其次 pending"]
    s4["Step 4: 增量实现<br/>按 steps 逐步编码"]
    s5["Step 5: 测试验证<br/>curl / Playwright / 选择性回归"]
    s6["Step 6: 收尾<br/>git commit + progress.txt + session_result.json"]

    s1 --> s2 --> s3 --> s4 --> s5 --> s6

    s5 -->|测试通过| done["status → done"]
    s5 -->|测试失败| failed["status → failed"]
    done --> s6
    failed --> s6
```

## 任务状态机

```mermaid
stateDiagram-v2
    [*] --> pending
    pending --> in_progress: 开始工作
    in_progress --> testing: 代码写完
    testing --> done: 测试通过
    testing --> failed: 测试失败
    failed --> in_progress: 重试修复
```

## 文件清单

### 工具核心（随 upstream 分发，update.sh 会覆盖）

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | Agent 协议：铁律、6 步流程、状态机、文件权限（注入为 system prompt） |
| `SCAN_PROTOCOL.md` | 首次扫描专用协议（与 CLAUDE.md 拼接后注入） |
| `ARCHITECTURE.md` | 本文件：工具架构概述 |
| `run.sh` | Harness 主控：扫描、编码循环、进度指示、错误回滚 |
| `setup.sh` | 交互式配置向导：模型选择、MCP、API Key |
| `validate.sh` | 独立校验脚本：session_result、git、健康检查、自定义钩子 |
| `update.sh` | 从 upstream 拉取最新代码（排除法，自动同步新增文件） |
| `hooks-settings.json` | Claude Code hooks 配置（PreToolUse 事件注册） |
| `hooks/phase-signal.py` | PreToolUse hook：步骤推断 + 活动日志写入 |
| `cursor.mdc` | Cursor IDE 规则文件（复制到 `.cursor/rules/`） |
| `requirements.example.md` | 需求文件模板 |
| `README.md` / `README.en.md` | 用户文档 |
| `.gitignore` | 排除运行时文件 |

### 项目运行时数据（由 Agent 生成，update.sh 不覆盖）

| 文件 | 生成时机 | 用途 |
|------|----------|------|
| `project_profile.json` | 首次扫描 | 项目元数据：技术栈、服务、健康检查 URL |
| `init.sh` | 首次扫描 | 环境初始化脚本（幂等设计） |
| `tasks.json` | 首次扫描 | 功能任务列表 + 状态跟踪 |
| `progress.txt` | 每次 session 结束 | 跨会话记忆日志（只追加） |
| `session_result.json` | 每次 session 结束 | 本次会话的结构化输出 |
| `tests.json` | 首次测试时（Agent 自动创建） | 测试用例注册表（选择性回归） |
| `sync_state.json` | 需求同步时 | 需求 hash 同步状态 |
| `config.env` | setup.sh 生成 | 模型配置 + API Key（gitignored） |

### 运行时临时文件（session 生命周期，自动清理）

| 文件 | 写入者 | 读取者 | 用途 |
|------|--------|--------|------|
| `.phase` | `phase-signal.py` | `run.sh` indicator | 当前阶段：thinking / coding |
| `.phase_step` | `phase-signal.py` | `run.sh` indicator | 当前步骤：1-恢复上下文 ~ 6-收尾 |
| `.activity_log` | `phase-signal.py` | `run.sh` indicator | 最近工具调用摘要（滚动日志） |
| `requirements_hash.current` | `run.sh` | Agent | 需求同步触发条件 |
| `logs/*.log` | `run.sh` | 开发者 | session 和校验日志 |

## Hook 系统

Claude Code 的 hooks 是 **进程外设计**（不是 in-process callback）。Hook handler 是独立进程，通过 stdin 接收 JSON，通过 stdout/exit code 返回结果。

### 配置

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "\"$CLAUDE_PROJECT_DIR\"/claude-auto-loop/hooks/phase-signal.py",
        "async": true
      }]
    }]
  }
}
```

注入方式：`run.sh` 通过 `--settings hooks-settings.json` 传递给 `claude` CLI。

### 可用的 hook 事件（Claude Code 原生支持）

| 事件 | 触发时机 | 本工具是否使用 |
|------|----------|----------------|
| `PreToolUse` | 工具调用前 | **是**（步骤推断 + 活动日志） |
| `PostToolUse` | 工具调用成功后 | 否（PreToolUse 已足够） |
| `SessionStart/End` | 会话开始/结束 | 否 |
| `Stop` | Claude 停止响应 | 否 |
| `Notification` | 通知事件 | 否 |

## 扩展点

| 扩展需求 | 方式 |
|----------|------|
| 增加校验逻辑 | 在 `validate.d/` 放 `.sh` 脚本，validate.sh 自动加载 |
| 增加 hook 事件 | 修改 `hooks-settings.json`，在 `hooks/` 新增脚本 |
| 支持新模型 | 修改 `setup.sh` 添加提供商 |
| 定制 Agent 行为 | 修改 `CLAUDE.md`（但用户项目不应修改，由 upstream 维护） |

## 设计原则

1. **工具与项目分离**：`claude-auto-loop/` 是独立子目录，不污染项目结构
2. **排除法优于包含法**：`update.sh` 和 `.gitignore` 定义"要保护什么"而非"要包含什么"
3. **Agent 自治**：Agent 通过 CLAUDE.md 协议自主决策，harness 只负责调度和校验
4. **幂等设计**：`init.sh`、`run.sh` 可重复执行，不产生副作用
5. **最小依赖**：仅需 `claude` CLI + `python3` + `git`，无 Node/jq 等额外依赖
