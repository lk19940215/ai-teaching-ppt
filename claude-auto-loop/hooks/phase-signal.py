#!/usr/bin/env python3
"""PreToolUse hook: 从 stdin JSON 推断 CLAUDE.md 6 步流程，写入 .phase 和 .phase_step

设计原则：步骤 1（恢复上下文）和 2（环境检查）仅在会话初期出现。
一旦进入 4/5/6，不再因 Read 或 curl 误判回退到 1/2。
"""
import json
import os
import re
import sys

# 步骤 1、2 仅在「早期阶段」可覆盖；进入 4/5/6 后不再回退
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
