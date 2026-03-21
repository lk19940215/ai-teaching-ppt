"""
LLM 服务商配置管理 API

提供 LLM 服务商（DeepSeek、OpenAI、Claude、GLM）的配置管理功能：
- 从环境变量获取默认配置
- API Key 验证和连接测试
- 配置元数据管理（不再保存 API Key 到数据库）

所有端点前缀：/api/v1/config

重要变更（feat-001/feat-002）：
- API Key 不再保存到数据库，由前端 localStorage 管理
- 新增 /config/default 端点返回环境变量中的默认配置
- /config/providers/default/active 改为返回环境变量配置
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Optional, List
from sqlalchemy.orm import Session
import logging

from ..models.database import get_db
from ..models.llm_config_crud import (
    get_all_configs,
    get_config_by_provider,
    get_default_config,
    create_config,
    update_config,
    delete_config,
    set_default_provider,
    validate_api_key,
)
from ..ai.llm_client import LLMClient
from ..config import settings

router = APIRouter(prefix="/api/v1", tags=["config"])

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ["deepseek", "openai", "claude", "glm"]

# 默认 LLM 参数
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4000
CONNECTION_TEST_TIMEOUT = 15


@router.get("/config/default")
async def get_default_llm_config():
    """
    获取环境变量中的默认 LLM 配置

    从 LLM_CONFIG 环境变量读取配置，供前端初始化使用。
    如果未配置环境变量，返回 404。

    Returns:
        - provider: 服务商标识
        - apiKey: API 密钥
        - baseUrl: API 基础 URL
        - model: 模型名称
        - temperature: 温度参数
        - maxInputTokens: 最大输入 token
        - maxOutputTokens: 最大输出 token
    """
    try:
        default_config = settings.get_default_llm_config()
        if not default_config:
            return JSONResponse(content={
                "success": False,
                "message": "未配置默认 LLM（请设置 LLM_CONFIG 环境变量）"
            }, status_code=404)

        logger.info("[get_default_llm_config] 成功返回环境变量配置")
        return JSONResponse(content={
            "success": True,
            "data": default_config
        })
    except Exception as e:
        logger.error(f"获取默认配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取默认配置失败：{str(e)}"
        }, status_code=500)


@router.get("/config/providers")
async def list_providers(db: Session = Depends(get_db)):
    """
    获取所有已配置的 LLM 服务商

    返回数据库中所有已保存的服务商配置列表。
    """
    try:
        configs = get_all_configs(db)
        return JSONResponse(content={
            "success": True,
            "data": [config.to_dict() for config in configs]
        })
    except Exception as e:
        logger.error(f"获取配置列表失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取配置列表失败：{str(e)}"
        }, status_code=500)


@router.get("/config/providers/default")
async def get_default_provider_config(db: Session = Depends(get_db)):
    """
    获取默认服务商配置

    返回当前标记为默认的服务商配置。
    如果没有设置默认，返回 null。
    """
    try:
        config = get_default_config(db)
        if not config:
            return JSONResponse(content={
                "success": True,
                "data": None
            })

        return JSONResponse(content={
            "success": True,
            "data": config.to_dict()
        })
    except Exception as e:
        logger.error(f"获取默认配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取默认配置失败：{str(e)}"
        }, status_code=500)


@router.get("/config/providers/default/active")
async def get_active_provider_config():
    """
    获取默认 LLM 配置（从环境变量读取）

    此端点供前端调用 LLM 功能时使用。
    优先返回环境变量 LLM_CONFIG 中的配置。

    注意：此路由必须放在 /config/providers/{provider} 之前，
    否则 'default' 会被当作 provider 参数匹配。

    Returns:
        - provider: 服务商标识
        - apiKey: API 密钥
        - baseUrl: API 基础 URL
        - model: 模型名称
        - temperature: 温度参数
        - maxInputTokens: 最大输入 token
        - maxOutputTokens: 最大输出 token
    """
    try:
        # 优先从环境变量获取配置
        default_config = settings.get_default_llm_config()
        if default_config:
            logger.info("[get_active_provider_config] 返回环境变量配置")
            return JSONResponse(content={
                "success": True,
                "data": default_config
            })

        # 如果环境变量未配置，返回错误提示
        return JSONResponse(content={
            "success": False,
            "message": "请先在设置页面配置 LLM API Key"
        }, status_code=404)
    except Exception as e:
        logger.error(f"获取活动配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取活动配置失败：{str(e)}"
        }, status_code=500)


@router.get("/config/providers/{provider}")
async def get_provider_config(provider: str, db: Session = Depends(get_db)):
    """
    获取指定服务商的配置

    参数：
    - provider: 服务商标识（deepseek、openai、claude、glm）
    """
    try:
        config = get_config_by_provider(db, provider)
        if not config:
            return JSONResponse(content={
                "success": False,
                "message": f"服务商 {provider} 尚未配置"
            }, status_code=404)

        return JSONResponse(content={
            "success": True,
            "data": config.to_dict()
        })
    except Exception as e:
        logger.error(f"获取配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"获取配置失败：{str(e)}"
        }, status_code=500)


@router.post("/config/providers/{provider}")
async def save_provider_config(
    provider: str,
    api_key: str = Body(..., embed=True),
    base_url: Optional[str] = Body(None, embed=True),
    model: Optional[str] = Body(None, embed=True),
    is_default: Optional[bool] = Body(False, embed=True),
    temperature: Optional[float] = Body(None, embed=True),
    max_input_tokens: Optional[int] = Body(None, embed=True),
    max_output_tokens: Optional[int] = Body(None, embed=True),
):
    """
    验证并保存服务商配置元数据

    注意（feat-002）：API Key 不再保存到数据库，由前端 localStorage 管理。
    此端点仅用于验证 API Key 格式和测试连接。

    支持的服务商：deepseek、openai、claude、glm

    参数：
    - provider: 服务商标识
    - api_key: API 密钥（仅用于验证，不保存）
    - base_url: 自定义 API 地址（可选）
    - model: 模型名称（可选）
    - is_default: 是否设为默认服务商（保留兼容性）
    - temperature: 生成温度（可选）
    - max_input_tokens: 最大输入 token（可选）
    - max_output_tokens: 最大输出 token（可选）

    Returns:
        - success: True 表示验证通过
        - message: 提示信息
    """
    try:
        # 验证服务商是否支持
        if provider not in SUPPORTED_PROVIDERS:
            return JSONResponse(content={
                "success": False,
                "message": f"不支持的服务商：{provider}，支持的服务商：{', '.join(SUPPORTED_PROVIDERS)}"
            }, status_code=400)

        # API Key 仅保存在前端 localStorage，此处仅验证格式
        if not api_key or len(api_key) < 8:
            return JSONResponse(content={
                "success": False,
                "message": "API Key 格式无效"
            }, status_code=400)

        logger.info(f"[save_provider_config] 验证通过，provider={provider}")

        return JSONResponse(content={
            "success": True,
            "message": "配置验证成功（API Key 由浏览器本地存储管理）",
            "data": {
                "provider": provider,
                "api_key_masked": f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            }
        })
    except Exception as e:
        logger.error(f"验证配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"验证配置失败：{str(e)}"
        }, status_code=500)


@router.delete("/config/providers/{provider}")
async def delete_provider_config(provider: str, db: Session = Depends(get_db)):
    """
    删除服务商配置

    参数：
    - provider: 服务商标识（deepseek、openai、claude、glm）
    """
    try:
        success = delete_config(db, provider)
        if not success:
            return JSONResponse(content={
                "success": False,
                "message": f"服务商 {provider} 配置不存在"
            }, status_code=404)

        return JSONResponse(content={
            "success": True,
            "message": "配置删除成功"
        })
    except Exception as e:
        logger.error(f"删除配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"删除配置失败：{str(e)}"
        }, status_code=500)


@router.post("/config/providers/{provider}/set-default")
async def set_as_default(provider: str, db: Session = Depends(get_db)):
    """
    设置默认服务商

    将指定服务商标记为默认，同时取消其他服务商的默认状态。

    参数：
    - provider: 服务商标识（deepseek、openai、claude、glm）
    """
    try:
        config = set_default_provider(db, provider)
        if not config:
            return JSONResponse(content={
                "success": False,
                "message": f"服务商 {provider} 配置不存在"
            }, status_code=404)

        return JSONResponse(content={
            "success": True,
            "message": f"已设置 {provider} 为默认服务商",
            "data": config.to_dict()
        })
    except Exception as e:
        logger.error(f"设置默认服务商失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"设置默认服务商失败：{str(e)}"
        }, status_code=500)


@router.post("/config/providers/{provider}/validate")
async def validate_provider_config(provider: str, db: Session = Depends(get_db)):
    """
    验证服务商配置

    检查指定服务商的配置是否存在，并验证 API Key 格式。

    参数：
    - provider: 服务商标识（deepseek、openai、claude、glm）
    """
    try:
        result = validate_api_key(db, provider)
        if not result:
            return JSONResponse(content={
                "success": False,
                "message": f"服务商 {provider} 尚未配置"
            }, status_code=404)

        return JSONResponse(content={
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"验证配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"验证配置失败：{str(e)}"
        }, status_code=500)


@router.post("/config/test-connection")
async def test_connection(
    provider: str = Body(..., embed=True),
    api_key: str = Body(..., embed=True),
    base_url: Optional[str] = Body(None, embed=True),
    model: Optional[str] = Body(None, embed=True),
    temperature: Optional[float] = Body(None, embed=True),
    max_tokens: Optional[int] = Body(None, embed=True)
):
    """
    测试 LLM 连接

    使用提供的参数创建 LLM 服务实例并发送测试请求，
    验证 API Key 和网络连接是否正常。

    参数：
    - provider: 服务商标识
    - api_key: API 密钥
    - base_url: 自定义 API 地址（可选）
    - model: 模型名称（可选）
    - temperature: 生成温度（可选，默认 0.7）
    - max_tokens: 最大 token 数（可选，默认 4000）
    """
    try:
        # 使用传入参数或默认值
        llm_temperature = temperature if temperature is not None else DEFAULT_TEMPERATURE
        llm_max_tokens = max_tokens if max_tokens is not None else DEFAULT_MAX_TOKENS

        llm_client = LLMClient(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens,
            timeout=CONNECTION_TEST_TIMEOUT,
        )

        response = llm_client.chat(
            messages=[{"role": "user", "content": "请回复'连接成功'"}],
        )

        return JSONResponse(content={
            "success": True,
            "message": "连接测试成功",
            "response": response
        })
    except TimeoutError as e:
        logger.error(f"连接测试超时：{e}")
        return JSONResponse(content={
            "success": False,
            "message": "连接测试超时，请检查网络"
        }, status_code=408)
    except Exception as e:
        logger.error(f"连接测试失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"连接测试失败：{str(e)}"
        }, status_code=400)

