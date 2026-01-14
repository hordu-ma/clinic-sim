"""限流配置模块

使用 slowapi 实现请求限流，防止滥用。
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from .logging_config import logger


def get_user_identifier(request: Request) -> str:
    """获取用户标识用于限流

    优先使用用户 ID（已认证），否则使用 IP 地址
    """
    # 尝试从 request.state 获取用户 ID（由认证中间件设置）
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)


# 创建限流器实例
limiter = Limiter(key_func=get_user_identifier)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """限流超限处理器"""
    trace_id = getattr(request.state, "trace_id", "-")
    logger.warning(
        "请求限流",
        path=request.url.path,
        limit=str(exc.detail),
        identifier=get_user_identifier(request),
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "请求过于频繁，请稍后重试",
            "trace_id": trace_id,
            "error_code": "RATE_LIMITED",
            "retry_after": exc.detail.split()[-1] if exc.detail else "60",
        },
    )


__all__ = ["limiter", "rate_limit_exceeded_handler"]
