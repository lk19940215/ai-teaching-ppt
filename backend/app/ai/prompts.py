"""
AI 处理提示词 — 统一模板加载器

prompt_template.md 是唯一的 AI 协议文档，定义了：
  - 输入格式（format_for_ai 的输出如何被 AI 理解）
  - 输出格式（AI 返回的 JSON 结构）
  - 字段规则与铁律

本文件的职责：
  1. 加载 prompt_template.md 作为 system prompt
  2. 根据 action 注入对应的操作指导到 {{action_instruction}} 占位符
  3. 构建完整的 messages 列表
"""

from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent / "prompt_template.md"
_TEMPLATE_RAW = _TEMPLATE_PATH.read_text(encoding="utf-8")

ACTION_INSTRUCTIONS: dict[str, str] = {
    "polish": """请对幻灯片内容进行**润色**：
- 优化文字表达，使语言更加流畅、专业
- 保持原意不变，不删减核心信息
- 保持段落结构，不改变元素数量
- 修改后的文本长度应与原文接近（不超过原文的 1.3 倍）
- 教学 PPT 应注重准确性、简洁性""",

    "expand": """请对幻灯片内容进行**扩展**：
- 在保持原有内容的基础上，补充更多细节、示例或说明
- 扩展后的内容应自然衔接，不违和
- 教学场景下可适当补充背景知识、举例说明
- 扩展后文本可能比原文长，这是允许的""",

    "rewrite": """请对幻灯片内容进行**改写**：
- 以不同的表达方式重新组织内容
- 可以调整语序、换用不同词汇、改变句式
- 核心信息和含义保持不变
- 修改后的文本长度应与原文相当""",

    "extract": """请从幻灯片内容中**提取知识点**：
- 提取核心概念、关键公式、重要方法
- 将提取的内容整理为清晰的知识点列表
- 用简洁的语言概括每个知识点
- 结果写回到对应的文本框中（替换原文）""",
}


def _build_system_prompt(action: str) -> str:
    """将 action 对应的指导注入到模板的 {{action_instruction}} 占位符"""
    instruction = ACTION_INSTRUCTIONS.get(action, "")
    return _TEMPLATE_RAW.replace("{{action_instruction}}", instruction)


def build_prompt(slide_text: str, action: str, custom_prompt: str | None = None) -> list[dict]:
    """构建 LLM 消息列表 — 唯一入口"""
    if action not in ACTION_INSTRUCTIONS:
        raise ValueError(f"不支持的操作类型: {action}，可选: {list(ACTION_INSTRUCTIONS.keys())}")

    system_prompt = _build_system_prompt(action)
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""**幻灯片内容**：
{slide_text}
{extra}

请严格按协议中的 JSON 格式返回结果。只返回需要修改的元素。"""},
    ]


