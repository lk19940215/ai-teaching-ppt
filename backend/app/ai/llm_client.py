"""
LLM 客户端

OpenAI 兼容协议的统一 LLM 调用层。
支持 DeepSeek / OpenAI / Claude / GLM / 自定义 provider。
"""

import re
import json
import logging
from typing import Optional

from openai import OpenAI, Timeout

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI 兼容协议的 LLM 客户端"""

    PROVIDER_DEFAULTS = {
        "deepseek": ("https://api.deepseek.com", "deepseek-chat"),
        "openai": ("https://api.openai.com/v1", "gpt-4"),
        "claude": ("https://api.anthropic.com/v1", "claude-3-opus-20240229"),
        "glm": ("https://open.bigmodel.cn/api/paas/v4", "glm-4"),
    }

    def __init__(
        self,
        provider: str = "deepseek",
        api_key: str = "",
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 3000,
        timeout: int = 300,
    ):
        defaults = self.PROVIDER_DEFAULTS.get(provider, (None, None))
        self.provider = provider
        self.base_url = base_url or defaults[0]
        self.model = model or defaults[1]
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.base_url:
            raise ValueError(f"自定义 provider '{provider}' 必须提供 base_url")
        if not api_key:
            raise ValueError("必须提供 api_key")

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=Timeout(connect=10.0, read=timeout, write=timeout, pool=timeout),
        )

    def chat(self, messages: list[dict], **kwargs) -> str:
        """调用 LLM，返回文本"""
        chat_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        rf = kwargs.get("response_format")
        if rf:
            chat_kwargs["response_format"] = rf

        try:
            response = self.client.chat.completions.create(**chat_kwargs)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise RuntimeError(f"LLM 调用失败: {e}") from e

    def chat_json(self, messages: list[dict], **kwargs) -> dict:
        """调用 LLM 并解析 JSON 响应"""
        kwargs["response_format"] = {"type": "json_object"}
        text = self.chat(messages, **kwargs)
        return self._parse_json(text)

    def _parse_json(self, text: str) -> dict:
        """健壮的 JSON 解析"""
        json_str = self._extract_json_block(text)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        fixed = self._fix_json(json_str)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        try:
            import json5
            return json5.loads(json_str)
        except (ImportError, Exception):
            pass

        try:
            import json5
            return json5.loads(fixed)
        except (ImportError, Exception):
            pass

        raise ValueError(f"无法解析 LLM 返回的 JSON:\n{text[:500]}")

    def _extract_json_block(self, text: str) -> str:
        """从 LLM 响应中提取 JSON"""
        m = re.search(r"```json\s*([\s\S]*?)\s*```", text)
        if m:
            return m.group(1)

        m = re.search(r"```\s*([\s\S]*?)\s*```", text)
        if m:
            return m.group(1)

        depth = 0
        start = None
        for i, c in enumerate(text):
            if c == "{":
                if start is None:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start : i + 1]

        return text.strip()

    def _fix_json(self, s: str) -> str:
        """修复常见 JSON 格式问题"""
        s = s.strip()
        s = re.sub(r"'([^']*)'(?=\s*:)", r'"\1"', s)
        s = re.sub(r",\s*([}\]])", r"\1", s)
        s = re.sub(r"([{,]\s*)(\w+)(\s*:)", r'\1"\2"\3', s)
        s = s.replace("\uff1a", ":").replace("\uff0c", ",")
        s = re.sub(r"\bTrue\b", "true", s)
        s = re.sub(r"\bFalse\b", "false", s)
        s = re.sub(r"\bNone\b", "null", s)
        return s
