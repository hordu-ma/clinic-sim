"""异常处理模块

提供：
- 自定义业务异常
- 全局异常处理器
- 统一错误响应格式
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .logging_config import logger


class ErrorResponse(BaseModel):
    """统一错误响应格式"""

    detail: str
    trace_id: str
    error_code: str | None = None


class BusinessError(Exception):
    """业务异常基类"""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


def setup_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
        """处理业务异常"""
        trace_id = getattr(request.state, "trace_id", "-")
        logger.warning(
            "业务异常",
            error=exc.message,
            error_code=exc.error_code,
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=exc.message,
                trace_id=trace_id,
                error_code=exc.error_code,
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """处理 HTTP 异常"""
        trace_id = getattr(request.state, "trace_id", "-")
        logger.warning(
            "HTTP 异常",
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=str(exc.detail),
                trace_id=trace_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """处理未捕获的异常"""
        trace_id = getattr(request.state, "trace_id", "-")
        logger.exception(
            "未处理异常",
            error=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                detail="服务器内部错误，请稍后重试",
                trace_id=trace_id,
                error_code="INTERNAL_ERROR",
            ).model_dump(),
        )


__all__ = ["BusinessError", "ErrorResponse", "setup_exception_handlers"]
