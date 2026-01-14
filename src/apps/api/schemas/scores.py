"""评分相关 schemas。

定义评分的请求和响应数据模型。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DiagnosisSubmit(BaseModel):
    """提交诊断请求。"""

    diagnosis: str = Field(..., min_length=2, max_length=1000, description="诊断结论")


class ScoreDimensions(BaseModel):
    """评分各维度得分。"""

    interview_completeness: float = Field(..., ge=0, le=100, description="问诊完整性得分（0-100）")
    test_appropriateness: float = Field(..., ge=0, le=100, description="检查合理性得分（0-100）")
    diagnosis_accuracy: float = Field(..., ge=0, le=100, description="诊断准确性得分（0-100）")


class ScoringDetails(BaseModel):
    """评分详情（可审计）。"""

    keywords_asked: list[str] = Field(default_factory=list, description="从对话中提取的关键词")
    key_points_covered: list[str] = Field(default_factory=list, description="覆盖的关键问诊点")
    key_points_total: list[str] = Field(default_factory=list, description="全部关键问诊点")
    tests_requested: list[str] = Field(default_factory=list, description="申请的检查项")
    recommended_tests: list[str] = Field(default_factory=list, description="推荐的检查项")
    diagnosis_keywords_matched: list[str] = Field(
        default_factory=list, description="诊断中匹配的关键词"
    )
    standard_diagnosis: str = Field("", description="标准诊断")
    submitted_diagnosis: str = Field("", description="提交的诊断")
    scoring_rule_version: str = Field("1.0", description="评分规则版本")


class ScoreResponse(BaseModel):
    """评分响应。"""

    id: int = Field(..., description="评分ID")
    session_id: int = Field(..., description="会话ID")
    total_score: float = Field(..., ge=0, le=100, description="总分（0-100）")
    dimensions: ScoreDimensions = Field(..., description="各维度得分")
    scoring_details: ScoringDetails = Field(..., description="评分详情")
    scoring_method: str = Field(..., description="评分方式")
    model_version: str | None = Field(None, description="模型版本（如适用）")
    scored_at: datetime = Field(..., description="评分时间")

    model_config = {"from_attributes": True}


class DiagnosisSubmitResponse(BaseModel):
    """提交诊断响应。"""

    session_id: int = Field(..., description="会话ID")
    status: str = Field(..., description="会话状态")
    submitted_diagnosis: str = Field(..., description="提交的诊断")
    score: ScoreResponse = Field(..., description="评分结果")
