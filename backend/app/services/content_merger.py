# -*- coding: utf-8 -*-
"""
PPT AI 内容融合引擎
支持整体合并、单页处理、多页融合

设计文档: .claude-coder/plans/ppt-merge-technical-design.md#3-ai-融合策略
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, TypedDict, Union
from enum import Enum

# 导入增强版提示词模板
from ..prompts.merge_prompts import (
    build_full_merge_prompt,
    build_partial_merge_prompt,
    build_single_page_prompt,
    get_strategy_prompt,
    MERGE_STRATEGY_TEMPLATES
)

logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================

class MergeAction(Enum):
    """合并动作"""
    KEEP = "keep"              # 保留原页
    MERGE = "merge"            # 合并多页
    CREATE = "create"          # 创建新页
    SKIP = "skip"              # 跳过
    POLISH = "polish"          # 润色
    EXPAND = "expand"          # 扩展
    REWRITE = "rewrite"        # 改写
    EXTRACT = "extract"        # 提取知识点


class MergeType(Enum):
    """合并类型"""
    FULL = "full"              # 整体合并
    PARTIAL = "partial"        # 选择页面融合
    SINGLE = "single"          # 单页处理


class MergeStrategy(Enum):
    """合并策略"""
    SEQUENTIAL = "sequential"   # 顺序合并
    PARALLEL = "parallel"       # 并行合并
    INTELLIGENT = "intelligent" # 智能合并（AI 决策）


# ==================== 类型别名定义 ====================

class SlideContent(TypedDict, total=False):
    """幻灯片内容结构"""
    title: str
    main_points: List[str]
    additional_content: str
    elements: List[Dict[str, Any]]


class SinglePageResult(TypedDict):
    """单页处理结果"""
    action: str
    original_slide: Dict[str, Any]
    new_content: SlideContent
    changes: List[str]
    success: bool
    error: Optional[str]


class MultiPageResult(TypedDict):
    """多页融合结果"""
    merge_strategy: str
    content_relationship: str
    new_slide: Dict[str, Any]
    preserved_from_a: List[str]
    preserved_from_b: List[str]
    success: bool
    error: Optional[str]


# ==================== 配置类 ====================

@dataclass
class MergeConfig:
    """合并引擎配置"""
    provider: str = "deepseek"
    api_key: str = ""
    temperature: float = 0.3
    max_tokens: int = 3000
    strategy: MergeStrategy = MergeStrategy.INTELLIGENT

    def __post_init__(self):
        """验证配置参数"""
        if not self.api_key:
            logger.warning("MergeConfig: api_key 为空，LLM 调用可能失败")
        if self.temperature < 0 or self.temperature > 1:
            logger.warning(f"MergeConfig: temperature={self.temperature} 超出推荐范围 [0, 1]")
        if self.max_tokens < 100:
            raise ValueError("max_tokens 必须大于等于 100")


# ==================== 数据类 ====================

@dataclass
class SlidePlan:
    """单页处理计划"""
    action: MergeAction
    source: Optional[str] = None      # "A" 或 "B"
    slide_index: Optional[int] = None  # 源页码
    sources: Optional[List[Dict]] = None  # 多页合并时的来源 [{"source": "A", "slide": 1}, ...]
    new_content: Optional[str] = None  # 新内容（AI 生成）
    instruction: Optional[str] = None  # 处理指令
    reason: Optional[str] = None       # 原因说明


@dataclass
class MergePlan:
    """合并计划"""
    merge_strategy: str                           # 合并策略说明
    slide_plan: List[SlidePlan] = field(default_factory=list)
    summary: str = ""                             # 摘要说明
    knowledge_points: List[str] = field(default_factory=list)  # 涉及的知识点


# ==================== 主类 ====================

class ContentMerger:
    """PPT AI 内容融合引擎

    主要功能：
    1. 整体合并两个 PPT（merge_full）
    2. 单页处理：润色、扩展、改写、提取（merge_single_slide）
    3. 多页融合（merge_multiple_slides）

    使用示例：
    ```python
    config = MergeConfig(provider="deepseek", api_key="sk-xxx")
    merger = ContentMerger(config)
    result = merger.merge_single_slide(slide_data, "polish")
    ```
    """

    # 单页处理动作映射
    SINGLE_PAGE_ACTIONS = {
        "polish": "润色文字，使表达更加流畅",
        "expand": "扩展内容，增加更多细节和例子",
        "rewrite": "改写风格，调整语言风格",
        "extract": "提取知识点，总结关键信息"
    }

    def __init__(self, config: Optional[MergeConfig] = None, **kwargs):
        """
        初始化融合引擎

        Args:
            config: MergeConfig 配置对象
            **kwargs: 可选的配置参数（provider, api_key, temperature, max_tokens）
        """
        if config is None:
            config = MergeConfig(**kwargs)

        self._config = config
        self._llm_service = None

    @property
    def config(self) -> MergeConfig:
        """获取当前配置"""
        return self._config

    # ==================== 公共方法 ====================

    def merge_full(
        self,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        custom_prompt: str = ""
    ) -> MergePlan:
        """
        整体合并两个 PPT

        Args:
            doc_a: PPT A 的中间结构
            doc_b: PPT B 的中间结构
            custom_prompt: 用户自定义提示语

        Returns:
            MergePlan 合并计划
        """
        logger.info(f"开始整体合并: A({doc_a.get('total_slides', 0)}页) + B({doc_b.get('total_slides', 0)}页)")

        # 根据策略选择处理方式
        if self._config.strategy == MergeStrategy.SEQUENTIAL:
            return self._merge_sequential(doc_a, doc_b, custom_prompt)
        elif self._config.strategy == MergeStrategy.PARALLEL:
            return self._merge_parallel(doc_a, doc_b, custom_prompt)
        else:
            # 默认智能合并
            return self._merge_intelligent(doc_a, doc_b, custom_prompt)

    def merge_single_slide(
        self,
        slide_data: Dict[str, Any],
        action: str,
        custom_prompt: str = ""
    ) -> SinglePageResult:
        """
        处理单个幻灯片

        Args:
            slide_data: 单页数据
            action: 动作 (polish/expand/rewrite/extract)
            custom_prompt: 自定义提示语

        Returns:
            SinglePageResult 处理结果
        """
        if action not in self.SINGLE_PAGE_ACTIONS:
            raise ValueError(f"不支持的动作: {action}，支持的动作: {list(self.SINGLE_PAGE_ACTIONS.keys())}")

        logger.info(f"单页处理: action={action}")

        # 构建提示词
        system_prompt, user_prompt = self._build_single_page_prompts(slide_data, action, custom_prompt)

        # 调用 LLM
        response = self._call_llm(system_prompt, user_prompt)
        logger.info(f"LLM 响应: {response[:200]}...")

        # 解析响应
        result = self._parse_single_page_response(response, slide_data, action)

        return result

    def merge_multiple_slides(
        self,
        pages_a: List[Dict[str, Any]],
        pages_b: List[Dict[str, Any]],
        custom_prompt: str = ""
    ) -> MultiPageResult:
        """
        多页融合

        Args:
            pages_a: PPT A 的选中页面
            pages_b: PPT B 的选中页面
            custom_prompt: 自定义提示语

        Returns:
            MultiPageResult 融合结果
        """
        logger.info(f"多页融合: A({len(pages_a)}页) + B({len(pages_b)}页)")

        # 构建提示词
        system_prompt, user_prompt = self._build_multi_page_prompts(pages_a, pages_b, custom_prompt)

        # 调用 LLM
        response = self._call_llm(system_prompt, user_prompt)
        logger.info(f"LLM 响应: {response[:200]}...")

        # 解析响应
        result = self._parse_pages_merge_response(response)

        return result

    # ==================== 策略方法 ====================

    def _merge_sequential(
        self,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        custom_prompt: str
    ) -> MergePlan:
        """顺序合并策略：先 A 后 B"""
        logger.info("使用顺序合并策略")

        slide_plan = []
        for i, slide in enumerate(doc_a.get('slides', [])):
            slide_plan.append(SlidePlan(
                action=MergeAction.KEEP,
                source="A",
                slide_index=i,
                reason="顺序保留 PPT A 内容"
            ))
        for i, slide in enumerate(doc_b.get('slides', [])):
            slide_plan.append(SlidePlan(
                action=MergeAction.KEEP,
                source="B",
                slide_index=i,
                reason="顺序保留 PPT B 内容"
            ))

        return MergePlan(
            merge_strategy="顺序合并：先 PPT A 后 PPT B",
            slide_plan=slide_plan,
            summary=f"共 {len(slide_plan)} 页"
        )

    def _merge_parallel(
        self,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        custom_prompt: str
    ) -> MergePlan:
        """并行合并策略：交替排列"""
        logger.info("使用并行合并策略")

        slides_a = doc_a.get('slides', [])
        slides_b = doc_b.get('slides', [])
        max_len = max(len(slides_a), len(slides_b))

        slide_plan = []
        for i in range(max_len):
            if i < len(slides_a):
                slide_plan.append(SlidePlan(
                    action=MergeAction.KEEP,
                    source="A",
                    slide_index=i,
                    reason="并行合并：PPT A 内容"
                ))
            if i < len(slides_b):
                slide_plan.append(SlidePlan(
                    action=MergeAction.KEEP,
                    source="B",
                    slide_index=i,
                    reason="并行合并：PPT B 内容"
                ))

        return MergePlan(
            merge_strategy="并行合并：交替排列两个 PPT",
            slide_plan=slide_plan,
            summary=f"共 {len(slide_plan)} 页"
        )

    def _merge_intelligent(
        self,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        custom_prompt: str
    ) -> MergePlan:
        """智能合并策略：AI 决策"""
        logger.info("使用智能合并策略")

        # 使用增强版提示词模板构建 LLM 提示词
        file_a_name = doc_a.get('source_file', 'PPT A')
        file_b_name = doc_b.get('source_file', 'PPT B')
        system_prompt, user_prompt = build_full_merge_prompt(
            doc_a, doc_b, file_a_name, file_b_name, custom_prompt
        )

        # 调用 LLM
        response = self._call_llm(system_prompt, user_prompt)
        logger.info(f"LLM 响应: {response[:200]}...")

        # 解析响应
        plan = self._parse_merge_response(response, MergeType.FULL)

        return plan

    # ==================== 私有方法：提示词构建 ====================

    def _build_single_page_prompts(
        self,
        slide_data: Dict[str, Any],
        action: str,
        custom_prompt: str
    ) -> tuple:
        """构建单页处理提示词"""
        return build_single_page_prompt(slide_data, action, custom_prompt)

    def _build_multi_page_prompts(
        self,
        pages_a: List[Dict[str, Any]],
        pages_b: List[Dict[str, Any]],
        custom_prompt: str
    ) -> tuple:
        """构建多页融合提示词"""
        return build_partial_merge_prompt(pages_a, pages_b, custom_prompt)

    def _build_system_prompt(self, merge_type: MergeType) -> str:
        """构建系统提示词（兼容旧接口）"""
        base_prompt = """你是一位专业的教学课件融合专家。你能够理解 PPT 的教学内容，并根据用户需求生成最优的融合方案。

## 你的能力
1. 理解教学内容的逻辑结构和知识点关系
2. 识别重复、冗余和互补的内容
3. 保持教学逻辑连贯性
4. 生成清晰可执行的融合方案

## 输出格式
请严格输出 JSON 格式，不要包含其他文字。"""

        if merge_type == MergeType.FULL:
            return base_prompt + """

## 整体合并任务
分析两个完整的 PPT，生成合并计划。

输出格式：
```json
{
  "merge_strategy": "合并策略说明",
  "summary": "合并后的课件概述",
  "knowledge_points": ["涉及的知识点"],
  "slide_plan": [
    {
      "action": "keep|merge|create|skip",
      "source": "A|B",
      "slide_index": 页码,
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
- create: 创建新页面
- skip: 跳过不使用"""
        elif merge_type == MergeType.SINGLE:
            return base_prompt + """

## 单页处理任务
对单个页面执行润色、扩展、改写或提取操作。

输出格式：
```json
{
  "action": "polish|expand|rewrite|extract",
  "original_summary": "原内容摘要",
  "new_content": {
    "title": "标题",
    "main_points": ["要点1", "要点2"],
    "additional_content": "扩展内容（如有）"
  },
  "changes": ["修改说明1", "修改说明2"]
}
```"""
        else:  # PARTIAL
            return base_prompt + """

## 多页融合任务
融合选中的多个页面，生成新页面。

输出格式：
```json
{
  "merge_strategy": "融合策略说明",
  "content_relationship": "页面内容关系分析",
  "new_slide": {
    "title": "融合后的标题",
    "elements": [
      {"type": "title", "content": "标题内容"},
      {"type": "text_body", "content": "正文内容"},
      {"type": "list_item", "content": "列表项"}
    ]
  },
  "preserved_from_a": ["保留自 A 的内容"],
  "preserved_from_b": ["保留自 B 的内容"]
}
```"""

    # ==================== 私有方法：LLM 调用 ====================

    def _get_llm_service(self):
        """延迟加载 LLM 服务"""
        if self._llm_service is None:
            from ..services.llm import get_llm_service
            self._llm_service = get_llm_service(
                provider=self._config.provider,
                api_key=self._config.api_key,
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens
            )
        return self._llm_service

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用 LLM 服务

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            LLM 响应文本
        """
        llm = self._get_llm_service()
        response, usage = llm.chat_with_usage([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        logger.info(f"Token 使用: {usage}")
        return response

    # ==================== 私有方法：响应解析 ====================

    def _parse_merge_response(self, response: str, merge_type: MergeType) -> MergePlan:
        """解析合并响应"""
        try:
            data = self._extract_json(response)

            plan = MergePlan(
                merge_strategy=data.get('merge_strategy', '未知策略'),
                summary=data.get('summary', ''),
                knowledge_points=data.get('knowledge_points', [])
            )

            # 解析 slide_plan
            for item in data.get('slide_plan', []):
                action_str = item.get('action', 'keep')
                try:
                    action = MergeAction(action_str)
                except ValueError:
                    action = MergeAction.KEEP

                slide_plan = SlidePlan(
                    action=action,
                    source=item.get('source'),
                    slide_index=item.get('slide_index'),
                    sources=item.get('sources'),
                    new_content=item.get('new_content'),
                    instruction=item.get('instruction'),
                    reason=item.get('reason')
                )
                plan.slide_plan.append(slide_plan)

            return plan

        except Exception as e:
            logger.error(f"解析合并响应失败: {e}")
            return MergePlan(
                merge_strategy="解析失败，使用默认策略",
                slide_plan=[]
            )

    def _parse_single_page_response(
        self,
        response: str,
        original: Dict[str, Any],
        action: str
    ) -> SinglePageResult:
        """解析单页处理响应

        注意：不同 action 的 LLM 返回格式不同：
        - polish → polished_content
        - expand → expanded_content
        - rewrite → rewritten_content
        - extract → extracted_knowledge
        - 通用 → new_content
        """
        try:
            data = self._extract_json(response)

            # 根据 action 提取对应的内容字段
            new_content = self._extract_content_by_action(data, action, original)

            # 确保 new_content 包含必要字段
            new_content = self._ensure_slide_content_fields(new_content, original)

            return {
                "action": action,
                "original_slide": original,
                "new_content": new_content,
                "changes": data.get('changes', []),
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"解析单页响应失败: {e}")
            new_content = self._extract_title_and_points(response, original)

            return {
                "action": action,
                "original_slide": original,
                "new_content": new_content,
                "changes": [],
                "success": False,
                "error": str(e)
            }

    def _parse_pages_merge_response(self, response: str) -> MultiPageResult:
        """解析多页融合响应"""
        try:
            data = self._extract_json(response)

            # 验证并清理 new_slide 的 elements
            new_slide = data.get('new_slide', {})
            new_slide = self._validate_new_slide(new_slide)

            return {
                "merge_strategy": data.get('merge_strategy', ''),
                "content_relationship": data.get('content_relationship', ''),
                "new_slide": new_slide,
                "preserved_from_a": self._validate_string_list(data.get('preserved_from_a', []), "preserved_from_a"),
                "preserved_from_b": self._validate_string_list(data.get('preserved_from_b', []), "preserved_from_b"),
                "success": True,
                "error": None
            }

        except Exception as e:
            logger.error(f"解析多页融合响应失败: {e}")
            return {
                "merge_strategy": '',
                "content_relationship": '',
                "new_slide": {},
                "preserved_from_a": [],
                "preserved_from_b": [],
                "success": False,
                "error": str(e)
            }

    # ==================== 私有方法：内容提取与标准化 ====================

    def _extract_content_by_action(
        self,
        data: Dict[str, Any],
        action: str,
        original: Dict[str, Any]
    ) -> SlideContent:
        """根据 action 类型提取对应的内容字段并标准化为 SlideContent 格式"""
        # 不同 action 的字段名映射
        action_field_map = {
            "polish": "polished_content",
            "expand": "expanded_content",
            "rewrite": "rewritten_content",
            "extract": "extracted_knowledge"
        }

        field_name = action_field_map.get(action, "new_content")
        content = data.get(field_name, data.get("new_content", {}))

        # 根据 action 类型标准化内容
        if action == "polish":
            return self._normalize_polish_content(content, data)
        elif action == "expand":
            return self._normalize_expand_content(content, data)
        elif action == "rewrite":
            return self._normalize_rewrite_content(content, data)
        elif action == "extract":
            return self._normalize_extract_content(content, data)
        else:
            result = content if isinstance(content, dict) else {}
            result["main_points"] = self._validate_and_convert_points(
                result.get("main_points", []),
                f"_extract_content_by_action.{action}"
            )
            return result

    def _normalize_polish_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> SlideContent:
        """标准化润色内容"""
        title = content.get("title", "")
        main_points = []
        changes = data.get("changes", [])

        # 优先从 changes 中提取标题
        if not title and changes:
            for change in changes:
                location = change.get("location", "")
                if "标题" in location or location in ["页面标题", "标题"]:
                    title = change.get("polished", "")
                    break

        # 优先从 content.main_points 提取要点
        raw_points = content.get("main_points", [])
        if raw_points:
            main_points = self._validate_and_convert_points(raw_points, "_normalize_polish_content.main_points")

        # 从 polished_elements 中提取要点
        if not main_points:
            elements = content.get("polished_elements", [])
            extracted = [e.get("polished") for e in elements if e.get("polished")]
            if extracted:
                main_points = self._validate_and_convert_points(extracted, "_normalize_polish_content.polished_elements")

        # 从 changes 中提取要点
        if not main_points and changes:
            extracted = [c.get("polished") for c in changes
                        if c.get("polished") and "标题" not in c.get("location", "")]
            if extracted:
                main_points = self._validate_and_convert_points(extracted, "_normalize_polish_content.changes")

        # 最终验证
        main_points = self._validate_and_convert_points(main_points, "_normalize_polish_content.final")

        return {
            "title": title or "润色后的内容",
            "main_points": main_points[:6],
            "additional_content": ""
        }

    def _normalize_expand_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> SlideContent:
        """标准化扩展内容"""
        title = content.get("title", "")
        main_points = content.get("expanded_points", content.get("original_points", []))

        # 合并原有和扩展的要点
        original_points = content.get("original_points", [])
        expanded_points = content.get("expanded_points", [])
        if original_points or expanded_points:
            main_points = original_points + expanded_points

        # 新增例题作为额外内容
        new_examples = content.get("new_examples", [])
        additional_content = ""
        if new_examples:
            example_strs = self._validate_and_convert_points(new_examples[:3], "_normalize_expand_content.examples")
            additional_content = "新增例题：" + "；".join(example_strs)

        additional = content.get("additional_content", additional_content)

        main_points = self._validate_and_convert_points(main_points, "_normalize_expand_content")

        return {
            "title": title or "扩展后的内容",
            "main_points": main_points[:6],
            "additional_content": additional
        }

    def _normalize_rewrite_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> SlideContent:
        """标准化改写内容"""
        title = content.get("title", "")
        main_content = content.get("main_content", "")

        # 将主要内容转为要点
        main_points = []
        if main_content:
            sentences = [s.strip() for s in main_content.replace('。', '。\n').split('\n') if s.strip()]
            main_points = sentences[:6]

        # 风格特点作为额外内容
        style_features = content.get("style_features", [])
        additional_content = ""
        if style_features:
            feature_strs = self._validate_and_convert_points(style_features, "_normalize_rewrite_content.style_features")
            additional_content = "风格特点：" + "、".join(feature_strs)

        main_points = self._validate_and_convert_points(main_points, "_normalize_rewrite_content")

        return {
            "title": title or "改写后的内容",
            "main_points": main_points,
            "additional_content": additional_content
        }

    def _normalize_extract_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> SlideContent:
        """标准化提取内容"""
        title = data.get("knowledge_summary", "知识点提取")
        main_points = []

        # 提取核心概念
        core_concepts = content.get("core_concepts", [])
        for concept in core_concepts[:3]:
            concept_name = concept.get("concept", "")
            definition = concept.get("definition", "")
            if concept_name:
                main_points.append(f"【{concept_name}】{definition}")

        # 提取公式
        formulas = content.get("formulas", [])
        for formula in formulas[:2]:
            name = formula.get("name", "")
            expr = formula.get("formula", "")
            if name and expr:
                main_points.append(f"【{name}】{expr}")

        # 提取方法
        methods = content.get("methods", [])
        for method in methods[:2]:
            name = method.get("name", "")
            steps = method.get("steps", [])
            if name:
                step_strs = self._validate_and_convert_points(steps[:3], "_normalize_extract_content.steps")
                step_str = "→".join(step_strs) if step_strs else ""
                main_points.append(f"【{name}】{step_str}")

        # 易错点作为额外内容
        common_mistakes = content.get("common_mistakes", [])
        additional_content = ""
        if common_mistakes:
            mistake_strs = []
            for m in common_mistakes[:3]:
                if isinstance(m, dict):
                    mistake_strs.append(f"{m.get('mistake', '')}→{m.get('correction', '')}")
                else:
                    mistake_strs.append(str(m))
            additional_content = "易错提醒：" + "；".join(mistake_strs)

        # 学习建议
        study_suggestions = data.get("study_suggestions", [])
        if study_suggestions and not additional_content:
            suggestion_strs = self._validate_and_convert_points(study_suggestions[:3], "_normalize_extract_content.suggestions")
            additional_content = "学习建议：" + "；".join(suggestion_strs)

        main_points = self._validate_and_convert_points(main_points, "_normalize_extract_content")

        return {
            "title": title,
            "main_points": main_points[:6],
            "additional_content": additional_content
        }

    # ==================== 私有方法：验证与清理 ====================

    def _validate_and_convert_points(
        self,
        points: Any,
        context: str = ""
    ) -> List[str]:
        """
        验证并转换 main_points 中的元素为字符串

        字段提取优先级：text → content → polished → description → item → str()
        """
        if points is None:
            return []

        if not isinstance(points, list):
            logger.warning(f"[{context}] main_points 不是列表类型: {type(points).__name__}")
            return [str(points)] if points else []

        result = []
        priority_fields = ["text", "content", "polished", "description", "item"]

        for idx, p in enumerate(points):
            if p is None:
                continue

            if isinstance(p, str):
                if p.strip():
                    result.append(p.strip())

            elif isinstance(p, dict):
                for field in priority_fields:
                    if field in p:
                        val = p[field]
                        if isinstance(val, str) and val.strip():
                            result.append(val.strip())
                            break
                        elif val is not None and not isinstance(val, str):
                            result.append(str(val))
                            break

            elif isinstance(p, (int, float, bool)):
                result.append(str(p))

            else:
                try:
                    converted = str(p)
                    if converted and converted.strip():
                        result.append(converted)
                except Exception:
                    pass

        if len(result) != len(points):
            logger.debug(f"[{context}] 类型转换: {len(points)} 项 -> {len(result)} 项字符串")
        return result

    def _validate_string_list(
        self,
        items: Any,
        context: str = ""
    ) -> List[str]:
        """验证并转换字符串列表"""
        if items is None:
            return []

        if not isinstance(items, list):
            return [str(items)] if items else []

        result = []
        for item in items:
            if item is None:
                continue
            if isinstance(item, str):
                if item.strip():
                    result.append(item.strip())
            elif isinstance(item, dict):
                for field in ["text", "content", "point"]:
                    if field in item and isinstance(item[field], str) and item[field].strip():
                        result.append(item[field].strip())
                        break
            else:
                try:
                    converted = str(item)
                    if converted.strip():
                        result.append(converted.strip())
                except Exception:
                    pass

        return result

    def _validate_new_slide(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """验证并清理 new_slide 结构"""
        if not slide or not isinstance(slide, dict):
            return {}

        result = {
            "title": "",
            "elements": []
        }

        # 验证 title
        title = slide.get("title", "")
        if isinstance(title, str):
            result["title"] = title
        elif title is not None:
            result["title"] = str(title)

        # 验证 elements
        elements = slide.get("elements", [])
        if isinstance(elements, list):
            for idx, elem in enumerate(elements):
                if not isinstance(elem, dict):
                    continue

                validated_elem = {
                    "type": elem.get("type", "text_body")
                }

                content = elem.get("content")
                if content is None:
                    validated_elem["content"] = ""
                elif isinstance(content, str):
                    validated_elem["content"] = content
                elif isinstance(content, dict):
                    for field in ["text", "value", "data"]:
                        if field in content:
                            validated_elem["content"] = str(content[field])
                            break
                    else:
                        validated_elem["content"] = str(content)
                else:
                    validated_elem["content"] = str(content)

                result["elements"].append(validated_elem)

        return result

    def _ensure_slide_content_fields(
        self,
        content: Dict[str, Any],
        original: Dict[str, Any]
    ) -> SlideContent:
        """确保 SlideContent 包含必要字段"""
        original_title = self._get_original_title(original)

        raw_points = content.get("main_points") or []
        main_points = self._validate_and_convert_points(raw_points, "_ensure_slide_content_fields")

        return {
            "title": content.get("title") or original_title or "处理后的内容",
            "main_points": main_points[:6],
            "additional_content": content.get("additional_content") or ""
        }

    def _get_original_title(self, original: Dict[str, Any]) -> str:
        """从原始页面数据中提取标题"""
        teaching = original.get('teaching_content', {})
        if teaching.get('title'):
            return teaching['title']

        for elem in original.get('elements', []):
            if elem.get('type') == 'title' and elem.get('text'):
                return elem['text']

        return ""

    def _extract_title_and_points(
        self,
        response_text: str,
        original: Dict[str, Any]
    ) -> SlideContent:
        """从响应文本中提取结构化内容（解析失败时的兜底方案）"""
        title = self._get_original_title(original)
        main_points = []
        additional_content = ""

        # 尝试提取标题
        title_patterns = [
            r'["\']title["\']\s*:\s*["\']([^"\']+)["\']',
            r'标题[：:]\s*(.+?)(?:\n|$)',
            r'##\s*(.+?)(?:\n|$)',
            r'#\s*(.+?)(?:\n|$)'
        ]

        for pattern in title_patterns:
            match = re.search(pattern, response_text)
            if match:
                title = match.group(1).strip()
                break

        # 尝试提取要点
        list_patterns = [
            r'^[-•]\s*(.+?)$',
            r'^\d+[\.、]\s*(.+?)$'
        ]

        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            for pattern in list_patterns:
                match = re.match(pattern, line)
                if match:
                    point = match.group(1).strip()
                    if len(point) > 5:
                        main_points.append(point)
                    break

        # 如果没有找到列表，尝试从 main_points JSON 字段提取
        if not main_points:
            mp_match = re.search(r'["\']main_points["\']\s*:\s*\[(.+?)\]', response_text, re.DOTALL)
            if mp_match:
                points_str = mp_match.group(1)
                point_matches = re.findall(r'["\']([^"\']+)["\']', points_str)
                main_points = [p.strip() for p in point_matches if len(p.strip()) > 5]

        # 提取额外内容
        para_match = re.search(r'["\']additional_content["\']\s*:\s*["\']([^"\']+)["\']', response_text)
        if para_match:
            additional_content = para_match.group(1).strip()

        main_points = main_points[:6]

        if not main_points and title:
            main_points = [f"内容处理完成，请查看预览"]

        return {
            "title": title or "处理后的内容",
            "main_points": main_points,
            "additional_content": additional_content
        }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取 JSON"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试提取 markdown 代码块中的 JSON
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { } 之间的内容
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError("无法从响应中提取有效 JSON")

    # ==================== 兼容方法（保持向后兼容） ====================

    def process_single_page(
        self,
        slide_data: Dict[str, Any],
        action: str,
        custom_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        处理单页（兼容旧接口）

        已弃用，请使用 merge_single_slide
        """
        logger.warning("process_single_page 已弃用，请使用 merge_single_slide")
        result = self.merge_single_slide(slide_data, action, custom_prompt)
        return dict(result)

    def merge_pages(
        self,
        pages_a: List[Dict[str, Any]],
        pages_b: List[Dict[str, Any]],
        custom_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        多页融合（兼容旧接口）

        已弃用，请使用 merge_multiple_slides
        """
        logger.warning("merge_pages 已弃用，请使用 merge_multiple_slides")
        result = self.merge_multiple_slides(pages_a, pages_b, custom_prompt)
        return dict(result)


# ==================== 便捷函数 ====================

def get_content_merger(
    provider: str = "deepseek",
    api_key: str = "",
    temperature: float = 0.3,
    max_tokens: int = 3000
) -> ContentMerger:
    """
    获取内容融合引擎实例

    Args:
        provider: LLM 服务商
        api_key: API Key
        temperature: 温度参数
        max_tokens: 最大输出 token

    Returns:
        ContentMerger 实例
    """
    config = MergeConfig(
        provider=provider,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return ContentMerger(config)