"""
AI 提示词 — 多槽位注入引擎

架构：
  prompt_template.md     通用 PPT 处理协议（格式 + Schema + 约束）
  domains/*.md           领域预设（学科/年级/风格，可热更新）
  operations/*.md        操作预设（润色/扩展/改写/提取）

注入槽位：
  {{domain_context}}       ← 从 domains/*.md 加载
  {{operation_guide}}      ← 从 operations/*.md 加载
  {{custom_instructions}}  ← 用户自由输入（Web UI 传入）

扩展方式：
  1. 新增学科：在 domains/ 下添加 .md 文件
  2. 新增操作：在 operations/ 下添加 .md 文件
  3. Web UI 交互：通过 custom_instructions 注入动态提示词
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_AI_DIR = Path(__file__).parent
_TEMPLATE_PATH = _AI_DIR / "prompt_template.md"
_DOMAINS_DIR = _AI_DIR / "domains"
_OPERATIONS_DIR = _AI_DIR / "operations"

_TEMPLATE_RAW = _TEMPLATE_PATH.read_text(encoding="utf-8")


def _load_md(directory: Path, name: str, fallback: str = "") -> str:
    """从目录加载 .md 文件内容，找不到时返回 fallback"""
    path = directory / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    logger.warning(f"预设文件不存在: {path}")
    return fallback


def list_operations() -> list[str]:
    """列出所有可用的操作预设"""
    if not _OPERATIONS_DIR.exists():
        return []
    return sorted(
        p.stem for p in _OPERATIONS_DIR.glob("*.md")
    )


def _build_system_prompt(
    action: str,
    domain: Optional[str] = None,
    custom_instructions: Optional[str] = None,
) -> str:
    """
    构建完整的 system prompt，填充所有注入槽位。

    注入顺序（对应模板中的占位符）：
      1. {{domain_context}}      ← domain 参数指定的领域规则
      2. {{operation_guide}}     ← action 对应的操作指导
      3. {{custom_instructions}} ← 用户自由输入
    """
    domain_key = domain or "_default"
    domain_content = _load_md(_DOMAINS_DIR, domain_key,
                              fallback=_load_md(_DOMAINS_DIR, "_default"))

    operation_content = _load_md(_OPERATIONS_DIR, action,
                                 fallback=f"请对幻灯片内容执行 {action} 操作。")

    custom = custom_instructions.strip() if custom_instructions else "（无）"

    prompt = _TEMPLATE_RAW
    prompt = prompt.replace("{{domain_context}}", domain_content)
    prompt = prompt.replace("{{operation_guide}}", operation_content)
    prompt = prompt.replace("{{custom_instructions}}", custom)

    return prompt


def build_prompt(
    slide_text: str,
    action: str,
    domain: Optional[str] = None,
    custom_prompt: Optional[str] = None,
) -> list[dict]:
    """
    构建 LLM 消息列表 — 唯一入口。

    Args:
        slide_text: format_for_ai() 生成的标签化文本
        action:     操作类型（对应 operations/*.md 的文件名）
        domain:     领域预设名（对应 domains/*.md 的文件名，None 则用 _default）
        custom_prompt: 用户自由输入的补充要求

    Returns:
        [{"role": "system", ...}, {"role": "user", ...}]
    """
    op_file = _OPERATIONS_DIR / f"{action}.md"
    if not op_file.exists():
        available = list_operations()
        raise ValueError(
            f"不支持的操作类型: {action}，可选: {available}"
        )

    system_prompt = _build_system_prompt(action, domain, custom_prompt)

    if action == "fuse":
        user_suffix = (
            "请严格按协议中的 JSON 格式返回结果。"
            "你**必须**创建新页面（is_new: true），将上述多页内容融合为全新的、有组织的内容。"
            "**不要修改已有页面**，只创建新页面。"
            "每个body_texts条目是一个独立板块，格式：\"板块标题:\\n• 要点1\\n• 要点2\"。"
            "控制每页3-5个板块，每个板块不超过5行。"
        )
    else:
        user_suffix = "请严格按协议中的 JSON 格式返回结果。只返回需要修改的元素。"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": (
            f"**幻灯片内容**：\n{slide_text}\n\n{user_suffix}"
        )},
    ]
