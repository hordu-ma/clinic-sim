"""检查申请相关 schemas。

定义检查申请的请求和响应数据模型。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TestRequestCreate(BaseModel):
    """申请检查请求。"""

    test_type: str = Field(..., description="检查类型（如：blood_routine、x_ray）")


class TestRequestResponse(BaseModel):
    """检查申请响应。"""

    id: int = Field(..., description="检查申请ID")
    session_id: int = Field(..., description="会话ID")
    test_type: str = Field(..., description="检查类型")
    test_name: str = Field(..., description="检查名称")
    result: dict[str, Any] = Field(..., description="检查结果")
    requested_at: datetime = Field(..., description="申请时间")

    model_config = {"from_attributes": True}


class TestRequestListItem(BaseModel):
    """已申请检查列表项。"""

    id: int = Field(..., description="检查申请ID")
    test_type: str = Field(..., description="检查类型")
    test_name: str = Field(..., description="检查名称")
    result: dict[str, Any] = Field(..., description="检查结果")
    requested_at: datetime = Field(..., description="申请时间")

    model_config = {"from_attributes": True}


class TestRequestListResponse(BaseModel):
    """已申请检查列表响应。"""

    items: list[TestRequestListItem] = Field(..., description="已申请检查列表")
    total: int = Field(..., description="总数")


class AvailableTestItem(BaseModel):
    """可用检查项（不含结果）。"""

    test_type: str = Field(..., alias="type", description="检查类型")
    test_name: str = Field(..., alias="name", description="检查名称")

    model_config = {"populate_by_name": True}


class AvailableTestsResponse(BaseModel):
    """可用检查列表响应。"""

    case_id: int = Field(..., description="病例ID")
    items: list[AvailableTestItem] = Field(..., description="可用检查列表")
    total: int = Field(..., description="总数")
