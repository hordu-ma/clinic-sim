"""会话相关 schemas。

定义会话的请求和响应数据模型。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """创建会话请求。"""

    case_id: int = Field(..., description="病例ID")


class SessionResponse(BaseModel):
    """创建会话响应。"""

    id: int = Field(..., description="会话ID")
    case_id: int = Field(..., description="病例ID")
    status: str = Field(..., description="会话状态")
    started_at: datetime = Field(..., description="开始时间")

    model_config = {"from_attributes": True}


class SessionListItem(BaseModel):
    """会话列表项（用于历史列表）。"""

    id: int = Field(..., description="会话ID")
    case_id: int = Field(..., description="病例ID")
    case_title: str = Field(..., description="病例标题")
    case_difficulty: str = Field(..., description="病例难度")
    status: str = Field(..., description="会话状态")
    started_at: datetime = Field(..., description="开始时间")
    ended_at: datetime | None = Field(None, description="结束时间")
    message_count: int = Field(0, description="消息数量")


class MessageItem(BaseModel):
    """消息项。"""

    id: int = Field(..., description="消息ID")
    role: Literal["user", "assistant"] = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    tokens: int | None = Field(None, description="token数量")
    latency_ms: int | None = Field(None, description="响应延迟（毫秒）")
    created_at: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


class SessionDetail(BaseModel):
    """会话详情（包含消息历史）。"""

    id: int = Field(..., description="会话ID")
    case_id: int = Field(..., description="病例ID")
    case_title: str = Field(..., description="病例标题")
    case_difficulty: str = Field(..., description="病例难度")
    status: str = Field(..., description="会话状态")
    submitted_diagnosis: str | None = Field(None, description="提交的诊断")
    started_at: datetime = Field(..., description="开始时间")
    ended_at: datetime | None = Field(None, description="结束时间")
    messages: list[MessageItem] = Field(default_factory=list, description="消息历史")


class SessionListResponse(BaseModel):
    """会话列表响应（分页）。"""

    items: list[SessionListItem] = Field(..., description="会话列表")
    total: int = Field(..., description="总数")
    skip: int = Field(..., description="跳过数量")
    limit: int = Field(..., description="每页数量")
