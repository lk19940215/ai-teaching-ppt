"""
LLM 服务商配置 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from .llm_config import LLMConfig


def get_all_configs(db: Session) -> List[LLMConfig]:
    """获取所有配置"""
    result = db.execute(select(LLMConfig).order_by(LLMConfig.provider))
    return list(result.scalars().all())


def get_config_by_provider(db: Session, provider: str) -> Optional[LLMConfig]:
    """根据服务商获取配置"""
    result = db.execute(
        select(LLMConfig).where(LLMConfig.provider == provider)
    )
    return result.scalar_one_or_none()


def get_default_config(db: Session) -> Optional[LLMConfig]:
    """获取默认服务商配置"""
    result = db.execute(
        select(LLMConfig).where(LLMConfig.is_default == True, LLMConfig.is_active == True)
    )
    return result.scalar_one_or_none()


def create_config(
    db: Session,
    provider: str,
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    is_default: bool = False,
    temperature: float = 0.7,
    max_input_tokens: int = 4096,
    max_output_tokens: int = 2000
) -> LLMConfig:
    """创建新配置"""
    # 如果设为默认，先取消其他默认
    if is_default:
        db.query(LLMConfig).update({"is_default": False})

    config = LLMConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        is_default=is_default,
        is_active=True,
        temperature=temperature,
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def update_config(
    db: Session,
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    is_default: Optional[bool] = None,
    is_active: Optional[bool] = None,
    temperature: Optional[float] = None,
    max_input_tokens: Optional[int] = None,
    max_output_tokens: Optional[int] = None
) -> Optional[LLMConfig]:
    """更新配置"""
    config = get_config_by_provider(db, provider)
    if not config:
        return None

    # 如果设为默认，先取消其他默认
    if is_default:
        db.query(LLMConfig).update({"is_default": False})

    # 更新字段
    if api_key is not None:
        config.api_key = api_key
    if base_url is not None:
        config.base_url = base_url
    if model is not None:
        config.model = model
    if is_default is not None:
        config.is_default = is_default
    if is_active is not None:
        config.is_active = is_active
    if temperature is not None:
        config.temperature = temperature
    if max_input_tokens is not None:
        config.max_input_tokens = max_input_tokens
    if max_output_tokens is not None:
        config.max_output_tokens = max_output_tokens

    db.commit()
    db.refresh(config)
    return config


def delete_config(db: Session, provider: str) -> bool:
    """删除配置"""
    config = get_config_by_provider(db, provider)
    if not config:
        return False

    db.delete(config)
    db.commit()
    return True


def set_default_provider(db: Session, provider: str) -> Optional[LLMConfig]:
    """设置默认服务商"""
    # 取消所有默认
    db.query(LLMConfig).update({"is_default": False})

    # 设置新的默认
    config = get_config_by_provider(db, provider)
    if config:
        config.is_default = True
        db.commit()
        db.refresh(config)
    return config


def validate_api_key(db: Session, provider: str) -> Optional[Dict[str, Any]]:
    """验证 API Key 是否已配置"""
    config = get_config_by_provider(db, provider)
    if not config:
        return None

    return {
        "configured": bool(config.api_key),
        "is_active": config.is_active,
        "provider": provider,
        "model": config.model,
        "base_url": config.base_url,
    }
