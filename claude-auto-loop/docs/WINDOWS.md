# Windows 兼容性规则

本文档记录 claude-auto-loop 在 Windows 上的兼容性问题根因、设计原则和编码规范。  
所有修改 `.sh` 脚本的 PR 必须遵循本文档的规则。

---

## 两层 Bash 环境模型

Windows 上存在两个完全不同的 bash 执行环境，这是所有兼容性问题的根源：

```
┌─────────────────────────────────────────────────────┐
│ 第一层：用户入口 bash（完整 MSYS 环境）              │
│                                                     │
│ 触发方式：loop.bat → Git Bash (bash.exe)            │
│ 执行脚本：run.sh / setup.sh / validate.sh           │
│                                                     │
│ 可用命令：cygpath, source activate, pip, git,       │
│           以及所有 MSYS 工具链                       │
│ PATH：    包含 Git/usr/bin, Git/mingw64/bin 等      │
│ OSTYPE：  msys                                      │
│ EXEPATH： E:\Git\bin（Git Bash 安装目录）            │
└─────────────────────────────────────────────────────┘
                        ↓
            run.sh 调用 claude CLI
                        ↓
┌─────────────────────────────────────────────────────┐
│ 第二层：Claude Code 内部 bash（受限环境）            │
│                                                     │
│ 触发方式：Agent 使用 Bash tool 执行命令              │
│ 执行脚本：init.sh / Agent 自行编写的任何 bash 命令   │
│                                                     │
│ 不可用命令：cygpath ❌, source activate ❌           │
│             pip (独立命令) ❌                        │
│ 可用命令：  基本 Unix 工具, python/python3,          │
│             node, npm, pnpm, git                    │
│ 已知 Bug：  #9883 (cygpath), #20118, #26486         │
│ 注意：     此环境可能随 Claude Code 版本变化          │
└─────────────────────────────────────────────────────┘
```

**核心原则：`init.sh` 和所有 Agent 会执行的脚本，必须在第二层环境下可运行。**

---

## 编码规范

### 1. Python 虚拟环境：不用 source activate

`source .venv/Scripts/activate` 依赖 `cygpath`，在第二层 bash 中必然失败。

```bash
# ❌ 错误 — 依赖 cygpath，在 Claude Code Bash tool 中崩溃
source .venv/Scripts/activate
pip install -r requirements.txt

# ✅ 正确 — 直接用 venv 内的 python，不需要 activate
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

规则：**永远用 `.venv/Scripts/python.exe`（Windows）或 `.venv/bin/python`（Unix）的绝对路径调用 python，通过 `-m pip`、`-m uvicorn` 等方式执行模块，不依赖 activate。**

推荐写法：

```bash
if [ "$IS_WINDOWS" = true ]; then
    PIP_CMD=".venv/Scripts/python.exe -m pip"
    PYTHON_VENV=".venv/Scripts/python.exe"
else
    PIP_CMD=".venv/bin/python -m pip"
    PYTHON_VENV=".venv/bin/python"
fi

$PIP_CMD install -r requirements.txt
$PYTHON_VENV -m uvicorn app.main:app --port 8000
```

### 2. 路径格式：只用正斜杠

```bash
# ❌ 错误 — 反斜杠在 bash 中是转义符
cd backend\app

# ❌ 错误 — 混合斜杠
"E:\Git\bin/bash.exe"

# ✅ 正确 — 统一正斜杠
cd backend/app

# ✅ 正确 — 需要 Windows 原生路径时用 cygpath（仅在第一层可用）
export CLAUDE_CODE_GIT_BASH_PATH="$(cygpath -w "$EXEPATH/bash.exe")"
```

### 3. 命令检测：先检测后使用

```bash
# ❌ 错误 — 假设 python3 存在
python3 -m venv .venv

# ✅ 正确 — 通过 _env.sh 提供的 $PYTHON_CMD
$PYTHON_CMD -m venv .venv
```

### 4. 服务启动：从正确目录用正确的 python

```bash
# ❌ 错误 — Agent 可能在项目根目录执行，uvicorn 找不到 app.main
uvicorn app.main:app --port 8000

# ❌ 错误 — Windows 反斜杠路径
cd backend && ..\.venv\Scripts\python.exe -m uvicorn ...

# ✅ 正确
cd backend && ../.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
```

---

## 受限 Bash 环境不可用命令清单

以下命令在 Claude Code 的 Bash tool 中**不可用**或**行为异常**：

| 命令 | 状态 | 替代方案 |
|------|------|----------|
| `cygpath` | 不可用 | 手动拼路径或在第一层 `_env.sh` 中预处理 |
| `source .venv/Scripts/activate` | 崩溃（依赖 cygpath） | 直接用 `.venv/Scripts/python.exe` |
| `pip`（独立命令） | activate 失败后不可用 | `.venv/Scripts/python.exe -m pip` |
| `python3` | 可能指向 Windows Store 桩 | 用 `$PYTHON_CMD` 或 `.venv/Scripts/python.exe` |
| 管道 stdout 重定向 | 可能失败 (#26486) | 简单命令优先，避免复杂管道 |

以下命令通常**可用**：

| 命令 | 说明 |
|------|------|
| `python` / `python.exe` | Anaconda 或官方安装器 |
| `node` / `npm` / `pnpm` | Node.js 工具链 |
| `git` | 基本 git 操作 |
| `curl` | HTTP 请求 |
| `ls` / `cat` / `grep` / `echo` | 基本 Unix 工具 |
| `cd` / `mkdir` / `rm` / `cp` | 文件操作 |

---

## 脚本分类与环境对应

| 脚本 | 执行者 | 执行环境 | 兼容要求 |
|------|--------|----------|----------|
| `run.sh` | 用户 (via loop.bat) | 第一层（完整 MSYS） | 可用 cygpath 等 |
| `setup.sh` | 用户 (via loop.bat) | 第一层（完整 MSYS） | 可用 cygpath 等 |
| `validate.sh` | run.sh 内部调用 | 第一层（完整 MSYS） | 可用 cygpath 等 |
| `update.sh` | 用户 (via loop.bat) | 第一层（完整 MSYS） | 可用 cygpath 等 |
| `_env.sh` | 被上述脚本 source | 第一层（完整 MSYS） | 可用 cygpath 等 |
| **`init.sh`** | **Agent (Bash tool)** | **第二层（受限）** | **必须绕过 cygpath** |
| **Agent 临时命令** | **Agent (Bash tool)** | **第二层（受限）** | **必须绕过 cygpath** |

---

## 测试规范

修改任何 `.sh` 脚本后，必须在以下两个环境中验证：

1. **第一层验证**（用户入口）：
   ```powershell
   claude-auto-loop\loop.bat run --max 0
   ```
   确认 `run.sh` 正常启动，不报 python/bash 错误。

2. **第二层验证**（Agent 内部）：
   ```
   # 在 Claude Code 交互模式中测试
   claude
   > bash claude-auto-loop/init.sh
   ```
   确认 `init.sh` 在 Claude Code 的 Bash tool 中不报 cygpath/pip 错误。

---

## 参考资料

- [Claude Code #9883](https://github.com/anthropics/claude-code/issues/9883) — Bash tool 不兼容 MSYS/Git Bash（cygpath 缺失）
- [Claude Code #20118](https://github.com/anthropics/claude-code/issues/20118) — PowerShell 中 cygpath command not found
- [Claude Code #26486](https://github.com/anthropics/claude-code/issues/26486) — Git Bash MSYS2 管道 stdout 损坏
- [Claude Code #16602](https://github.com/anthropics/claude-code/issues/16602) — CLAUDE_CODE_GIT_BASH_PATH 文档缺失
- [Claude Code #25593](https://github.com/anthropics/claude-code/issues/25593) — 安装后仍报 requires git-bash
