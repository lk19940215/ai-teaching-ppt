#!/bin/bash
# ============================================================
# 从 upstream 拉取 claude-auto-loop 最新代码
#
# 用法: bash update.sh  或  bash claude-auto-loop/update.sh
#
# 会覆盖: CLAUDE.md, run.sh, setup.sh, validate.sh 等核心脚本
# 会保留: config.env, tasks.json, progress.txt, project_profile.json 等项目文件
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="/tmp/claude-auto-loop-upstream-$$"
UPSTREAM="https://github.com/lk19940215/claude-auto-loop.git"

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

echo "正在从 upstream 拉取最新代码..."
git clone --depth 1 "$UPSTREAM" "$TMP"

echo "正在更新核心文件..."
cp "$TMP"/{CLAUDE.md,README.md,README.en.md,SCAN_PROTOCOL.md,run.sh,setup.sh,validate.sh,cursor.mdc,requirements.example.md,hooks-settings.json} "$SCRIPT_DIR/"

mkdir -p "$SCRIPT_DIR/hooks"
cp -r "$TMP"/hooks/* "$SCRIPT_DIR/hooks/"

echo "claude-auto-loop 已更新（config.env、tasks.json、progress.txt 等项目文件已保留）"
