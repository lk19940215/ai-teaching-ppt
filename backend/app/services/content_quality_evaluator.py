"""
内容质量评估器

对 PPT 内容进行多维度质量评估，包括：
- 内容完整性：是否有标题、正文、要点等必要元素
- 逻辑连贯性：内容组织是否合理、层次是否清晰
- 表达准确性：语言表达是否准确、简洁
- 教学适配性：是否符合目标年级和学科的教学要求
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """质量评估维度"""
    COMPLETENESS = "content_completeness"      # 内容完整性
    COHERENCE = "logical_coherence"            # 逻辑连贯性
    ACCURACY = "expression_accuracy"           # 表达准确性
    ADAPTABILITY = "teaching_adaptability"     # 教学适配性


@dataclass
class DimensionScore:
    """维度评分"""
    dimension: QualityDimension
    score: float  # 0-1
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 3),
            "issues": self.issues,
            "suggestions": self.suggestions
        }


@dataclass
class QualityReport:
    """质量评估报告"""
    overall_score: float  # 0-1
    dimension_scores: List[DimensionScore]
    slide_count: int
    total_issues: int
    quality_level: str  # excellent/good/acceptable/poor
    summary: str
    improvement_priority: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 3),
            "quality_level": self.quality_level,
            "slide_count": self.slide_count,
            "total_issues": self.total_issues,
            "dimension_scores": [ds.to_dict() for ds in self.dimension_scores],
            "summary": self.summary,
            "improvement_priority": self.improvement_priority
        }


class ContentQualityEvaluator:
    """
    内容质量评估器

    评估 PPT 内容的质量，支持单页评估和整体报告生成
    """

    # 不同年级的语言复杂度期望
    GRADE_COMPLEXITY_MAP = {
        "1": {"min_words": 20, "max_words": 80, "complexity": "very_low"},
        "2": {"min_words": 25, "max_words": 100, "complexity": "very_low"},
        "3": {"min_words": 30, "max_words": 120, "complexity": "low"},
        "4": {"min_words": 40, "max_words": 150, "complexity": "low"},
        "5": {"min_words": 50, "max_words": 180, "complexity": "medium"},
        "6": {"min_words": 60, "max_words": 200, "complexity": "medium"},
        "7": {"min_words": 80, "max_words": 250, "complexity": "medium"},
        "8": {"min_words": 100, "max_words": 300, "complexity": "medium_high"},
        "9": {"min_words": 120, "max_words": 350, "complexity": "high"},
        "10": {"min_words": 150, "max_words": 400, "complexity": "high"},
        "11": {"min_words": 180, "max_words": 450, "complexity": "very_high"},
        "12": {"min_words": 200, "max_words": 500, "complexity": "very_high"},
    }

    # 必要内容元素
    REQUIRED_ELEMENTS = {
        "cover": ["title"],
        "outline": ["title", "items"],
        "content": ["title", "content"],
        "interactive": ["title", "question"],
        "practice": ["title", "exercise"],
        "summary": ["title", "points"]
    }

    # 学科特色关键词
    SUBJECT_KEYWORDS = {
        "chinese": ["朗读", "拼音", "词语", "句子", "段落", "作文", "诗词", "文言文"],
        "math": ["公式", "定理", "证明", "计算", "方程", "函数", "图形", "几何"],
        "english": ["word", "sentence", "grammar", "dialogue", "vocabulary", "listening"],
        "physics": ["实验", "原理", "公式", "受力分析", "运动", "能量", "电学", "力学"],
        "chemistry": ["反应", "方程式", "元素", "实验", "化学式", "原子", "分子"],
        "biology": ["细胞", "生物", "实验", "遗传", "生态", "进化", "器官"],
        "history": ["时间", "事件", "人物", "朝代", "战争", "改革", "条约"],
        "geography": ["地图", "气候", "地形", "资源", "人口", "城市", "环境"],
        "politics": ["概念", "原理", "观点", "意义", "作用", "关系"],
        "science": ["观察", "实验", "假设", "结论", "现象", "原理"],
        "general": []
    }

    def __init__(self, grade: str = "7", subject: str = "general"):
        """
        初始化内容质量评估器

        Args:
            grade: 年级（1-12）
            subject: 学科
        """
        self.grade = grade
        self.subject = subject
        self.grade_config = self.GRADE_COMPLEXITY_MAP.get(
            grade, self.GRADE_COMPLEXITY_MAP["7"]
        )

    def evaluate_slide_content(self, slide: Dict[str, Any]) -> DimensionScore:
        """
        评估单页幻灯片内容

        Args:
            slide: 幻灯片内容数据

        Returns:
            综合评分结果
        """
        # 计算各维度分数
        completeness = self._evaluate_completeness(slide)
        coherence = self._evaluate_coherence(slide)
        accuracy = self._evaluate_accuracy(slide)
        adaptability = self._evaluate_adaptability(slide)

        # 合并所有问题
        all_issues = completeness.issues + coherence.issues + accuracy.issues + adaptability.issues
        all_suggestions = completeness.suggestions + coherence.suggestions + accuracy.suggestions + adaptability.suggestions

        # 计算综合分数（加权平均）
        weights = {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.COHERENCE: 0.25,
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.ADAPTABILITY: 0.25
        }
        overall = (
            completeness.score * weights[QualityDimension.COMPLETENESS] +
            coherence.score * weights[QualityDimension.COHERENCE] +
            accuracy.score * weights[QualityDimension.ACCURACY] +
            adaptability.score * weights[QualityDimension.ADAPTABILITY]
        )

        return DimensionScore(
            dimension=QualityDimension.COMPLETENESS,  # 用作综合评分的标识
            score=overall,
            issues=all_issues[:5],  # 限制问题数量
            suggestions=all_suggestions[:5]
        )

    def generate_quality_report(self, slides: List[Dict[str, Any]]) -> QualityReport:
        """
        生成整体质量评估报告

        Args:
            slides: 所有幻灯片内容

        Returns:
            质量评估报告
        """
        if not slides:
            return QualityReport(
                overall_score=0.0,
                dimension_scores=[],
                slide_count=0,
                total_issues=1,
                quality_level="poor",
                summary="无内容可评估",
                improvement_priority=["添加幻灯片内容"]
            )

        # 计算各维度的总体分数
        completeness_scores = []
        coherence_scores = []
        accuracy_scores = []
        adaptability_scores = []

        all_issues: Dict[str, List[str]] = {
            "completeness": [],
            "coherence": [],
            "accuracy": [],
            "adaptability": []
        }

        for i, slide in enumerate(slides):
            c = self._evaluate_completeness(slide)
            coh = self._evaluate_coherence(slide)
            a = self._evaluate_accuracy(slide)
            ad = self._evaluate_adaptability(slide)

            completeness_scores.append(c.score)
            coherence_scores.append(coh.score)
            accuracy_scores.append(a.score)
            adaptability_scores.append(ad.score)

            # 收集问题（添加页码前缀）
            for issue in c.issues:
                all_issues["completeness"].append(f"第{i+1}页: {issue}")
            for issue in coh.issues:
                all_issues["coherence"].append(f"第{i+1}页: {issue}")
            for issue in a.issues:
                all_issues["accuracy"].append(f"第{i+1}页: {issue}")
            for issue in ad.issues:
                all_issues["adaptability"].append(f"第{i+1}页: {issue}")

        # 计算平均分数
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        avg_coherence = sum(coherence_scores) / len(coherence_scores)
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        avg_adaptability = sum(adaptability_scores) / len(adaptability_scores)

        # 创建维度评分
        dimension_scores = [
            DimensionScore(
                dimension=QualityDimension.COMPLETENESS,
                score=avg_completeness,
                issues=all_issues["completeness"][:3],
                suggestions=self._get_completeness_suggestions(avg_completeness)
            ),
            DimensionScore(
                dimension=QualityDimension.COHERENCE,
                score=avg_coherence,
                issues=all_issues["coherence"][:3],
                suggestions=self._get_coherence_suggestions(avg_coherence)
            ),
            DimensionScore(
                dimension=QualityDimension.ACCURACY,
                score=avg_accuracy,
                issues=all_issues["accuracy"][:3],
                suggestions=self._get_accuracy_suggestions(avg_accuracy)
            ),
            DimensionScore(
                dimension=QualityDimension.ADAPTABILITY,
                score=avg_adaptability,
                issues=all_issues["adaptability"][:3],
                suggestions=self._get_adaptability_suggestions(avg_adaptability)
            )
        ]

        # 计算总体分数
        overall_score = (avg_completeness + avg_coherence + avg_accuracy + avg_adaptability) / 4

        # 确定质量等级
        quality_level = self._determine_quality_level(overall_score)

        # 总问题数
        total_issues = sum(
            len(issues) for issues in all_issues.values()
        )

        # 生成总结
        summary = self._generate_summary(
            overall_score, quality_level, dimension_scores
        )

        # 确定改进优先级
        improvement_priority = self._determine_improvement_priority(dimension_scores)

        return QualityReport(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            slide_count=len(slides),
            total_issues=total_issues,
            quality_level=quality_level,
            summary=summary,
            improvement_priority=improvement_priority
        )

    def _evaluate_completeness(self, slide: Dict[str, Any]) -> DimensionScore:
        """
        评估内容完整性

        检查是否包含必要元素：标题、正文、要点等
        """
        issues = []
        score = 1.0

        page_type = slide.get("page_type", "content")
        title = slide.get("title", "")
        content = slide.get("content", "")
        elements = slide.get("elements", [])

        # 检查标题
        if not title or len(title.strip()) < 2:
            issues.append("缺少有效的标题")
            score -= 0.3

        # 检查正文内容
        content_text = content
        if isinstance(content, list):
            content_text = " ".join(str(item) for item in content)

        if not content_text or len(content_text.strip()) < 10:
            issues.append("正文内容过少")
            score -= 0.3

        # 检查要点/列表
        points = slide.get("points", slide.get("key_points", []))
        if isinstance(points, list) and len(points) == 0:
            # 内容页应有要点
            if page_type in ["知识点讲解页", "概念引入页", "总结回顾页"]:
                issues.append("缺少要点列表")
                score -= 0.1

        # 检查互动元素
        if page_type in ["互动问答页", "课堂练习页"]:
            question = slide.get("question", slide.get("exercise", ""))
            if not question:
                issues.append("互动/练习页缺少问题")
                score -= 0.2

        score = max(0.0, min(1.0, score))

        return DimensionScore(
            dimension=QualityDimension.COMPLETENESS,
            score=score,
            issues=issues,
            suggestions=self._get_completeness_suggestions(score)
        )

    def _evaluate_coherence(self, slide: Dict[str, Any]) -> DimensionScore:
        """
        评估逻辑连贯性

        检查内容组织是否合理、层次是否清晰
        """
        issues = []
        score = 1.0

        title = slide.get("title", "")
        content = slide.get("content", "")
        points = slide.get("points", slide.get("key_points", []))

        # 将内容转为文本
        content_text = content
        if isinstance(content, list):
            content_text = " ".join(str(item) for item in content)
        if isinstance(points, list):
            content_text += " " + " ".join(str(p) for p in points)

        # 检查标题与内容的相关性
        if title and content_text:
            # 简单的关键词匹配检查
            title_words = set(title)
            content_words = set(content_text)
            overlap = len(title_words & content_words)

            if overlap == 0 and len(title) > 2:
                # 标题和内容没有重叠，可能不相关
                issues.append("标题与内容关联度较低")
                score -= 0.15

        # 检查内容层次
        if isinstance(points, list) and len(points) > 0:
            # 有要点列表，层次较好
            if len(points) > 7:
                issues.append("要点过多，建议分组展示")
                score -= 0.1
            elif len(points) < 2:
                current_page_type = slide.get("page_type", "")
                if current_page_type in ["知识点讲解页", "总结回顾页"]:
                    issues.append("要点数量较少，内容层次不够丰富")
                    score -= 0.1

        # 检查过渡词/连接词
        transition_words = ["因此", "所以", "但是", "然而", "首先", "其次", "最后", "总之", "例如", "比如"]
        has_transition = any(word in content_text for word in transition_words)

        if not has_transition and len(content_text) > 100:
            issues.append("缺少过渡词，内容衔接可能不流畅")
            score -= 0.1

        score = max(0.0, min(1.0, score))

        return DimensionScore(
            dimension=QualityDimension.COHERENCE,
            score=score,
            issues=issues,
            suggestions=self._get_coherence_suggestions(score)
        )

    def _evaluate_accuracy(self, slide: Dict[str, Any]) -> DimensionScore:
        """
        评估表达准确性

        检查语言表达是否准确、简洁
        """
        issues = []
        score = 1.0

        content = slide.get("content", "")
        title = slide.get("title", "")

        # 转为文本
        content_text = content
        if isinstance(content, list):
            content_text = " ".join(str(item) for item in content)

        # 检查句子长度（过长可能表达不清）
        sentences = re.split(r'[。！？\n]', content_text)
        long_sentences = [s for s in sentences if len(s) > 100]

        if len(long_sentences) > 0:
            issues.append(f"存在{len(long_sentences)}个过长句子（超过100字）")
            score -= 0.1 * min(len(long_sentences), 3)

        # 检查重复词汇
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', content_text)
        if words:
            word_count = {}
            for word in words:
                word_count[word] = word_count.get(word, 0) + 1

            repeated = [w for w, c in word_count.items() if c > 3]
            if len(repeated) > 2:
                issues.append(f"词汇重复较多：{', '.join(repeated[:3])}")
                score -= 0.1

        # 检查标点符号使用
        punctuation_issues = self._check_punctuation(content_text)
        issues.extend(punctuation_issues)
        score -= 0.05 * len(punctuation_issues)

        # 检查是否有明显的格式问题
        if "  " in content_text or "\t\t" in content_text:
            issues.append("存在多余空格或制表符")
            score -= 0.05

        score = max(0.0, min(1.0, score))

        return DimensionScore(
            dimension=QualityDimension.ACCURACY,
            score=score,
            issues=issues,
            suggestions=self._get_accuracy_suggestions(score)
        )

    def _evaluate_adaptability(self, slide: Dict[str, Any]) -> DimensionScore:
        """
        评估教学适配性

        检查内容是否符合目标年级和学科的教学要求
        """
        issues = []
        score = 1.0

        content = slide.get("content", "")
        title = slide.get("title", "")

        # 转为文本
        content_text = content
        if isinstance(content, list):
            content_text = " ".join(str(item) for item in content)

        # 检查内容长度是否适合年级
        word_count = len(content_text)
        min_words = self.grade_config["min_words"]
        max_words = self.grade_config["max_words"]

        if word_count < min_words:
            issues.append(f"内容量偏少（{word_count}字），建议增加到{min_words}字以上")
            score -= 0.15
        elif word_count > max_words:
            issues.append(f"内容量过多（{word_count}字），建议精简到{max_words}字以内")
            score -= 0.1

        # 检查学科特色关键词
        subject_keywords = self.SUBJECT_KEYWORDS.get(self.subject, [])
        if subject_keywords:
            has_subject_content = any(kw in content_text for kw in subject_keywords)
            if not has_subject_content:
                issues.append(f"缺少{self.subject}学科特色内容")
                score -= 0.1

        # 检查年级适配的语言风格
        complexity = self.grade_config["complexity"]
        if complexity in ["very_low", "low"]:
            # 低年级应有更多视觉提示
            if "？" not in content_text and "！" not in content_text:
                # 低年级内容建议有更多互动语气
                pass  # 不扣分，只是建议

        # 检查教学目标是否明确
        page_type = slide.get("page_type", "")
        if page_type in ["知识点讲解页", "概念引入页"]:
            # 知识讲解页应有明确的知识点
            points = slide.get("points", slide.get("key_points", []))
            if not points or (isinstance(points, list) and len(points) == 0):
                issues.append("知识讲解页缺少明确的知识点")
                score -= 0.1

        score = max(0.0, min(1.0, score))

        return DimensionScore(
            dimension=QualityDimension.ADAPTABILITY,
            score=score,
            issues=issues,
            suggestions=self._get_adaptability_suggestions(score)
        )

    def _check_punctuation(self, text: str) -> List[str]:
        """检查标点符号使用"""
        issues = []

        # 连续标点
        if re.search(r'[，。、；：]{2,}', text):
            issues.append("存在连续标点符号")

        # 英文标点混用
        if re.search(r'[,.:;]', text) and re.search(r'[，。、；：]', text):
            # 中英文标点混用是常见情况，不作为问题
            pass

        return issues

    def _determine_quality_level(self, score: float) -> str:
        """确定质量等级"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.6:
            return "acceptable"
        else:
            return "poor"

    def _generate_summary(
        self,
        overall_score: float,
        quality_level: str,
        dimension_scores: List[DimensionScore]
    ) -> str:
        """生成评估总结"""
        level_names = {
            "excellent": "优秀",
            "good": "良好",
            "acceptable": "合格",
            "poor": "待改进"
        }

        # 找出最弱维度
        weakest = min(dimension_scores, key=lambda x: x.score)

        summary = f"整体质量{level_names[quality_level]}（{overall_score:.1%}）。"

        if weakest.score < 0.7:
            summary += f"需重点关注{weakest.dimension.value}方面的改进。"

        return summary

    def _determine_improvement_priority(
        self,
        dimension_scores: List[DimensionScore]
    ) -> List[str]:
        """确定改进优先级"""
        # 按分数排序，最低的优先级最高
        sorted_scores = sorted(dimension_scores, key=lambda x: x.score)

        priorities = []
        dimension_names = {
            QualityDimension.COMPLETENESS: "内容完整性",
            QualityDimension.COHERENCE: "逻辑连贯性",
            QualityDimension.ACCURACY: "表达准确性",
            QualityDimension.ADAPTABILITY: "教学适配性"
        }

        for ds in sorted_scores:
            if ds.score < 0.8:
                priorities.append(f"提升{dimension_names[ds.dimension]}")

        return priorities[:3]  # 最多3个优先项

    def _get_completeness_suggestions(self, score: float) -> List[str]:
        """获取完整性改进建议"""
        if score >= 0.8:
            return ["内容完整性良好"]
        elif score >= 0.6:
            return ["补充必要的内容元素", "确保每页都有清晰标题"]
        else:
            return ["添加缺失的内容元素", "检查是否遗漏关键信息", "确保标题明确"]

    def _get_coherence_suggestions(self, score: float) -> List[str]:
        """获取连贯性改进建议"""
        if score >= 0.8:
            return ["逻辑连贯性良好"]
        elif score >= 0.6:
            return ["增加过渡词和连接词", "调整内容顺序使层次更清晰"]
        else:
            return ["重新组织内容结构", "明确各部分之间的逻辑关系", "使用过渡句串联内容"]

    def _get_accuracy_suggestions(self, score: float) -> List[str]:
        """获取准确性改进建议"""
        if score >= 0.8:
            return ["表达准确性良好"]
        elif score >= 0.6:
            return ["精简冗长句子", "减少词汇重复"]
        else:
            return ["简化复杂表达", "检查并修正语言错误", "精简不必要的内容"]

    def _get_adaptability_suggestions(self, score: float) -> List[str]:
        """获取适配性改进建议"""
        suggestions = []

        if score < 0.8:
            complexity = self.grade_config["complexity"]

            if complexity in ["very_low", "low"]:
                suggestions.append("使用更简单易懂的语言")
                suggestions.append("增加图示和互动元素")
            elif complexity in ["medium", "medium_high"]:
                suggestions.append("平衡知识讲解与互动练习")
            else:
                suggestions.append("可以增加深度分析和拓展内容")

            if self.subject != "general":
                suggestions.append(f"增强{self.subject}学科特色内容")

        if not suggestions:
            suggestions.append("教学适配性良好")

        return suggestions


def get_quality_evaluator(grade: str = "7", subject: str = "general") -> ContentQualityEvaluator:
    """
    获取内容质量评估器实例

    Args:
        grade: 年级（1-12）
        subject: 学科

    Returns:
        ContentQualityEvaluator 实例
    """
    return ContentQualityEvaluator(grade, subject)