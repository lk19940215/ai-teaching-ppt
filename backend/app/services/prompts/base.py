"""
提示词引擎基类定义
提供可插拔的学科提示词策略系统接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class SubjectPromptStrategy(ABC):
    """
    学科提示词策略基类

    每个学科策略需要实现三个核心方法：
    1. build_prompt: 构建该学科的提示词
    2. build_schema: 构建该学科的输出结构
    3. get_page_types: 获取该学科支持的页面类型
    """

    # 年级对应的深度描述（所有学科共享）
    GRADE_DESCRIPTIONS = {
        "1": "小学一年级（需要用最简单的语言、大量图片、拼音标注）",
        "2": "小学二年级（需要用简单的语言、配合图片）",
        "3": "小学三年级（需要用通俗易懂的语言、配合插图）",
        "4": "小学四年级（需要用清晰的语言、加入互动游戏）",
        "5": "小学五年级（需要用详细的语言、添加思考题）",
        "6": "小学六年级（需要用准确的语言、添加练习题）",
        "7": "初中一年级（需要用正式的语言、建立知识体系）",
        "8": "初中二年级（需要用严谨的语言、深入讲解）",
        "9": "初中三年级（需要用专业的语言、重点突出）",
        "10": "高中一年级（需要用系统化的语言、注重知识深度和广度、培养抽象思维）",
        "11": "高中二年级（需要用学术化的语言、强调知识迁移和综合运用、高考导向）",
        "12": "高中三年级（需要用精炼专业的语言、强化考点突破和应试技巧、冲刺高考）",
    }

    # 学科特色描述（所有学科共享）
    SUBJECT_DESCRIPTIONS = {
        "chinese": "语文（注重拼音、朗读、感悟、书写）",
        "math": "数学（注重逻辑思维、计算、应用题、图形）",
        "english": "英语（注重单词、发音、句型、情景对话）",
        "science": "科学（注重实验、观察、探究、记录）",
        "physics": "物理（注重公式、实验、原理、应用）",
        "chemistry": "化学（注重反应、实验、结构、性质）",
        "biology": "生物（注重观察、实验、生命过程、生态系统）",
        "history": "历史（注重时间线、事件、人物、因果关系）",
        "politics": "政治（注重概念、原理、联系实际、价值观念）",
        "geography": "地理（注重地图、位置、环境、人文）",
        "general": "通用学科",
    }

    @abstractmethod
    def build_prompt(
        self,
        content: str,
        grade: str,
        subject: str,
        slide_count: int,
        chapter: Optional[str] = None
    ) -> str:
        """
        构建该学科的 PPT 内容生成提示词

        Args:
            content: 教学内容
            grade: 年级
            subject: 学科
            slide_count: 幻灯片数量
            chapter: 章节名称（可选）

        Returns:
            构建好的提示词
        """
        pass

    @abstractmethod
    def build_schema(self, slide_count: int) -> Dict[str, Any]:
        """
        构建该学科的输出结构定义

        Args:
            slide_count: 幻灯片数量

        Returns:
            JSON Schema 结构定义
        """
        pass

    @abstractmethod
    def get_page_types(self) -> List[str]:
        """
        获取该学科支持的页面类型列表

        Returns:
            页面类型字符串列表
        """
        pass

    def get_grade_description(self, grade: str) -> str:
        """获取年级描述"""
        return self.GRADE_DESCRIPTIONS.get(grade, f"未知年级 {grade}")

    def get_subject_description(self, subject: str) -> str:
        """获取学科描述"""
        return self.SUBJECT_DESCRIPTIONS.get(subject, self.SUBJECT_DESCRIPTIONS["general"])


class CognitiveLoadMixin:
    """
    认知负荷优化混入类

    基于 Mayer 多媒体学习理论，控制每页信息量和呈现方式
    包含 5 大核心原则：聚焦要义、空间邻近、时间邻近、切块呈现、冗余控制
    """

    # 年级对应的最大要点数（聚焦要义原则）
    MAX_POINTS_PER_SLIDE = {
        "1": 2,
        "2": 2,
        "3": 3,
        "4": 3,
        "5": 4,
        "6": 4,
        "7": 4,
        "8": 5,
        "9": 5,
        "10": 5,
        "11": 6,
        "12": 6,
    }

    # 复杂概念分块规则（切块呈现原则）
    # 定义哪些内容类型需要分块展示
    COMPLEX_CONCEPT_TYPES = [
        "公式推导",
        "语法树分析",
        "时态对比",
        "实验步骤",
        "化学反应过程",
        "生命活动过程",
        "历史因果链",
        "地理过程",
        "政治原理推导",
    ]

    def get_max_points_for_grade(self, grade: str) -> int:
        """
        获取指定年级每页最大要点数（聚焦要义原则）

        Args:
            grade: 年级（1-12）

        Returns:
            每页最大要点数
        """
        return self.MAX_POINTS_PER_SLIDE.get(grade, 4)

    def get_chunk_size_for_grade(self, grade: str) -> int:
        """
        获取指定年级的分块大小（切块呈现原则）

        复杂概念需要拆分的页数
        """
        chunk_mapping = {
            "1": 3,  # 低年级拆分为更多页
            "2": 3,
            "3": 3,
            "4": 2,
            "5": 2,
            "6": 2,
            "7": 2,
            "8": 2,
            "9": 2,
            "10": 2,
            "11": 2,
            "12": 2,
        }
        return chunk_mapping.get(grade, 2)

    def apply_cognitive_load_constraints(self, prompt: str, grade: str) -> str:
        """
        应用认知负荷约束到提示词

        基于 Mayer 多媒体学习理论的 5 大原则：
        1. 聚焦要义原则（Coherence Principle）：每页内容不超过指定要点数
        2. 空间邻近原则（Spatial Contiguity Principle）：图示与文字在同一页
        3. 时间邻近原则（Temporal Contiguity Principle）：相关内容同时呈现
        4. 切块呈现原则（Segmenting Principle）：复杂内容分步展示
        5. 冗余控制原则（Redundancy Principle）：避免重复信息

        Args:
            prompt: 原始提示词
            grade: 年级

        Returns:
            增强后的提示词
        """
        max_points = self.get_max_points_for_grade(grade)
        chunk_size = self.get_chunk_size_for_grade(grade)

        constraints = f"""

【认知负荷优化要求 - 基于 Mayer 多媒体学习理论】

1. **聚焦要义原则**：每页内容不超过{max_points}个要点，去除冗余信息，保持内容精炼
2. **空间邻近原则**：相关的文字说明和图示必须在同一页呈现，避免学生来回翻看
3. **切块呈现原则**：复杂概念（如公式推导、语法分析、实验过程等）拆分为{chunk_size}页逐步展开，每页聚焦一个子步骤
4. **冗余控制原则**：避免用文字重复图示/表格已清晰表达的信息，图文并茂但不重复
5. **时间邻近原则**：讲解语音与对应画面应同步呈现，避免先讲后看或先看后讲"""

        return prompt + constraints

    def needs_chunking(self, concept_type: str) -> bool:
        """
        判断某概念类型是否需要分块展示

        Args:
            concept_type: 概念类型

        Returns:
            是否需要分块
        """
        return concept_type in self.COMPLEX_CONCEPT_TYPES

    def get_suggested_layout(self, page_type: str) -> str:
        """
        根据页面类型建议布局方式

        Args:
            page_type: 页面类型

        Returns:
            布局建议
        """
        layout_suggestions = {
            "公式推导页": "上一步骤 + 下一步骤分两栏展示，箭头连接表示推导关系",
            "语法树页": "左侧原句 + 右侧树状图对照",
            "实验步骤页": "顶部步骤说明 + 底部操作图示",
            "时间轴页": "水平时间轴贯穿页面，事件标注在轴上下方",
            "对比分析页": "左右分栏对比，中间用虚线分隔",
            "概念引入页": "顶部生活实例图 + 底部抽象概念定义",
        }
        return layout_suggestions.get(page_type, "标准布局：标题 + 要点列表 + 底部图示")
