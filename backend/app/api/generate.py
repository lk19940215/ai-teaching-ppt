from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ..services.llm import get_llm_service, LLMProvider
from ..services.content_generator import get_content_generator
from ..config import settings

router = APIRouter(prefix=settings.API_V1_STR, tags=["generate"])

logger = logging.getLogger(__name__)

@router.post("/generate/ppt")
async def generate_ppt(
    content: str = Body(..., embed=True),
    grade: str = Body(..., embed=True),
    subject: str = Body(..., embed=True),
    slide_count: int = Body(15, embed=True),
    chapter: Optional[str] = Body(None, embed=True),
    provider: Optional[str] = Body(None, embed=True),
    api_key: Optional[str] = Body(None, embed=True),
    temperature: Optional[float] = Body(None, embed=True),
    max_output_tokens: Optional[int] = Body(None, embed=True)
):
    """
    生成 PPT 内容
    Args:
        content: 教学内容
        grade: 年级（1-9）
        subject: 学科
        slide_count: 幻灯片数量
        chapter: 章节名称（可选）
        provider: LLM 服务商（可选）
        api_key: API Key（可选）
        temperature: 温度参数（可选）
        max_output_tokens: 最大输出 token 数（可选）
    Returns:
        生成的 PPT 内容
    """
    if not content or not content.strip():
        raise HTTPException(status_code=400, detail="教学内容不能为空")

    if grade not in [str(i) for i in range(1, 10)]:
        raise HTTPException(status_code=400, detail="年级必须在 1-9 之间")

    if slide_count < 8 or slide_count > 30:
        raise HTTPException(status_code=400, detail="幻灯片数量必须在 8-30 之间")

    try:
        # 获取或创建 LLM 服务
        llm_provider = provider or settings.DEFAULT_LLM_PROVIDER
        llm_api_key = api_key or settings.OPENAI_API_KEY

        if not llm_api_key:
            raise HTTPException(
                status_code=400,
                detail="请提供 API Key 或在设置中配置默认的 API Key"
            )

        # 使用前端传递的参数，或使用默认值
        llm_temperature = temperature if temperature is not None else 0.7
        llm_max_tokens = max_output_tokens if max_output_tokens is not None else 4000

        # 注意：base_url 和 model 参数不传递，让 LLMService 根据 provider 使用默认值
        llm_service = get_llm_service(
            provider=llm_provider,
            api_key=llm_api_key,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens
        )

        # 获取内容生成器
        generator = get_content_generator(llm_service)

        # 英语学科使用专门的内容生成器
        if subject == "english":
            result = generator.generate_for_english(
                content=content,
                grade=grade,
                slide_count=slide_count,
                chapter=chapter
            )
        else:
            result = generator.generate(
                content=content,
                grade=grade,
                subject=subject,
                slide_count=slide_count,
                chapter=chapter
            )

        return JSONResponse(content={
            "success": True,
            "message": "PPT 内容生成成功",
            "data": result
        })

    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        logger.error(f"生成超时: {e}")
        raise HTTPException(status_code=408, detail="生成超时，请稍后重试")
    except Exception as e:
        logger.error(f"PPT 内容生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"PPT 内容生成失败: {str(e)}")


@router.get("/generate/providers")
async def get_supported_providers():
    """获取支持的 LLM 服务商列表"""
    providers = [
        {"value": LLMProvider.DEEPSEEK, "name": "DeepSeek"},
        {"value": LLMProvider.OPENAI, "name": "OpenAI"},
        {"value": LLMProvider.CLAUDE, "name": "Claude"},
        {"value": LLMProvider.GLM, "name": "智谱 GLM"},
    ]
    return JSONResponse(content={"providers": providers})


@router.post("/generate/test")
async def test_llm_connection(
    provider: str = Body(..., embed=True),
    api_key: str = Body(..., embed=True)
):
    """
    测试 LLM 连接
    Args:
        provider: LLM 服务商
        api_key: API Key
    Returns:
        测试结果
    """
    try:
        llm_service = get_llm_service(provider=provider, api_key=api_key)
        # 发送一个简单的测试请求
        response = llm_service.chat(
            messages=[
                {"role": "user", "content": "请回复'连接成功'"}
            ],
            timeout=10
        )
        return JSONResponse(content={
            "success": True,
            "message": "LLM 连接测试成功",
            "response": response
        })
    except Exception as e:
        logger.error(f"LLM 连接测试失败: {e}")
        return JSONResponse(content={
            "success": False,
            "message": f"LLM 连接测试失败: {str(e)}"
        }, status_code=400)