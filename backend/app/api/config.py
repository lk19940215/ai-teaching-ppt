"""
LLM 服务商配置管理 API
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


@router.get("/config/providers")
async def list_providers(db: Session = Depends(get_db)):
    """获取所有已配置的 LLM 服务商"""
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
    """获取默认服务商配置"""
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
    """获取指定服务商的配置"""
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
    db: Session = Depends(get_db)
):
    """保存服务商配置"""
    try:
        # 验证 provider 是否合法
        valid_providers = [LLMProvider.DEEPSEEK, LLMProvider.OPENAI, LLMProvider.CLAUDE, LLMProvider.GLM]
        if provider not in valid_providers:
            return JSONResponse(content={
                "success": False,
                "message": f"不支持的服务商：{provider}，支持的：{', '.join(valid_providers)}"
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
                is_default=is_default
            )
        else:
            # 创建配置
            config = create_config(
                db, provider,
                api_key=api_key,
                base_url=base_url,
                model=model,
                is_default=is_default
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
    """删除服务商配置"""
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
    """设置默认服务商"""
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
    """验证服务商配置"""
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
    model: Optional[str] = Body(None, embed=True)
):
    """测试 LLM 连接"""
    try:
        llm_service = LLMService(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

        # 发送测试请求
        response = llm_service.chat(
            messages=[{"role": "user", "content": "请回复'连接成功'"}],
            timeout=15
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
