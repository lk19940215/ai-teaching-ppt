from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pathlib import Path
from .config import settings
from .api import upload, process, generate, ppt

app = FastAPI(
    title="AI 教学 PPT 生成器 API",
    description="教师上传教材内容，AI 自动生成教学 PPT 的后端服务",
    version="1.0.0",
)

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

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/templates", StaticFiles(directory=settings.TEMPLATE_DIR), name="templates")

@app.get("/")
async def root():
    return {"message": "AI 教学 PPT 生成器后端服务运行中"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)