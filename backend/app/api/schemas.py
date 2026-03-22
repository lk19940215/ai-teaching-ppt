"""
API 请求/响应模型
"""

from typing import Optional
from pydantic import BaseModel, Field

from ..core.models import (
    SlideSelector,
    PPTVersion, ProcessingResult,
)


# ---- 请求模型 ----

class ProcessRequest(BaseModel):
    """AI 处理请求

    单源模式（polish/expand/rewrite/extract）:
      slide_indices + source → 从同一个源文件提取多页

    多源模式（fuse）:
      selections → 从不同源文件提取页面进行融合
    """
    session_id: str
    slide_indices: list[int] = []
    action: str = Field(..., pattern="^(polish|expand|rewrite|extract|fuse)$")
    custom_prompt: Optional[str] = None
    domain: Optional[str] = None
    source: str = "ppt_a"
    selections: Optional[list[SlideSelector]] = None

    provider: str = "deepseek"
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4000


class ComposeRequest(BaseModel):
    """页面组合请求"""
    session_id: str
    selections: list[SlideSelector]


# ---- 响应模型 ----

class UploadResponse(BaseModel):
    """上传响应"""
    session_id: str
    parsed: dict                        # ParsedPresentation 的 dict
    preview_images: list[dict] = []     # [{slide_index, url}]


class ProcessResponse(BaseModel):
    """AI 处理响应"""
    success: bool
    version: Optional[PPTVersion] = None
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None


class ComposeResponse(BaseModel):
    """页面组合响应"""
    success: bool
    version: Optional[PPTVersion] = None
    error: Optional[str] = None


class VersionListResponse(BaseModel):
    """版本列表响应"""
    session_id: str
    versions: list[PPTVersion]
    current_version_id: Optional[str] = None
