import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from app.ai.prompts import build_prompt, ACTION_INSTRUCTIONS

print("=== 支持的操作 ===")
for k in ACTION_INSTRUCTIONS:
    print(f"  - {k}")

for action in ACTION_INSTRUCTIONS:
    msgs = build_prompt("test content", action)
    sys_content = msgs[0]["content"]

    sections = ["## 你的角色", "## 数据映射", "## 输入格式", "## 输出格式", "## 操作指导"]
    missing = [s for s in sections if s not in sys_content]
    placeholder_ok = "{{action_instruction}}" not in sys_content

    print(f"\n--- {action} ---")
    print(f"  system prompt: {len(sys_content)} 字")
    print(f"  placeholder replaced: {placeholder_ok}")
    if missing:
        print(f"  MISSING sections: {missing}")
    else:
        print(f"  all sections present: OK")
    assert placeholder_ok, f"{action}: placeholder not replaced!"
    assert not missing, f"{action}: missing sections: {missing}"

print("\n=== ALL CHECKS PASSED ===")
