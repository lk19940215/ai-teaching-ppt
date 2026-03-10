import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent.parent

    # 后端配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI 教学 PPT 生成器"

    # 文件上传配置
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/jpg"]
    ALLOWED_PDF_TYPE: str = "application/pdf"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./ai_teaching_ppt.db"

    # LLM 配置
    DEFAULT_LLM_PROVIDER: str = "deepseek"
    OPENAI_API_BASE: str = "https://api.deepseek.com"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "deepseek-chat"

    # PPT 模板配置
    TEMPLATE_DIR: Path = BASE_DIR / "app" / "templates"

    # 公开静态文件目录（图片预览等）
    PUBLIC_DIR: Path = BASE_DIR / "public"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# 确保上传目录存在
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
settings.PUBLIC_DIR.mkdir(parents=True, exist_ok=True)