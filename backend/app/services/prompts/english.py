"""
英语学科提示词策略（深度增强版）
专为英语教学设计的提示词模板，包含词根词缀分解、固定搭配网络、语法树、时态时间轴
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin


class EnglishPromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    英语学科提示词策略（深度增强版）

    专为英语教学设计，包含：
    1. 词根词缀分解：单词构词法分析、词源解析
    2. 固定搭配网络：短语搭配、同义词/反义词、词汇网络
    3. 语法树：句子成分分析、句法结构图解
    4. 时态时间轴：时态可视化、时间参照系
    """

    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None,
        difficulty_level: str = "unified"
    ) -> str:
        """
        构建英语学科的 PPT 内容生成提示词（深度增强版）

        Args:
            difficulty_level: 教学层次（unified/basic/intermediate/advanced）
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        # 难度分层策略（feat-040）
        difficulty_strategy = {
            "unified": "统一模式：生成包含基础（1 星）、提高（2 星）、拓展（3 星）三个难度的混合练习",
            "basic": "基础版：只生成基础难度（1 星）练习，侧重单词回忆和简单句型",
            "intermediate": "提高版：只生成中等难度（2 星）练习，侧重语言理解和综合应用",
            "advanced": "拓展版：只生成高难度（3 星）练习，侧重分析评价和创造迁移"
        }

        prompt = f"""你是一位经验丰富的英语教师，请根据以下英语教学内容，设计一份高质量的英语教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：英语
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【英语教学原则】
1. **情境创设**：在真实或模拟的情境中呈现语言，让学生在语境中理解和使用
2. **听说领先**：先听后说，先输入后输出，遵循语言习得规律
3. **词不离句**：单词教学要放在句子和语篇中，避免孤立记忆
4. **循环复现**：设计多种活动让学生反复接触目标语言
5. **文化渗透**：适时介绍英语国家的文化背景，培养跨文化意识

【差异化教学要求（feat-040）】
当前模式：{difficulty_level} - {difficulty_strategy.get(difficulty_level, "")}

**难度标注规范**：
- 基础题（1 星★）：单词拼写、短语匹配、简单句型模仿
- 提高题（2 星★★）：句子翻译、对话填空、语法应用
- 拓展题（3 星★★★）：话题写作、角色扮演、批判性讨论

**输出要求**：
- 在"课堂练习页"和"情景对话页"中，每道题必须包含 `difficulty` 字段（basic/intermediate/advanced）
- 统一模式下：3 种难度都要有，比例约 50%/30%/20%
- 分层模式下：只生成指定难度的题目

【情境创设自动生成要求（feat-039）- 英语学科】

**年级差异化策略**：
- 低年级（1-4 年级）：使用童话故事、动画人物、简单游戏等情境，语言简单重复，多用图片辅助
- 中年级（5-8 年级）：使用校园生活、旅行游记、文化交流等情境，语言贴近学生经验
- 高年级（9-12 年级）：使用职场体验、社会热点、学术讨论等情境，注重语言实际应用

**英语情境创设类型**：
1. **旅行游记情境**：问路指路、酒店入住、餐厅点餐、景点参观（适用于交际用语、方向介词）
2. **校园生活情境**：结交朋友、课堂对话、社团活动、运动会（适用于日常交流、现在时态）
3. **文化交流情境**：节日庆祝、习俗对比、礼仪差异、饮食文化（适用于文化词汇、比较级）
4. **职场体验情境**：面试求职、工作汇报、商务会议、客户服务（适用于正式用语、将来时态）
5. **日常生活情境**：购物消费、健康管理、娱乐活动、家庭聚会（适用于生活词汇、各种时态）
6. **媒体素养情境**：新闻阅读、广告分析、社交媒体、影视评论（适用于读写技能、被动语态）

**情境导入页设计要求**：
1. **情境描述（scenario_description）**：用英语或双语描述具体场景，让学生有身临其境的感觉
2. **引导问题（guiding_question）**：提出 1 个可以用英语解决的问题，如"How would you ask for directions?"
3. **视觉建议（visual_suggestion）**：描述相关的图示（如地图、菜单、对话场景等）
4. **情境类型（scenario_type）**：从以上 6 种类型中选择最贴合教学内容的情境

**输出格式要求**：
在 Warm-up/Lead-in 页面中，必须包含 `scenario` 字段：
```json
{{
    "page_type": "情境导入页",
    "title": "Engaging Title",
    "scenario": {{
        "scenario_description": "Situation description in English or bilingual",
        "guiding_question": "Guiding question to spark inquiry",
        "visual_suggestion": "Visual aid suggestion",
        "scenario_type": "Scenario type"
    }}
}}
```

【英语学科深度增强要求】

### 一、词根词缀分解（Word Analysis）

1. **词根分析页**：
   - 词根（root）：单词的核心部分，表示基本意义
   - 词根来源（拉丁/希腊/古英语）
   - 词根含义
   - 同根词族（word family）

2. **前缀分析页**：
   - 前缀（prefix）：加在词根前面，改变词义
   - 常见前缀：un-/dis-/re-/pre-/mis-/inter-等
   - 前缀含义解析
   - 举例说明

3. **后缀分析页**：
   - 后缀（suffix）：加在词根后面，改变词性或词义
   - 名词后缀：-tion/-ment/-ness/-ity 等
   - 动词后缀：-ize/-fy/-ate 等
   - 形容词后缀：-able/-ful/-less/-ive 等
   - 副词后缀：-ly 等

4. **构词法图解页**：
   - 单词 = 前缀 + 词根 + 后缀
   - 用树状图/流程图展示构词过程
   - 记忆技巧

5. **词源故事页**：
   - 单词的历史来源
   - 词义演变过程
   - 相关文化背景

### 二、固定搭配网络（Collocations Network）

1. **短语搭配页**：
   - 动词短语（phrasal verbs）
   - 介词短语（prepositional phrases）
   - 固定搭配（fixed expressions）
   - 惯用语（idioms）

2. **词汇网络页**：
   - 核心词（core word）
   - 同义词（synonyms）
   - 反义词（antonyms）
   - 上义词（hypernyms）
   - 下义词（hyponyms）
   - 相关词（related words）

3. **搭配矩阵页**：
   - 动词 + 名词搭配
   - 形容词 + 名词搭配
   - 副词 + 动词搭配
   - 用表格/矩阵展示

4. **语境运用页**：
   - 搭配在句子中的运用
   - 搭配在对话中的运用
   - 搭配在语篇中的运用

### 三、语法树（Syntax Tree）

1. **句子成分分析页**：
   - 主语（Subject）
   - 谓语（Predicate）
   - 宾语（Object）
   - 定语（Attribute）
   - 状语（Adverbial）
   - 补语（Complement）
   - 表语（Predicative）

2. **句法树图解页**：
   - S（句子）→ NP（名词短语）+ VP（动词短语）
   - NP → Det（限定词）+ N（名词）
   - VP → V（动词）+ NP/AdjP/PP 等
   - 用树状图展示句子结构

3. **从句分析页**：
   - 名词性从句（主语从句/宾语从句/表语从句/同位语从句）
   - 定语从句（限制性/非限制性）
   - 状语从句（时间/地点/原因/条件/让步/目的/结果）
   - 引导词分析

4. **特殊句型页**：
   - 被动语态
   - 倒装句
   - 强调句
   - 虚拟语气
   - 非谓语动词结构

### 四、时态时间轴（Tense Timeline）

1. **时态概览页**：
   - 16 种时态总览表
   - 四大时间：现在/过去/将来/过去将来
   - 四大状态：一般/进行/完成/完成进行

2. **时间轴图示页**：
   - 时间轴线（过去 ←→ 现在 ←→ 将来）
   - 动作发生点
   - 动作持续段
   - 参照时间点

3. **现在时态组页**：
   - 一般现在时：习惯、真理
   - 现在进行时：正在进行
   - 现在完成时：过去动作对现在的影响
   - 现在完成进行时：从过去持续到现在

4. **过去时态组页**：
   - 一般过去时：过去发生的动作
   - 过去进行时：过去某时正在进行
   - 过去完成时：过去的过去
   - 过去完成进行时：持续到过去某时

5. **将来时态组页**：
   - 一般将来时：将要发生
   - 将来进行时：将来某时正在进行
   - 将来完成时：到将来某时已完成
   - 将来完成进行时：持续到将来某时

6. **时态对比页**：
   - 易混时态对比（如现在完成时 vs 一般过去时）
   - 时间状语对比
   - 用法区别

n### 五、错题分析页（feat-041 智能错题分析）

1. **常见错误类型**：
   - 拼写错误：单词拼写错误、大小写错误
   - 时态混用：时态不一致、时态选择错误
   - 搭配错误：动词短语搭配错误、介词使用错误
   - 语序颠倒：疑问句语序、从句语序错误
   - 主谓不一致：单复数不一致、人称不一致

2. **错题分析页设计要求**：
   - 错误示例：展示学生常见错误句子
   - 错误原因：分析为什么这个答案是错误的
   - 正确解法：给出正确的句子表达
   - 预防策略：如何避免这类错误

3. **输出格式要求**：
   ```json
   {
     "page_type": "错题分析页",
     "title": "Common Mistakes",
     "common_mistakes": [
       {
         "mistake_type": "错误类型",
         "mistake_example": "错误示例句子",
         "reason": "错误原因分析",
         "correct_method": "正确句子",
         "prevention_strategy": "预防策略"
       }
     ]
   }
   ```
【PPT 结构建议】
1. **封面页**：Unit/Topic + Grade + Teacher
2. **Learning Objectives**（1 页）：本节课的学习目标
3. **Warm-up/Lead-in（情境导入）**（1 页）：创设情境、激发兴趣（必须包含 scenario 字段）
4. **Vocabulary Learning**（3-4 页）：
   - 单词呈现（含词根词缀分析）
   - 词汇网络（同义词/反义词/搭配）
   - 单词操练、运用
5. **Grammar Focus**（3-4 页）：
   - 语法规则呈现（含语法树分析）
   - 时态时间轴可视化
   - 结构分析、操练活动
6. **Dialogue/Text Study**（2-3 页）：听/读理解、语言点、跟读模仿
7. **Practice/Production**（2-3 页）：控制性练习、半控制练习、自由表达
8. **Summary & Homework**（1 页）：总结 + 作业

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 语法树与句子应在同一页对照呈现
- 时态时间轴需清晰标注动作发生点和参照点
- 复杂词汇网络分步展示：拆分为 2-3 页逐步展开

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题（单元/主题名称）",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            # 情境导入页字段（feat-039）
            "scenario": {{"scenario_description": "情境描述", "guiding_question": "引导问题", "visual_suggestion": "视觉建议", "scenario_type": "情境类型"}},
            "vocabulary": [{{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句"}}],
            "word_analysis": {{"root": "词根", "prefix": "前缀", "suffix": "后缀", "etymology": "词源"}},
            "collocations": {{"phrases": ["短语 1", "短语 2"], "synonyms": ["同义词"], "antonyms": ["反义词"]}},
            "grammar": "语法规则说明",
            "syntax_tree": {{"sentence": "原句", "structure": "S → NP + VP", "components": [{{"name": "成分名", "type": "成分类型", "text": "对应文本"}}]}},
            "tense_timeline": {{"tense": "时态名", "time_axis": "时间轴描述", "reference_point": "参照点", "action_point": "动作点"}},
            "dialogue": "对话内容",
            "exercise": "练习题描述"
        }}
    ],
    "vocabulary_list": [{{"word": "单词", "phonetic": "音标", "meaning": "释义", "example": "例句", "word_family": ["同根词"]}}],
    "grammar_points": [{{"name": "语法点名", "explanation": "解释", "example": "例句"}}],
    "word_network": {{
        "core_words": ["核心词"],
        "synonyms": {{}},
        "antonyms": {{}},
        "collocations": {{}}
    }},
    "tense_overview": [{{"tense": "时态名", "usage": "用法", "time_marker": "时间状语", "example": "例句"}}],
    "summary": "整体内容总结"
}}

请生成内容，确保学生能够在情境中学习、在运用中掌握，同时理解词汇构词规律、掌握句法分析能力、建立时态时间概念。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建英语学科的输出结构定义（深度增强版）

        Args:
            slide_count: 幻灯片数量
            difficulty_level: 教学层次（unified/basic/intermediate/advanced）
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/情境导入页/单词学习页/语法讲解页/情景对话页/课文分析页/课堂练习页/总结回顾页/词根词缀页/固定搭配页/语法树页/时态时间轴页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 情境导入页字段（feat-039）
                    "scenario": {
                        "scenario_description": "情境描述（英语或双语描述具体场景）",
                        "guiding_question": "引导性问题（用英语提出问题）",
                        "visual_suggestion": "视觉素材建议",
                        "scenario_type": "情境类型（旅行游记/校园生活/文化交流/职场体验/日常生活/媒体素养）"
                    },
                    # 基础词汇字段
                    "vocabulary": [
                        {
                            "word": "单词",
                            "phonetic": "音标",
                            "meaning": "释义",
                            "example": "例句"
                        }
                    ],
                    # 词根词缀分析字段（新增）
                    "word_analysis": {
                        "root": "词根（如：spect=看）",
                        "root_origin": "词根来源（拉丁/希腊/古英语）",
                        "root_meaning": "词根含义",
                        "prefix": "前缀（如：re-/un-/dis-）",
                        "prefix_meaning": "前缀含义",
                        "suffix": "后缀（如：-tion/-able）",
                        "suffix_function": "后缀功能（改变词性/词义）",
                        "etymology": "词源故事",
                        "word_family": ["同根词 1", "同根词 2"],
                        "structure_diagram": "构词法图解（前缀 + 词根 + 后缀）"
                    },
                    # 固定搭配网络字段（新增）
                    "collocations": {
                        "phrasal_verbs": ["动词短语 1", "动词短语 2"],
                        "prepositional_phrases": ["介词短语 1", "介词短语 2"],
                        "fixed_expressions": ["固定表达 1", "固定表达 2"],
                        "idioms": ["惯用语 1", "惯用语 2"],
                        "synonyms": [
                            {"word": "同义词", "similarity": "相似度", "usage_diff": "用法区别"}
                        ],
                        "antonyms": [
                            {"word": "反义词", "contrast": "对比说明"}
                        ],
                        "hypernym": "上义词",
                        "hyponyms": ["下义词 1", "下义词 2"],
                        "collocation_matrix": {
                            "verb_noun": [["动词", "名词搭配"]],
                            "adj_noun": [["形容词", "名词搭配"]],
                            "adverb_verb": [["副词", "动词搭配"]]
                        }
                    },
                    # 基础语法字段
                    "grammar": "语法规则说明（如适用）",
                    # 语法树字段（新增）
                    "syntax_tree": {
                        "sentence": "原句",
                        "sentence_type": "句子类型（陈述/疑问/祈使/感叹）",
                        "main_structure": "主干结构（如：S → NP + VP）",
                        "components": [
                            {
                                "name": "成分名称（如：主语/谓语/宾语）",
                                "type": "成分类型（NP/VP/AdjP/AdvP/PP）",
                                "text": "对应的文本内容",
                                "position": "位置（句首/句中/句末）",
                                "function": "功能说明"
                            }
                        ],
                        "tree_diagram": "树状图描述（S → NP + VP → Det + N + V + ...）",
                        "clause_analysis": {
                            "main_clause": "主句",
                            "subordinate_clauses": [
                                {
                                    "type": "从句类型（名词性/定语/状语）",
                                    "introducer": "引导词",
                                    "function": "从句功能",
                                    "text": "从句内容"
                                }
                            ]
                        }
                    },
                    # 时态时间轴字段（新增）
                    "tense_timeline": {
                        "tense_name": "时态名称（如：现在完成时）",
                        "tense_group": "时态组（现在/过去/将来/过去将来）",
                        "aspect": "状态（一般/进行/完成/完成进行）",
                        "time_axis_description": "时间轴描述",
                        "reference_point": "参照时间点（现在/过去某时/将来某时）",
                        "action_point": "动作发生点",
                        "duration": "动作持续段",
                        "visual_description": "可视化描述（时间轴线 + 标记）",
                        "usage": "用法说明",
                        "time_markers": ["常用时间状语 1", "常用时间状语 2"],
                        "comparison": {
                            "similar_tense": "易混时态",
                            "difference": "区别说明"
                        }
                    },
                    "dialogue": "对话内容（如适用）",
                    "exercise": "练习题描述（如适用）",
                    # 错题分析字段 (feat-041)
                    "common_mistakes": [
                        {
                            "mistake_type": "错误类型（拼写错误/时态混用/搭配错误/语序颠倒）",
                            "mistake_example": "错误示例句子",
                            "reason": "错误原因分析",
                            "correct_method": "正确解法/句子",
                            "prevention_strategy": "预防策略"
                        }
                    ],
                }
                for _ in range(slide_count)
            ],
            # 词汇列表（增强版）
            "vocabulary_list": [
                {
                    "word": "单词",
                    "phonetic": "音标",
                    "meaning": "释义",
                    "example": "例句",
                    "word_family": ["同根词 1", "同根词 2"],
                    "word_analysis": {
                        "root": "词根",
                        "prefix": "前缀",
                        "suffix": "后缀"
                    },
                    "collocations": ["固定搭配 1", "固定搭配 2"]
                }
            ],
            # 语法点（增强版）
            "grammar_points": [
                {
                    "name": "语法点名称",
                    "explanation": "解释",
                    "structure": "结构公式",
                    "example": "例句",
                    "syntax_analysis": {
                        "sentence": "例句",
                        "tree": "语法树分析"
                    },
                    "tense_info": {
                        "tense": "时态",
                        "timeline": "时间轴描述"
                    }
                }
            ],
            # 词汇网络（新增）
            "word_network": {
                "core_words": [
                    {
                        "word": "核心词",
                        "definition": "定义",
                        "part_of_speech": "词性"
                    }
                ],
                "synonyms": {
                    "word1": [
                        {"word": "同义词", "similarity": "相似度", "usage_diff": "用法区别"}
                    ]
                },
                "antonyms": {
                    "word1": [
                        {"word": "反义词", "contrast": "对比说明"}
                    ]
                },
                "collocations": {
                    "word1": {
                        "verb_noun": ["动宾搭配"],
                        "adj_noun": ["形名搭配"],
                        "phrases": ["短语搭配"]
                    }
                }
            },
            # 时态概览（新增）
            "tense_overview": [
                {
                    "tense": "时态名称",
                    "tense_group": "时态组",
                    "aspect": "状态",
                    "usage": "用法说明",
                    "structure": "结构公式",
                    "time_marker": ["时间状语"],
                    "example": "例句",
                    "timeline_visual": "时间轴可视化描述"
                }
            ],
            # 总结
            "summary": "整体内容总结（知识 + 能力 + 素养）"
        }

    def get_page_types(self) -> List[str]:
        """
        获取英语学科支持的页面类型列表（深度增强版）
        """
        return [
            "封面页",
            "目录页",
            "情境导入页",        # 情境创设自动生成（feat-039）
            # 基础页面类型
            "单词学习页",
            "语法讲解页",
            "情景对话页",
            "课文分析页",
            "课堂练习页",
            "总结回顾页",
            # 词根词缀相关（新增）
            "词根词缀页",        # 词根/前缀/后缀分析
            "构词法图解页",      # 单词构成树状图
            "词源故事页",        # 单词来源和文化背景
            # 固定搭配相关（新增）
            "固定搭配页",        # 短语/搭配/惯用语
            "词汇网络页",        # 同义词/反义词/上义词/下义词
            "搭配矩阵页",        # 搭配表格
            # 语法树相关（新增）
            "语法树页",          # 句子成分分析
            "句法结构页",        # 树状图展示
            "从句分析页",        # 各类从句讲解
            "特殊句型页",        # 被动/倒装/强调/虚拟
            # 时态时间轴相关（新增）
            "时态时间轴页",      # 时态可视化
            "时态概览页",        # 16 种时态总览
            "时态对比页",        # 易混时态对比
        ]
