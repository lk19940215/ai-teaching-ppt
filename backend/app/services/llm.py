from openai import OpenAI, APITimeoutError as OpenAITimeoutError, APIError as OpenAIAPIError
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

class LLMProvider:
    """LLM 服务提供商枚举"""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CLAUDE = "claude"
    GLM = "glm"

class LLMService:
    """LLM 统一调用服务"""

    def __init__(
        self,
        provider: str = LLMProvider.DEEPSEEK,
        api_key: str = "",
        base_url: str = "",
        model: str = ""
    ):
        """
        初始化 LLM 服务
        Args:
            provider: 服务商
            api_key: API Key
            base_url: API 基础 URL
            model: 模型名称
        """
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

        # 设置默认值
        if provider == LLMProvider.DEEPSEEK:
            self.base_url = base_url or "https://api.deepseek.com"
            self.model = model or "deepseek-chat"
        elif provider == LLMProvider.OPENAI:
            self.base_url = base_url or "https://api.openai.com/v1"
            self.model = model or "gpt-4"
        elif provider == LLMProvider.CLAUDE:
            self.base_url = base_url or "https://api.anthropic.com/v1"
            self.model = model or "claude-3-opus-20240229"
        elif provider == LLMProvider.GLM:
            self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4"
            self.model = model or "glm-4"

        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        调用 LLM 对话接口
        Args:
            messages: 消息列表
            **kwargs: 额外参数
        Returns:
            LLM 返回的文本
        """
        if not self.client:
            raise ValueError("LLM 客户端未初始化，请先配置 API Key")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
                timeout=kwargs.get("timeout", 60)
            )
            return response.choices[0].message.content
        except OpenAITimeoutError as e:
            logger.error(f"LLM 调用超时: {e}")
            raise TimeoutError("LLM 调用超时") from e
        except OpenAIAPIError as e:
            logger.error(f"LLM API 错误: {e}")
            raise RuntimeError(f"LLM API 错误: {e}") from e
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise RuntimeError(f"LLM 调用失败: {e}") from e

    def generate_structured_content(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化内容
        Args:
            prompt: 提示词
            output_schema: 输出结构定义
            **kwargs: 额外参数
        Returns:
            结构化的输出结果
        """
        schema_description = json.dumps(output_schema, ensure_ascii=False, indent=2)

        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的教学 PPT 内容生成助手。请根据用户提供的教学内容，生成结构化的 PPT 内容。

请严格按照以下 JSON 格式输出：
{schema_description}

只返回 JSON，不要包含其他文字。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.chat(messages, **kwargs)

        # 解析 JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}, 原始响应: {response}")
            raise ValueError("LLM 返回的内容无法解析为 JSON") from e


# 全局 LLM 服务实例
_llm_service_instance: Optional[LLMService] = None

def get_llm_service(
    provider: str = LLMProvider.DEEPSEEK,
    api_key: str = "",
    base_url: str = "",
    model: str = ""
) -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service_instance
    if _llm_service_instance is None or \
       _llm_service_instance.api_key != api_key or \
       _llm_service_instance.provider != provider:
        _llm_service_instance = LLMService(provider, api_key, base_url, model)
    return _llm_service_instance