"""病例相关的 Pydantic schemas。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CaseListItem(BaseModel):
    """病例列表项（不含敏感信息）。"""

    id: int = Field(..., description="病例ID")
    title: str = Field(..., description="病例标题")
    difficulty: str = Field(..., description="难度：easy/medium/hard")
    department: str = Field(..., description="科室")
    is_active: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        """Pydantic 配置。"""

        from_attributes = True


class CaseDetail(BaseModel):
    """病例详情（学生端，不含标准答案和关键点）。"""

    id: int = Field(..., description="病例ID")
    title: str = Field(..., description="病例标题")
    difficulty: str = Field(..., description="难度")
    department: str = Field(..., description="科室")
    patient_info: dict[str, Any] = Field(..., description="患者基本信息")
    chief_complaint: str = Field(..., description="主诉")
    present_illness: str = Field(..., description="现病史")
    past_history: dict[str, Any] = Field(..., description="既往史")
    physical_exam: dict[str, Any] = Field(..., description="体格检查")
    available_tests: list[dict[str, Any]] = Field(..., description="可申请的检查项")

    class Config:
        """Pydantic 配置。"""

        from_attributes = True


class CaseDetailFull(CaseDetail):
    """病例完整详情（教师端，含标准答案）。"""

    standard_diagnosis: dict[str, Any] = Field(..., description="标准诊断")
    key_points: list[str] = Field(..., description="关键问诊点")
    recommended_tests: list[str] | None = Field(None, description="推荐检查项")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
