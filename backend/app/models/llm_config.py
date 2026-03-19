"""
LLM 服务商配置模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

# 使用统一的 Base
from .database import Base

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

    # LLM 参数配置
    temperature = Column(Integer, default=70, nullable=False, comment="温度参数（0-100，默认 70 代表 0.7）")
    max_input_tokens = Column(Integer, default=8000, nullable=False, comment="最大输入 token 数（默认 8000）")
    max_output_tokens = Column(Integer, default=4000, nullable=False, comment="最大输出 token 数（默认 4000）")

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
            "temperature": self.temperature / 100 if self.temperature else 0.7,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
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
            "temperature": self.temperature / 100 if self.temperature else 0.7,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
