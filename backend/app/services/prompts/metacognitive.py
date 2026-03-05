"""
问题链与元认知提示系统模块

基于问题链教学法（Question Chain Pedagogy）和元认知理论（Metacognition Theory），
设计递进式问题序列，嵌入自我反思触发点，促进学生深度思考。

核心组件：
1. 问题链模板：是什么 → 为什么 → 怎么用 → 如果...会怎样 → 还有其他方法吗
2. 元认知提示：想一想 / 试着解释 / 和之前学的有什么关系
3. 反思触发点：学习 checkpoints，促进学生监控自己的理解
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class MetacognitiveType(Enum):
    """元认知提示类型枚举"""

    REFLECT = "reflect"           # 反思型：想一想、试着解释
    CONNECT = "connect"           # 连接型：和之前学的有什么关系
    PREDICT = "predict"           # 预测型：你觉得会发生什么
    EVALUATE = "evaluate"         # 评估型：你理解了吗、为什么
    EXTEND = "extend"             # 拓展型：还有其他方法吗、如果...会怎样
    MONITOR = "monitor"           # 监控型：检查你的答案、确认步骤

    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        names = {
            "reflect": "反思",
            "connect": "连接",
            "predict": "预测",
            "evaluate": "评估",
            "extend": "拓展",
            "monitor": "监控",
        }
        return names[self.value]

    @property
    def icon(self) -> str:
        """获取对应图标"""
        icons = {
            "reflect": "💭",      # 思考气泡
            "connect": "🔗",      # 链接
            "predict": "🔮",      # 水晶球
            "evaluate": "✓",       # 对勾
            "extend": "🚀",       # 火箭
            "monitor": "📊",      # 图表
        }
        return icons[self.value]


class QuestionChainLevel(Enum):
    """问题链认知层级"""

    WHAT = "what"                 # 是什么：事实性问题
    WHY = "why"                   # 为什么：解释性问题
    HOW = "how"                   # 怎么用：应用性问题
    WHAT_IF = "what_if"          # 如果...会怎样：假设性问题
    WHAT_ELSE = "what_else"      # 还有其他方法吗：发散性问题

    @property
    def chinese_name(self) -> str:
        """获取中文名称"""
        names = {
            "what": "是什么",
            "why": "为什么",
            "how": "怎么用",
            "what_if": "如果...会怎样",
            "what_else": "还有其他方法吗",
        }
        return names[self.value]

    @property
    def description(self) -> str:
        """获取层级描述"""
        descriptions = {
            "what": "事实性问题，关注基本概念、定义、特征",
            "why": "解释性问题，关注原因、原理、机制",
            "how": "应用性问题，关注方法、步骤、操作",
            "what_if": "假设性问题，关注变式、迁移、推理",
            "what_else": "发散性问题，关注创新、多元、拓展",
        }
        return descriptions[self.value]

    @property
    def question_templates(self) -> List[str]:
        """获取问题模板"""
        templates = {
            "what": [
                "什么是...？",
                "...的定义是什么？",
                "...有哪些特征？",
                "请描述...的主要内容",
                "...包括哪些部分？",
            ],
            "why": [
                "为什么...？",
                "...的原因是什么？",
                "为什么会出现这种情况？",
                "...背后的原理是什么？",
                "如何解释...现象？",
            ],
            "how": [
                "如何...？",
                "怎样使用...？",
                "...的步骤是什么？",
                "请演示如何...",
                "解决这个问题需要哪些方法？",
            ],
            "what_if": [
                "如果...会发生什么？",
                "假如条件改变，结果会怎样？",
                "...和...有什么联系？",
                "这个知识可以用在哪些情境？",
                "如果换一种方式，会如何？",
            ],
            "what_else": [
                "还有其他方法吗？",
                "除了这种方法，还能怎样？",
                "这个问题有哪些不同的解决思路？",
                "你还能想到哪些相关的例子？",
                "如何将这个知识与其他领域联系？",
            ],
        }
        return templates[self.value]


class QuestionChainMixin:
    """
    问题链教学法混入类

    基于问题链教学法（Question Chain Pedagogy），设计递进式问题序列：
    是什么 → 为什么 → 怎么用 → 如果...会怎样 → 还有其他方法吗

    认知递进层次：
    1. 事实性理解（What）：基础概念、定义
    2. 原理性理解（Why）：原因、机制
    3. 应用性理解（How）：方法、步骤
    4. 迁移性理解（What if）：变式、情境迁移
    5. 创造性理解（What else）：多元、创新
    """

    # 年级到问题链深度的映射
    GRADE_QUESTION_CHAIN_DEPTH = {
        "1": {"max_depth": 2, "focus": ["what", "how"]},      # 低年级：是什么 + 怎么用
        "2": {"max_depth": 2, "focus": ["what", "how"]},
        "3": {"max_depth": 2, "focus": ["what", "how"]},
        "4": {"max_depth": 3, "focus": ["what", "why", "how"]},  # 中年级：增加为什么
        "5": {"max_depth": 3, "focus": ["what", "why", "how"]},
        "6": {"max_depth": 3, "focus": ["what", "why", "how"]},
        "7": {"max_depth": 4, "focus": ["what", "why", "how", "what_if"]},  # 初中：增加如果
        "8": {"max_depth": 4, "focus": ["what", "why", "how", "what_if"]},
        "9": {"max_depth": 4, "focus": ["what", "why", "how", "what_if"]},
        "10": {"max_depth": 5, "focus": ["what", "why", "how", "what_if", "what_else"]},  # 高中：完整链条
        "11": {"max_depth": 5, "focus": ["what", "why", "how", "what_if", "what_else"]},
        "12": {"max_depth": 5, "focus": ["what", "why", "how", "what_if", "what_else"]},
    }

    def get_question_chain_for_grade(self, grade: str, topic: str) -> List[Dict[str, Any]]:
        """
        根据年级生成问题链

        Args:
            grade: 年级（1-12）
            topic: 学习主题

        Returns:
            问题链列表，每个元素包含 level、question_template、description
        """
        depth_config = self.GRADE_QUESTION_CHAIN_DEPTH.get(
            grade, self.GRADE_QUESTION_CHAIN_DEPTH["5"]
        )
        max_depth = depth_config["max_depth"]
        focus_levels = depth_config["focus"][:max_depth]

        chain = []
        for level_name in focus_levels:
            level = QuestionChainLevel(level_name)
            chain.append({
                "level": level.value,
                "chinese_name": level.chinese_name,
                "templates": level.question_templates,
                "description": level.description,
                "cognitive_demand": ["低", "中", "高"][min(focus_levels.index(level_name), 2)],
            })

        return chain

    def get_question_chain_prompt_section(self, grade: str, subject: str) -> str:
        """
        获取问题链提示词段落

        Args:
            grade: 年级
            subject: 学科

        Returns:
            问题链提示词段落
        """
        depth_config = self.GRADE_QUESTION_CHAIN_DEPTH.get(
            grade, self.GRADE_QUESTION_CHAIN_DEPTH["5"]
        )
        focus_levels = depth_config["focus"][:depth_config["max_depth"]]
        level_names = [QuestionChainLevel(level).chinese_name for level in focus_levels]

        return f"""
【问题链教学法 - 递进式问题序列设计】

基于问题链教学法（Question Chain Pedagogy），请为每个核心知识点设计递进式问题序列：

**问题链认知递进层次**：

1. **是什么**（What）- 事实性问题
   - 关注：基本概念、定义、特征
   - 示例："什么是...？"、"...的定义是什么？"、"...有哪些特征？"

2. **为什么**（Why）- 解释性问题
   - 关注：原因、原理、机制
   - 示例："为什么...？"、"...的原因是什么？"、"...背后的原理是什么？"

3. **怎么用**（How）- 应用性问题
   - 关注：方法、步骤、操作
   - 示例："如何...？"、"怎样使用...？"、"...的步骤是什么？"

4. **如果...会怎样**（What if）- 假设性问题
   - 关注：变式、迁移、推理
   - 示例："如果...会发生什么？"、"假如条件改变，结果会怎样？"

5. **还有其他方法吗**（What else）- 发散性问题
   - 关注：创新、多元、拓展
   - 示例："还有其他方法吗？"、"除了这种方法，还能怎样？"

【{grade}年级问题链深度要求】：

- 问题链层级：{" → ".join(level_names)}
- 每个核心知识点至少设计{len(level_names)}个递进问题
- 问题难度呈梯度上升，避免认知跳跃过大
- 在"互动问答页"和"课堂练习页"中明确标注每个问题所属的层级

【{subject}学科问题链适配】：

- 语文：是什么（字词含义）→ 为什么（作者意图）→ 怎么用（写作手法）→ 如果（改写结局）→ 还有（其他解读）
- 数学：是什么（概念定义）→ 为什么（公式推导）→ 怎么用（解题方法）→ 如果（变式条件）→ 还有（多种解法）
- 英语：是什么（单词/语法）→ 为什么（语言规则）→ 怎么用（造句/对话）→ 如果（情境变化）→ 还有（其他表达）
- 科学：是什么（现象/概念）→ 为什么（科学原理）→ 怎么用（实验方法）→ 如果（变量改变）→ 还有（其他解释）
"""


class MetacognitivePromptMixin:
    """
    元认知提示混入类

    基于元认知理论（Metacognition Theory），在学习关键节点嵌入自我反思触发点，
    促进学生监控、调节和评估自己的学习过程。

    元认知的三大功能：
    1. 计划（Planning）：学习前的目标设定和策略选择
    2. 监控（Monitoring）：学习中的理解检查
    3. 评估（Evaluating）：学习后的反思和调整

    实现方式：
    - 反思提示：想一想、试着解释
    - 连接提示：和之前学的有什么关系
    - 预测提示：你觉得会发生什么
    - 评估提示：你理解了吗、为什么
    - 拓展提示：还有其他方法吗、如果...会怎样
    """

    # 元认知提示模板库
    METACOGNITIVE_PROMPT_TEMPLATES = {
        "reflect": [
            "想一想：{topic}的核心概念是什么？",
            "试着用自己的话解释{topic}",
            "停下来思考：{question}",
            "回顾一下：我们刚刚学到了什么？",
            "这个概念和你原来想的一样吗？",
        ],
        "connect": [
            "和之前学的{old_topic}有什么关系？",
            "这个知识和{old_topic}有什么联系？",
            "还记得我们学过的{old_topic}吗？它和现在的内容有何异同？",
            "能否用之前学过的{old_topic}来理解这个新概念？",
            "这是{old_topic}的延伸还是新的知识？",
        ],
        "predict": [
            "你觉得接下来会发生什么？",
            "如果{condition}，结果会怎样？",
            "根据你的理解，预测一下...",
            "你认为哪种方法更有效？为什么？",
            "猜一猜，这个公式可以用来解决什么问题？",
        ],
        "evaluate": [
            "你理解了吗？请解释...",
            "为什么这个方法是正确的？",
            "你的答案合理吗？请说明理由",
            "这个方法有什么优点和缺点？",
            "你能判断以下哪种情况适用这个方法吗？",
        ],
        "extend": [
            "还有其他方法吗？",
            "除了这种方法，还能怎样解决？",
            "这个知识可以用在哪些实际场景中？",
            "你还能想到哪些相关的例子？",
            "如何将这个知识与生活实际联系？",
        ],
        "monitor": [
            "检查你的答案是否符合逻辑",
            "确认每一步都有清晰的理由",
            "你的解题过程完整吗？",
            "是否有遗漏的步骤或条件？",
            "重新审视：这个结论在所有情况下都成立吗？",
        ],
    }

    # 年级到元认知提示频率的映射
    GRADE_METACOGNITIVE_FREQUENCY = {
        "1": {"frequency": "high", "interval": 2, "simple": True},    # 每 2 页一次，简单语言
        "2": {"frequency": "high", "interval": 2, "simple": True},
        "3": {"frequency": "high", "interval": 2, "simple": True},
        "4": {"frequency": "medium", "interval": 3, "simple": False},
        "5": {"frequency": "medium", "interval": 3, "simple": False},
        "6": {"frequency": "medium", "interval": 3, "simple": False},
        "7": {"frequency": "standard", "interval": 4, "simple": False},
        "8": {"frequency": "standard", "interval": 4, "simple": False},
        "9": {"frequency": "standard", "interval": 4, "simple": False},
        "10": {"frequency": "low", "interval": 5, "simple": False},
        "11": {"frequency": "low", "interval": 5, "simple": False},
        "12": {"frequency": "low", "interval": 5, "simple": False},
    }

    def get_metacognitive_prompt_for_page(
        self,
        grade: str,
        page_type: str,
        topic: str,
        old_topic: Optional[str] = None,
        page_number: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        根据页面类型和位置生成元认知提示

        Args:
            grade: 年级
            page_type: 页面类型
            topic: 当前主题
            old_topic: 旧知识主题（用于连接型提示）
            page_number: 页码

        Returns:
            元认知提示字典，包含 type、content、icon、position
        """
        freq_config = self.GRADE_METACOGNITIVE_FREQUENCY.get(
            grade, self.GRADE_METACOGNITIVE_FREQUENCY["5"]
        )
        interval = freq_config["interval"]
        use_simple = freq_config["simple"]

        # 特定页面类型必须插入元认知提示
        must_insert_types = ["互动问答页", "课堂练习页", "总结回顾页", "概念桥接页"]

        # 根据间隔决定是否插入
        should_insert = (page_number % interval == 0) or (page_type in must_insert_types)

        if not should_insert:
            return None

        # 根据页面类型选择合适的元认知提示类型
        type_priority_map = {
            "互动问答页": ["reflect", "evaluate"],
            "课堂练习页": ["monitor", "evaluate", "extend"],
            "总结回顾页": ["reflect", "connect", "extend"],
            "概念桥接页": ["connect", "reflect"],
            "知识点讲解页": ["reflect", "predict", "connect"],
            "公式推导页": ["monitor", "reflect"],
            "实验步骤页": ["predict", "monitor"],
        }

        priority_types = type_priority_map.get(page_type, ["reflect"])
        prompt_type = priority_types[page_number % len(priority_types)]

        # 选择具体提示语
        templates = self.METACOGNITIVE_PROMPT_TEMPLATES[prompt_type]
        template = templates[page_number % len(templates)]

        # 填充模板变量
        content = template.format(
            topic=topic,
            old_topic=old_topic or "之前的知识",
            question=f"关于{topic}，你有什么疑问？"
        )

        # 获取类型信息
        meta_type = MetacognitiveType(prompt_type)

        return {
            "type": meta_type.value,
            "chinese_name": meta_type.chinese_name,
            "icon": meta_type.icon,
            "content": content,
            "position": "after_content",  # 内容后插入
            "visual_style": "thought_bubble" if use_simple else "highlight_box",
        }

    def get_metacognitive_prompt_section(self, grade: str, subject: str) -> str:
        """
        获取元认知提示的提示词段落

        Args:
            grade: 年级
            subject: 学科

        Returns:
            元认知提示词段落
        """
        freq_config = self.GRADE_METACOGNITIVE_FREQUENCY.get(
            grade, self.GRADE_METACOGNITIVE_FREQUENCY["5"]
        )
        frequency_desc = {
            "high": "高频率（低年级需要频繁提醒）",
            "medium": "中等频率",
            "standard": "标准频率",
            "low": "低频率（高年级培养自主学习能力）",
        }.get(freq_config["frequency"], "标准频率")

        return f"""
【元认知提示系统 - 自我反思触发点设计】

基于元认知理论（Metacognition Theory），在学习关键节点嵌入自我反思触发点，
促进学生监控、调节和评估自己的学习过程。

**元认知六大功能模块**：

1. **反思型**（💭 想一想）
   - 功能：促进学生对知识的深度思考
   - 示例："想一想：这个概念的核心是什么？"、"试着用自己的话解释..."

2. **连接型**（🔗 联系）
   - 功能：连接新旧知识，建立知识网络
   - 示例："和之前学的...有什么关系？"、"还记得我们学过的...吗？"

3. **预测型**（🔮 猜一猜）
   - 功能：激发好奇心和探究欲
   - 示例："你觉得接下来会发生什么？"、"如果...结果会怎样？"

4. **评估型**（✓ 查一查）
   - 功能：检查理解程度，评估答案合理性
   - 示例："你理解了吗？请解释..."、"你的答案合理吗？为什么？"

5. **拓展型**（🚀 想一想）
   - 功能：培养发散思维和迁移能力
   - 示例："还有其他方法吗？"、"这个知识可以用在哪些实际场景？"

6. **监控型**（📊 检一检）
   - 功能：培养自我监控学习习惯
   - 示例："检查你的答案是否符合逻辑"、"确认每一步都有清晰的理由"

【{grade}年级元认知提示频率】：

- 频率等级：{frequency_desc}
- 插入间隔：每{freq_config.get("interval", 3)}页或关键节点（互动/练习/总结页）必须插入
- 语言风格：{"简洁直白、配合图标" if freq_config.get("simple", False) else "适当深入、引导思考"}

【学科适配策略】：

- 语文：侧重反思型（感悟文意）、连接型（联系生活）
- 数学：侧重监控型（检查步骤）、拓展型（多种解法）
- 英语：侧重预测型（猜测词义）、评估型（自我检测）
- 科学：侧重连接型（实验与理论）、监控型（实验步骤检查）

【输出格式要求】：

在 PPT 内容 JSON 中，元认知提示使用以下字段：
```json
{{
  "meta_prompt": {{
    "type": "reflect | connect | predict | evaluate | extend | monitor",
    "icon": "💭 | 🔗 | 🔮 | ✓ | 🚀 | 📊",
    "content": "提示语内容",
    "position": "before_content | after_content | side_note"
  }}
}}
```
"""


class MetacognitivePromptSystem(QuestionChainMixin, MetacognitivePromptMixin):
    """
    问题链与元认知提示系统

    整合问题链教学法和元认知理论，提供完整的递进式问题序列
    和自我反思触发点生成功能
    """

    def __init__(self):
        """初始化问题链与元认知提示系统"""
        pass

    def build_question_chain_and_metacognitive_prompt(
        self,
        grade: str,
        subject: str,
        topic: str
    ) -> str:
        """
        构建问题链与元认知提示的完整提示词

        Args:
            grade: 年级
            subject: 学科
            topic: 学习主题

        Returns:
            完整的提示词段落
        """
        question_chain_section = self.get_question_chain_prompt_section(grade, subject)
        metacognitive_section = self.get_metacognitive_prompt_section(grade, subject)

        return question_chain_section + metacognitive_section

    def get_full_metacognitive_schema(self) -> Dict[str, Any]:
        """
        获取元认知提示的完整 schema 结构

        Returns:
            JSON Schema 结构定义
        """
        return {
            "meta_prompt": {
                "type": "object",
                "description": "元认知提示配置",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["reflect", "connect", "predict", "evaluate", "extend", "monitor"],
                        "description": "元认知提示类型"
                    },
                    "chinese_name": {
                        "type": "string",
                        "description": "中文名称"
                    },
                    "icon": {
                        "type": "string",
                        "description": "图标符号"
                    },
                    "content": {
                        "type": "string",
                        "description": "提示语内容"
                    },
                    "position": {
                        "type": "string",
                        "enum": ["before_content", "after_content", "side_note"],
                        "description": "插入位置"
                    },
                    "visual_style": {
                        "type": "string",
                        "enum": ["thought_bubble", "highlight_box", "sidebar"],
                        "description": "视觉样式"
                    }
                }
            }
        }
