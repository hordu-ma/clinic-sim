"""FastAPI 应用入口。

提供核心 API 路由和中间件配置。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

# 创建 FastAPI 应用
app = FastAPI(
    title="Clinic Simulation API",
    version="0.1.0",
    description="临床医学模拟问诊系统 API",
    docs_url="/docs" if settings.ENV == "dev" else None,  # 生产环境禁用文档
    redoc_url="/redoc" if settings.ENV == "dev" else None,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """健康检查端点。

    Returns:
        包含状态信息的字典
    """
    return {"status": "ok", "env": settings.ENV}


# 根路径
@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """API 根路径。

    Returns:
        欢迎信息
    """
    return {
        "message": "Clinic Simulation API",
        "version": "0.1.0",
        "docs": "/docs" if settings.ENV == "dev" else "disabled",
    }


# 注册路由
from .routes import auth, cases, chat, sessions  # noqa: E402

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(cases.router, prefix="/api/cases", tags=["cases"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# TODO: 其他路由待实现
# from .routes import sessions, chat
# app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
# app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
