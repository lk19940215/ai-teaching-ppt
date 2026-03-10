from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
import logging
import mimetypes
import sys
import os

# 添加项目根目录到 Python 路径（支持 python main.py 启动）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志（确保所有模块的日志都能输出）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from app.config import settings
from app.api import upload, process, generate, ppt, history, config as config_router

logger = logging.getLogger(__name__)

# 配置 PPTX MIME 类型
mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx', strict=True)

app = FastAPI(
    title="AI 教学 PPT 生成器 API",
    description="教师上传教材内容，AI 自动生成教学 PPT 的后端服务",
    version="1.0.0",
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"收到请求：{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"响应：{request.method} {request.url.path} - {response.status_code}")
    return response

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(upload.router)
app.include_router(process.router)
app.include_router(generate.router)
app.include_router(ppt.router)
app.include_router(history.router)
app.include_router(config_router.router)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/templates", StaticFiles(directory=settings.TEMPLATE_DIR), name="templates")
app.mount("/public", StaticFiles(directory=settings.PUBLIC_DIR), name="public")

@app.get("/")
async def root():
    return {"message": "AI 教学 PPT 生成器后端服务运行中"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # 支持 python main.py 启动
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)