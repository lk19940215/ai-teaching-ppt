#!/bin/bash
# ============================================================
# 从 upstream 拉取 claude-auto-loop 最新代码
#
# 用法: bash update.sh  或  bash claude-auto-loop/update.sh
#
# 策略: 排除法 — 保护项目运行时数据，其余全部更新
# 好处: upstream 新增脚本/文档/hooks 无需手动维护列表即可自动同步
#
# 会保留: config.env, tasks.json, progress.txt, project_profile.json 等项目文件
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="/tmp/claude-auto-loop-upstream-$$"
UPSTREAM="https://github.com/lk19940215/claude-auto-loop.git"

# 项目运行时数据 — 绝不覆盖（空格分隔）
SKIP_FILES="config.env tasks.json progress.txt project_profile.json init.sh session_result.json sync_state.json requirements_hash.current tests.json"
SKIP_DIRS="logs validate.d .git"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

_should_skip_file() {
    local fname="$1"
    for s in $SKIP_FILES; do
        [ "$fname" = "$s" ] && return 0
    done
    return 1
}

_should_skip_dir() {
    local dname="$1"
    for s in $SKIP_DIRS; do
        [ "$dname" = "$s" ] && return 0
    done
    return 1
}

echo "正在从 upstream 拉取最新代码..."
git clone --depth 1 "$UPSTREAM" "$TMP"

echo "正在更新核心文件..."

# 1) 复制顶层文件（排除项目数据）
for f in "$TMP"/*; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    _should_skip_file "$fname" || cp "$f" "$SCRIPT_DIR/"
done

# 2) 复制隐藏文件（.gitignore 等）
for f in "$TMP"/.[!.]*; do
    [ -f "$f" ] || continue
    cp "$f" "$SCRIPT_DIR/"
done

# 3) 同步子目录（排除项目数据目录）
for d in "$TMP"/*/; do
    [ -d "$d" ] || continue
    dname=$(basename "$d")
    _should_skip_dir "$dname" || {
        mkdir -p "$SCRIPT_DIR/$dname"
        cp -r "$d"* "$SCRIPT_DIR/$dname/" 2>/dev/null || true
    }
done

echo ""
echo "claude-auto-loop 已更新"
echo "  已保留: config.env, tasks.json, progress.txt, project_profile.json 等项目文件"
echo "  已同步: 脚本、hooks、文档、.gitignore"
