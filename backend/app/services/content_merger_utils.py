# -*- coding: utf-8 -*-
"""
PPT AI 内容融合工具模块

提供验证、准备上下文、执行 AI 合并等工具函数
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== 验证函数 ====================

def validate_merge_request(
    api_key: Optional[str],
    slide_data: Optional[Dict[str, Any]] = None,
    action: Optional[str] = None,
    supported_actions: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    验证合并请求参数

    Args:
        api_key: LLM API Key
        slide_data: 幻灯片数据（可选，用于单页处理）
        action: 处理动作（可选，用于单页处理）
        supported_actions: 支持的动作列表（可选）

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    # 验证 API Key
    if not api_key:
        return False, "API Key 不能为空"

    if not isinstance(api_key, str):
        return False, "API Key 必须是字符串类型"

    if len(api_key.strip()) < 10:
        return False, "API Key 格式不正确"

    # 验证幻灯片数据（如果提供）
    if slide_data is not None:
        if not isinstance(slide_data, dict):
            return False, "幻灯片数据必须是字典类型"

        # 验证必要字段
        if not slide_data.get('elements') and not slide_data.get('teaching_content'):
            logger.warning("幻灯片数据缺少 elements 和 teaching_content 字段")

    # 验证动作（如果提供）
    if action is not None:
        if not isinstance(action, str):
            return False, "动作必须是字符串类型"

        if supported_actions and action not in supported_actions:
            return False, f"不支持的动作: {action}，支持的动作: {supported_actions}"

    return True, ""


def validate_multi_page_request(
    api_key: Optional[str],
    pages_a: Optional[List[Dict[str, Any]]],
    pages_b: Optional[List[Dict[str, Any]]]
) -> Tuple[bool, str]:
    """
    验证多页合并请求

    Args:
        api_key: LLM API Key
        pages_a: PPT A 的页面列表
        pages_b: PPT B 的页面列表

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    # 验证 API Key
    valid, error = validate_merge_request(api_key)
    if not valid:
        return False, error

    # 验证页面列表
    if pages_a is not None:
        if not isinstance(pages_a, list):
            return False, "pages_a 必须是列表类型"
        if len(pages_a) == 0:
            return False, "pages_a 不能为空列表"

    if pages_b is not None:
        if not isinstance(pages_b, list):
            return False, "pages_b 必须是列表类型"
        if len(pages_b) == 0:
            return False, "pages_b 不能为空列表"

    # 至少需要一个页面列表
    if not pages_a and not pages_b:
        return False, "至少需要提供一个页面列表"

    return True, ""


def validate_full_merge_request(
    api_key: Optional[str],
    doc_a: Optional[Dict[str, Any]],
    doc_b: Optional[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    验证整体合并请求

    Args:
        api_key: LLM API Key
        doc_a: PPT A 的文档结构
        doc_b: PPT B 的文档结构

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    # 验证 API Key
    valid, error = validate_merge_request(api_key)
    if not valid:
        return False, error

    # 验证文档结构
    if doc_a is not None:
        if not isinstance(doc_a, dict):
            return False, "doc_a 必须是字典类型"
        if 'slides' not in doc_a:
            logger.warning("doc_a 缺少 'slides' 字段")

    if doc_b is not None:
        if not isinstance(doc_b, dict):
            return False, "doc_b 必须是字典类型"
        if 'slides' not in doc_b:
            logger.warning("doc_b 缺少 'slides' 字段")

    # 必须提供两个文档
    if not doc_a or not doc_b:
        return False, "必须提供两个 PPT 文档"

    return True, ""


# ==================== 上下文准备函数 ====================

def prepare_merge_context(
    provider: str = "deepseek",
    api_key: str = "",
    temperature: float = 0.3,
    max_tokens: int = 3000
) -> Dict[str, Any]:
    """
    准备合并上下文配置

    Args:
        provider: LLM 服务商
        api_key: API Key
        temperature: 温度参数
        max_tokens: 最大输出 token

    Returns:
        Dict[str, Any]: 合并上下文配置
    """
    context = {
        "provider": provider,
        "api_key": api_key,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "model_config": _get_model_config(provider)
    }

    logger.info(f"准备合并上下文: provider={provider}, temperature={temperature}")
    return context


def _get_model_config(provider: str) -> Dict[str, Any]:
    """
    获取服务商对应的模型配置

    Args:
        provider: LLM 服务商名称

    Returns:
        Dict[str, Any]: 模型配置
    """
    model_configs = {
        "deepseek": {
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com/v1",
            "max_context": 64000
        },
        "openai": {
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "max_context": 128000
        },
        "claude": {
            "model": "claude-3-5-sonnet-20241022",
            "base_url": "https://api.anthropic.com/v1",
            "max_context": 200000
        },
        "glm": {
            "model": "glm-4",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "max_context": 128000
        }
    }

    return model_configs.get(provider, model_configs["deepseek"])


def prepare_single_page_context(
    slide_data: Dict[str, Any],
    action: str,
    custom_prompt: str = ""
) -> Dict[str, Any]:
    """
    准备单页处理上下文

    Args:
        slide_data: 幻灯片数据
        action: 处理动作
        custom_prompt: 自定义提示词

    Returns:
        Dict[str, Any]: 单页处理上下文
    """
    # 提取幻灯片标题
    title = _extract_slide_title(slide_data)

    # 提取幻灯片内容
    content = _extract_slide_content(slide_data)

    context = {
        "action": action,
        "slide_title": title,
        "slide_content": content,
        "custom_prompt": custom_prompt,
        "has_custom_prompt": bool(custom_prompt.strip())
    }

    logger.debug(f"单页处理上下文: action={action}, title={title[:20] if title else 'N/A'}")
    return context


def prepare_multi_page_context(
    pages_a: List[Dict[str, Any]],
    pages_b: List[Dict[str, Any]],
    custom_prompt: str = ""
) -> Dict[str, Any]:
    """
    准备多页融合上下文

    Args:
        pages_a: PPT A 的页面列表
        pages_b: PPT B 的页面列表
        custom_prompt: 自定义提示词

    Returns:
        Dict[str, Any]: 多页融合上下文
    """
    # 提取页面摘要
    summary_a = [_extract_slide_summary(p, i) for i, p in enumerate(pages_a)]
    summary_b = [_extract_slide_summary(p, i) for i, p in enumerate(pages_b)]

    context = {
        "pages_a_count": len(pages_a),
        "pages_b_count": len(pages_b),
        "pages_a_summary": summary_a,
        "pages_b_summary": summary_b,
        "custom_prompt": custom_prompt,
        "has_custom_prompt": bool(custom_prompt.strip())
    }

    logger.debug(f"多页融合上下文: A={len(pages_a)}页, B={len(pages_b)}页")
    return context


def _extract_slide_title(slide_data: Dict[str, Any]) -> str:
    """从幻灯片数据中提取标题"""
    # 尝试从 teaching_content 提取
    teaching = slide_data.get('teaching_content', {})
    if teaching.get('title'):
        return teaching['title']

    # 尝试从 elements 提取
    for elem in slide_data.get('elements', []):
        if elem.get('type') == 'title' and elem.get('text'):
            return elem['text']

    return ""


def _extract_slide_content(slide_data: Dict[str, Any]) -> str:
    """从幻灯片数据中提取内容文本"""
    parts = []

    # 从 elements 提取
    for elem in slide_data.get('elements', []):
        elem_type = elem.get('type', '')
        text = elem.get('text', '')

        if not text:
            continue

        if elem_type == 'title':
            parts.append(f"【标题】{text}")
        elif elem_type == 'text_body':
            parts.append(text)
        elif elem_type == 'list_item':
            parts.append(f"- {text}")

    # 从 teaching_content 提取
    teaching = slide_data.get('teaching_content', {})
    if teaching.get('main_points'):
        points = teaching['main_points']
        if isinstance(points, list):
            parts.append("【要点】")
            parts.extend([f"- {p}" for p in points if isinstance(p, str)])

    return "\n".join(parts)


def _extract_slide_summary(slide_data: Dict[str, Any], index: int) -> Dict[str, Any]:
    """提取幻灯片摘要"""
    title = _extract_slide_title(slide_data)
    content_preview = _extract_slide_content(slide_data)[:100]

    return {
        "index": index,
        "title": title or f"第 {index + 1} 页",
        "preview": content_preview
    }


# ==================== AI 执行函数 ====================

def execute_ai_merge(
    llm_service,
    system_prompt: str,
    user_prompt: str,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    执行 AI 合并操作

    Args:
        llm_service: LLM 服务实例
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        context: 合并上下文（可选，用于日志）

    Returns:
        Tuple[str, Dict[str, Any]]: (响应文本, token 使用情况)
    """
    if llm_service is None:
        raise ValueError("LLM 服务实例不能为空")

    if not system_prompt:
        raise ValueError("系统提示词不能为空")

    if not user_prompt:
        raise ValueError("用户提示词不能为空")

    # 记录请求信息
    context_info = context or {}
    logger.info(f"执行 AI 合并: provider={context_info.get('provider', 'unknown')}")

    try:
        # 调用 LLM 服务
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response, usage = llm_service.chat_with_usage(messages)

        # 记录响应信息
        logger.info(f"AI 合并完成: tokens={usage}")

        return response, usage

    except Exception as e:
        logger.error(f"AI 合并执行失败: {e}")
        raise


def execute_ai_merge_with_retry(
    llm_service,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 2,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    带重试机制的 AI 合并执行

    Args:
        llm_service: LLM 服务实例
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        max_retries: 最大重试次数
        context: 合并上下文

    Returns:
        Tuple[str, Dict[str, Any]]: (响应文本, token 使用情况)
    """
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return execute_ai_merge(
                llm_service,
                system_prompt,
                user_prompt,
                context
            )
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(f"AI 合并失败，尝试重试 ({attempt + 1}/{max_retries}): {e}")
            else:
                logger.error(f"AI 合并最终失败: {e}")

    raise last_error


# ==================== 便捷函数 ====================

def create_error_result(
    error: str,
    action: Optional[str] = None,
    original_slide: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建错误结果

    Args:
        error: 错误信息
        action: 动作类型
        original_slide: 原始幻灯片数据

    Returns:
        Dict[str, Any]: 错误结果字典
    """
    result = {
        "success": False,
        "error": error
    }

    if action:
        result["action"] = action

    if original_slide:
        result["original_slide"] = original_slide
        result["new_content"] = {
            "title": _extract_slide_title(original_slide) or "处理失败",
            "main_points": ["处理过程中发生错误，请重试"],
            "additional_content": ""
        }

    return result


def create_success_result(
    new_content: Dict[str, Any],
    changes: Optional[List[str]] = None,
    **extra_fields
) -> Dict[str, Any]:
    """
    创建成功结果

    Args:
        new_content: 新内容
        changes: 变更列表
        **extra_fields: 额外字段

    Returns:
        Dict[str, Any]: 成功结果字典
    """
    result = {
        "success": True,
        "error": None,
        "new_content": new_content
    }

    if changes:
        result["changes"] = changes

    result.update(extra_fields)

    return result