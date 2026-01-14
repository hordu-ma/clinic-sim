"""中间件模块

提供：
- Trace ID 中间件：为每个请求生成唯一标识
- 请求日志中间件：记录请求/响应信息
"""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logging_config import logger, trace_id_var


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Trace ID 中间件

    为每个请求生成唯一的 trace_id，用于：
    - 日志追踪
    - 响应头返回
    - 错误排查
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 生成或从请求头获取 trace_id
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())[:8]

        # 设置到上下文变量
        token = trace_id_var.set(trace_id)

        # 设置到 request.state 供其他地方使用
        request.state.trace_id = trace_id

        try:
            response = await call_next(request)
            # 添加到响应头
            response.headers["X-Trace-ID"] = trace_id
            return response
        finally:
            # 重置上下文变量
            trace_id_var.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件

    记录每个请求的：
    - 方法、路径
    - 响应状态码
    - 处理耗时
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start_time = time.perf_counter()

        # 跳过健康检查等不需要详细日志的路径
        skip_paths = {"/health", "/docs", "/openapi.json", "/redoc"}
        should_log = request.url.path not in skip_paths

        if should_log:
            logger.info(
                "请求开始",
                method=request.method,
                path=request.url.path,
                client=request.client.host if request.client else "-",
            )

        response = await call_next(request)

        if should_log:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_func = logger.info if response.status_code < 400 else logger.warning
            log_func(
                "请求完成",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=f"{duration_ms:.2f}",
            )

        return response


__all__ = ["TraceIdMiddleware", "RequestLoggingMiddleware"]
