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
IS_WINDOWS=false
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]] || [[ "$OSTYPE" == "cygwin" ]]; then
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

# ============ 颜色常量 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
