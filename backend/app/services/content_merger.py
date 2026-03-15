# -*- coding: utf-8 -*-
"""
PPT AI 内容融合引擎
支持整体合并、单页处理、多页融合

设计文档: .claude-coder/plans/ppt-merge-technical-design.md#3-ai-融合策略
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
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


class ContentMerger:
    """PPT AI 内容融合引擎"""

    # 单页处理动作
    SINGLE_PAGE_ACTIONS = {
        "polish": "润色文字，使表达更加流畅",
        "expand": "扩展内容，增加更多细节和例子",
        "rewrite": "改写风格，调整语言风格",
        "extract": "提取知识点，总结关键信息"
    }

    def __init__(
        self,
        provider: str = "deepseek",
        api_key: str = "",
        temperature: float = 0.3,
        max_tokens: int = 3000
    ):
        """
        初始化融合引擎

        Args:
            provider: LLM 服务商
            api_key: API Key
            temperature: 温度参数
            max_tokens: 最大输出 token
        """
        self.provider = provider
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm_service = None

    def _get_llm_service(self):
        """延迟加载 LLM 服务"""
        if self._llm_service is None:
            from ..services.llm import get_llm_service
            self._llm_service = get_llm_service(
                provider=self.provider,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
        return self._llm_service

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

        # 使用增强版提示词模板构建 LLM 提示词
        file_a_name = doc_a.get('source_file', 'PPT A')
        file_b_name = doc_b.get('source_file', 'PPT B')
        system_prompt, user_prompt = build_full_merge_prompt(
            doc_a, doc_b, file_a_name, file_b_name, custom_prompt
        )

        # 调用 LLM
        llm = self._get_llm_service()
        response, usage = llm.chat_with_usage([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        logger.info(f"LLM 响应: {response[:200]}...")
        logger.info(f"Token 使用: {usage}")

        # 解析响应
        plan = self._parse_merge_response(response, MergeType.FULL)

        return plan

    def process_single_page(
        self,
        slide_data: Dict[str, Any],
        action: str,
        custom_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        处理单页

        Args:
            slide_data: 单页数据
            action: 动作 (polish/expand/rewrite/extract)
            custom_prompt: 自定义提示语

        Returns:
            处理后的页面数据
        """
        if action not in self.SINGLE_PAGE_ACTIONS:
            raise ValueError(f"不支持的动作: {action}")

        logger.info(f"单页处理: action={action}")

        # 使用增强版提示词模板构建提示词
        system_prompt, user_prompt = build_single_page_prompt(slide_data, action, custom_prompt)

        # 调用 LLM
        llm = self._get_llm_service()
        response, usage = llm.chat_with_usage([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        logger.info(f"LLM 响应: {response[:200]}...")

        # 解析响应
        result = self._parse_single_page_response(response, slide_data, action)

        return result

    def merge_pages(
        self,
        pages_a: List[Dict[str, Any]],
        pages_b: List[Dict[str, Any]],
        custom_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        多页融合

        Args:
            pages_a: PPT A 的选中页面
            pages_b: PPT B 的选中页面
            custom_prompt: 自定义提示语

        Returns:
            融合后的页面数据
        """
        logger.info(f"多页融合: A({len(pages_a)}页) + B({len(pages_b)}页)")

        # 使用增强版提示词模板构建提示词
        system_prompt, user_prompt = build_partial_merge_prompt(
            pages_a, pages_b, custom_prompt
        )

        # 调用 LLM
        llm = self._get_llm_service()
        response, usage = llm.chat_with_usage([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])

        logger.info(f"LLM 响应: {response[:200]}...")

        # 解析响应
        result = self._parse_pages_merge_response(response)

        return result

    def _build_system_prompt(self, merge_type: MergeType) -> str:
        """构建系统提示词"""
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

    def _build_full_merge_prompt(
        self,
        doc_a: Dict[str, Any],
        doc_b: Dict[str, Any],
        custom_prompt: str
    ) -> str:
        """构建整体合并提示词"""
        # 提取摘要
        a_summary = self._extract_doc_summary(doc_a)
        b_summary = self._extract_doc_summary(doc_b)

        prompt = f"""## PPT A 概览
文件名: {doc_a.get('source_file', '未知')}
总页数: {doc_a.get('total_slides', 0)}
复杂元素页面: {doc_a.get('complex_element_slides', [])}

### 页面摘要
{json.dumps(a_summary, ensure_ascii=False, indent=2)}

## PPT B 概览
文件名: {doc_b.get('source_file', '未知')}
总页数: {doc_b.get('total_slides', 0)}
复杂元素页面: {doc_b.get('complex_element_slides', [])}

### 页面摘要
{json.dumps(b_summary, ensure_ascii=False, indent=2)}

## 用户需求
{custom_prompt if custom_prompt else "请根据两份课件的内容，生成最优的合并方案。保留核心知识点，避免重复内容。"}

请生成合并计划 JSON。"""

        return prompt

    def _build_single_page_prompt(
        self,
        slide_data: Dict[str, Any],
        action: str,
        custom_prompt: str
    ) -> str:
        """构建单页处理提示词"""
        action_desc = self.SINGLE_PAGE_ACTIONS.get(action, "")

        # 提取页面内容
        content = self._extract_slide_content(slide_data)

        prompt = f"""## 页面信息
页码: {slide_data.get('slide_index', 0)}
类型: {slide_data.get('slide_type', '未知')}
教学角色: {slide_data.get('teaching_role', '未知')}

### 页面内容
{json.dumps(content, ensure_ascii=False, indent=2)}

## 处理任务
动作: {action}
说明: {action_desc}

## 用户要求
{custom_prompt if custom_prompt else "请按照动作要求处理页面内容。"}

请生成处理结果 JSON。"""

        return prompt

    def _build_pages_merge_prompt(
        self,
        pages_a: List[Dict[str, Any]],
        pages_b: List[Dict[str, Any]],
        custom_prompt: str
    ) -> str:
        """构建多页融合提示词"""
        a_content = [self._extract_slide_content(p) for p in pages_a]
        b_content = [self._extract_slide_content(p) for p in pages_b]

        prompt = f"""## PPT A 选中页面 ({len(pages_a)} 页)
{json.dumps(a_content, ensure_ascii=False, indent=2)}

## PPT B 选中页面 ({len(pages_b)} 页)
{json.dumps(b_content, ensure_ascii=False, indent=2)}

## 用户需求
{custom_prompt if custom_prompt else "请融合以上页面内容，生成新的页面。"}

请生成融合结果 JSON。"""

        return prompt

    def _extract_doc_summary(self, doc: Dict[str, Any]) -> List[Dict]:
        """提取文档摘要"""
        summary = []
        for slide in doc.get('slides', []):
            slide_info = {
                "index": slide.get('slide_index', 0),
                "type": slide.get('slide_type', '未知'),
                "role": slide.get('teaching_role', '未知'),
                "title": "",
                "main_points": []
            }

            # 提取标题和要点
            teaching = slide.get('teaching_content', {})
            slide_info['title'] = teaching.get('title', '')
            slide_info['main_points'] = teaching.get('main_points', [])[:3]  # 最多3个要点

            summary.append(slide_info)

        return summary

    def _extract_slide_content(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """提取页面内容"""
        content = {
            "title": "",
            "elements": []
        }

        for elem in slide.get('elements', []):
            elem_type = elem.get('type', '')
            if elem_type == 'title':
                content['title'] = elem.get('text', '')
            elif elem_type in ('text_body', 'list_item', 'subtitle'):
                content['elements'].append({
                    "type": elem_type,
                    "content": elem.get('text', '')[:200]  # 限制长度
                })
            elif elem_type == 'image':
                content['elements'].append({
                    "type": "image",
                    "description": elem.get('description', '图片')
                })
            elif elem_type == 'table':
                content['elements'].append({
                    "type": "table",
                    "headers": elem.get('table_headers', []),
                    "rows": len(elem.get('table_data', []))
                })

        return content

    def _parse_merge_response(self, response: str, merge_type: MergeType) -> MergePlan:
        """解析合并响应"""
        try:
            # 尝试提取 JSON
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
            # 返回默认计划
            return MergePlan(
                merge_strategy="解析失败，使用默认策略",
                slide_plan=[]
            )

    def _parse_single_page_response(
        self,
        response: str,
        original: Dict[str, Any],
        action: str
    ) -> Dict[str, Any]:
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
                "success": True
            }

        except Exception as e:
            logger.error(f"解析单页响应失败: {e}")
            # 解析失败时，尝试从响应文本中提取结构化内容
            new_content = self._extract_title_and_points(response, original)

            return {
                "action": action,
                "original_slide": original,
                "new_content": new_content,
                "changes": [],
                "success": False,
                "error": str(e)
            }

    def _extract_content_by_action(
        self,
        data: Dict[str, Any],
        action: str,
        original: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            return content

    def _normalize_polish_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化润色内容"""
        title = content.get("title", "")
        main_points = content.get("main_points", [])
        changes = data.get("changes", [])

        # 优先从 changes 中提取标题
        if not title and changes:
            for change in changes:
                location = change.get("location", "")
                if "标题" in location or location in ["页面标题", "标题"]:
                    title = change.get("polished", "")
                    break

        # 从 polished_elements 或 changes 中提取要点
        if not main_points:
            elements = content.get("polished_elements", [])
            main_points = [e.get("polished", "") for e in elements if e.get("polished")]

        # 从 changes 中提取要点（排除标题相关的更改）
        if not main_points and changes:
            main_points = [
                c.get("polished", "") for c in changes
                if c.get("polished") and "标题" not in c.get("location", "")
            ]

        return {
            "title": title or "润色后的内容",
            "main_points": main_points[:6],
            "additional_content": ""
        }

    def _normalize_expand_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
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
            additional_content = "新增例题：" + "；".join(new_examples[:3])

        additional = content.get("additional_content", additional_content)

        return {
            "title": title or "扩展后的内容",
            "main_points": main_points[:6],
            "additional_content": additional
        }

    def _normalize_rewrite_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化改写内容"""
        title = content.get("title", "")
        main_content = content.get("main_content", "")

        # 将主要内容转为要点
        main_points = []
        if main_content:
            # 按句子分割，每句作为一个要点
            sentences = [s.strip() for s in main_content.replace('。', '。\n').split('\n') if s.strip()]
            main_points = sentences[:6]

        # 风格特点作为额外内容
        style_features = content.get("style_features", [])
        additional_content = ""
        if style_features:
            additional_content = "风格特点：" + "、".join(style_features)

        return {
            "title": title or "改写后的内容",
            "main_points": main_points,
            "additional_content": additional_content
        }

    def _normalize_extract_content(self, content: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化提取内容"""
        # 知识点总结作为标题
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
                step_str = "→".join(steps[:3]) if steps else ""
                main_points.append(f"【{name}】{step_str}")

        # 易错点作为额外内容
        common_mistakes = content.get("common_mistakes", [])
        additional_content = ""
        if common_mistakes:
            mistakes = [f"{m.get('mistake', '')}→{m.get('correction', '')}" for m in common_mistakes[:3]]
            additional_content = "易错提醒：" + "；".join(mistakes)

        # 学习建议
        study_suggestions = data.get("study_suggestions", [])
        if study_suggestions and not additional_content:
            additional_content = "学习建议：" + "；".join(study_suggestions[:3])

        return {
            "title": title,
            "main_points": main_points[:6],
            "additional_content": additional_content
        }

    def _ensure_slide_content_fields(
        self,
        content: Dict[str, Any],
        original: Dict[str, Any]
    ) -> Dict[str, Any]:
        """确保 SlideContent 包含必要字段"""
        # 获取原始标题作为备用
        original_title = self._get_original_title(original)

        return {
            "title": content.get("title") or original_title or "处理后的内容",
            "main_points": content.get("main_points") or [],
            "additional_content": content.get("additional_content") or ""
        }

    def _get_original_title(self, original: Dict[str, Any]) -> str:
        """从原始页面数据中提取标题"""
        # 尝试从 teaching_content 获取
        teaching = original.get('teaching_content', {})
        if teaching.get('title'):
            return teaching['title']

        # 尝试从 elements 中获取
        for elem in original.get('elements', []):
            if elem.get('type') == 'title' and elem.get('text'):
                return elem['text']

        return ""

    def _extract_title_and_points(
        self,
        response_text: str,
        original: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从响应文本中提取结构化内容（解析失败时的兜底方案）"""
        import re

        title = self._get_original_title(original)
        main_points = []
        additional_content = ""

        # 尝试提取标题（多种模式）
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

        # 尝试提取要点（列表形式）
        # 匹配 "- " 或 "• " 或数字编号 "1. " 开头的行
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
                    if len(point) > 5:  # 过滤太短的内容
                        main_points.append(point)
                    break

        # 如果没有找到列表形式的要点，尝试从 main_points JSON 字段提取
        if not main_points:
            mp_match = re.search(r'["\']main_points["\']\s*:\s*\[(.+?)\]', response_text, re.DOTALL)
            if mp_match:
                # 提取数组内容
                points_str = mp_match.group(1)
                # 匹配引号内的内容
                point_matches = re.findall(r'["\']([^"\']+)["\']', points_str)
                main_points = [p.strip() for p in point_matches if len(p.strip()) > 5]

        # 提取额外内容（段落形式）
        para_match = re.search(r'["\']additional_content["\']\s*:\s*["\']([^"\']+)["\']', response_text)
        if para_match:
            additional_content = para_match.group(1).strip()

        # 限制要点数量
        main_points = main_points[:6]

        # 如果什么都没提取到，至少返回原始标题
        if not main_points and title:
            main_points = [f"内容处理完成，请查看预览"]

        return {
            "title": title or "处理后的内容",
            "main_points": main_points,
            "additional_content": additional_content
        }

    def _parse_pages_merge_response(self, response: str) -> Dict[str, Any]:
        """解析多页融合响应"""
        try:
            data = self._extract_json(response)

            return {
                "merge_strategy": data.get('merge_strategy', ''),
                "content_relationship": data.get('content_relationship', ''),
                "new_slide": data.get('new_slide', {}),
                "preserved_from_a": data.get('preserved_from_a', []),
                "preserved_from_b": data.get('preserved_from_b', []),
                "success": True
            }

        except Exception as e:
            logger.error(f"解析多页融合响应失败: {e}")
            return {
                "merge_strategy": '',
                "new_slide": {},
                "success": False,
                "error": str(e)
            }

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """从文本中提取 JSON"""
        import re

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


# 便捷函数
def get_content_merger(
    provider: str = "deepseek",
    api_key: str = "",
    temperature: float = 0.3,
    max_tokens: int = 3000
) -> ContentMerger:
    """获取内容融合引擎实例"""
    return ContentMerger(
        provider=provider,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens
    )