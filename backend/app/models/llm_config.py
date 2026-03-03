"""
LLM 服务商配置模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

# 使用与 history 相同的 Base，确保表能一起创建
from .history import Base

class LLMConfig(Base):
    """LLM 服务商配置表"""
    __tablename__ = "llm_config"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 服务商标识
    provider = Column(String(32), unique=True, nullable=False, comment="服务商标识（deepseek/openai/claude/glm）")

    # API 配置
    api_key = Column(String(512), nullable=False, comment="API Key（加密存储）")
    base_url = Column(String(255), nullable=True, comment="API 基础 URL")
    model = Column(String(128), nullable=True, comment="模型名称")

    # 配置状态
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认服务商")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self):
        """转换为字典格式（不包含敏感信息）"""
        return {
            "id": self.id,
            "provider": self.provider,
            "api_key_masked": f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***",
            "base_url": self.base_url,
            "model": self.model,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_full_dict(self):
        """转换为完整字典格式（包含敏感信息，仅内部使用）"""
        return {
            "id": self.id,
            "provider": self.provider,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
