"""
有声书制作系统 - FastAPI 主应用
"""
import logging
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import books, tts, export
from app.config import get_settings

settings = get_settings()

# 创建应用
app = FastAPI(
    title=f"🎙️ {settings.PROJECT_NAME}",
    description="电子书转有声书，支持 PDF/EPUB/TXT/MD，使用 TTS 语音合成",
    version=settings.VERSION
)

# 挂载导出目录
output_dir = settings.OUTPUT_DIR
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
app.mount("/outputs", StaticFiles(directory=output_dir), name="outputs")

# CORS 中间件 (允许前端访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(books.router)
app.include_router(tts.router)
app.include_router(export.router)


@app.on_event("startup")
def startup():
    """启动时初始化数据库"""
    init_db()
    logger = logging.getLogger(__name__)
    logger.info("%s v%s 已启动", settings.PROJECT_NAME, settings.VERSION)
    logger.info("API 文档: http://localhost:8000/docs")
    logger.info("TTS 引擎: %s", settings.TTS_PROVIDER)


@app.get("/")
def index():
    """API 根路径"""
    return {
        "name": "有声书制作系统 API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

