#!/bin/bash
# ============================================================
# 共享环境引导 — 被所有 .sh 脚本 source
#
# 提供:
#   $PYTHON_CMD   — 检测后的 Python 命令 (python3 或 python)
#   $IS_WINDOWS   — 是否 Windows 环境 (Git Bash / MSYS / Cygwin)
#   颜色常量      — RED / GREEN / YELLOW / BLUE / NC
#
# 用法 (在各 .sh 脚本顶部):
#   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
#   source "$SCRIPT_DIR/_env.sh"
# ============================================================

# ============ 操作系统检测 ============
# 第一层 bash (Git Bash) 有 OSTYPE=msys；第二层 (Claude Code 内部 bash) 可能没有，
# 所以用 WINDIR/COMSPEC 环境变量作为后备检测（见 docs/WINDOWS.md 两层模型）
IS_WINDOWS=false
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
elif [ -n "${WINDIR:-}" ] || [ -n "${COMSPEC:-}" ]; then
    IS_WINDOWS=true
fi

# ============ Python 命令检测 ============
if [ -z "${PYTHON_CMD:-}" ]; then
    if command -v python3 &> /dev/null && python3 --version &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null && python --version &> /dev/null; then
        PYTHON_CMD="python"
    else
        PYTHON_CMD=""
    fi
fi

# ============ Windows: Claude Code 需要 Git Bash 路径 ============
if [ "$IS_WINDOWS" = true ] && [ -z "${CLAUDE_CODE_GIT_BASH_PATH:-}" ]; then
    if [ -n "${EXEPATH:-}" ] && [ -f "$EXEPATH/bash.exe" ]; then
        # EXEPATH 是 Git Bash 特有变量（仅第一层可用）
        # cygpath 仅在完整 MSYS 环境中可用，需先检测（见 docs/WINDOWS.md）
        if command -v cygpath &> /dev/null; then
            export CLAUDE_CODE_GIT_BASH_PATH="$(cygpath -w "$EXEPATH/bash.exe")"
        else
            export CLAUDE_CODE_GIT_BASH_PATH="$EXEPATH/bash.exe"
        fi
    else
        for _p in "/c/Program Files/Git/bin/bash.exe" "/c/Program Files (x86)/Git/bin/bash.exe"; do
            if [ -f "$_p" ]; then
                export CLAUDE_CODE_GIT_BASH_PATH="$_p"
                break
            fi
        done
        unset _p
    fi
fi

# ============ 颜色常量 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
