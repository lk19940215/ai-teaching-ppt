"""
LLM 服务商配置管理 API

提供 LLM 服务商（DeepSeek、OpenAI、Claude、GLM）的配置管理功能：
- 配置 CRUD 操作
- 默认服务商设置
- API Key 验证
- 连接测试

所有端点前缀：/api/v1/config
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
from ..services.llm import LLMService, LLMProvider

router = APIRouter(prefix="/api/v1", tags=["config"])

logger = logging.getLogger(__name__)

# 支持的 LLM 服务商列表
SUPPORTED_PROVIDERS = [
    LLMProvider.DEEPSEEK,
    LLMProvider.OPENAI,
    LLMProvider.CLAUDE,
    LLMProvider.GLM,
]

# 默认 LLM 参数
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4000
CONNECTION_TEST_TIMEOUT = 15


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
    db: Session = Depends(get_db)
):
    """
    保存服务商配置

    支持的服务商：deepseek、openai、claude、glm

    参数：
    - provider: 服务商标识
    - api_key: API 密钥
    - base_url: 自定义 API 地址（可选）
    - model: 模型名称（可选）
    - is_default: 是否设为默认服务商
    - temperature: 生成温度（可选）
    - max_input_tokens: 最大输入 token（可选）
    - max_output_tokens: 最大输出 token（可选）
    """
    try:
        # 验证服务商是否支持
        if provider not in SUPPORTED_PROVIDERS:
            return JSONResponse(content={
                "success": False,
                "message": f"不支持的服务商：{provider}，支持的服务商：{', '.join(SUPPORTED_PROVIDERS)}"
            }, status_code=400)

        # 检查是否已存在配置
        existing = get_config_by_provider(db, provider)
        if existing:
            # 更新配置
            config = update_config(
                db, provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                is_default=is_default,
                temperature=temperature,
                max_input_tokens=max_input_tokens,
                max_output_tokens=max_output_tokens
            )
        else:
            # 创建配置
            config = create_config(
                db, provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                is_default=is_default,
                temperature=temperature,
                max_input_tokens=max_input_tokens,
                max_output_tokens=max_output_tokens
            )

        return JSONResponse(content={
            "success": True,
            "message": "配置保存成功",
            "data": config.to_dict()
        })
    except Exception as e:
        logger.error(f"保存配置失败：{e}")
        return JSONResponse(content={
            "success": False,
            "message": f"保存配置失败：{str(e)}"
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

        llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )

        # 发送测试请求
        response = llm_service.chat(
            messages=[{"role": "user", "content": "请回复'连接成功'"}],
            timeout=CONNECTION_TEST_TIMEOUT
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
