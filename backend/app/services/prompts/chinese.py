"""
语文学科提示词策略
专为语文教学设计的提示词模板
"""

from typing import Dict, Any, List, Optional
from .base import SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin


class ChinesePromptStrategy(SubjectPromptStrategy, CognitiveLoadMixin, BloomTaxonomyMixin):
    """
    语文学科提示词策略

    专为语文教学设计，包含：
    1. 古诗鉴赏：朗读节奏、意象分析、背景知识
    2. 字词教学：字形演变、组词造句、近反义词
    3. 阅读理解：段落分析、修辞手法、主题思想
    4. 作文指导：审题立意、结构框架、好词好句
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
        构建语文学科的 PPT 内容生成提示词
        """
        grade_desc = self.get_grade_description(grade)
        max_points = self.get_max_points_for_grade(grade)

        prompt = f"""你是一位经验丰富的语文教师，请根据以下语文教学内容，设计一份高质量的语文教学 PPT。

【教学内容】
{content}

【教学信息】
- 年级：{grade} - {grade_desc}
- 学科：语文
- 章节名称：{chapter if chapter else '未指定'}
- 幻灯片数量：{slide_count} 页

【语文教学原则】
1. **工具性与人文性统一**：既重视语言文字运用能力，又注重人文素养熏陶
2. **诵读感悟**：通过朗读、背诵体会语言韵律和情感
3. **品词析句**：品味关键词句的表达效果和深层含义
4. **读写结合**：以读促写，以写带读，相互促进
5. **文化传承**：渗透中华优秀传统文化，培养文化自信

【语文专属教学要求】
1. **古诗鉴赏页**：
   - 原文展示（带朗读节奏划分）
   - 作者及背景介绍
   - 逐句翻译和意象分析
   - 诗歌意境和主旨感悟
   - 朗读指导（停顿、重音、语调）

2. **字词教学页**：
   - 生字认读（字 + 拼音 + 部首 + 笔画）
   - 字形演变（甲骨文→金文→小篆→楷书，可选）
   - 组词练习（2-3 个常用词）
   - 造句示范（1-2 个典型例句）
   - 近反义词拓展

3. **阅读理解页**：
   - 段落层次划分
   - 关键句赏析（修辞手法、表达效果）
   - 主题思想提炼
   - 写作特色分析
   - 拓展思考问题

4. **作文指导页**：
   - 审题立意（关键词分析、立意角度）
   - 结构框架（开头→主体→结尾的布局）
   - 素材积累（相关事例、名言警句）
   - 好词好句（优美词句积累）
   - 常见误区提醒

【PPT 结构建议】
1. **封面页**：课题 + 年级 + 教师
2. **学习目标**（1 页）：知识与能力、过程与方法、情感态度价值观
3. **导入新课**（1 页）：情境创设、激趣导入
4. **字词学习**（2-3 页）：生字认读、词语理解、书写指导
5. **课文研读**（3-4 页）：整体感知→局部品析→主旨提炼
6. **古诗鉴赏**（2-3 页，如适用）：朗读→理解→赏析→背诵
7. **拓展延伸**（1-2 页）：比较阅读、迁移运用
8. **作业布置**（1 页）：巩固性作业 + 拓展性作业

【认知负荷优化要求】
- 每页内容不超过{max_points}个要点，避免信息过载
- 图文并茂：图示与文字说明应在同一页呈现
- 复杂内容分步展示：拆分为 2-3 页逐步展开
- 避免冗余：文字不要重复图示已表达的信息

【输出结构要求】
请严格按照以下 JSON 结构生成内容：
{{
    "title": "PPT 标题",
    "slides": [
        {{
            "page_type": "页面类型",
            "title": "页面标题",
            "content": ["页面内容要点"],
            "character": {{"word": "字", "pinyin": "拼音", "radical": "部首", "strokes": "笔画"}},
            "poem": {{"title": "诗名", "author": "作者", "dynasty": "朝代", "lines": ["诗句 1", "诗句 2"], "analysis": "赏析"}},
            "reading": {{"paragraph": "段落", "key_sentence": "关键句", "analysis": "赏析", "theme": "主题思想"}},
            "writing": {{"topic": "题目", "structure": ["开头", "主体", "结尾"], "tips": "写作提示"}}
        }}
    ],
    "vocabulary_list": [{{"word": "词语", "pinyin": "拼音", "meaning": "释义", "example": "例句"}}],
    "key_points": ["重点 1", "重点 2"],
    "summary": "总结"
}}

请生成内容，确保学生在语言文字运用和人文素养方面都能得到提升。"""

        # 应用认知负荷约束
        prompt = self.apply_cognitive_load_constraints(prompt, grade)

        # 应用布鲁姆分类法约束
        prompt += self.get_bloom_prompt_section(grade, subject)

        return prompt

    def build_schema(self, slide_count: int, difficulty_level: str = "unified") -> Dict[str, Any]:
        """
        构建语文学科的输出结构定义
        """
        return {
            "title": "PPT 标题（章节名称）",
            "slides": [
                {
                    "page_type": "封面页/目录页/生字学习页/古诗鉴赏页/阅读理解页/作文指导页/段落分析页/修辞手法页/课堂练习页/总结回顾页",
                    "title": "页面标题",
                    "content": ["页面内容要点 1", "页面内容要点 2"],
                    # 生字学习页字段
                    "character": {
                        "word": "生字",
                        "pinyin": "拼音",
                        "radical": "部首",
                        "strokes": "笔画数",
                        "structure": "字形结构（左右/上下/独体等）",
                        "evolution": ["甲骨文", "金文", "小篆", "楷书"],  # 可选
                        "groups": ["组词 1", "组词 2"],
                        "sentences": ["造句 1", "造句 2"],
                        "synonyms": ["近义词 1", "近义词 2"],
                        "antonyms": ["反义词 1", "反义词 2"]
                    },
                    # 古诗鉴赏页字段
                    "poem": {
                        "title": "诗名",
                        "author": "作者",
                        "dynasty": "朝代",
                        "lines": ["诗句 1", "诗句 2", "诗句 3", "诗句 4"],
                        "rhythm": "朗读节奏（如：床前/明月/光）",
                        "translation": "逐句翻译",
                        "imagery": ["意象 1", "意象 2"],
                        "theme": "主旨思想",
                        "appreciation": "艺术特色赏析"
                    },
                    # 阅读理解页字段
                    "reading": {
                        "paragraph": "段落内容",
                        "structure": "段落层次划分",
                        "key_sentence": "关键句",
                        "rhetoric": "修辞手法",
                        "analysis": "赏析",
                        "theme": "主题思想"
                    },
                    # 作文指导页字段
                    "writing": {
                        "topic": "作文题目",
                        "keywords": ["关键词 1", "关键词 2"],
                        "angle": "立意角度",
                        "structure": ["开头方法", "主体展开", "结尾技巧"],
                        "materials": ["素材 1", "素材 2"],
                        "good_words": ["好词 1", "好词 2"],
                        "good_sentences": ["好句 1", "好句 2"],
                        "tips": "写作注意事项"
                    }
                }
                for _ in range(slide_count)
            ],
            "vocabulary_list": [
                {
                    "word": "词语",
                    "pinyin": "拼音",
                    "meaning": "释义",
                    "part_of_speech": "词性",
                    "example": "例句"
                }
            ],
            "key_points": ["重点 1", "重点 2", "重点 3"],
            "summary": "整体内容总结"
        }

    def get_page_types(self) -> List[str]:
        """
        获取语文学科支持的页面类型列表
        """
        return [
            "封面页",
            "目录页",
            "生字学习页",        # 语文专属：字 + 拼音 + 组词 + 造句
            "古诗鉴赏页",        # 语文专属：原文 + 注释 + 赏析
            "阅读理解页",        # 语文专属：段落分析 + 主题提炼
            "作文指导页",        # 语文专属：审题 + 结构 + 素材
            "段落分析页",        # 语文专属：层次划分 + 关键句
            "修辞手法页",        # 语文专属：比喻/拟人/排比等
            "课堂练习页",
            "总结回顾页",
            "图示页",
            "表格页",
            "对比分析页",
        ]
