# -*- coding: utf-8 -*-
"""
PPT AI 合并提示词模板
针对教学场景优化的提示词

设计文档：.claude-coder/plans/ppt-merge-technical-design.md#3-ai-融合策略
"""

# ==================== 系统提示词 ====================

SYSTEM_PROMPT_MERGE_EXPERT = """你是一位专业的教学课件融合专家。你能够理解 PPT 的教学内容，并根据用户需求生成最优的融合方案。

## 你的能力
1. 理解教学内容的逻辑结构和知识点关系
2. 识别重复、冗余和互补的内容
3. 保持教学逻辑连贯性
4. 生成清晰可执行的融合方案

## 输出格式
请严格输出 JSON 格式，不要包含其他文字。"""

# ==================== 整体合并提示词 ====================

FULL_MERGE_SYSTEM_PROMPT = SYSTEM_PROMPT_MERGE_EXPERT + """

## 整体合并任务
分析两个完整的 PPT，生成合并计划。

## 输出格式
```json
{
  "merge_strategy": "合并策略说明",
  "summary": "合并后的课件概述",
  "knowledge_points": ["涉及的知识点列表"],
  "slide_plan": [
    {
      "action": "keep|merge|create|skip",
      "source": "A|B",
      "slide_index": 页码，
      "sources": [{"source": "A", "slide": 1}, {"source": "B", "slide": 2}],
      "new_content": "新页面内容（仅 create/merge 时）",
      "instruction": "处理指令",
      "reason": "原因说明"
    }
  ]
}
```

## action 说明
- keep: 保留原页
- merge: 合并多页内容
- create: 创建新页面（如总结页、练习页）
- skip: 跳过不使用

## 合并原则
1. 避免重复：相似知识点只保留一份
2. 逻辑连贯：保持教学流程顺畅
3. 互补增强：A 和 B 的互补内容应融合
4. 用户优先：尊重用户的明确指令"""

# ==================== 单页处理提示词 ====================

SINGLE_PAGE_SYSTEM_PROMPT = SYSTEM_PROMPT_MERGE_EXPERT + """

## 单页处理任务
对单个页面执行润色、扩展、改写或提取操作。

## 支持的动作
- polish: 润色文字，使表达更加流畅
- expand: 扩展内容，增加更多细节和例子
- rewrite: 改写风格，调整语言风格
- extract: 提取知识点，总结关键信息

## 输出格式
```json
{
  "action": "polish|expand|rewrite|extract",
  "original_summary": "原内容摘要",
  "new_content": {
    "title": "标题",
    "main_points": ["要点 1", "要点 2"],
    "additional_content": "扩展内容（如有）"
  },
  "changes": ["修改说明 1", "修改说明 2"]
}
```"""

# ==================== 多页融合提示词 ====================

PARTIAL_MERGE_SYSTEM_PROMPT = SYSTEM_PROMPT_MERGE_EXPERT + """

## 多页融合任务
融合选中的多个页面，生成新页面。

## 输出格式
```json
{
  "merge_strategy": "融合策略说明",
  "content_relationship": "页面内容关系分析",
  "new_slide": {
    "title": "融合后的标题",
    "slide_type": "content_slide|concept_slide|example_slide|exercise_slide",
    "teaching_role": "concept|example|exercise|summary",
    "elements": [
      {"type": "title", "content": "标题内容"},
      {"type": "text_body", "content": "正文内容"},
      {"type": "list_item", "content": "列表项"}
    ]
  },
  "preserved_from_a": ["保留自 A 的内容"],
  "preserved_from_b": ["保留自 B 的内容"]
}
```

## 融合原则
1. 保持知识点完整性
2. 避免内容重复
3. 逻辑顺序合理
4. 语言风格统一"""

# ==================== 预设合并策略模板 ====================

MERGE_STRATEGY_TEMPLATES = {
    "knowledge_integration": """
## 知识点整合策略
适用场景：两个 PPT 讲解同一主题的不同方面

策略说明：
1. 识别两份课件的核心知识点
2. 合并相似知识点，保留最完整的版本
3. 互补知识点按逻辑顺序排列
4. 创建综合练习页面
""",

    "difficulty_gradient": """
## 难度递进策略
适用场景：一份课件基础、一份课件进阶

策略说明：
1. 保留基础内容作为前半部分
2. 进阶内容作为后半部分
3. 添加过渡页面连接两个难度层级
4. 创建分层练习题
""",

    "example_enhancement": """
## 例题增强策略
适用场景：一份课件重概念、一份课件重例题

策略说明：
1. 保留概念讲解部分
2. 融合双方的例题
3. 按难度梯度排列例题
4. 添加变式练习
""",

    "cross_subject": """
## 跨学科融合策略
适用场景：不同学科的课件融合（如数学 + 物理）

策略说明：
1. 识别跨学科的共同知识点
2. 以一方为主干，另一方为补充
3. 标注学科交叉点
4. 创建综合应用题
""",

    "review_synthesis": """
## 复习综合策略
适用场景：多份复习课件整合

策略说明：
1. 按知识模块重组内容
2. 合并重复的知识点总结
3. 整合各方的典型例题
4. 创建综合测试页面
"""
}

# ==================== 提示词构建函数 ====================

def build_full_merge_prompt(
    doc_a_summary: list,
    doc_b_summary: list,
    file_a_name: str,
    file_b_name: str,
    custom_prompt: str = ""
) -> str:
    """构建整体合并提示词"""

    a_summary_str = "\n".join([
        f"  - 第{item['index'] + 1}页 [{item['type']}]: {item.get('title', '')} - {'; '.join(item.get('main_points', [])[:3])}"
        for item in doc_a_summary
    ])

    b_summary_str = "\n".join([
        f"  - 第{item['index'] + 1}页 [{item['type']}]: {item.get('title', '')} - {'; '.join(item.get('main_points', [])[:3])}"
        for item in doc_b_summary
    ])

    prompt = f"""## PPT A 概览
文件名：{file_a_name}
总页数：{len(doc_a_summary)}

### 页面摘要
{a_summary_str}

## PPT B 概览
文件名：{file_b_name}
总页数：{len(doc_b_summary)}

### 页面摘要
{b_summary_str}

## 用户需求
{custom_prompt if custom_prompt else "请根据两份课件的内容，生成最优的合并方案。保留核心知识点，避免重复内容。"}

请生成合并计划 JSON。"""

    return prompt


def build_single_page_prompt(
    slide_content: dict,
    action: str,
    custom_prompt: str = ""
) -> str:
    """构建单页处理提示词"""

    action_descriptions = {
        "polish": "润色文字，使表达更加流畅自然",
        "expand": "扩展内容，增加更多细节、例子或解释",
        "rewrite": "改写风格，调整语言表达方式",
        "extract": "提取知识点，总结关键信息"
    }

    content_str = f"""
页面标题：{slide_content.get('title', '无标题')}
页面类型：{slide_content.get('slide_type', 'unknown')}
教学角色：{slide_content.get('teaching_role', 'unknown')}

### 页面内容元素：
"""

    for elem in slide_content.get('elements', []):
        elem_type = elem.get('type', 'unknown')
        content = elem.get('content', elem.get('text', ''))[:200]
        content_str += f"- [{elem_type}] {content}\n"

    prompt = f"""## 页面信息
{content_str}

## 处理任务
动作：{action}
说明：{action_descriptions.get(action, '')}

## 用户要求
{custom_prompt if custom_prompt else "请按照动作要求处理页面内容。"}

请生成处理结果 JSON。"""

    return prompt


def build_pages_merge_prompt(
    pages_a: list,
    pages_b: list,
    custom_prompt: str = ""
) -> str:
    """构建多页融合提示词"""

    def format_pages(pages, label):
        result = f"## {label} 选中页面 ({len(pages)} 页)\n"
        for i, page in enumerate(pages):
            result += f"\n### 第{i + 1}页\n"
            result += f"类型：{page.get('slide_type', 'unknown')}\n"
            result += f"标题：{page.get('title', '无标题')}\n"
            for elem in page.get('elements', [])[:3]:
                content = elem.get('content', elem.get('text', ''))[:100]
                result += f"- {elem.get('type', 'unknown')}: {content}\n"
        return result

    prompt = f"""
{format_pages(pages_a, 'PPT A')}

{format_pages(pages_b, 'PPT B')}

## 用户需求
{custom_prompt if custom_prompt else "请融合以上页面内容，生成新的页面。"}

请生成融合结果 JSON。"""

    return prompt
