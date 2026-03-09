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

        # 构建 LLM 提示词
        system_prompt = self._build_system_prompt(MergeType.FULL)
        user_prompt = self._build_full_merge_prompt(doc_a, doc_b, custom_prompt)

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

        # 构建提示词
        system_prompt = self._build_system_prompt(MergeType.SINGLE)
        user_prompt = self._build_single_page_prompt(slide_data, action, custom_prompt)

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

        # 构建提示词
        system_prompt = self._build_system_prompt(MergeType.PARTIAL)
        user_prompt = self._build_pages_merge_prompt(pages_a, pages_b, custom_prompt)

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
        """解析单页处理响应"""
        try:
            data = self._extract_json(response)

            return {
                "action": action,
                "original_slide": original,
                "new_content": data.get('new_content', {}),
                "changes": data.get('changes', []),
                "success": True
            }

        except Exception as e:
            logger.error(f"解析单页响应失败: {e}")
            return {
                "action": action,
                "original_slide": original,
                "new_content": {},
                "changes": [],
                "success": False,
                "error": str(e)
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