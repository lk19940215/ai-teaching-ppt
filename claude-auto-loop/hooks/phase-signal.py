#!/usr/bin/env python3
"""PreToolUse hook: 从 stdin JSON 推断 CLAUDE.md 6 步流程，写入 .phase 和 .phase_step

同时追加工具调用摘要到 .activity_log，供 run.sh 进度指示器展示最近活动。

设计原则：步骤 1（恢复上下文）和 2（环境检查）仅在会话初期出现。
一旦进入 4/5/6，不再因 Read 或 curl 误判回退到 1/2。
"""
import json
import os
import re
import sys
from datetime import datetime

_EARLY_STEPS = ("1-恢复上下文", "2-环境检查")


def _allow_early_step_overwrite(step_file: str, new_step: str) -> bool:
    """仅当新步骤为 1/2 且当前为早期或空时，允许写入"""
    if new_step not in _EARLY_STEPS:
        return True
    try:
        with open(step_file) as f:
            current = f.read().strip()
    except OSError:
        return True
    return not current or current in _EARLY_STEPS


def _extract_summary(tool_name: str, tool_input: dict, cwd: str) -> str:
    """从工具调用中提取可读摘要"""
    if tool_name in ("Read", "Edit", "Write"):
        raw = (tool_input.get("path") or tool_input.get("file_path") or "").strip()
        if cwd and raw.startswith(cwd):
            return raw[len(cwd):].lstrip("/")
        parts = raw.replace("\\", "/").rsplit("/", 3)
        return "/".join(parts[-3:]) if len(parts) > 3 else raw
    if tool_name == "Bash":
        return (tool_input.get("command") or "").strip()[:60]
    if tool_name in ("Glob", "Grep"):
        return (tool_input.get("pattern") or tool_input.get("glob_pattern") or "")[:40]
    return ""


def _write_activity(loop_dir: str, tool_name: str, summary: str):
    """追加一行活动日志；超过 200 行时截断保留最新 100 行"""
    log_file = os.path.join(loop_dir, ".activity_log")
    ts = datetime.now().strftime("%H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{ts}|{tool_name}|{summary}\n")
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
        if len(lines) > 200:
            with open(log_file, "w") as f:
                f.writelines(lines[-100:])
    except OSError:
        pass


try:
    d = json.load(sys.stdin)
    cwd = d.get("cwd", "")
    tool_name = d.get("tool_name", "")
    tool_input = d.get("tool_input", {}) or {}
    if not cwd or not os.path.isdir(cwd):
        sys.exit(0)
    loop_dir = os.path.join(cwd, "claude-auto-loop")
    if not os.path.isdir(loop_dir):
        sys.exit(0)

    # --- 活动日志 ---
    summary = _extract_summary(tool_name, tool_input, cwd)
    _write_activity(loop_dir, tool_name, summary)

    # --- 步骤推断 ---
    phase_file = os.path.join(loop_dir, ".phase")
    step_file = os.path.join(loop_dir, ".phase_step")
    step = None
    if tool_name == "Bash":
        cmd = (tool_input.get("command") or "").strip()
        if re.search(r"git\s+(add|commit)", cmd, re.I):
            step = "6-收尾"
        elif re.search(r"init\.sh", cmd):
            # 仅 init.sh 为环境检查；curl 测 /posts 等为 step 5，避免误判
            step = "2-环境检查"
        elif re.search(r"(npm\s+test|pytest|jest|vitest|curl\s|browser_)", cmd, re.I):
            step = "5-测试验证"
        else:
            step = "4-增量实现"
    elif tool_name in ("Read", "Edit", "Write"):
        path = (tool_input.get("path") or tool_input.get("file_path") or "").strip()
        path_lower = path.lower().replace("\\", "/")
        if (
            "project_profile.json" in path_lower
            or "progress.txt" in path_lower
            or "tasks.json" in path_lower
            or "requirements.md" in path_lower
        ):
            if tool_name == "Read":
                step = "1-恢复上下文"
            elif "progress.txt" in path_lower or "session_result.json" in path_lower:
                step = "6-收尾"
            elif "tasks.json" in path_lower and tool_name != "Read":
                step = "3-选择任务"
            else:
                step = "1-恢复上下文"
        elif "session_result.json" in path_lower:
            step = "6-收尾"
        elif any(
            p in path_lower
            for p in [
                "/src/",
                "/components/",
                "/lib/",
                "\\src\\",
                "\\components\\",
                "\\lib\\",
                "src/",
                "components/",
                "lib/",
            ]
        ):
            step = "4-增量实现"
        elif tool_name == "Read":
            step = "1-恢复上下文"
        elif tool_name in ("Edit", "Write"):
            step = "4-增量实现"
    elif tool_name and tool_name.startswith("mcp__"):
        if "browser" in tool_name.lower() or "playwright" in tool_name.lower():
            step = "5-测试验证"
        else:
            step = "4-增量实现"
    if step:
        if _allow_early_step_overwrite(step_file, step):
            with open(step_file, "w") as f:
                f.write(step)
    with open(phase_file, "w") as f:
        f.write("coding")
except Exception:
    pass
