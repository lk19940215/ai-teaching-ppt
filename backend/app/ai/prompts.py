"""
AI 处理提示词模板

每个 action 对应一套 system + user prompt。
LLM 返回结构化 JSON，通过 shape_index 映射回原始 PPTX。
"""


SYSTEM_PROMPT = """你是一个专业的 PPT 内容处理助手。
用户会提供 PPT 幻灯片的文本内容，你需要按照指定操作处理并返回 JSON 结果。

**返回格式要求**：
1. 必须返回合法的 JSON 对象
2. 每个修改通过 shape_index 对应到原始元素
3. 不要修改 shape_index 的值，保持与输入一致
4. 如果某个元素不需要修改，不要包含在结果中
5. 表格单元格通过 row 和 col 索引定位"""


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


def _build_polish_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请对以下 PPT 幻灯片内容进行**润色**：
- 优化文字表达，使语言更加流畅自然
- 保持原意不变，不删减核心信息
- 保持段落结构，不改变元素数量
- 修改后的文本长度应与原文接近（不超过原文的 1.3 倍）

**幻灯片内容**：
{slide_text}
{extra}

**返回 JSON 格式**：
```json
{{
  "text_blocks": [
    {{"shape_index": 0, "new_text": "润色后的文字"}},
    {{"shape_index": 2, "new_text": "润色后的文字"}}
  ],
  "table_cells": [
    {{"shape_index": 1, "row": 0, "col": 1, "new_text": "润色后的单元格"}}
  ],
  "summary": "简要说明做了哪些润色"
}}
```

只返回需要修改的元素，不需要修改的不要包含。"""},
    ]


def _build_expand_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请对以下 PPT 幻灯片内容进行**扩展**：
- 在保持原有内容的基础上，补充更多细节、示例或说明
- 扩展后的内容应自然衔接，不违和
- 每个文本块可以适当增加内容
- 注意：扩展后文本可能会比原文长，这是允许的

**幻灯片内容**：
{slide_text}
{extra}

**返回 JSON 格式**：
```json
{{
  "text_blocks": [
    {{"shape_index": 0, "new_text": "扩展后的文字"}},
    {{"shape_index": 2, "new_text": "扩展后的文字（含新增内容）"}}
  ],
  "table_cells": [
    {{"shape_index": 1, "row": 1, "col": 1, "new_text": "扩展后的单元格内容"}}
  ],
  "summary": "简要说明扩展了哪些内容"
}}
```"""},
    ]


def _build_rewrite_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请对以下 PPT 幻灯片内容进行**改写**：
- 以不同的表达方式重新组织内容
- 可以调整语序、换用不同词汇、改变句式
- 核心信息和含义保持不变
- 修改后的文本长度应与原文相当

**幻灯片内容**：
{slide_text}
{extra}

**返回 JSON 格式**：
```json
{{
  "text_blocks": [
    {{"shape_index": 0, "new_text": "改写后的文字"}},
    {{"shape_index": 2, "new_text": "改写后的文字"}}
  ],
  "table_cells": [
    {{"shape_index": 1, "row": 0, "col": 0, "new_text": "改写后的单元格"}}
  ],
  "summary": "简要说明改写了哪些内容"
}}
```"""},
    ]


def _build_extract_prompt(slide_text: str, custom_prompt: str | None) -> list[dict]:
    extra = f"\n\n用户额外要求：{custom_prompt}" if custom_prompt else ""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请从以下 PPT 幻灯片内容中**提取知识点**：
- 提取核心概念、关键公式、重要方法
- 将提取的内容整理为清晰的知识点列表
- 用简洁的语言概括每个知识点
- 结果写回到对应的文本框中（替换原文）

**幻灯片内容**：
{slide_text}
{extra}

**返回 JSON 格式**：
```json
{{
  "text_blocks": [
    {{"shape_index": 0, "new_text": "知识点标题"}},
    {{"shape_index": 2, "new_text": "【知识点1】概念说明\\n【知识点2】公式方法\\n【知识点3】注意事项"}}
  ],
  "summary": "提取了 N 个核心知识点"
}}
```"""},
    ]


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
