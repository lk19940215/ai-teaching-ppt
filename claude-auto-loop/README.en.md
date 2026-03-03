# Claude Auto Loop

[中文](README.md) | **English**

Let AI Agents autonomously complete complex, multi-step coding tasks.

A single AI session has limited context. When facing large requirements, agents tend to lose progress, prematurely declare success, or produce broken code. This tool wraps the agent in an **external harness** that manages task state, validates every session's output, and automatically rolls back + retries on failure — turning the agent into a "reliable, retryable function."

Based on [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), with multiple engineering-grade enhancements.

---

## Installation

**Prerequisites**: [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`) + Python 3 + Git

```bash
cd /path/to/your/project
git clone --depth 1 https://github.com/lk19940215/claude-auto-loop.git
rm -rf claude-auto-loop/.git    # Remove the tool's own git history to avoid nested repos
```

---

## Usage

### Basic Usage

```bash
# First run (must provide a requirement, pick one)

# Quick mode: one-liner requirement
bash claude-auto-loop/run.sh "Implement user login with email and OAuth support"

# Detailed mode: write a requirements doc (recommended for specific tech/design preferences)
cp claude-auto-loop/requirements.example.md requirements.md
vim requirements.md                # Edit your requirements
bash claude-auto-loop/run.sh     # Automatically reads requirements.md

# Resume later (automatically picks up where it left off)
bash claude-auto-loop/run.sh
```

> **Tip**: `requirements.md` takes priority over CLI arguments. You can edit it anytime — the next session will automatically pick up the latest content.

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--view` | Interactive observation mode, shows Agent decisions in real-time | Off |
| `--add "instruction"` | Task append mode, generates new tasks in tasks.json (no coding) | — |
| `--max N` | Maximum number of sessions before auto-stop | 50 |
| `--pause N` | Pause every N sessions for user confirmation | 5 |

```bash
bash claude-auto-loop/run.sh                          # Default: 50 sessions, pause every 5
bash claude-auto-loop/run.sh --max 3                  # Stop after 3 sessions
bash claude-auto-loop/run.sh --max 10 --pause 3       # Run 10, pause every 3
bash claude-auto-loop/run.sh --view                   # Observation mode
bash claude-auto-loop/run.sh --view "requirement"     # Observation mode + project init
bash claude-auto-loop/run.sh --add "Add avatar upload" # Append new tasks
```

### Observation Mode (Debug / Watch Agent Behavior)

`run.sh` defaults to `-p` (Print mode) for automated looping, which only outputs the final text. Add the `--view` flag to switch to Claude Code's interactive mode, **watching the Agent's tool calls, file edits, and decision-making in real-time**:

```bash
bash claude-auto-loop/run.sh --view           # Watch the next coding task
bash claude-auto-loop/run.sh --view "requirement"  # Watch project initialization
```

`--view` automatically inherits the model configuration from `config.env` (DeepSeek / GLM / Claude), injects the CLAUDE.md protocol, and uses the same hooks and settings. The only difference is running in interactive mode — exit manually when done (`Ctrl+C` or `/exit`).

When all tasks are already `done`, `--view` automatically skips the 6-step workflow (no init.sh, no context recovery, etc.) and enters direct conversation mode.

**Mode comparison**:

| | Automated Mode | Observation Mode (`--view`) | Task Append (`--add`) |
|---|---|---|---|
| Command | `bash run.sh "requirement"` | `bash run.sh --view` | `bash run.sh --add "instruction"` |
| Visibility | Final text only + progress indicator | Live tool calls, file diffs, thinking | Final text only |
| Exit | Auto-exit and loop | Manual exit (`Ctrl+C` or `/exit`) | Auto-exit |
| Execution | Full 6-step workflow | 6-step workflow (skipped when all done) | Only updates tasks.json |
| Best for | Unattended, batch execution | Debugging prompts, observing behavior | Appending new requirements after all tasks are done |

### Task Append Mode (Add Requirements After Completion)

When all tasks are `done`, the coding loop exits immediately. To add new requirements, use `--add` mode to generate new `pending` tasks:

```bash
bash claude-auto-loop/run.sh --add "Add user avatar upload with cropping and compression"
bash claude-auto-loop/run.sh      # Continue coding loop with the new tasks
```

`--add` is a lightweight session: no 6-step workflow, no init.sh, no coding. The Agent only reads `tasks.json` and `project_profile.json`, appends new tasks based on the instruction, then git commits.

---

## Playwright MCP (Web Frontend Auto-Testing)

### Why It Matters

In the Agent's 6-step workflow, Step 5 (test & verify) is critical for web frontend projects. Without Playwright MCP, the Agent can only use `curl` to check HTTP status codes and text matching — it cannot verify page rendering, interaction behavior, or whether components display correctly.

| | Without Playwright MCP | With Playwright MCP |
|---|---|---|
| Frontend testing | curl checks status codes (can only verify page exists) | Browser rendering + screenshots + click interactions |
| Test quality | Low (cannot verify visual effects or interactions) | High (end-to-end verification) |
| Tool calls | Multiple curl + grep trial-and-error | Precise snapshot + click |
| Session efficiency | Testing phase consumes many turns | Testing phase passes quickly |

### Dependencies

Playwright MCP (`@playwright/mcp`) is an npm package maintained by Microsoft:
- **Includes Chromium browser** (auto-downloads ~150MB on first run, no need to manually install Chrome)
- **Does not depend on** Python playwright package
- Requires Node.js 18+

### Installation

**Option 1: Via setup.sh (recommended)**

```bash
bash claude-auto-loop/setup.sh
# After configuring the model, you'll be prompted to install Playwright MCP
```

**Option 2: Manual installation**

```bash
# Claude CLI
claude mcp add playwright -- npx @playwright/mcp@latest

# Cursor IDE: Settings → MCP → Add
# name: playwright
# command: npx @playwright/mcp@latest
```

### Verify Installation

```bash
claude mcp list                       # Should show playwright
npx @playwright/mcp@latest --help     # Should show help info
```

After installation, Chromium will auto-download on the Agent's first browser tool call (requires internet).

---

## Automated Testing

The Agent runs test verification in Step 5 of each session. Testing strategy is defined by the protocol in [CLAUDE.md](CLAUDE.md).

### Testing Strategy Priority

| Project Type | With Playwright MCP | Without Playwright MCP |
|---|---|---|
| Web Frontend | `browser_navigate` + `browser_snapshot` (recommended) | `curl` + `grep` (limited) |
| API Backend | `curl` to verify status codes and responses | `curl` to verify status codes and responses |
| Pure Logic | Run `pytest` / `npm test` | Call entry functions to verify |

### Testing Efficiency Rules

CLAUDE.md defines rules to prevent the Agent from wasting API calls during testing:

- **Verify data before UI**: When a component depends on data (e.g., recommendation list), confirm the data source has output first
- **Max 3 curl tests per URL**: If expected content isn't found in 3 attempts, switch test cases
- **No standalone test files**: Don't create `test-*.js` / `test-*.html`
- **No server restarts for testing**: Unless there's a build error
- **Prefer Playwright MCP**: One `browser_snapshot` beats multiple rounds of `curl`

### Harness External Validation

Agent testing is only the first layer. After each session, `run.sh` automatically runs `validate.sh` for external validation:

- Is `session_result.json` valid?
- Are there new git commits?
- Service health checks
- Custom hooks in `validate.d/`

### Custom Test Hooks

Place `.sh` scripts in the `validate.d/` directory. `validate.sh` will automatically execute them:

```bash
mkdir -p claude-auto-loop/validate.d

# Example: add a lint check
cat > claude-auto-loop/validate.d/lint.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
npm run lint 2>&1 || exit 2  # exit 2 = warning, exit 1 = fatal
EOF
```

Hook exit code convention: `0` = pass, `1` = fatal failure (triggers git rollback), `2+` = warning (non-blocking).

---

## How It Works

### What Happens After You Run It

```
bash claude-auto-loop/run.sh "your requirement"
        |
        v
  ┌───────────────────────────────────────────────────┐
  │ 1. Project Scan (auto on first run)               │
  │    Injects: CLAUDE.md + SCAN_PROTOCOL.md (concat) │
  │    Agent scans project files → generates:          │
  │    - project_profile.json (project metadata)       │
  │    - init.sh (environment init script)             │
  │    - tasks.json (task list + status)               │
  └───────────────────────────────────────────────────┘
        |
        v
  ┌─────────────────────────────────────────────┐
  │ 2. Coding Loop (repeats until all done)      │
  │                                              │
  │    Each session:                             │
  │    ① Restore context (read progress + git)   │
  │    ② Health check (start services, ports)    │
  │    ③ Pick a task (failed first, then pending)│
  │    ④ Incremental impl (one feature at a time)│
  │    ⑤ Test & verify (end-to-end)              │
  │    ⑥ Wrap up (git commit + update progress)  │
  └─────────────────────────────────────────────┘
        |
        v
  ┌─────────────────────────────────────────────┐
  │ 3. Harness Validation (after every session)  │
  │                                              │
  │    ✓ session_result.json valid?              │
  │    ✓ New git commit exists?                  │
  │    ✓ Service health check passed?            │
  │    ✓ Custom hooks passed?                    │
  │                                              │
  │    Fail → git rollback → retry (up to 3x)   │
  │    Pass → continue to next session           │
  └─────────────────────────────────────────────┘
        |
        v
  All tasks done → auto exit
  Ctrl+C mid-way → resume on next run
```

### Script Call Order

| Script | When | Description |
|--------|------|-------------|
| **check_prerequisites** | Auto on run.sh start | Checks claude CLI, python3, CLAUDE.md, SCAN_PROTOCOL.md, validate.sh; prompts to run setup.sh if no config.env |
| **setup.sh** | Manual (optional) | Configure model (Claude / GLM / DeepSeek) and MCP tools. **To switch provider or fix quota**: run again and choose `y` to reconfigure |
| **init.sh** | Per session by Agent | Auto-generated on first scan; starts environment (install deps, start services) |
| **validate.sh** | Auto after each session | Validates Agent output, git commit, health checks |

### Core Loop: Who Does What

The system has two layers, each with a clear responsibility:

- **Outer layer — run.sh (harness)**: A while loop that makes no intelligent decisions. It only: invokes the Agent → validates output → rolls back on failure → repeats.
- **Inner layer — Agent (Claude)**: Within each session, the Agent reads `tasks.json`, picks a task, writes code, tests, and commits.

```
run.sh core logic (pseudocode):

while session < MAX_SESSIONS:              # Default 50, adjustable via --max
    if all tasks done:
        exit                               # All done, exit

    record git HEAD                        # Remember pre-session code state

    claude -p "concise prompt"              # ← -p = Print mode
        --append-system-prompt-file CLAUDE.md #    Coding sessions inject CLAUDE.md only (scan sessions concat SCAN_PROTOCOL.md)
        --allowedTools "Read,Edit,Write,..."  #    Tool whitelist to prevent misuse
        --verbose                             #    Real-time tool call details
        2>&1 | tee session.log                #    Foreground pipeline: live terminal output + log file

    bash validate.sh                        # ← Harness externally validates Agent's output

    if validation passed:
        continue                            # Next session
    else:
        git reset --hard HEAD_BEFORE        # Roll back to pre-session state
        consecutive_failures++
        if consecutive_failures >= 3:
            force-mark current task as failed # Skip this task, prevent dead loops
            consecutive_failures = 0

    every PAUSE_EVERY sessions, pause       # Default 5, adjustable via --pause
```

**Why doesn't the harness pick tasks?** Because the Agent has full project context (code, dependencies, previous progress) — it's better at making decisions than a shell script. The harness only does what the Agent can't: external validation and forced rollback.

### Check Progress

```bash
cat claude-auto-loop/progress.txt          # Work log for each session
cat claude-auto-loop/tasks.json            # Task list and statuses
cat claude-auto-loop/project_profile.json  # Auto-detected project metadata
```

### Task Selection Logic

At the start of each session, the Agent selects a task from `tasks.json` following these rules:

1. **Prioritize `failed` tasks** — fixing previous failures is more important than new features
2. **Then `pending` tasks** — new features that haven't been started
3. **Sort by `priority`** — lower number = higher priority
4. **Check `depends_on`** — skip if dependencies aren't `done` yet
5. **One task at a time** — prevents context exhaustion

Once selected, the Agent changes the task `status` to `in_progress` and begins implementation.

### Task State Machine

Each task has 5 states and must flow in order — no skipping:

```
pending ──→ in_progress ──→ testing ──→ done
                               │
                               v
                            failed ──→ in_progress (retry)
```

| Status | Meaning | Set By |
|---|---|---|
| `pending` | Not started | Auto-set during initialization |
| `in_progress` | Being implemented | Agent when it picks the task |
| `testing` | Code done, running tests | Agent when it starts verification |
| `done` | Tests passed | Agent after confirming tests pass |
| `failed` | Tests failed or implementation broken | Agent on discovery / harness after 3 consecutive failures |

**Forbidden transitions**: `pending` cannot go directly to `done` (must code then test), `in_progress` cannot go directly to `done` (must test first).

### Validation & Failure Handling

After each session, the harness runs `validate.sh` to check the Agent's output. There are 4 scenarios:

**Scenario 1 — Normal completion**

```
Agent implements feature → tests pass → status set to done → git commit → writes session_result.json
    → validate.sh checks: session_result valid ✓ new git commit ✓
    → Pass, move to next session
```

**Scenario 2 — Agent self-reports failure**

```
Agent implements feature → tests fail → status set to failed → git commit → session_result says "failed"
    → validate.sh checks: session_result valid (Agent honestly reported failure) ✓
    → Pass (no rollback), next session Agent will prioritize fixing this failed task
```

**Scenario 3 — Agent output invalid (rollback needed)**

```
Agent crashes / times out / didn't write session_result.json / JSON format error
    → validate.sh checks: session_result missing or invalid ✗
    → Fatal failure → harness executes git reset --hard (back to pre-session state)
    → tasks.json also rolled back, task status restored
    → Next session retries the same task
```

**Scenario 4 — 3 consecutive failures (skip)**

```
Same task triggers Scenario 3 three times in a row
    → Harness decides the Agent can't handle this task
    → Force-marks in_progress task as failed
    → Resets failure counter, moves on to next pending task
```

### Git Rollback Consistency

Rollback uses `git reset --hard HEAD_BEFORE`, which restores **all files** to pre-session state — including `tasks.json`. So the task status is also reverted. This means:

- After rollback, there's no "half-modified" dirty state
- The next session sees `tasks.json` exactly as it was after the last successful session
- The Agent will re-select the same task (since it's still `pending` or `in_progress`)

### Safety Mechanisms

Safeguards to prevent the Agent from running indefinitely or going out of control:

| Mechanism | Description |
|---|---|
| Max sessions | Defaults to 50 sessions then auto-stops (`--max` to adjust); shows how to continue |
| Per-task max retry | After 3 consecutive failures on the same task, force-marks it as `failed` and moves on |
| Periodic human check | Pauses every 5 sessions (`--pause` to adjust), waits for user confirmation to continue |
| Ctrl+C safe exit | Gracefully exits on interrupt signal, shows how to resume with `bash claude-auto-loop/run.sh` |
| Init retry | Project scan phase retries up to 3 times to handle transient errors |
| Git rollback | Auto `git reset --hard` on every validation failure — code never stays in a broken state |

**Checkpoint recovery**: Whether interrupted by Ctrl+C, unexpected terminal closure, or session limit reached — just re-run `bash claude-auto-loop/run.sh` to resume from where it left off. All progress is persisted in `tasks.json` and `progress.txt`.

### Observability During Run

run.sh provides three layers of observability:

**Real-time output (`--verbose` + `| tee`)**: Coding sessions enable `--verbose` by default, so Claude Code prints tool call names and results in the terminal. All output is also piped through `| tee` to a log file for later review.

**Progress indicator (PreToolUse hook)**: Prints a progress status every 15 seconds. Via Claude Code's **PreToolUse** hook (`hooks/phase-signal.py`): when the model first calls a tool, the message switches from "Thinking..." to "Coding...".

**Real-time activity log**: The hook writes to `.activity_log` on each tool call, recording the tool name and a summary (e.g. `Read backend/app/main.py`, `Bash npm install`). The progress indicator reads the latest entry and displays it as:
- `Coding · Step 4: Implementation · Write backend/app/api.py`

**6-step workflow display**: After the Agent enters the coding phase, the indicator shows the inferred step from [CLAUDE.md](CLAUDE.md), e.g. `Coding · Step 4: Implementation`, `Coding · Step 5: Testing`. Steps are inferred from tool call patterns (e.g. Read profile/progress/tasks → Step 1, Bash init.sh → Step 2); slight inaccuracies are possible.

### Environment Check Optimization

In the coding loop, the Agent's Step 2 is "Environment & Health Check" (running init.sh to install deps, start services). To avoid redundant execution:

- **Skip on consecutive success**: When the previous session succeeded, run.sh injects a hint telling the Agent the environment is ready — skip init.sh, just curl to verify services are alive
- **Full check on first run or after failure**: The first session or after a rollback, the Agent runs the full environment check
- **Safety valve**: If the current task involves dependency changes (e.g. modified package.json), the Agent will still decide to run init.sh on its own

### Common Issues

**Quota exhausted / 429 error?**  
Run `bash claude-auto-loop/setup.sh` to switch provider. Options: **DeepSeek** (granted balance for new users, [create API Key](https://platform.deepseek.com/api_keys)); OpenRouter (50 req/day unpaid, [openrouter.ai](https://openrouter.ai)); Anthropic Console ($5 one-time, [console.anthropic.com](https://console.anthropic.com)).

**No output for a long time after model call?**  
run.sh uses `2>&1 | tee` for real-time terminal output, and coding sessions enable `--verbose` to show detailed tool call info. First API response often takes 1–2 minutes (longer for some endpoints). If still no output, add `CLAUDE_DEBUG=api` in config.env.

**How does "Thinking..." switch to "Coding..."?**  
See "Progress Indicator During Run" above: PreToolUse hook writes `.phase` on first tool call.

**Model says "needs permission to create file" but project_profile.json/tasks.json not generated?**  
run.sh adds `--permission-mode bypassPermissions`. If it still fails, try `--dangerously-skip-permissions` (trusted environments only).

**Ctrl+C doesn't exit?**  
claude runs as a foreground pipeline; Ctrl+C directly terminates claude and tee. The trap handler cleans up the background progress indicator and exits gracefully. Try Ctrl+C twice, or `kill -9 <run.sh PID>`.

**How to get more logs (e.g. playwright-mcp Click)?**  
Coding sessions already enable `--verbose` by default, showing tool call names and results per turn. For deeper debugging, add to config.env (no need to re-run setup):
```
CLAUDE_DEBUG=mcp        # MCP calls (incl. Playwright)
CLAUDE_DEBUG=api,mcp    # API + MCP
```

**DeepSeek usage still shows deepseek-reasoner calls?**  
This tool follows DeepSeek's official Claude Code integration and should avoid reasoner mixing. If you still see reasoner:  
1. Check `~/.claude/settings.json` or project `.claude/settings.json` for `model` overrides (e.g. `opus`, `opusplan`);  
2. Confirm config.env has `ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat`;  
3. Re-run `bash claude-auto-loop/setup.sh` and select DeepSeek to regenerate full config.

**Can I interact with Claude in CLI mode?**  
run.sh uses `-p` (headless) so the Agent works autonomously. For interactive observation, use `--view` mode; for conversational collaboration, use **Cursor IDE mode** (see section below).

---

## Requirements Changes and User Intervention

**When requirements evolve:**

- After editing `requirements.md`, the next `bash claude-auto-loop/run.sh` run will have the Agent read the latest content.
- During context restoration, the Agent **conditionally** syncs requirements: only when `requirements.md` has changed will it compare with `tasks.json`. If it finds new requirements not yet covered, it will break them down into new tasks, append them to `tasks.json`, then proceed as usual.
- The protocol permits the Agent to add new tasks (it only forbids deleting or modifying existing task descriptions), so requirement changes are reflected in the task list automatically.

**When you personally spot something to improve, you have four options:**

| Option | Action | When to use |
|--------|--------|-------------|
| Update requirements | Add new requirements or improvements to `requirements.md`, then run `bash claude-auto-loop/run.sh` | Let the Agent decompose and implement; **recommended** |
| `--add` append | `bash claude-auto-loop/run.sh --add "new feature description"` | All tasks done and you want to add new requirements; Agent auto-decomposes into tasks.json |
| Add task manually | Add a new entry to `features` in `tasks.json` with `status: "pending"`, then run `run.sh` | Requirements are clear and you want precise control over the task description |
| Edit code directly | Make changes in Cursor, `git commit`, then run `run.sh` | Small fixes you can do faster yourself |

In any case, continue with `bash claude-auto-loop/run.sh` as usual.

---

## Cursor IDE Mode

If you use Cursor instead of Claude CLI, this tool still works. The difference: you manually trigger each conversation instead of run.sh auto-looping.

### Setup

```bash
# One-time: copy the rules file to Cursor config
mkdir -p .cursor/rules
cp claude-auto-loop/cursor.mdc .cursor/rules/claude-auto-loop.mdc
```

### Usage

1. **First conversation**: Create a new chat in Cursor and enter your requirement, e.g.:

   > "Implement user login with email and OAuth support"

   Cursor auto-reads the Agent protocol (via cursor.mdc). The Agent will perform project scanning, generate tasks.json, etc.

2. **Subsequent conversations**: Just create a new chat. The Agent will automatically:
   - Read `CLAUDE.md` for the work protocol
   - Read `progress.txt` and `tasks.json` to restore context
   - Pick the next task, implement, test, and commit

3. **After each conversation** (optional): Run validation to confirm the Agent's output is acceptable

   ```bash
   bash claude-auto-loop/validate.sh
   ```

### CLI Mode vs Cursor Mode

| Dimension | Claude CLI Mode | Cursor IDE Mode |
|---|---|---|
| Who drives the loop | `run.sh` auto-loops | You manually start each conversation |
| Validation | Automatic (after every session) | Optional (manually run validate.sh) |
| Rollback | Automatic git reset | Manual / Agent self-check |
| Best for | Unattended batch development | Interactive development, human-in-the-loop |

---

## Optional Configuration

By default, no configuration is needed. The following are **optional**.

```bash
bash claude-auto-loop/setup.sh
```

### Alternative Models (Cost Reduction)

Defaults to the official Claude API. For alternative models:

| Option | Description |
|---|---|
| Claude Official | Default, highest quality |
| GLM (Zhipu) | `open.bigmodel.cn` compatible gateway, optional GLM 4.7 / GLM 5 |
| GLM (Z.AI) | `api.z.ai` compatible gateway, overseas node |
| **DeepSeek** | `api.deepseek.com` official Anthropic-compatible API; new users get granted balance |
| Custom | Any Anthropic-compatible BASE_URL |

**DeepSeek Three Modes** (Select in setup.sh):

| Mode | Use Case | Cost | Mechanism |
|---|---|---|---|
| **Chat Mode** (Recommended) | Daily coding, frequent tasks | Low | Uses `deepseek-chat` (V3) everywhere. Uses `optimized` alias to force disable Thinking, ensuring 0 Reasoner costs. |
| **Hybrid Mode** | Complex tasks, balanced | Medium | Brain (Opus) uses **R1**, Hands (Sonnet/Haiku) use **V3**. Balanced intelligence and cost. |
| **Reasoner Mode** | Hard problems, logic heavy | High | Uses `deepseek-reasoner` (R1) everywhere. Strongest reasoning, but every operation (including reading files) is billed as R1. |

> **Note**: DeepSeek Reasoner costs 5-10x more than Chat. **Chat Mode** or **Hybrid Mode** is recommended.

Configuration is saved in `config.env` (auto-added to `.gitignore`), only affects this tool, doesn't change global settings. **To switch model provider**: run `bash claude-auto-loop/setup.sh` again, choose `y` to reconfigure.

**config.env is editable** after generation — no need to re-run setup. For example: add `CLAUDE_DEBUG=mcp` for debug logs; change `ANTHROPIC_MODEL` to switch model version.

---

## Enhancements Over the Anthropic Article

This tool builds on Anthropic's [long-running agent harness](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) with engineering-grade enhancements:

| Dimension | Anthropic Original | This Tool |
|---|---|---|
| Task status | Simple bool (`passes`) | 5-state machine (`pending` → `in_progress` → `testing` → `done` / `failed`) |
| Validation | Relies on Agent self-report | External harness hard-validation (`validate.sh`) |
| Failure handling | None | Auto git rollback + up to 3 retries |
| Project info | Hardcoded in CLAUDE.md | Auto-scanned `project_profile.json` |
| Environment init | Hand-written init.sh | Agent auto-generates after scanning |
| Structured output | None | Mandatory `session_result.json` per session (machine-readable) |
| Runtime env | Claude CLI only | Claude CLI + Cursor IDE |
| Testing tools | None | Pluggable Playwright MCP browser automation |
| Validation hooks | None | `validate.d/` hook directory, user-extensible |
| Model selection | Claude only | GLM 4.7/5, DeepSeek, and other Anthropic-compatible models |
| Requirements input | CLI one-liner argument | `requirements.md` document (specify tech stack, styles, editable anytime) |
| Progress indicator | None | PreToolUse hook switches "Thinking..." → "Coding..." + real-time activity log |
| Debug output | None | `--verbose` enabled by default + `CLAUDE_DEBUG` in config.env for mcp/api logs |
| Agent protocol loading | Agent manually Reads CLAUDE.md (may skip) | `--append-system-prompt-file` guarantees 100% injection; coding sessions inject CLAUDE.md only, scan sessions concat SCAN_PROTOCOL.md; leverages API prefix caching to reduce token cost |
| Tool constraints | Unrestricted | `--allowedTools` whitelist prevents tool misuse and hallucinated calls |
| Failure retry | Blind retry | Injects previous validation failure reason, avoids repeating the same mistake |
| Environment optimization | Full init every time | Skips init.sh on consecutive success, quick health check only |
| Task append | None | `--add` mode: lightweight task creation after all tasks complete |

---

## Reference

### File Descriptions

**Pre-packaged files** (generic, copy to any project):

| File | Description |
|---|---|
| `CLAUDE.md` | Agent protocol: hard rules + reference formats + state machine + 6-step workflow (attention-optimized: constraints at top, action instructions at bottom) |
| `SCAN_PROTOCOL.md` | Scan-only protocol: project scan steps + `project_profile.json` format + `init.sh` generation rules (injected only during first scan) |
| `run.sh` | CLI mode entry: outer loop + system prompt injection + tool whitelist + validation + rollback + retry |
| `validate.sh` | Standalone validation script: auto-called by CLI / manually run for Cursor |
| `setup.sh` | Interactive setup (model selection + MCP tool installation) |
| `cursor.mdc` | Cursor rules file: copy to `.cursor/rules/` to use |
| `requirements.example.md` | Requirements template: copy as `requirements.md` and fill in your detailed needs |
| `hooks/phase-signal.py` | PreToolUse hook: writes `.phase` (progress switch), `.phase_step` (step inference), `.activity_log` (real-time activity log) |
| `hooks-settings.json` | Claude Code hooks config, loaded via `--settings` |
| `update.sh` | Pulls latest code from upstream (exclude strategy: preserves project runtime data, syncs all core files) |
| `ARCHITECTURE.md` | Architecture doc: system overview, Mermaid diagrams, file responsibilities (for AI Agents to quickly understand the tool design) |
| `README.md` | Chinese documentation |
| `README.en.md` | This file (English documentation) |

**Runtime-generated** (project-specific, created by Agent or setup.sh):

| File | Description |
|---|---|
| `config.env` | Model + MCP config (by setup.sh; API Key, optional CLAUDE_DEBUG, gitignored) |
| `project_profile.json` | Auto-detected project metadata (tech stack, services, ports, etc.) |
| `init.sh` | Auto-generated environment init script (idempotent design) |
| `tasks.json` | Task list + state machine tracking |
| `progress.txt` | Cross-session memory log (append-only) |
| `session_result.json` | Temporary file (deleted by harness after each session) |
| `sync_state.json` | Requirements sync state (`last_requirements_hash`, etc.; created on conditional trigger) |
| `.phase` | Progress state (thinking/coding), written by hook, gitignored |
| `.phase_step` | Inferred 6-step workflow step, written by hook, gitignored |
| `.activity_log` | Real-time activity log (tool call summaries), written by hook, gitignored |
