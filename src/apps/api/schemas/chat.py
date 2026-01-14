"""聊天相关 schemas。

定义聊天请求和响应数据模型。
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求。"""

    session_id: int = Field(..., description="会话ID")
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")


class ChatChunk(BaseModel):
    """流式响应块。"""

    content: str = Field(..., description="内容片段")
    done: bool = Field(False, description="是否完成")


class ChatComplete(BaseModel):
    """聊天完成响应（非流式）。"""

    session_id: int = Field(..., description="会话ID")
    user_message: str = Field(..., description="用户消息")
    assistant_message: str = Field(..., description="助手回复")
    tokens: int | None = Field(None, description="回复token数")
    latency_ms: int | None = Field(None, description="响应延迟（毫秒）")
