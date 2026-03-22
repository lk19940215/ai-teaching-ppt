"""
AI 处理提示词模板

每个 action 对应一套 system + user prompt。
LLM 返回结构化 JSON，通过 shape_index 映射回原始 PPTX。

slide_io_template.json 定义了通用的输入/输出数据格式，
被注入到 SYSTEM_PROMPT 中引导 AI 理解数据结构。
"""

import json
from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent / "slide_io_template.json"
_template_data = json.loads(_TEMPLATE_PATH.read_text(encoding="utf-8"))

_OUTPUT_SCHEMA = json.dumps(_template_data["output_format"], ensure_ascii=False, indent=2)
_FIELD_RULES = "\n".join(f"- **{k}**: {v}" for k, v in _template_data["field_rules"].items())

SYSTEM_PROMPT = f"""你是一个专业的教学 PPT 内容处理助手。
用户会提供 PPT 幻灯片的文本内容（格式为 【角色·shape_N】文本），你需要按照指定操作处理并返回 JSON 结果。

**数据映射机制**：
- 每个文本元素有唯一的 shape_index（如 shape_4 对应 shape_index=4）
- 你返回的修改指令必须通过 shape_index 精确定位到原始元素
- 系统会自动保留原始格式（字体、颜色、大小、粗体、动画等），你只需关注文本内容

**返回 JSON 的标准格式**：
{_OUTPUT_SCHEMA}

**字段规则**：
{_FIELD_RULES}"""


def build_prompt(slide_text: str, action: str, custom_prompt: str | None = None) -> list[dict]:
    """构建 LLM 消息列表"""
    action_prompts = {
        "polish": _build_polish_prompt,
        "expand": _build_expand_prompt,
        "rewrite": _build_rewrite_prompt,
        "extract": _build_extract_prompt,
    }

    builder = action_prompts.get(action)
    if not builder:
        raise ValueError(f"不支持的操作类型: {action}")

    return builder(slide_text, custom_prompt)


_ACTION_INSTRUCTIONS = {
    "polish": """请对以下 PPT 幻灯片内容进行**润色**：
- 优化文字表达，使语言更加流畅、专业
- 保持原意不变，不删减核心信息
- 保持段落结构，不改变元素数量
- 修改后的文本长度应与原文接近（不超过原文的 1.3 倍）
- 教学 PPT 应注重准确性、简洁性""",

    "expand": """请对以下 PPT 幻灯片内容进行**扩展**：
- 在保持原有内容的基础上，补充更多细节、示例或说明
- 扩展后的内容应自然衔接，不违和
- 教学场景下可适当补充背景知识、举例说明
- 注意：扩展后文本可能会比原文长，这是允许的""",

    "rewrite": """请对以下 PPT 幻灯片内容进行**改写**：
- 以不同的表达方式重新组织内容
- 可以调整语序、换用不同词汇、改变句式
- 核心信息和含义保持不变
- 修改后的文本长度应与原文相当""",

    "extract": """请从以下 PPT 幻灯片内容中**提取知识点**：
- 提取核心概念、关键公式、重要方法
- 将提取的内容整理为清晰的知识点列表
- 用简洁的语言概括每个知识点
- 结果写回到对应的文本框中（替换原文）""",
}


def _build_action_prompt(slide_text: str, action: str, custom_prompt: str | None) -> list[dict]:
    instruction = _ACTION_INSTRUCTIONS[action]
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""{instruction}

**幻灯片内容**：
{slide_text}
{extra}

请严格按系统提示中的 JSON 格式返回结果。只返回需要修改的元素，不需要修改的不要包含。"""},
    ]


def _build_polish_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    return _build_action_prompt(slide_text, "polish", custom_prompt)


def _build_expand_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    return _build_action_prompt(slide_text, "expand", custom_prompt)


def _build_rewrite_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    return _build_action_prompt(slide_text, "rewrite", custom_prompt)


def _build_extract_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    return _build_action_prompt(slide_text, "extract", custom_prompt)


def build_merge_prompt(slide_texts: list[str], custom_prompt: str | None = None) -> list[dict]:
    """构建多页融合的提示词"""
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    slides_str = ""
    for i, text in enumerate(slide_texts):
        slides_str += f"\n--- 第 {i+1} 页 ---\n{text}\n"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请将以下多页 PPT 的内容进行**融合**：
- 将多页内容合并整理为一页的内容
- 去除重复信息，保留所有不重复的要点
- 内容组织要有逻辑性和层次感
- 输出的文本应适合放入一页幻灯片

**多页内容**：
{slides_str}
{extra}

**返回 JSON 格式**：
```json
{{
  "merged_title": "融合后的标题",
  "merged_content": "融合后的正文内容（用换行分段）",
  "summary": "融合说明"
}}
```"""},
    ]
