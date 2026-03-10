# -*- coding: utf-8 -*-
"""
教学语义提取器
解析 PPT 时提取 slide_type、teaching_role、knowledge_points

设计文档: .claude-coder/plans/ppt-merge-technical-design.md#2.4-教学语义提取
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..models.ppt_structure import (
    ElementData, ElementType, SlideType, TeachingRole, TeachingContent
)

logger = logging.getLogger(__name__)


@dataclass
class SemanticExtractionResult:
    """语义提取结果"""
    slide_type: SlideType
    teaching_role: TeachingRole
    knowledge_points: List[str]
    confidence: float  # 置信度 0-1


class TeachingSemanticExtractor:
    """教学语义提取器"""

    # 教学角色关键词映射
    TEACHING_ROLE_KEYWORDS: Dict[TeachingRole, List[str]] = {
        TeachingRole.COVER: ['封面', '标题', '课件', '课程', '教学'],
        TeachingRole.OUTLINE: ['目录', 'contents', 'outline', '内容', '章节', '结构'],
        TeachingRole.CONCEPT: [
            '概念', '定义', '什么是', '含义', '意义', '性质', '特点', '特征',
            '原理', '理论', '知识点', '知识', '认识', '理解'
        ],
        TeachingRole.EXAMPLE: [
            '例题', '示例', '例', '示范', '演示', '实例', '案例', '举例',
            '解析', '解答', '求解'
        ],
        TeachingRole.EXERCISE: [
            '练习', '习题', '试一试', '练一练', '巩固', '检测', '测试',
            '题目', '题', '做一做', '算一算', '填一填'
        ],
        TeachingRole.SUMMARY: [
            '总结', '小结', '回顾', '归纳', '梳理', '整理', '复习',
            '要点', '重点', '难点', '关键', '核心'
        ],
        TeachingRole.HOMEWORK: [
            '作业', '课后', '练习册', '课后题', '家庭作业', '思考题',
            '拓展', '延伸', '预习'
        ],
    }

    # 页面类型特征规则
    SLIDE_TYPE_RULES: List[Tuple[SlideType, Dict[str, Any]]] = [
        # 封面页：第一页，通常有标题无正文
        (SlideType.TITLE_SLIDE, {
            'is_first_slide': True,
        }),
        # 目录页：有列表项或数字序列，标题可能是"目录"或"Contents"
        (SlideType.OUTLINE_SLIDE, {
            'keyword_patterns': [r'目录|contents|outline', r'\d+[\.\s]'],
            'element_ratio': {'list_item': 0.3},  # 列表项占比
        }),
        # 章节页：无正文或正文很少，通常是章节标题
        (SlideType.SECTION_SLIDE, {
            'min_body_text_ratio': 0.0,
            'max_body_text_ratio': 0.1,
            'has_title': True,
        }),
        # 结束页：最后一页或包含感谢语
        (SlideType.END_SLIDE, {
            'keyword_patterns': [r'谢谢|感谢|thank|end|结束|再见'],
        }),
    ]

    # 知识点提取模式
    KNOWLEDGE_PATTERNS: List[re.Pattern] = [
        # 定义模式："...是..."、"...叫做..."、"...称为..."
        re.compile(r'([^。；\n]+(?:是|叫做|称为|定义为|表示|指)[^。；\n]+)'),
        # 规则模式："...法则"、"...定理"、"...性质"
        re.compile(r'([^。；\n]*(?:法则|定理|性质|公式|规律|方法|步骤)[^。；\n]*)'),
        # 重点标记模式："重点"、"注意"、"要点"
        re.compile(r'(?:重点|注意|要点|关键)[：:]([^。；\n]+)'),
        # 列表项模式：以"•"、"-"、"1."等开头的完整句子
        re.compile(r'^[•\-\·◆►\d][\s\.]*([^\n]+)', re.MULTILINE),
    ]

    # 学科特定知识点关键词
    SUBJECT_KEYWORDS: Dict[str, List[str]] = {
        'math': [
            '分数', '小数', '整数', '方程', '函数', '几何', '代数', '统计',
            '比例', '百分数', '周长', '面积', '体积', '角度', '三角形',
            '四边形', '圆', '直线', '平面', '坐标', '向量', '集合', '逻辑'
        ],
        'chinese': [
            '拼音', '汉字', '词语', '句子', '段落', '文章', '阅读', '写作',
            '修辞', '比喻', '拟人', '排比', '夸张', '设问', '反问',
            '记叙文', '说明文', '议论文', '散文', '诗歌', '小说'
        ],
        'english': [
            'vocabulary', 'grammar', 'sentence', 'paragraph', 'reading',
            'writing', 'listening', 'speaking', 'tense', 'voice', 'clause'
        ],
        'science': [
            '实验', '观察', '测量', '物质', '能量', '力', '运动', '光',
            '声音', '电', '磁', '化学', '生物', '植物', '动物', '细胞'
        ],
    }

    def __init__(self):
        """初始化提取器"""
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式以提高性能"""
        self._subject_patterns: Dict[str, List[re.Pattern]] = {}
        for subject, keywords in self.SUBJECT_KEYWORDS.items():
            # 匹配完整关键词或包含关键词的短语
            pattern = re.compile(
                r'([^。；\n]*(?:' + '|'.join(keywords) + r')[^。；\n]*)'
            )
            self._subject_patterns[subject] = pattern

    def extract(
        self,
        slide_idx: int,
        total_slides: int,
        elements: List[ElementData],
        title: Optional[str] = None
    ) -> SemanticExtractionResult:
        """
        提取页面教学语义

        Args:
            slide_idx: 页面索引
            total_slides: 总页数
            elements: 页面元素列表
            title: 页面标题

        Returns:
            SemanticExtractionResult 语义提取结果
        """
        # 提取所有文本内容
        all_text = self._extract_all_text(elements)

        # 判断页面类型
        slide_type = self._detect_slide_type(slide_idx, total_slides, elements, title, all_text)

        # 判断教学角色
        teaching_role = self._detect_teaching_role(slide_idx, all_text, title)

        # 提取知识点
        knowledge_points = self._extract_knowledge_points(elements, title, all_text)

        # 计算置信度
        confidence = self._calculate_confidence(slide_type, teaching_role, elements, all_text)

        return SemanticExtractionResult(
            slide_type=slide_type,
            teaching_role=teaching_role,
            knowledge_points=knowledge_points,
            confidence=confidence
        )

    def _extract_all_text(self, elements: List[ElementData]) -> str:
        """提取页面所有文本内容"""
        texts = []
        for elem in elements:
            if elem.text:
                texts.append(elem.text)
        return ' '.join(texts)

    def _detect_slide_type(
        self,
        slide_idx: int,
        total_slides: int,
        elements: List[ElementData],
        title: Optional[str],
        all_text: str
    ) -> SlideType:
        """
        判断页面类型

        基于页面布局特征（标题大小、内容区、图片比例）
        """
        is_first = slide_idx == 0
        is_last = slide_idx == total_slides - 1

        # 统计元素类型
        elem_types = {}
        for elem in elements:
            elem_types[elem.type] = elem_types.get(elem.type, 0) + 1

        total_elems = len(elements) if elements else 1

        # 计算各元素占比
        title_ratio = elem_types.get(ElementType.TITLE, 0) / total_elems
        body_ratio = elem_types.get(ElementType.TEXT_BODY, 0) / total_elems
        list_ratio = elem_types.get(ElementType.LIST_ITEM, 0) / total_elems
        image_ratio = elem_types.get(ElementType.IMAGE, 0) / total_elems

        # 规则 1: 第一页通常是封面页
        if is_first:
            # 但如果第一页有很多正文，可能是内容页
            if body_ratio > 0.3:
                return SlideType.CONTENT_SLIDE
            return SlideType.TITLE_SLIDE

        # 规则 2: 最后一页可能是结束页
        if is_last:
            end_keywords = ['谢谢', '感谢', 'thank', 'end', '结束', '再见']
            if any(kw in all_text.lower() for kw in end_keywords):
                return SlideType.END_SLIDE

        # 规则 3: 目录页特征
        if title and any(kw in title.lower() for kw in ['目录', 'contents', 'outline']):
            return SlideType.OUTLINE_SLIDE

        if list_ratio > 0.3 and body_ratio < 0.2:
            # 主要是列表，可能是目录或总结
            if '目录' in all_text or 'contents' in all_text.lower():
                return SlideType.OUTLINE_SLIDE

        # 规则 4: 章节页特征（标题 + 很少正文）
        if title and body_ratio < 0.1 and list_ratio < 0.1:
            # 检查是否是章节标题（通常包含"第X章"、"Chapter X"）
            chapter_patterns = [
                r'第[一二三四五六七八九十\d]+[章节]',
                r'chapter\s+\d+',
                r'unit\s+\d+',
                r'模块[一二三四五六七八九十\d]+',
            ]
            for pattern in chapter_patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    return SlideType.SECTION_SLIDE

        # 规则 5: 内容页（默认）
        return SlideType.CONTENT_SLIDE

    def _detect_teaching_role(
        self,
        slide_idx: int,
        all_text: str,
        title: Optional[str]
    ) -> TeachingRole:
        """
        判断教学角色

        基于关键词匹配（定义/例题/练习/总结）
        """
        text_lower = all_text.lower()
        title_lower = (title or '').lower()

        # 封面页
        if slide_idx == 0:
            return TeachingRole.COVER

        # 计算每个角色的匹配分数
        role_scores: Dict[TeachingRole, int] = {}

        for role, keywords in self.TEACHING_ROLE_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # 标题匹配权重更高
                if keyword in title_lower:
                    score += 3
                # 正文匹配
                if keyword in text_lower:
                    score += 1
            role_scores[role] = score

        # 排除 COVER（已经在上面处理）
        if TeachingRole.COVER in role_scores:
            del role_scores[TeachingRole.COVER]

        # 返回得分最高的角色
        if role_scores:
            best_role = max(role_scores, key=role_scores.get)
            if role_scores[best_role] > 0:
                return best_role

        # 默认：概念讲解
        return TeachingRole.CONCEPT

    def _extract_knowledge_points(
        self,
        elements: List[ElementData],
        title: Optional[str],
        all_text: str
    ) -> List[str]:
        """
        提取知识点

        从标题和正文提取核心概念
        """
        knowledge_points: List[str] = []
        seen: set = set()

        def add_unique(point: str):
            """添加不重复的知识点"""
            point_clean = point.strip()
            if len(point_clean) < 3 or len(point_clean) > 100:
                return
            # 使用模糊匹配去重
            point_key = point_clean.lower().replace(' ', '')
            if point_key not in seen:
                seen.add(point_key)
                knowledge_points.append(point_clean)

        # 1. 从标题提取
        if title:
            # 去除章节编号
            clean_title = re.sub(r'^第[一二三四五六七八九十\d]+[章节][\s：:]*', '', title)
            clean_title = re.sub(r'^chapter\s+\d+[\s:]*', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'^\d+[\.\s]+', '', clean_title)
            if clean_title and len(clean_title) > 2:
                add_unique(clean_title)

        # 2. 从正文提取知识点模式
        for pattern in self.KNOWLEDGE_PATTERNS:
            matches = pattern.findall(all_text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ''
                add_unique(match)

        # 3. 从列表项提取（通常是知识点列表）
        for elem in elements:
            if elem.type == ElementType.LIST_ITEM and elem.text:
                text = elem.text.strip()
                # 去除列表标记
                text = re.sub(r'^[•\-\·◆►\d][\s\.]*', '', text)
                if text and len(text) > 3:
                    add_unique(text)

        # 4. 从学科关键词提取（可选，用于增强）
        for subject, pattern in self._subject_patterns.items():
            matches = pattern.findall(all_text)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ''
                add_unique(match)

        # 限制数量，按长度排序（优先较长的，通常更完整）
        knowledge_points.sort(key=lambda x: len(x), reverse=True)
        return knowledge_points[:10]  # 最多返回 10 个

    def _calculate_confidence(
        self,
        slide_type: SlideType,
        teaching_role: TeachingRole,
        elements: List[ElementData],
        all_text: str
    ) -> float:
        """
        计算提取置信度

        基于元素丰富度和文本清晰度
        """
        confidence = 0.5  # 基础置信度

        # 有标题增加置信度
        has_title = any(e.type == ElementType.TITLE for e in elements)
        if has_title:
            confidence += 0.1

        # 有正文增加置信度
        has_body = any(e.type == ElementType.TEXT_BODY for e in elements)
        if has_body:
            confidence += 0.1

        # 文本长度适中增加置信度
        text_len = len(all_text)
        if 20 <= text_len <= 500:
            confidence += 0.1
        elif text_len > 500:
            confidence += 0.05  # 太长可能包含噪音

        # 明确识别 teaching_role 增加置信度
        if teaching_role != TeachingRole.UNKNOWN:
            confidence += 0.1

        # 明确识别 slide_type 增加置信度
        if slide_type != SlideType.UNKNOWN:
            confidence += 0.1

        return min(confidence, 1.0)

    def extract_teaching_content(
        self,
        slide_idx: int,
        total_slides: int,
        elements: List[ElementData],
        title: Optional[str] = None
    ) -> TeachingContent:
        """
        提取完整的教学语义内容

        这是便捷方法，直接返回 TeachingContent 对象
        """
        result = self.extract(slide_idx, total_slides, elements, title)

        # 提取要点
        main_points: List[str] = []
        examples: List[str] = []

        for elem in elements:
            if elem.type == ElementType.TEXT_BODY and elem.text:
                text = elem.text.strip()
                if text and len(text) > 5:
                    # 简单判断是否是例子
                    example_keywords = ['例如', '比如', '例', '如', '例：', '例:']
                    if any(kw in text for kw in example_keywords):
                        examples.append(text[:200])
                    else:
                        main_points.append(text[:200])

        return TeachingContent(
            title=title,
            main_points=main_points[:5],  # 最多 5 个要点
            knowledge_points=result.knowledge_points,
            examples=examples[:3],  # 最多 3 个例子
            has_images=any(e.type == ElementType.IMAGE for e in elements),
            has_tables=any(e.type == ElementType.TABLE for e in elements)
        )
