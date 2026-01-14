"""Pydantic schemas for API request/response validation."""

from src.apps.api.schemas.auth import LoginCredentials, Token, UserResponse
from src.apps.api.schemas.cases import CaseDetail, CaseDetailFull, CaseListItem
from src.apps.api.schemas.chat import ChatChunk, ChatComplete, ChatRequest
from src.apps.api.schemas.sessions import (
    MessageItem,
    SessionCreate,
    SessionDetail,
    SessionListItem,
    SessionListResponse,
    SessionResponse,
)
from src.apps.api.schemas.tests import (
    AvailableTestItem,
    AvailableTestsResponse,
    TestRequestCreate,
    TestRequestListItem,
    TestRequestListResponse,
    TestRequestResponse,
)

__all__ = [
    "LoginCredentials",
    "Token",
    "UserResponse",
    "CaseListItem",
    "CaseDetail",
    "CaseDetailFull",
    "SessionCreate",
    "SessionResponse",
    "SessionListItem",
    "SessionListResponse",
    "SessionDetail",
    "MessageItem",
    "ChatRequest",
    "ChatChunk",
    "ChatComplete",
    "TestRequestCreate",
    "TestRequestResponse",
    "TestRequestListItem",
    "TestRequestListResponse",
    "AvailableTestItem",
    "AvailableTestsResponse",
]
