# Claude Auto Loop

**中文** | [English](README.en.md)

让 AI Agent 自动完成复杂的多步编码任务。

AI Agent 单次会话的上下文有限，面对大型需求时容易丢失进度、过早宣布完成、或改出不可用的代码。本工具通过**外部 harness** 管理任务状态、自动校验每次会话的产出、失败时自动 git 回滚并重试，让 Agent 变成一个"可靠的、可重试的函数"。

基于 [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)，并做了多项工程级增强。

---

## 安装

**前置条件**: [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`) + Python 3 + Git

```bash
cd /path/to/your/project
git clone --depth 1 https://github.com/lk19940215/claude-auto-loop.git
rm -rf claude-auto-loop/.git    # 移除工具自带的 git 历史，避免嵌套仓库
```

### 更新工具

若已将工具作为子目录集成到项目中，可用 `update.sh` 从 upstream 拉取最新代码，**保留** `config.env`、`tasks.json`、`progress.txt` 等项目文件：

```bash
# 工具在 claude-auto-loop/ 子目录时
bash claude-auto-loop/update.sh

# 工具在项目根目录时（扁平结构）
bash update.sh
```

更新会覆盖：`CLAUDE.md`、`run.sh`、`setup.sh`、`validate.sh`、`cursor.mdc`、`hooks/` 等核心文件。

---

## 使用方式

### 基本用法

```bash
# 首次运行（必须提供需求，二选一）

# 快捷模式：一句话需求
bash claude-auto-loop/run.sh "实现用户登录功能，支持邮箱和 OAuth"

# 详细模式：写需求文档（推荐，可指定技术栈、样式、功能细节）
cp claude-auto-loop/requirements.example.md requirements.md
vim requirements.md                # 编辑你的需求
bash claude-auto-loop/run.sh     # 自动读取 requirements.md

# 后续继续（自动从上次中断处恢复）
bash claude-auto-loop/run.sh
```

> **提示**：`requirements.md` 优先于 CLI 参数。你可以随时修改它，下一个 session 会自动读取最新内容。

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--view` | 交互式观测模式，实时显示 Agent 决策过程 | 关闭 |
| `--max N` | 最大 session 数，达到后自动停止 | 50 |
| `--pause N` | 每 N 个 session 暂停一次，等待用户确认 | 5 |

```bash
bash claude-auto-loop/run.sh                          # 默认：50 sessions, 每 5 个暂停
bash claude-auto-loop/run.sh --max 3                  # 跑 3 个 session 就停
bash claude-auto-loop/run.sh --max 10 --pause 3       # 跑 10 个，每 3 个暂停确认
bash claude-auto-loop/run.sh --view                   # 观测模式
bash claude-auto-loop/run.sh --view "需求描述"         # 观测模式 + 项目初始化
```

### 观测模式（调试 / 观察 Agent 行为）

`run.sh` 默认使用 `-p`（Print 模式）做自动化循环，只输出最终文本。加上 `--view` 参数可切换为 Claude Code 交互模式，**实时观察 Agent 的工具调用、文件编辑和决策过程**：

```bash
bash claude-auto-loop/run.sh --view           # 观测下一个编码任务
bash claude-auto-loop/run.sh --view "需求"     # 观测项目初始化过程
```

`--view` 会自动继承 `config.env` 中的模型配置（DeepSeek / GLM / Claude），注入 CLAUDE.md 协议，使用相同的 hooks 和 settings。唯一区别是以交互模式运行，完成后需手动退出（`Ctrl+C` 或 `/exit`）。

**两种模式对比**：

| | 自动化模式 | 观测模式 (`--view`) |
|---|---|---|
| 命令 | `bash run.sh "需求"` | `bash run.sh --view` |
| 可见性 | 仅最终文本 + 进度指示器 | 实时工具调用、文件 diff、thinking |
| 退出 | 自动退出并循环 | 手动退出（`Ctrl+C` 或 `/exit`） |
| 校验 | 自动运行 `validate.sh` | 需手动运行 `bash claude-auto-loop/validate.sh` |
| 适合 | 无人值守、批量执行 | 调试 prompt、观察行为、验证单个任务 |

---

## Playwright MCP（Web 前端自动测试）

### 为什么重要

Agent 的 6 步工作流中，第 5 步（测试验证）对 Web 前端项目至关重要。没有 Playwright MCP 时，Agent 只能用 `curl` 检查 HTTP 状态码和文本匹配，无法验证页面渲染、交互行为、组件是否正确显示。

| | 无 Playwright MCP | 有 Playwright MCP |
|---|---|---|
| 前端测试 | curl 检查状态码（只能验证页面存在） | 浏览器渲染 + 截图 + 点击交互 |
| 测试质量 | 低（无法验证视觉效果和交互） | 高（端到端验证） |
| 工具调用 | 多次 curl + grep 试错 | 精准的 snapshot + click |
| session 效率 | 测试阶段消耗大量 turns | 测试阶段快速通过 |

### 依赖说明

Playwright MCP (`@playwright/mcp`) 是 npm 包，由微软维护：
- **自带 Chromium 浏览器**（首次运行时自动下载 ~150MB，不需要手动安装 Chrome）
- **不依赖** Python playwright 包
- 需要 Node.js 18+

### 安装方式

**方式一：通过 setup.sh 安装（推荐）**

```bash
bash claude-auto-loop/setup.sh
# 配置模型后会提示是否安装 Playwright MCP
```

**方式二：手动安装**

```bash
# Claude CLI
claude mcp add playwright -- npx @playwright/mcp@latest

# Cursor IDE: Settings → MCP → Add
# name: playwright
# command: npx @playwright/mcp@latest
```

### 确认安装成功

```bash
claude mcp list                       # 应显示 playwright
npx @playwright/mcp@latest --help     # 应显示帮助信息
```

安装后，首次 Agent 调用浏览器工具时会自动下载 Chromium（需联网）。

---

## 自动测试

Agent 在每个 session 的第 5 步执行测试验证。测试策略由 [CLAUDE.md](CLAUDE.md) 中的协议定义。

### 测试策略优先级

| 项目类型 | 有 Playwright MCP | 无 Playwright MCP |
|---|---|---|
| Web 前端 | `browser_navigate` + `browser_snapshot`（推荐） | `curl` + `grep`（有限） |
| API 后端 | `curl` 验证状态码和响应 | `curl` 验证状态码和响应 |
| 纯逻辑 | 运行 `pytest` / `npm test` | 调用入口函数验证 |

### 测试效率规则

CLAUDE.md 中定义了防止 Agent 在测试阶段浪费 API 调用的规则：

- **先验证数据再验证 UI**：组件依赖数据时，先确认数据源是否有输出
- **curl 测试最多 3 次**：同一 URL 找不到预期内容就换测试用例
- **禁止创建独立测试文件**：不要生成 `test-*.js` / `test-*.html`
- **禁止为了测试重启服务器**：除非构建报错
- **优先使用 Playwright MCP**：一次 `browser_snapshot` 胜过多轮 `curl`

### Harness 外部校验

Agent 的测试只是第一层。每个 session 结束后，`run.sh` 自动调用 `validate.sh` 做外部校验：

- `session_result.json` 是否合法
- 是否有新 git 提交
- 服务健康检查
- `validate.d/` 中的自定义钩子

### 自定义测试钩子

在 `validate.d/` 目录下放置 `.sh` 脚本，`validate.sh` 会自动执行它们：

```bash
mkdir -p claude-auto-loop/validate.d

# 示例：添加 lint 检查
cat > claude-auto-loop/validate.d/lint.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
npm run lint 2>&1 || exit 2  # exit 2 = 警告，exit 1 = 致命
EOF
```

钩子退出码约定：`0` = 通过，`1` = 致命失败（触发 git 回滚），`2+` = 警告（不阻断）。

---

## 运行机制详解

### 运行后会发生什么

```
bash claude-auto-loop/run.sh "你的需求"
        |
        v
  ┌──────────────────────────────────────────────┐
  │ 1. 项目扫描（首次自动执行）                     │
  │    注入: CLAUDE.md + SCAN_PROTOCOL.md（拼接）  │
  │    Agent 扫描项目文件 → 生成:                   │
  │    - project_profile.json (项目元数据)          │
  │    - init.sh (环境初始化脚本)                   │
  │    - tasks.json (任务列表 + 状态)               │
  └──────────────────────────────────────────────┘
        |
        v
  ┌─────────────────────────────────────────┐
  │ 2. 编码循环（自动重复直到全部完成）        │
  │                                         │
  │    每个 session:                         │
  │    ① 恢复上下文（读进度文件 + git log）   │
  │    ② 健康检查（启动服务、检查端口）        │
  │    ③ 选一个任务（优先修复失败的）          │
  │    ④ 增量实现（一次只做一个功能）          │
  │    ⑤ 测试验证（端到端测试）               │
  │    ⑥ 收尾（git commit + 更新进度）        │
  └─────────────────────────────────────────┘
        |
        v
  ┌─────────────────────────────────────────┐
  │ 3. Harness 校验（每次 session 后自动）    │
  │                                         │
  │    ✓ session_result.json 合法？          │
  │    ✓ git 有新提交？                      │
  │    ✓ 服务健康检查通过？                   │
  │    ✓ 自定义钩子通过？                     │
  │                                         │
  │    失败 → git 回滚 → 重试（最多 3 次）    │
  │    通过 → 继续下一个 session              │
  └─────────────────────────────────────────┘
        |
        v
  所有任务 done → 自动退出
  中途 Ctrl+C → 下次运行自动恢复
```

### 脚本调用顺序

| 脚本 | 何时调用 | 说明 |
|------|----------|------|
| **check_prerequisites** | run.sh 启动时自动执行 | 检查 claude CLI、python3、CLAUDE.md、SCAN_PROTOCOL.md、validate.sh 是否存在；无 config.env 时会提示可运行 setup.sh |
| **setup.sh** | 用户手动运行（可选） | 配置模型（Claude / GLM / DeepSeek 等）和 MCP 工具。**切换模型或额度不足时**：再次运行并选择 `y` 重新配置 |
| **init.sh** | 每次 coding session 内由 Agent 调用 | Agent 首次扫描后自动生成，负责项目环境的启动（安装依赖、启动服务等） |
| **validate.sh** | 每次 session 结束后由 run.sh 自动调用 | 校验 Agent 产出、git 提交、服务健康检查 |

### 核心循环：谁驱动什么

整个系统分两层，各司其职：

- **外层 -- run.sh（harness）**：一个 while 循环，不做任何智能决策。它只负责：调用 Agent → 校验产出 → 失败就回滚 → 重复。
- **内层 -- Agent（Claude）**：每个 session 内部，Agent 自己读 `tasks.json`，选任务、写代码、测试、提交。

```
run.sh 核心逻辑（伪代码）:

while session < MAX_SESSIONS:              # 默认 50，可通过 --max 调整
    if all tasks done:
        exit                               # 全部完成，退出

    记录 git HEAD                           # 记住 session 前的代码状态

    claude -p "精简 prompt"                  # ← -p 为 Print 模式
        --append-system-prompt-file CLAUDE.md #    编码 session 仅注入 CLAUDE.md（扫描 session 额外拼接 SCAN_PROTOCOL.md）
        --allowedTools "Read,Edit,Write,..."  #    工具白名单，防止工具滥用
        --verbose                             #    实时显示 tool call 详情
        2>&1 | tee session.log                #    前台管道，终端实时输出 + 日志记录

    bash validate.sh                        # ← harness 外部校验 Agent 的产出

    if 校验通过:
        continue                            # 进入下一个 session
    else:
        git reset --hard HEAD_BEFORE        # 回滚到 session 前
        consecutive_failures++
        if consecutive_failures >= 3:
            强制标记当前任务为 failed          # 跳过这个任务，防止死循环
            consecutive_failures = 0

    每 PAUSE_EVERY 个 session 暂停一次       # 默认 5，可通过 --pause 调整
```

**为什么 harness 不选任务？** 因为 Agent 拥有完整的项目上下文（代码、依赖关系、上次的进度），它比一个 shell 脚本更适合做决策。harness 只做 Agent 做不好的事情：外部校验和强制回滚。

### 查看进度

```bash
cat claude-auto-loop/progress.txt          # 每次 session 的工作记录
cat claude-auto-loop/tasks.json            # 任务列表和状态
cat claude-auto-loop/project_profile.json  # 自动检测的项目元数据
```

### 任务选择逻辑

每个 session 开始时，Agent 按以下规则从 `tasks.json` 中选一个任务：

1. **优先选 `failed` 的任务** -- 修复之前失败的，比做新功能更重要
2. **其次选 `pending` 的任务** -- 还没开始的新功能
3. **按 `priority` 排序** -- 数字越小越优先
4. **检查 `depends_on`** -- 如果依赖的任务还没 `done`，跳过
5. **一次只选一个** -- 防止上下文耗尽

选中后，Agent 把任务 `status` 改为 `in_progress`，然后开始实现。

### 任务状态机

每个任务有 5 种状态，必须按箭头方向流转，不能跳步：

```
pending ──→ in_progress ──→ testing ──→ done
                               │
                               v
                            failed ──→ in_progress（重试）
```

| 状态 | 含义 | 谁设置 |
|---|---|---|
| `pending` | 未开始 | 初始化时自动设置 |
| `in_progress` | 正在实现 | Agent 选中任务时 |
| `testing` | 代码写完，正在测试 | Agent 开始验证时 |
| `done` | 测试通过 | Agent 确认测试通过后 |
| `failed` | 测试失败或实现有问题 | Agent 发现问题时 / harness 连续失败 3 次时强制标记 |

**禁止的操作**：`pending` 不能直接到 `done`（必须先写代码再测试），`in_progress` 不能直接到 `done`（必须先测试）。

### 校验与失败处理

每个 session 结束后，harness 运行 `validate.sh` 检查 Agent 的产出。根据结果有 4 种场景：

**场景 1 -- 正常完成**

```
Agent 实现功能 → 测试通过 → status 改为 done → git commit → 写 session_result.json
    → validate.sh 检查: session_result 合法 ✓ git 有新提交 ✓
    → 通过，进入下一个 session
```

**场景 2 -- Agent 自报失败**

```
Agent 实现功能 → 测试未通过 → status 改为 failed → git commit → session_result 写 "failed"
    → validate.sh 检查: session_result 合法（Agent 诚实地报告了失败）✓
    → 通过（不回滚），下一个 session Agent 会优先修复这个 failed 的任务
```

**场景 3 -- Agent 产出不合格（需要回滚）**

```
Agent 崩溃 / 超时 / 没写 session_result.json / JSON 格式错误
    → validate.sh 检查: session_result 缺失或非法 ✗
    → 致命失败 → harness 执行 git reset --hard（回到 session 前的状态）
    → tasks.json 也被回滚，任务状态恢复原样
    → 下一个 session 重新尝试同一个任务
```

**场景 4 -- 连续失败 3 次（跳过）**

```
同一个任务连续 3 次触发场景 3
    → harness 判断这个任务 Agent 做不了
    → 强制把 in_progress 的任务标记为 failed
    → 重置失败计数器，继续选下一个 pending 的任务
```

### git 回滚如何保证一致性

回滚用的是 `git reset --hard HEAD_BEFORE`，它会把**所有文件**恢复到 session 开始前的状态 -- 包括 `tasks.json`。所以任务的状态也会回到修改前。这意味着：

- 回滚后，没有"改了一半"的脏状态
- 下一个 session 看到的 `tasks.json` 和上一个成功 session 结束时一样
- Agent 会重新选择同一个任务（因为它还是 `pending` 或 `in_progress`）

### 安全机制

防止 Agent 无限运行或失控的保护措施：

| 机制 | 说明 |
|---|---|
| 最大会话数 | 默认 50 个 session 后自动停止（`--max` 调整），达到上限后提示如何继续 |
| 单任务最大重试 | 同一任务连续失败 3 次后强制标记为 `failed`，跳到下一个任务 |
| 定期人工确认 | 每 5 个 session 暂停一次（`--pause` 调整），等待用户确认是否继续 |
| Ctrl+C 安全退出 | 收到中断信号时优雅退出，并提示 `bash claude-auto-loop/run.sh` 即可恢复 |
| 初始化重试 | 项目扫描阶段最多重试 3 次，避免因偶发错误导致无法启动 |
| git 回滚 | 每次校验失败自动 `git reset --hard`，代码永远不会停留在不可用状态 |

**断点恢复**：无论是 Ctrl+C 中断、终端意外关闭、还是达到会话上限，只需重新运行 `bash claude-auto-loop/run.sh` 即可从上次中断处继续。所有进度都持久化在 `tasks.json` 和 `progress.txt` 中。

### 运行时的观察能力

run.sh 提供两层观察能力：

**实时输出（`--verbose` + `| tee`）**：编码 session 默认启用 `--verbose`，Claude Code 会在终端输出每轮的 tool call 名称和结果。所有输出通过 `| tee` 同时写入日志文件，可回溯查看。

**进度提示（PreToolUse hook）**：每 15 秒输出一次进度状态。通过 Claude Code 的 **PreToolUse** hook（`hooks/phase-signal.py`）检测：当模型首次调用工具时，提示从「思考中」切换为「AI 编码中」。

**6 步流程提示**：当 Agent 进入编码阶段后，提示会显示当前推断的 [CLAUDE.md](CLAUDE.md) 工作流步骤，例如：
- `AI 编码中 · 步骤1-恢复上下文`
- `AI 编码中 · 步骤4-增量实现`
- `AI 编码中 · 步骤5-测试验证`

步骤由工具调用模式推断（如 Read profile/progress/tasks → 步骤1，Bash init.sh → 步骤2），可能有偏差，仅供参考。

### 常见问题

**额度不足 / 429 错误？**  
运行 `bash claude-auto-loop/setup.sh` 切换到其它提供商。推荐：

| 提供商 | 免费额度 | 说明 |
|--------|----------|------|
| **DeepSeek** | 赠送余额（以平台为准） | 新用户注册即得，[创建 API Key](https://platform.deepseek.com/api_keys) |
| OpenRouter | 50 次/日（未充值） | 需自备 key 或选免费模型，[openrouter.ai](https://openrouter.ai) |
| Anthropic Console | $5 一次性 | 需海外手机，[console.anthropic.com](https://console.anthropic.com) |

**模型调用后长时间无输出？**  
run.sh 通过 `2>&1 | tee` 管道实时显示模型输出，编码 session 还启用了 `--verbose` 显示详细 tool call 信息。首次 API 响应通常需 1–2 分钟（智谱等国内节点可能更长）。若仍无输出，在 `config.env` 中添加 `CLAUDE_DEBUG=api` 查看 API 请求日志。

**「思考中」如何切换为「AI 编码中」？**  
见上节「运行时的进度提示」：PreToolUse hook 在首次工具调用时写入 `.phase`，进度提示自动切换。

**模型报告「需要授权创建文件」但 project_profile.json/tasks.json 未生成？**  
run.sh 已为 claude 添加 `--permission-mode bypassPermissions`，允许 Agent 在无人值守时直接创建/编辑文件，无需交互确认。若仍出现此问题，可改用 `--dangerously-skip-permissions`（仅建议在可信环境中使用）。

**Ctrl+C 无法退出？**  
claude 以前台管道方式运行，Ctrl+C 会直接终止 claude 和 tee 进程。trap 会清理后台的进度提示进程并安全退出。若仍无法退出，可尝试连续按两次 Ctrl+C，或使用 `kill -9 <run.sh的PID>`。

**如何让终端显示更多日志（如 playwright-mcp Click）？**  
编码 session 已默认启用 `--verbose`，终端会显示每轮 tool call 的名称和结果。如需更详细的调试信息，在 `config.env` 中添加 `CLAUDE_DEBUG`，可随时修改、无需重跑 setup：

```
CLAUDE_DEBUG=mcp        # MCP 调用（含 Playwright）
CLAUDE_DEBUG=api,mcp    # API + MCP
```

**DeepSeek 后台仍显示 deepseek-reasoner 调用？**  
本工具已按 DeepSeek 官方 Claude Code 接入要求配置，应避免 reasoner 混用。若仍看到 reasoner 调用，可检查：  
1. `~/.claude/settings.json` 或项目 `.claude/settings.json` 中是否覆盖了 `model`（如设为 `opus`、`opusplan` 等）；  
2. 确认 config.env 包含 `ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat`；  
3. 重新运行 `bash claude-auto-loop/setup.sh` 选择 DeepSeek 以生成完整配置。

调试完注释或删掉该行即可恢复静默。

**CLI 模式下能否与 Claude 交互？**  
run.sh 使用 `-p`（headless）模式运行，Agent 自主完成任务，不暂停等待确认。如需交互式观察，使用 `--view` 模式；如需对话式协作，使用 **Cursor IDE 模式**（见下方章节）。

---

## 需求变更与用户介入

**需求会变动时：**

- 修改 `requirements.md` 后，下次运行 `bash claude-auto-loop/run.sh` 时，Agent 会读取最新内容。
- Agent 在恢复上下文时会**条件触发**需求同步：仅当 `requirements.md` 内容发生变化时，才对比 `requirements.md` 与 `tasks.json`；若发现未被覆盖的新需求，会拆解为新任务追加到 `tasks.json`，然后照常选任务、实现。
- 协议允许 Agent 新增任务（仅禁止删除或修改已有任务描述），因此需求变更会自动反映到任务列表。

**当你自己发现需要改进时，有三种方式：**

| 方式 | 操作 | 适用场景 |
|------|------|----------|
| 更新需求文档 | 在 `requirements.md` 中补充新需求或改进点，然后 `bash claude-auto-loop/run.sh` | 希望 Agent 拆解并实现，推荐 |
| 手动添加任务 | 在 `tasks.json` 的 `features` 中新增一项（`status: "pending"`），然后运行 `run.sh` | 需求已明确，希望精确控制任务描述 |
| 直接修改代码 | 在 Cursor 中改完并 `git commit`，再运行 `run.sh` | 小改动，自己改更快 |

无论哪种方式，之后照常运行 `bash claude-auto-loop/run.sh` 即可继续。

---

## Cursor IDE 模式

如果你用 Cursor 而不是 Claude CLI，也能用这套工具。区别是：你手动触发每次对话，而不是 run.sh 自动循环。

### 安装

```bash
# 一次性：复制规则文件到 Cursor 配置目录
mkdir -p .cursor/rules
cp claude-auto-loop/cursor.mdc .cursor/rules/claude-auto-loop.mdc
```

### 使用

1. **第一次对话**：在 Cursor 中新建对话，输入你的需求，例如：

   > "实现用户登录功能，支持邮箱和 OAuth"

   Cursor 会自动读取 Agent 协议（通过 cursor.mdc），Agent 会执行项目扫描、生成 tasks.json 等初始化工作。

2. **后续每次对话**：直接新建对话即可。Agent 会自动：
   - 读取 `CLAUDE.md` 了解工作协议
   - 读取 `progress.txt` 和 `tasks.json` 恢复上下文
   - 选择下一个任务，实现、测试、提交

3. **每次对话结束后**（可选）：运行校验确认 Agent 的产出合格

   ```bash
   bash claude-auto-loop/validate.sh
   ```

### CLI 模式 vs Cursor 模式

| 维度 | Claude CLI 模式 | Cursor IDE 模式 |
|---|---|---|
| 谁驱动循环 | `run.sh` 自动循环 | 你手动发起每次对话 |
| 校验 | 自动（每次 session 后） | 可选（手动运行 validate.sh） |
| 回滚 | 自动 git reset | 手动 / Agent 自我检查 |
| 适合场景 | 无人值守批量开发 | 交互式开发、需要人工介入 |

---

## 可选配置

默认情况下，不需要任何配置就能运行。以下配置是**可选的**。

```bash
bash claude-auto-loop/setup.sh
```

### 替代模型（降低成本）

默认使用 Claude 官方 API。如需替代模型：

| 选项 | 说明 |
|---|---|
| Claude 官方 | 默认，质量最高 |
| GLM (智谱) | `open.bigmodel.cn` 兼容网关，国内直连；可选 **GLM 4.7** 或 **GLM 5** |
| GLM (Z.AI) | `api.z.ai` 兼容网关，海外节点；可选 GLM 4.7 或 GLM 5 |
| **DeepSeek** | `api.deepseek.com` 官方 Anthropic 兼容（含 `ANTHROPIC_AUTH_TOKEN`、`API_TIMEOUT_MS=600000`）；新用户有赠送余额 |
| 自定义 | 任意 Anthropic 兼容的 BASE_URL |

选择 GLM 时，setup.sh 会提示选择模型版本（GLM 4.7 / GLM 5）。**额度不足时可选 DeepSeek**：新用户有赠送余额，官网 <https://platform.deepseek.com/api_keys> 创建 API Key 即可。

**DeepSeek 三种模式**（setup.sh 中选择）：

| 模式 | 适用场景 | 成本 | 原理 |
|---|---|---|---|
| **Chat 模式** (推荐) | 日常开发、高频小任务 | ⭐ (最低) | 全链路使用 `deepseek-chat` (V3)。通过 `optimized` 别名强制禁用 Thinking，确保 0 Reasoner 费用。 |
| **Hybrid 模式** (混合) | 复杂任务、性价比 | ⭐⭐ (中) | 大脑 (Opus) 用 **R1** 规划，手脚 (Sonnet/Haiku) 用 **V3** 执行。平衡智商与成本。 |
| **Reasoner 模式** | 攻坚克难、逻辑推理 | ⭐⭐⭐ (最高) | 全链路使用 `deepseek-reasoner` (R1)。推理能力最强，但每次操作（含读文件）都按 R1 计费。 |

> **提示**：DeepSeek Reasoner 价格约为 Chat 的 5-10 倍。推荐使用 **Chat 模式** 或 **Hybrid 模式**。

setup 选择 DeepSeek 后，config.env 会根据所选模式自动生成对应的 `ANTHROPIC_MODEL` 和别名映射。

配置保存在 `config.env`（自动加入 `.gitignore`），仅影响本工具，不改变全局配置。**切换模型提供商**：再次运行 `bash claude-auto-loop/setup.sh`，选择 `y` 重新配置即可。

**config.env 可编辑项**：生成后可手动编辑，无需重跑 setup。例如添加 `CLAUDE_DEBUG=mcp` 开启调试日志；修改 `ANTHROPIC_MODEL` 切换模型版本。

---

## 相比 Anthropic 文章的增强

本工具基于 Anthropic 的 [long-running agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 思想，在以下维度做了工程级增强：

| 维度 | Anthropic 原文方案 | 本工具增强 |
|---|---|---|
| 任务状态 | 简单 bool (`passes`) | 5 态状态机 (`pending` → `in_progress` → `testing` → `done` / `failed`) |
| 校验方式 | 依赖 Agent 自报告 | 外部 harness 硬校验 (`validate.sh`) |
| 失败处理 | 无 | git 自动回滚 + 最多 3 次重试 |
| 项目信息 | 硬编码在 CLAUDE.md | 自动扫描生成 `project_profile.json` |
| 环境初始化 | 手写 init.sh | Agent 扫描后自动生成 |
| 结构化输出 | 无 | 每次 session 强制输出 `session_result.json`（machine-readable） |
| 运行环境 | 仅 Claude CLI | 同时支持 Claude CLI + Cursor IDE |
| 测试工具 | 无 | 可插拔 Playwright MCP 浏览器自动化 |
| 校验扩展 | 无 | `validate.d/` 钩子目录，用户可自定义 |
| 模型选择 | 仅 Claude | 支持 GLM 4.7/5、DeepSeek 等 Anthropic 兼容模型 |
| 需求输入 | CLI 一句话参数 | 支持 `requirements.md` 需求文档（可指定技术栈、样式、随时可改） |
| 进度提示 | 无 | PreToolUse hook 精准切换「思考中」→「AI 编码中」 |
| 调试输出 | 无 | `--verbose` 默认启用 + config.env 中 `CLAUDE_DEBUG` 可开启 mcp/api 日志 |
| Agent 协议加载 | Agent 自行 Read CLAUDE.md（可能跳过） | `--append-system-prompt-file` 保证 100% 注入；编码 session 仅注入 CLAUDE.md，扫描 session 拼接 SCAN_PROTOCOL.md；利用 API 前缀缓存降低 token 成本 |
| 工具约束 | 无限制 | `--allowedTools` 白名单，防止工具滥用和幻觉调用 |
| 失败重试 | 盲重试 | 注入上次校验失败原因，避免重复同样的错误 |

---

## 参考

### 文件说明

**预置文件**（通用，复制到任何项目即可用）：

| 文件 | 说明 |
|---|---|
| `CLAUDE.md` | Agent 协议：铁律 + 参考格式 + 状态机 + 6 步工作流（注意力优化排列：硬约束在顶部、行动指令在底部） |
| `SCAN_PROTOCOL.md` | 扫描专用协议：项目扫描步骤 + `project_profile.json` 格式 + `init.sh` 生成规则（仅在首次扫描时注入） |
| `run.sh` | CLI 模式入口：外部循环 + system prompt 注入 + 工具白名单 + 校验 + 回滚 + 重试 |
| `validate.sh` | 独立校验脚本：CLI 自动调用 / Cursor 手动运行 |
| `setup.sh` | 交互式前置配置（模型选择 + MCP 工具安装） |
| `cursor.mdc` | Cursor 规则文件：复制到 `.cursor/rules/` 使用 |
| `requirements.example.md` | 需求文档模板：复制为 `requirements.md` 填写详细需求 |
| `hooks/phase-signal.py` | PreToolUse hook：首次工具调用时写入 `.phase`，供进度提示切换 |
| `hooks-settings.json` | Claude Code hooks 配置，run.sh 通过 `--settings` 加载 |
| `update.sh` | 从 upstream 拉取最新代码，保留 config.env、tasks.json 等项目文件（见上方「更新工具」） |
| `README.md` | 本文件 |

**运行时生成**（项目特定，由 Agent 或 setup.sh 创建）：

| 文件 | 说明 |
|---|---|
| `config.env` | 模型 + MCP 配置（由 setup.sh 生成，含 API Key、ANTHROPIC_MODEL、可选 CLAUDE_DEBUG 调试开关，已 gitignore） |
| `project_profile.json` | 自动检测的项目元数据（技术栈、服务、端口等） |
| `init.sh` | 自动生成的环境初始化脚本（幂等设计） |
| `tasks.json` | 任务列表 + 状态机跟踪 |
| `progress.txt` | 跨会话记忆日志（追加式） |
| `session_result.json` | 临时文件（每次 session 后由 harness 删除） |
| `.phase` | 进度状态文件（thinking/coding），由 PreToolUse hook 写入，已 gitignore） |
