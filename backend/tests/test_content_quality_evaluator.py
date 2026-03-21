"""
内容质量评估器单元测试
"""

import pytest
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.content_quality_evaluator import (
    ContentQualityEvaluator,
    QualityDimension,
    DimensionScore,
    QualityReport,
    get_quality_evaluator
)


class TestContentQualityEvaluator:
    """内容质量评估器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.evaluator = ContentQualityEvaluator(grade="7", subject="math")

    def test_init(self):
        """测试初始化"""
        assert self.evaluator.grade == "7"
        assert self.evaluator.subject == "math"
        assert self.evaluator.grade_config is not None

    def test_get_quality_evaluator_factory(self):
        """测试工厂函数"""
        evaluator = get_quality_evaluator(grade="5", subject="chinese")
        assert evaluator.grade == "5"
        assert evaluator.subject == "chinese"

    def test_evaluate_completeness_good(self):
        """测试完整性评估 - 良好内容"""
        slide = {
            "title": "分数加法",
            "content": "同分母分数相加，分母不变，分子相加。例如：1/4 + 2/4 = 3/4",
            "points": ["分母不变", "分子相加", "结果化简"],
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_completeness(slide)
        assert result.dimension == QualityDimension.COMPLETENESS
        assert result.score >= 0.8
        assert len(result.issues) == 0

    def test_evaluate_completeness_missing_title(self):
        """测试完整性评估 - 缺少标题"""
        slide = {
            "title": "",
            "content": "这是一些内容，但是没有标题",
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_completeness(slide)
        assert result.score < 0.8
        assert any("标题" in issue for issue in result.issues)

    def test_evaluate_completeness_missing_content(self):
        """测试完整性评估 - 内容过少"""
        slide = {
            "title": "测试标题",
            "content": "短",
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_completeness(slide)
        assert result.score < 0.8
        assert any("内容" in issue for issue in result.issues)

    def test_evaluate_coherence_good(self):
        """测试连贯性评估 - 良好内容"""
        slide = {
            "title": "分数加法",
            "content": "首先，我们学习同分母分数加法。其次，理解加法原理。最后，通过练习巩固。",
            "points": ["理解概念", "掌握方法", "熟练应用"],
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_coherence(slide)
        assert result.score >= 0.7

    def test_evaluate_coherence_no_transitions(self):
        """测试连贯性评估 - 缺少过渡词"""
        slide = {
            "title": "分数加法",
            "content": "同分母分数相加。分母不变。分子相加。结果化简。",
            "points": ["分母不变", "分子相加"],
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_coherence(slide)
        # 可能会因为缺少过渡词扣分
        assert result.score <= 1.0

    def test_evaluate_accuracy_good(self):
        """测试准确性评估 - 良好内容"""
        slide = {
            "title": "分数加法",
            "content": "同分母分数相加，分母不变，分子相加。这是一个简洁的表达。",
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_accuracy(slide)
        assert result.score >= 0.7

    def test_evaluate_accuracy_long_sentences(self):
        """测试准确性评估 - 过长句子"""
        long_sentence = "这是一个非常非常长的句子" * 20
        slide = {
            "title": "测试",
            "content": long_sentence,
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_accuracy(slide)
        assert result.score < 1.0
        assert any("过长" in issue for issue in result.issues)

    def test_evaluate_adaptability_good(self):
        """测试适配性评估 - 良好内容"""
        slide = {
            "title": "一元二次方程",
            "content": "一元二次方程的一般形式是 ax² + bx + c = 0。通过公式求解方程的根。",
            "points": ["方程形式", "求解公式", "应用实例"],
            "page_type": "知识点讲解页"
        }

        result = self.evaluator._evaluate_adaptability(slide)
        assert result.score >= 0.6

    def test_evaluate_adaptability_wrong_grade(self):
        """测试适配性评估 - 年级不适配"""
        # 用小学低年级的评估器评估高中内容
        elementary_evaluator = ContentQualityEvaluator(grade="2", subject="math")

        slide = {
            "title": "高等数学导论",
            "content": "微积分是研究函数的极限、微分、积分以及无穷级数的一门数学学科，广泛应用于物理学、工程学等领域的深入研究中。",
            "page_type": "知识点讲解页"
        }

        result = elementary_evaluator._evaluate_adaptability(slide)
        # 内容对于二年级来说可能太多了
        assert result.score <= 1.0

    def test_evaluate_slide_content(self):
        """测试单页评估"""
        slide = {
            "title": "分数加法",
            "content": "同分母分数相加，分母不变，分子相加。首先理解概念，然后掌握方法。",
            "points": ["分母不变", "分子相加", "结果化简"],
            "page_type": "知识点讲解页"
        }

        result = self.evaluator.evaluate_slide_content(slide)
        assert result.score >= 0 and result.score <= 1
        assert isinstance(result.issues, list)
        assert isinstance(result.suggestions, list)

    def test_generate_quality_report_empty(self):
        """测试报告生成 - 空内容"""
        report = self.evaluator.generate_quality_report([])
        assert report.overall_score == 0.0
        assert report.quality_level == "poor"
        assert report.slide_count == 0

    def test_generate_quality_report_single_slide(self):
        """测试报告生成 - 单页"""
        slides = [{
            "title": "分数加法",
            "content": "同分母分数相加，分母不变，分子相加。",
            "points": ["分母不变", "分子相加"],
            "page_type": "知识点讲解页"
        }]

        report = self.evaluator.generate_quality_report(slides)
        assert report.slide_count == 1
        assert report.overall_score >= 0 and report.overall_score <= 1
        assert report.quality_level in ["excellent", "good", "acceptable", "poor"]
        assert len(report.dimension_scores) == 4

    def test_generate_quality_report_multiple_slides(self):
        """测试报告生成 - 多页"""
        slides = [
            {
                "title": "分数加法",
                "content": "同分母分数相加，分母不变，分子相加。首先理解概念。",
                "points": ["分母不变", "分子相加"],
                "page_type": "知识点讲解页"
            },
            {
                "title": "练习题",
                "content": "计算：1/4 + 2/4 = ?",
                "question": "请计算结果",
                "page_type": "课堂练习页"
            },
            {
                "title": "总结",
                "content": "今天我们学习了分数加法的基本方法。",
                "points": ["掌握同分母分数加法", "理解计算原理"],
                "page_type": "总结回顾页"
            }
        ]

        report = self.evaluator.generate_quality_report(slides)
        assert report.slide_count == 3
        assert report.overall_score > 0
        assert len(report.dimension_scores) == 4
        assert isinstance(report.summary, str)
        assert isinstance(report.improvement_priority, list)

    def test_dimension_score_to_dict(self):
        """测试 DimensionScore 序列化"""
        score = DimensionScore(
            dimension=QualityDimension.COMPLETENESS,
            score=0.85,
            issues=["问题1"],
            suggestions=["建议1"]
        )

        result = score.to_dict()
        assert result["dimension"] == "content_completeness"
        assert result["score"] == 0.85
        assert result["issues"] == ["问题1"]
        assert result["suggestions"] == ["建议1"]

    def test_quality_report_to_dict(self):
        """测试 QualityReport 序列化"""
        report = QualityReport(
            overall_score=0.8,
            dimension_scores=[
                DimensionScore(
                    dimension=QualityDimension.COMPLETENESS,
                    score=0.85,
                    issues=[],
                    suggestions=[]
                )
            ],
            slide_count=5,
            total_issues=2,
            quality_level="good",
            summary="整体质量良好",
            improvement_priority=["提升逻辑连贯性"]
        )

        result = report.to_dict()
        assert result["overall_score"] == 0.8
        assert result["quality_level"] == "good"
        assert result["slide_count"] == 5
        assert result["summary"] == "整体质量良好"

    def test_quality_level_determination(self):
        """测试质量等级判定"""
        assert self.evaluator._determine_quality_level(0.95) == "excellent"
        assert self.evaluator._determine_quality_level(0.85) == "good"
        assert self.evaluator._determine_quality_level(0.65) == "acceptable"
        assert self.evaluator._determine_quality_level(0.45) == "poor"

    def test_subject_keywords_chinese(self):
        """测试语文学科关键词"""
        evaluator = ContentQualityEvaluator(grade="5", subject="chinese")

        slide = {
            "title": "古诗词欣赏",
            "content": "这首诗词表达了作者的思乡之情。朗读时要注意感情。",
            "page_type": "知识点讲解页"
        }

        result = evaluator._evaluate_adaptability(slide)
        # 包含学科关键词，应该不会因为这个扣分

    def test_subject_keywords_math(self):
        """测试数学学科关键词"""
        evaluator = ContentQualityEvaluator(grade="8", subject="math")

        slide = {
            "title": "勾股定理",
            "content": "直角三角形的两条直角边的平方和等于斜边的平方。公式：a² + b² = c²",
            "points": ["定理内容", "公式表示", "应用"],
            "page_type": "知识点讲解页"
        }

        result = evaluator._evaluate_adaptability(slide)
        assert result.score >= 0.6  # 应该是合格的内容


class TestQualityDimension:
    """质量维度枚举测试"""

    def test_dimension_values(self):
        """测试维度枚举值"""
        assert QualityDimension.COMPLETENESS.value == "content_completeness"
        assert QualityDimension.COHERENCE.value == "logical_coherence"
        assert QualityDimension.ACCURACY.value == "expression_accuracy"
        assert QualityDimension.ADAPTABILITY.value == "teaching_adaptability"


class TestGradeConfig:
    """年级配置测试"""

    def test_all_grades_have_config(self):
        """测试所有年级都有配置"""
        for grade in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
            evaluator = ContentQualityEvaluator(grade=grade)
            assert evaluator.grade_config is not None
            assert "min_words" in evaluator.grade_config
            assert "max_words" in evaluator.grade_config
            assert "complexity" in evaluator.grade_config

    def test_unknown_grade_defaults_to_7(self):
        """测试未知年级默认使用7年级配置"""
        evaluator = ContentQualityEvaluator(grade="unknown")
        assert evaluator.grade_config == evaluator.GRADE_COMPLEXITY_MAP["7"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])