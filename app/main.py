import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.models import init_db
from app.api.history import router as history_router
from app.api.file_upload import router as file_upload_router
from app.api.resume import router as resume_router
from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.api.office import router as office_router
from app.api.redis_test import router as redis_router

# 确保上传目录存在
os.makedirs(settings.upload_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时初始化数据库"""
    init_db()
    print("[OK] Database initialized")
    yield
    print("[BYE] Shutting down")


app = FastAPI(
    title="AI智能助手 API",
    description="基于 RAG + Agent 的智能个人助理系统",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS：允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由模块
# 核心功能
app.include_router(agent_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

# 业务功能
app.include_router(resume_router, prefix="/api")
app.include_router(office_router, prefix="/api")
app.include_router(file_upload_router, prefix="/api")

# 系统功能
app.include_router(history_router, prefix="/api")
app.include_router(redis_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
