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
        model: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ):
        """
        初始化 LLM 服务
        Args:
            provider: 服务商
            api_key: API Key
            base_url: API 基础 URL
            model: 模型名称
            temperature: 温度参数（0-2，默认 0.7）
            max_tokens: 最大输出 token 数（默认 4000）
        """
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

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
            **kwargs: 额外参数，支持 temperature, max_tokens, response_format 等
        Returns:
            LLM 返回的文本
        """
        if not self.client:
            raise ValueError("LLM 客户端未初始化，请先配置 API Key")

        # 构建基础参数，优先使用 kwargs，其次使用实例默认值
        chat_kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "timeout": kwargs.get("timeout", 60)
        }

        # OpenAI 支持 response_format 参数用于 JSON 输出
        if self.provider == LLMProvider.OPENAI and kwargs.get("response_format"):
            chat_kwargs["response_format"] = kwargs["response_format"]

        try:
            response = self.client.chat.completions.create(**chat_kwargs)
            return response.choices[0].message.content
        except OpenAITimeoutError as e:
            logger.error(f"LLM 调用超时：{e}")
            raise TimeoutError("LLM 调用超时") from e
        except OpenAIAPIError as e:
            logger.error(f"LLM API 错误：{e}")
            raise RuntimeError(f"LLM API 错误：{e}") from e
        except Exception as e:
            logger.error(f"LLM 调用失败：{e}")
            raise RuntimeError(f"LLM 调用失败：{e}") from e

    def _extract_json_from_response(self, response: str) -> str:
        """
        从 LLM 响应中提取 JSON 内容
        处理多种格式变体：代码块、文字说明前后缀、混合内容等
        """
        import re

        # 1. 优先匹配 ```json ... ```
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
        if json_match:
            return json_match.group(1)

        # 2. 匹配 ``` ... ```（无语言标记）
        code_match = re.search(r'```\s*([\s\S]*?)\s*```', response)
        if code_match:
            return code_match.group(1)

        # 3. 匹配 JSON 对象：从第一个 { 到最后一个 }
        # 处理大括号嵌套，找到最外层的 JSON 对象
        brace_count = 0
        start_idx = None
        end_idx = None

        for i, char in enumerate(response):
            if char == '{':
                if start_idx is None:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    end_idx = i + 1
                    break

        if start_idx is not None and end_idx is not None:
            json_candidate = response[start_idx:end_idx]
            # 验证是否包含基本的 JSON 特征
            if re.search(r'".*?"\s*:', json_candidate):  # 至少有一个键值对
                return json_candidate

        # 4. 移除常见的前缀说明文字
        # 匹配： "以下是...："、"JSON 如下："、"返回结果：" 等
        prefix_patterns = [
            r'^[\s\S]*?(?=\{)',  # 移除 { 之前的所有内容
        ]
        for pattern in prefix_patterns:
            match = re.match(pattern, response, re.MULTILINE)
            if match:
                remaining = response[match.end():]
                # 检查剩余部分是否以 { 开头
                if remaining.strip().startswith('{'):
                    return remaining.strip()

        # 5. 没有匹配到，返回原始内容（去除首尾空白）
        return response.strip()

    def _fix_json(self, json_str: str) -> str:
        """
        修复常见的 JSON 格式问题
        处理：尾部逗号、缺失引号、单引号、未转义引号、特殊字符等
        """
        import re

        # 去除首尾空白
        json_str = json_str.strip()

        # 1. 替换单引号为双引号（键名和值都处理）
        # 先处理键名的单引号：'key':
        json_str = re.sub(r"'([^']*)'(?=\s*:)", r'"\1"', json_str)

        # 处理值的单引号：将字符串值两边的单引号换成双引号
        def replace_value_quotes(match):
            prefix = match.group(1)  # ': ' 部分
            value = match.group(2)   # 值内容
            suffix = match.group(3)  # 后面的逗号、} 或]
            return f'{prefix}"{value}"{suffix}'

        # 匹配单引号包裹的字符串值
        json_str = re.sub(r"(:\s*)'([^']*)'(\s*[,}\]])", replace_value_quotes, json_str)

        # 2. 移除尾部的逗号（} 或] 之前的逗号）
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        # 移除属性值末尾的逗号（在}或]之前）
        json_str = re.sub(r'(["\d\w}\]])\s*,\s*([}\]])', r'\1\2', json_str)

        # 3. 处理 key 没有引号的情况：{key: 或 , key:
        json_str = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)

        # 4. 处理字符串值中未转义的双引号
        # 匹配 "hello "world" test" → "hello \"world\" test"
        def escape_inner_quotes(match):
            content = match.group(1)
            # 转义内部的双引号
            escaped = content.replace('\\"', '"').replace('"', '\\"')
            return f'"{escaped}"'

        # 先识别已经是字符串的内容（在双引号之间的内容），避免重复处理
        # 这个步骤比较复杂，只在简单情况下处理
        # 更复杂的情况交给 json5 处理

        # 5. 处理中文字符后的冒号可能是全角冒号
        json_str = json_str.replace('：', ':')

        # 6. 替换全角逗号为半角逗号
        json_str = json_str.replace('，', ',')

        # 7. 处理可能存在的换行符在字符串值中（需要转义）
        # 这个比较复杂，只在确定安全的情况下处理

        # 8. 移除控制字符（但保留正常的换行和制表符）
        json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', json_str)

        # 9. 确保布尔值和 null 是小写的
        json_str = re.sub(r'\bTrue\b', 'true', json_str)
        json_str = re.sub(r'\bFalse\b', 'false', json_str)
        json_str = re.sub(r'\bNone\b', 'null', json_str)

        return json_str

    def generate_structured_content(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成结构化内容（单次执行，不自动重试）
        Args:
            prompt: 提示词
            output_schema: 输出结构定义
            **kwargs: 额外参数
        Returns:
            结构化的输出结果

        Raises:
            ValueError: 当无法解析 JSON 时抛出，包含详细错误信息
        """
        schema_description = json.dumps(output_schema, ensure_ascii=False, indent=2)

        messages = [
            {
                "role": "system",
                "content": f"""你是一个专业的教学 PPT 内容生成助手。请根据用户提供的教学内容，生成结构化的 PPT 内容。

请严格按照以下 JSON 格式输出：
{schema_description}

**重要要求**：
1. 只返回 JSON 对象本身，不要包含 ```json 或 ``` 等代码块标记
2. 不要添加任何解释性文字
3. 确保 JSON 格式正确：键名用双引号、没有尾部逗号、括号匹配"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # OpenAI 使用 response_format 确保 JSON 输出
        if self.provider == LLMProvider.OPENAI:
            kwargs["response_format"] = {"type": "json_object"}

        # 单次执行，不重试
        response = self.chat(messages, **kwargs)

        # 第 1 步：提取 JSON 代码块
        json_str = self._extract_json_from_response(response)

        # 第 2 步：尝试直接用标准 json 解析
        try:
            result = json.loads(json_str)
            logger.info("JSON 解析成功（标准解析器）")
            return result
        except json.JSONDecodeError as parse_error:
            logger.warning(f"JSON 直接解析失败：{parse_error}")

        # 第 3 步：尝试修复后解析
        fixed_json = self._fix_json(json_str)
        logger.debug(f"修复后的 JSON: {fixed_json[:200]}...")

        try:
            result = json.loads(fixed_json)
            logger.info("JSON 修复后解析成功（标准解析器）")
            return result
        except json.JSONDecodeError as fix_error:
            logger.warning(f"JSON 修复后仍失败：{fix_error}")

        # 第 4 步：尝试使用 json5 解析（更宽松的语法）
        try:
            import json5
            result = json5.loads(json_str)
            logger.info("JSON 解析成功（json5 解析器）")
            return result
        except ImportError:
            logger.warning("json5 未安装，跳过")
        except Exception as json5_error:
            logger.warning(f"json5 解析失败：{json5_error}")

        # 第 5 步：尝试使用 json5 解析修复后的 JSON
        try:
            import json5
            result = json5.loads(fixed_json)
            logger.info("JSON 修复后解析成功（json5 解析器）")
            return result
        except (ImportError, Exception) as final_error:
            logger.warning(f"json5 解析修复后的 JSON 也失败：{final_error}")

        # 所有方法都失败，抛出详细错误信息
        logger.error(f"JSON 解析最终失败，原始响应：{response[:500]}...")
        error_details = [
            f"LLM 返回的内容无法解析为有效的 JSON",
            f"原始响应片段：{response[:300]}...",
            f"直接解析错误：{type(parse_error).__name__}: {parse_error}",
            f"修复后解析错误：{type(fix_error).__name__}: {fix_error}",
            "",
            "可能的原因：",
            "1. LLM 生成的 JSON 格式不完整或有语法错误",
            "2. 教学内容描述不够清晰，导致 LLM 理解偏差",
            "3. 输出包含了非 JSON 的额外内容",
            "",
            "建议：",
            "- 检查教学内容是否清晰、具体",
            "- 尝试简化输入内容后重新生成",
            "- 如问题持续，请联系管理员"
        ]
        raise ValueError("\n".join(error_details)) from fix_error


# 全局 LLM 服务实例
_llm_service_instance: Optional[LLMService] = None

def get_llm_service(
    provider: str = LLMProvider.DEEPSEEK,
    api_key: str = "",
    base_url: str = "",
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4000
) -> LLMService:
    """获取 LLM 服务单例"""
    global _llm_service_instance
    if _llm_service_instance is None or \
       _llm_service_instance.api_key != api_key or \
       _llm_service_instance.provider != provider or \
       _llm_service_instance.temperature != temperature or \
       _llm_service_instance.max_tokens != max_tokens:
        _llm_service_instance = LLMService(provider, api_key, base_url, model, temperature, max_tokens)
    return _llm_service_instance
