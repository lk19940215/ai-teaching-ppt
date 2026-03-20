# -*- coding: utf-8 -*-
"""
PPT AI 合并提示词模板 - 教学场景优化版

设计文档：.claude-coder/plans/ppt-merge-technical-design.md#3-ai-融合策略

模板结构：
- 系统提示：角色定义 + 能力描述 + 输出格式规范
- 用户提示：具体任务 + 上下文数据 + 用户需求
- 自定义覆盖：用户可通过 custom_prompt 覆盖默认需求描述
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ==================== 枚举定义 ====================

class MergeType(Enum):
    """合并类型"""
    FULL = "full"              # 整体合并
    PARTIAL = "partial"        # 选择页面融合
    SINGLE = "single"          # 单页处理


class SinglePageAction(Enum):
    """单页处理动作"""
    POLISH = "polish"          # 润色文字
    EXPAND = "expand"          # 扩展内容
    REWRITE = "rewrite"        # 改写风格
    EXTRACT = "extract"        # 提取知识点


# ==================== 模板结构定义 ====================

@dataclass
class PromptTemplate:
    """提示词模板结构"""
    system_prompt: str                    # 系统提示
    user_prompt_template: str             # 用户提示模板
    context_template: str = ""            # 上下文模板
    examples: List[str] = field(default_factory=list)  # 示例


# ==================== 基础系统提示词 ====================

BASE_SYSTEM_PROMPT = """你是一位专业的教学课件融合专家，专注于 K-12 教学内容的智能处理。

## 核心能力
1. **教学内容理解**：理解教学内容的逻辑结构、知识点关系和教学目标
2. **内容质量分析**：识别重复、冗余、互补的内容，评估教学价值
3. **教学逻辑构建**：保持教学流程连贯性，符合认知规律
4. **结构化输出**：生成清晰可执行的 JSON 格式融合方案

## 教学场景知识
- **课件结构**：封面页、目录页、概念讲解、例题讲解、练习题、总结页
- **知识点类型**：概念定义、定理公式、例题演示、练习巩固、应用拓展
- **教学逻辑**：引入→讲解→示范→练习→总结

## 输出规范
- 严格输出 JSON 格式，不包含其他文字
- JSON 必须是合法的可解析格式
- 字段命名使用 snake_case"""


# ==================== 教学增强提示词 ====================
# feat-236: 支持教学场景增强

TEACHING_ENHANCEMENT_PROMPT = """
## 教学增强功能

在处理教学内容时，你应当生成以下教学增强字段：

### 1. 教学笔记 (teaching_notes)
为教师提供的授课要点和提示，包括：
- 重点强调的内容
- 常见学生困惑点及解答方法
- 教学节奏建议
- 与前后知识的衔接点

### 2. 互动提示 (interaction_prompts)
课堂互动环节设计建议，包括：
- 引发思考的问题
- 课堂讨论话题
- 学生参与活动
- 互动时机建议

### 3. 练习题 (exercise_questions)
配套练习题列表，每道题包含：
- type: 题型（choice 选择题 / fill_blank 填空题 / short_answer 简答题 / judgment 判断题）
- question: 题目内容
- answer: 参考答案
- explanation: 解析说明（可选）
- options: 选项列表（选择题专用，可选）

### 4. 关键词汇 (key_vocabulary)
本页涉及的核心术语，每个词汇包含：
- word: 词汇
- definition: 释义/解释
- example: 例句或使用场景（可选）

### 输出格式增强
在原有输出格式的 new_content / polished_content / expanded_content 等字段中，
应当包含以上教学增强字段。"""

# 练习题生成模板
EXERCISE_TEMPLATES = {
    "basic": """生成基础练习题，用于巩固核心知识点：
- 题目难度：基础
- 题型分布：2道选择题 + 1道填空题 + 1道简答题
- 覆盖范围：本页所有核心知识点""",

    "varied": """生成变式练习题，用于拓展应用能力：
- 题目难度：中等
- 题型分布：1道选择题 + 1道填空题 + 2道简答题
- 特点：与例题相似但条件变化，训练迁移能力""",

    "advanced": """生成提高练习题，用于挑战思维深度：
- 题目难度：较高
- 题型分布：2道简答题 + 1道综合应用题
- 特点：需要综合运用多个知识点"""
}

# 互动提示模板
INTERACTION_TEMPLATES = {
    "thinking": """设计思考问题：
- 问题应引发深度思考，非简单是/否问题
- 与学生已有知识建立联系
- 答案需要分析推理""",

    "discussion": """设计课堂讨论话题：
- 话题具有开放性，允许多种观点
- 与实际生活相关联
- 能激发学生表达欲望""",

    "activity": """设计学生活动：
- 活动时长：3-5分钟
- 活动形式：小组讨论/动手操作/角色扮演
- 活动目标：明确的学习目标"""
}


# ==================== 整体合并模板 ====================

FULL_MERGE_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + """

## 整体合并任务说明

你需要分析两个完整的 PPT 课件，生成最优的合并方案。

### 分析步骤
1. **知识点梳理**：识别每个 PPT 的核心知识点和教学目标
2. **内容对比**：对比两个 PPT 的内容重叠度和互补性
3. **结构设计**：设计合并后的课件结构，确保逻辑连贯
4. **方案生成**：为每一页生成处理指令

### 知识点整合原则
- **核心优先**：保留双方的核心知识点
- **去重合精**：相同知识点选择更完整、更清晰的版本
- **互补增强**：互补知识点按逻辑顺序整合
- **适度扩展**：可创建综合练习或应用拓展页

### 内容去重策略
- 标题相同或高度相似：选择内容更丰富的版本
- 例题相同类型：保留难度梯度合理的多个例题
- 练习题重复：合并去重后保留

### 结构优化建议
- 封面页：选择标题更完整的版本
- 目录页：根据合并后内容重新生成
- 概念讲解：按由浅入深顺序排列
- 例题讲解：按难度梯度排列
- 练习题：整合双方练习，可分层设计
- 总结页：可重新生成综合性总结

### 输出格式
```json
{
  "merge_strategy": "合并策略说明（如：知识点整合、难度递进、例题增强等）",
  "summary": "合并后的课件概述，包含预计页数和主要内容",
  "knowledge_points": ["涉及的核心知识点列表"],
  "content_analysis": {
    "overlapping": ["重叠的知识点或内容"],
    "complementary_a": ["PPT A 独有的有价值内容"],
    "complementary_b": ["PPT B 独有的有价值内容"],
    "redundant": ["建议删除的冗余内容"]
  },
  "slide_plan": [
    {
      "action": "keep|merge|create|skip",
      "source": "A|B",
      "slide_index": 0,
      "sources": [{"source": "A", "slide": 1}, {"source": "B", "slide": 2}],
      "new_content": "新页面内容说明（仅 create/merge 时）",
      "instruction": "具体处理指令",
      "reason": "决策原因说明"
    }
  ]
}
```

### action 动作说明
| action | 说明 | 必填字段 |
|--------|------|----------|
| keep | 保留原页面 | source, slide_index, reason |
| merge | 合并多页内容 | sources, new_content, reason |
| create | 创建新页面 | new_content, reason |
| skip | 跳过不使用 | source, slide_index, reason |"""


# ==================== 多页融合模板 ====================

PARTIAL_MERGE_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + """

## 多页融合任务说明

你需要融合选中的多个页面，生成一个或多个新的页面。

### 内容关系分析方法

#### 1. 相同主题关系
- 页面讲解同一概念的不同方面
- 融合策略：合并为一个完整的讲解页面
- 示例：A 讲同分母加法，B 讲同分母减法 → 合并为同分母分数运算

#### 2. 互补内容关系
- 页面内容相互补充，构成完整知识点
- 融合策略：按逻辑顺序组合内容
- 示例：A 讲概念定义，B 讲例题 → 概念+例题组合

#### 3. 因果/递进关系
- 页面内容存在因果或难度递进关系
- 融合策略：保持逻辑顺序，添加过渡
- 示例：A 讲基础方法，B 讲进阶方法 → 基础→进阶

#### 4. 对比关系
- 页面内容形成对比，便于理解
- 融合策略：并列展示，突出对比点
- 示例：A 讲方法一，B 讲方法二 → 方法对比页面

### 融合策略建议

| 关系类型 | 融合方式 | 输出页数 |
|----------|----------|----------|
| 相同主题 | 合并为一个完整页面 | 1 页 |
| 互补内容 | 按逻辑组合，可能需要 1-2 页 | 1-2 页 |
| 因果递进 | 保持顺序，可合并或分开 | 1-2 页 |
| 对比关系 | 并列展示，一页呈现 | 1 页 |

### 输出格式
```json
{
  "merge_strategy": "融合策略说明",
  "content_relationship": {
    "type": "same_topic|complementary|progressive|contrast",
    "description": "内容关系的详细分析",
    "key_connections": ["关键关联点"]
  },
  "fusion_suggestions": [
    {
      "strategy": "具体融合策略",
      "advantages": ["优势说明"],
      "considerations": ["注意事项"]
    }
  ],
  "new_slides": [
    {
      "title": "融合后的标题",
      "slide_type": "content_slide|concept_slide|example_slide|exercise_slide",
      "teaching_role": "concept|example|exercise|summary",
      "elements": [
        {"type": "title", "content": "标题内容"},
        {"type": "text_body", "content": "正文内容"},
        {"type": "list_item", "content": "列表项内容"}
      ],
      "preserved_from_a": ["从 A 保留的内容"],
      "preserved_from_b": ["从 B 保留的内容"]
    }
  ]
}
```

### 融合原则
1. **完整性**：保持知识点完整性，不丢失关键信息
2. **连贯性**：逻辑顺序合理，过渡自然
3. **简洁性**：避免内容重复，精简表达
4. **教学性**：符合教学规律，便于学生理解"""


# ==================== 单页处理模板 ====================

# 润色专用提示词
# feat-236: 集成教学增强功能
POLISH_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + TEACHING_ENHANCEMENT_PROMPT + """

## 润色任务说明

你需要对教学课件页面进行文字润色，使表达更加流畅、准确、专业，并生成教学增强内容。

### 润色原则
1. **准确性**：保持原意不变，确保知识表述正确
2. **流畅性**：优化语句结构，使表达更加自然
3. **专业性**：使用规范的学科术语
4. **简洁性**：去除冗余表达，精简文字

### 润色要点
- 标题：简洁明了，突出主题
- 定义：表述准确，逻辑清晰
- 例题：步骤清晰，解答完整
- 练习：题目表述清楚，无歧义

### 输出格式
```json
{
  "action": "polish",
  "original_summary": "原内容摘要",
  "polished_content": {
    "title": "润色后的标题",
    "main_points": ["润色后的要点 1", "润色后的要点 2"],
    "polished_elements": [
      {"type": "元素类型", "original": "原文内容", "polished": "润色后内容"}
    ],
    "teaching_notes": "教师授课要点和提示",
    "interaction_prompts": ["思考问题1", "讨论话题2"],
    "exercise_questions": [
      {
        "type": "choice",
        "question": "题目内容",
        "answer": "正确答案",
        "explanation": "解析说明",
        "options": ["A选项", "B选项", "C选项", "D选项"]
      }
    ],
    "key_vocabulary": [
      {"word": "术语", "definition": "释义", "example": "例句"}
    ]
  },
  "changes": [
    {"location": "修改位置", "original": "原文", "polished": "润色后", "reason": "修改原因"}
  ],
  "quality_improvement": "质量提升说明"
}
```"""


# 扩展专用提示词
# feat-236: 集成教学增强功能
EXPAND_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + TEACHING_ENHANCEMENT_PROMPT + """

## 扩展任务说明

你需要对教学课件页面进行内容扩展，增加更多细节、例子或解释，并生成教学增强内容。

### 扩展方向
1. **概念扩展**：补充概念的背景、意义、应用场景
2. **例题扩展**：增加类似例题或变式练习
3. **解释扩展**：添加更详细的步骤说明或思路分析
4. **应用扩展**：添加实际应用案例或跨学科联系

### 扩展原则
1. **相关性**：扩展内容与主题紧密相关
2. **适度性**：扩展量适中，不过度堆砌
3. **层次性**：由浅入深，符合认知规律
4. **实用性**：对教学有实际帮助

### 不同页面类型的扩展策略
| 页面类型 | 扩展策略 |
|----------|----------|
| 概念讲解页 | 补充概念背景、对比辨析、易错提醒 |
| 例题讲解页 | 增加解题思路、变式训练、方法总结 |
| 练习页 | 增加分层练习、拓展题、思考题 |
| 总结页 | 补充知识框架、易错归纳、延伸学习 |

### 输出格式
```json
{
  "action": "expand",
  "original_summary": "原内容摘要",
  "expanded_content": {
    "title": "标题",
    "original_points": ["原有要点"],
    "expanded_points": ["扩展要点"],
    "new_examples": ["新增例题或案例"],
    "additional_content": "其他扩展内容",
    "teaching_notes": "教师授课要点和提示",
    "interaction_prompts": ["思考问题1", "讨论话题2"],
    "exercise_questions": [
      {
        "type": "choice|fill_blank|short_answer|judgment",
        "question": "题目内容",
        "answer": "正确答案",
        "explanation": "解析说明",
        "options": ["选项列表（选择题专用）"]
      }
    ],
    "key_vocabulary": [
      {"word": "术语", "definition": "释义", "example": "例句"}
    ]
  },
  "expansion_rationale": "扩展理由说明",
  "teaching_value": "教学价值说明"
}
```"""


# 改写专用提示词
# feat-236: 集成教学增强功能
REWRITE_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + TEACHING_ENHANCEMENT_PROMPT + """

## 改写任务说明

你需要对教学课件页面进行风格改写，调整语言表达方式以适应不同的教学场景，并生成教学增强内容。

### 支持的改写风格
1. **通俗易懂**：用生活化语言解释概念，适合基础较弱的学生
2. **严谨学术**：使用规范学科术语，适合高年级或竞赛
3. **故事化**：将知识点融入故事情境，增加趣味性
4. **问答式**：以问答形式呈现，便于启发思考

### 改写原则
1. **语义保持**：改写后意思不变，知识点准确
2. **风格一致**：全文风格统一
3. **目标适配**：符合目标学生群体的认知水平
4. **完整覆盖**：原有知识点不遗漏

### 不同学科的改写建议
| 学科 | 改写特点 |
|------|----------|
| 数学 | 强调逻辑推导，步骤清晰 |
| 语文 | 注重情感表达，语言优美 |
| 英语 | 突出语言应用，情境自然 |
| 科学 | 重视探究过程，表达准确 |

### 输出格式
```json
{
  "action": "rewrite",
  "original_summary": "原内容摘要",
  "rewrite_style": "通俗易懂|严谨学术|故事化|问答式",
  "rewritten_content": {
    "title": "改写后的标题",
    "main_content": "改写后的主要内容",
    "style_features": ["风格特点 1", "风格特点 2"],
    "teaching_notes": "教师授课要点和提示",
    "interaction_prompts": ["思考问题1", "讨论话题2"],
    "exercise_questions": [
      {
        "type": "choice|fill_blank|short_answer|judgment",
        "question": "题目内容",
        "answer": "正确答案",
        "explanation": "解析说明",
        "options": ["选项列表（选择题专用）"]
      }
    ],
    "key_vocabulary": [
      {"word": "术语", "definition": "释义", "example": "例句"}
    ]
  },
  "target_audience": "目标受众说明",
  "adaptation_notes": "改写适配说明"
}
```"""


# 提取专用提示词
# feat-236: 集成教学增强功能
EXTRACT_SYSTEM_PROMPT = BASE_SYSTEM_PROMPT + TEACHING_ENHANCEMENT_PROMPT + """

## 提取任务说明

你需要从教学课件页面中提取知识点，总结关键信息，并生成教学增强内容。

### 提取内容
1. **核心概念**：页面的核心概念和定义
2. **关键公式**：涉及的公式、定理、法则
3. **重要方法**：解题方法、技巧、步骤
4. **易错点**：容易出错的地方
5. **关联知识**：与其他知识点的联系

### 提取原则
1. **准确性**：提取内容必须准确无误
2. **完整性**：不遗漏重要知识点
3. **结构化**：按逻辑组织提取结果
4. **简洁性**：表述简洁，便于记忆

### 不同页面类型的提取重点
| 页面类型 | 提取重点 |
|----------|----------|
| 概念讲解页 | 概念定义、关键特征、辨析要点 |
| 例题讲解页 | 解题方法、关键步骤、易错提醒 |
| 练习页 | 考查知识点、题型分类、难度分析 |
| 总结页 | 知识框架、核心要点、应用要点 |

### 输出格式
```json
{
  "action": "extract",
  "original_summary": "原内容摘要",
  "extracted_knowledge": {
    "core_concepts": [
      {"concept": "概念名称", "definition": "定义", "key_points": ["要点"]}
    ],
    "formulas": [
      {"name": "公式名称", "formula": "公式表达", "conditions": "适用条件"}
    ],
    "methods": [
      {"name": "方法名称", "steps": ["步骤 1", "步骤 2"], "tips": ["技巧提示"]}
    ],
    "common_mistakes": [
      {"mistake": "常见错误", "correction": "正确做法", "reason": "错误原因"}
    ],
    "related_knowledge": ["关联知识点 1", "关联知识点 2"]
  },
  "knowledge_summary": "知识点总结（一句话概括）",
  "study_suggestions": ["学习建议"],
  "teaching_notes": "教师授课要点和提示",
  "interaction_prompts": ["思考问题1", "讨论话题2"],
  "exercise_questions": [
    {
      "type": "choice|fill_blank|short_answer|judgment",
      "question": "题目内容",
      "answer": "正确答案",
      "explanation": "解析说明",
      "options": ["选项列表（选择题专用）"]
    }
  ],
  "key_vocabulary": [
    {"word": "术语", "definition": "释义", "example": "例句"}
  ]
}
```"""


# ==================== 单页动作映射 ====================

SINGLE_PAGE_PROMPTS = {
    "polish": POLISH_SYSTEM_PROMPT,
    "expand": EXPAND_SYSTEM_PROMPT,
    "rewrite": REWRITE_SYSTEM_PROMPT,
    "extract": EXTRACT_SYSTEM_PROMPT,
}


# ==================== 提示词构建函数 ====================

def build_full_merge_prompt(
    doc_a: Dict[str, Any],
    doc_b: Dict[str, Any],
    file_a_name: str = "PPT A",
    file_b_name: str = "PPT B",
    custom_prompt: str = ""
) -> tuple:
    """
    构建整体合并提示词

    Args:
        doc_a: PPT A 的中间结构
        doc_b: PPT B 的中间结构
        file_a_name: PPT A 文件名
        file_b_name: PPT B 文件名
        custom_prompt: 用户自定义需求（覆盖默认需求）

    Returns:
        (system_prompt, user_prompt) 元组
    """
    system_prompt = FULL_MERGE_SYSTEM_PROMPT

    # 提取摘要
    a_summary = _extract_doc_summary(doc_a)
    b_summary = _extract_doc_summary(doc_b)

    # 默认用户需求
    default_prompt = """请根据两份课件的内容，生成最优的合并方案。

要求：
1. 分析两个课件的知识点重叠和互补情况
2. 保留双方的核心教学内容
3. 去除冗余重复的内容
4. 设计合理的教学流程顺序
5. 如有需要，可创建过渡页或综合练习页"""

    user_prompt = f"""## PPT A 概览
文件名：{file_a_name}
总页数：{doc_a.get('total_slides', len(doc_a.get('slides', [])))}
学科：{doc_a.get('metadata', {}).get('subject', '未知')}
年级：{doc_a.get('metadata', {}).get('grade', '未知')}
复杂元素页面：{doc_a.get('complex_element_slides', [])}

### 页面摘要
{_format_summary(a_summary)}

## PPT B 概览
文件名：{file_b_name}
总页数：{doc_b.get('total_slides', len(doc_b.get('slides', [])))}
学科：{doc_b.get('metadata', {}).get('subject', '未知')}
年级：{doc_b.get('metadata', {}).get('grade', '未知')}
复杂元素页面：{doc_b.get('complex_element_slides', [])}

### 页面摘要
{_format_summary(b_summary)}

## 用户需求
{(custom_prompt or '').strip() if custom_prompt else default_prompt}

请生成合并计划 JSON。"""

    return system_prompt, user_prompt


def build_partial_merge_prompt(
    pages_a: List[Dict[str, Any]],
    pages_b: List[Dict[str, Any]],
    custom_prompt: str = ""
) -> tuple:
    """
    构建多页融合提示词

    Args:
        pages_a: PPT A 的选中页面列表
        pages_b: PPT B 的选中页面列表
        custom_prompt: 用户自定义需求

    Returns:
        (system_prompt, user_prompt) 元组
    """
    system_prompt = PARTIAL_MERGE_SYSTEM_PROMPT

    # 默认用户需求
    default_prompt = """请融合选中的页面内容，生成新的页面。

要求：
1. 分析选中页面之间的关系（相同主题/互补内容/因果递进/对比关系）
2. 根据关系类型选择合适的融合策略
3. 确保融合后内容完整、逻辑连贯
4. 如有冲突内容，标注并提供处理建议"""

    user_prompt = f"""## PPT A 选中页面 ({len(pages_a)} 页)
{_format_pages(pages_a, 'A')}

## PPT B 选中页面 ({len(pages_b)} 页)
{_format_pages(pages_b, 'B')}

## 用户需求
{(custom_prompt or '').strip() if custom_prompt else default_prompt}

请生成融合结果 JSON。"""

    return system_prompt, user_prompt


def build_single_page_prompt(
    slide_data: Dict[str, Any],
    action: str,
    custom_prompt: str = ""
) -> tuple:
    """
    构建单页处理提示词

    Args:
        slide_data: 单页数据
        action: 动作类型 (polish/expand/rewrite/extract)
        custom_prompt: 用户自定义需求

    Returns:
        (system_prompt, user_prompt) 元组
    """
    if action not in SINGLE_PAGE_PROMPTS:
        raise ValueError(f"不支持的动作: {action}，支持的动作: {list(SINGLE_PAGE_PROMPTS.keys())}")

    system_prompt = SINGLE_PAGE_PROMPTS[action]

    # 动作描述
    action_descriptions = {
        "polish": "润色文字，使表达更加流畅、准确、专业",
        "expand": "扩展内容，增加更多细节、例子或解释",
        "rewrite": "改写风格，调整语言表达方式",
        "extract": "提取知识点，总结关键信息"
    }

    # 默认用户需求
    default_prompts = {
        "polish": "请润色页面文字，保持原意不变，使表达更加流畅专业。",
        "expand": "请扩展页面内容，增加必要的细节、例子或解释，丰富教学内容。",
        "rewrite": "请改写页面风格，使内容更适合目标学生群体理解。",
        "extract": "请提取页面的核心知识点，总结关键信息，便于学生掌握。"
    }

    user_prompt = f"""## 页面信息
页码：第 {slide_data.get('slide_index', 0) + 1} 页
类型：{slide_data.get('slide_type', '未知')}
教学角色：{slide_data.get('teaching_role', '未知')}
学科：{slide_data.get('subject', '未知')}
年级：{slide_data.get('grade', '未知')}

### 页面内容
{_format_slide_content(slide_data)}

## 处理任务
动作：{action}
说明：{action_descriptions.get(action, '')}

## 用户需求
{(custom_prompt or '').strip() if custom_prompt else default_prompts.get(action, '')}

请生成处理结果 JSON。"""

    return system_prompt, user_prompt


# ==================== 辅助函数 ====================

def _extract_doc_summary(doc: Dict[str, Any]) -> List[Dict]:
    """提取文档摘要"""
    summary = []
    for slide in doc.get('slides', []):
        slide_info = {
            "index": slide.get('slide_index', 0),
            "type": slide.get('slide_type', '未知'),
            "role": slide.get('teaching_role', '未知'),
            "title": "",
            "main_points": [],
            "has_images": False,
            "has_tables": False
        }

        # 提取标题和要点
        teaching = slide.get('teaching_content', {})
        slide_info['title'] = teaching.get('title', '')
        slide_info['main_points'] = teaching.get('main_points', teaching.get('knowledge_points', []))[:3]

        # 检查元素类型
        for elem in slide.get('elements', []):
            elem_type = elem.get('type', '')
            if elem_type == 'image':
                slide_info['has_images'] = True
            elif elem_type == 'table':
                slide_info['has_tables'] = True

        summary.append(slide_info)

    return summary


def _format_summary(summary: List[Dict]) -> str:
    """格式化摘要输出"""
    lines = []
    for item in summary:
        # feat-192: 确保 main_points 中的元素都是字符串
        raw_points = item.get('main_points', [])[:2]
        str_points = []
        for p in raw_points:
            if isinstance(p, str):
                str_points.append(p)
            elif isinstance(p, dict):
                text = p.get('text', p.get('content', p.get('point', '')))
                if text and isinstance(text, str):
                    str_points.append(text)
                else:
                    str_points.append(str(p))
            elif p is not None:
                str_points.append(str(p))
        points_str = '、'.join(str_points) if str_points else ""
        if points_str:
            points_str = f" - {points_str}"

        flags = []
        if item.get('has_images'):
            flags.append('有图')
        if item.get('has_tables'):
            flags.append('有表')
        flags_str = f" [{', '.join(flags)}]" if flags else ""

        lines.append(
            f"  第{item['index'] + 1}页 [{item.get('role', item.get('type', '未知'))}]: "
            f"{item.get('title', '无标题')}{points_str}{flags_str}"
        )
    return '\n'.join(lines)


def _format_pages(pages: List[Dict[str, Any]], label: str) -> str:
    """格式化页面列表"""
    lines = []
    for i, page in enumerate(pages):
        lines.append(f"### {label} 第 {i + 1} 页")
        lines.append(f"类型：{page.get('slide_type', '未知')}")
        lines.append(f"教学角色：{page.get('teaching_role', '未知')}")

        # 提取标题
        title = ""
        teaching = page.get('teaching_content', {})
        title = teaching.get('title', '')

        if not title:
            for elem in page.get('elements', []):
                if elem.get('type') == 'title':
                    title = elem.get('text', elem.get('content', ''))
                    break

        lines.append(f"标题：{title or '无标题'}")

        # 提取内容要点
        content_items = []
        for elem in page.get('elements', [])[:4]:
            elem_type = elem.get('type', '')
            if elem_type in ('text_body', 'list_item', 'subtitle'):
                content = elem.get('text', elem.get('content', ''))[:100]
                if content:
                    content_items.append(f"  - [{elem_type}] {content}")
            elif elem_type == 'image':
                content_items.append(f"  - [image] {elem.get('description', '图片')}")
            elif elem_type == 'table':
                headers = elem.get('table_headers', [])
                # feat-192: 确保 headers 中的元素都是字符串
                header_str = ' | '.join(str(h) if not isinstance(h, str) else h for h in headers) if headers else '表格'
                content_items.append(f"  - [table] {header_str}")

        if content_items:
            lines.append("内容：")
            lines.extend(content_items)

        lines.append("")

    return '\n'.join(lines)


def _format_slide_content(slide: Dict[str, Any]) -> str:
    """格式化单页内容"""
    lines = []

    # 标题
    title = ""
    teaching = slide.get('teaching_content', {})
    title = teaching.get('title', '')

    if not title:
        for elem in slide.get('elements', []):
            if elem.get('type') == 'title':
                title = elem.get('text', elem.get('content', ''))
                break

    lines.append(f"标题：{title or '无标题'}")

    # 内容元素
    lines.append("内容元素：")
    for i, elem in enumerate(slide.get('elements', []), 1):
        elem_type = elem.get('type', '')
        if elem_type == 'title':
            continue  # 标题已单独处理

        content = elem.get('text', elem.get('content', ''))
        if elem_type == 'text_body':
            lines.append(f"  {i}. [正文] {content[:200]}{'...' if len(content) > 200 else ''}")
        elif elem_type == 'list_item':
            lines.append(f"  {i}. [列表] {content[:150]}{'...' if len(content) > 150 else ''}")
        elif elem_type == 'subtitle':
            lines.append(f"  {i}. [副标题] {content}")
        elif elem_type == 'image':
            lines.append(f"  {i}. [图片] {elem.get('description', '图片内容')}")
        elif elem_type == 'table':
            headers = elem.get('table_headers', [])
            rows = len(elem.get('table_data', []))
            # feat-192: 确保 headers 中的元素都是字符串
            header_str = ' | '.join(str(h) if not isinstance(h, str) else h for h in headers) if headers else '未知'
            lines.append(f"  {i}. [表格] {rows} 行，列：{header_str}")

    # 教学内容摘要
    if teaching:
        points = teaching.get('main_points', teaching.get('knowledge_points', []))
        if points:
            # feat-192: 确保 points 中的元素都是字符串，避免 join 失败
            str_points = []
            for p in points[:5]:
                if isinstance(p, str):
                    str_points.append(p)
                elif isinstance(p, dict):
                    text = p.get('text', p.get('content', p.get('point', '')))
                    if text and isinstance(text, str):
                        str_points.append(text)
                    else:
                        str_points.append(str(p))
                elif p is not None:
                    str_points.append(str(p))
            if str_points:
                lines.append(f"\n教学要点：{'、'.join(str_points)}")

    return '\n'.join(lines)


# ==================== 预设策略模板 ====================

MERGE_STRATEGY_TEMPLATES = {
    "knowledge_integration": {
        "name": "知识点整合",
        "description": "适用于两个 PPT 讲解同一主题的不同方面",
        "steps": [
            "识别两份课件的核心知识点",
            "合并相似知识点，保留最完整的版本",
            "互补知识点按逻辑顺序排列",
            "创建综合练习页面"
        ],
        "prompt_suffix": "请采用知识点整合策略，合并相似内容，保留互补内容。"
    },

    "difficulty_gradient": {
        "name": "难度递进",
        "description": "适用于一份课件基础、一份课件进阶的情况",
        "steps": [
            "保留基础内容作为前半部分",
            "进阶内容作为后半部分",
            "添加过渡页面连接两个难度层级",
            "创建分层练习题"
        ],
        "prompt_suffix": "请采用难度递进策略，先基础后进阶，添加过渡内容。"
    },

    "example_enhancement": {
        "name": "例题增强",
        "description": "适用于一份课件重概念、一份课件重例题",
        "steps": [
            "保留概念讲解部分",
            "融合双方的例题",
            "按难度梯度排列例题",
            "添加变式练习"
        ],
        "prompt_suffix": "请采用例题增强策略，整合概念和例题，丰富练习内容。"
    },

    "cross_subject": {
        "name": "跨学科融合",
        "description": "适用于不同学科的课件融合",
        "steps": [
            "识别跨学科的共同知识点",
            "以一方为主干，另一方为补充",
            "标注学科交叉点",
            "创建综合应用题"
        ],
        "prompt_suffix": "请采用跨学科融合策略，突出学科交叉点，创建综合应用内容。"
    },

    "review_synthesis": {
        "name": "复习综合",
        "description": "适用于多份复习课件整合",
        "steps": [
            "按知识模块重组内容",
            "合并重复的知识点总结",
            "整合各方的典型例题",
            "创建综合测试页面"
        ],
        "prompt_suffix": "请采用复习综合策略，按模块重组，整合典型例题和测试内容。"
    }
}


def get_strategy_prompt(strategy_name: str) -> str:
    """获取策略预设提示词"""
    strategy = MERGE_STRATEGY_TEMPLATES.get(strategy_name)
    if strategy:
        return strategy.get('prompt_suffix', '')
    return ""


def list_available_strategies() -> List[Dict[str, str]]:
    """列出所有可用的合并策略"""
    return [
        {
            "name": s["name"],
            "description": s["description"],
            "steps": s["steps"]
        }
        for s in MERGE_STRATEGY_TEMPLATES.values()
    ]