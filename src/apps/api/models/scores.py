"""评分模型。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .sessions import Session


class Score(Base):
    """评分表。

    记录会话的评分结果。
    """

    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True, comment="评分ID")
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        comment="会话ID（唯一）",
    )

    # 评分结果
    total_score: Mapped[float] = mapped_column(Numeric(5, 2), comment="总分（0-100）")
    dimensions: Mapped[dict] = mapped_column(
        JSON, comment="各维度得分（问诊完整性、检查合理性、诊断准确性等）"
    )

    # 评分依据（可审计）
    scoring_details: Mapped[dict] = mapped_column(
        JSON, comment="评分详情（关键词覆盖、推荐检查匹配等）"
    )

    # 评分方式
    scoring_method: Mapped[str] = mapped_column(
        default="rule_based", comment="评分方式：rule_based/llm_based"
    )
    model_version: Mapped[str | None] = mapped_column(
        nullable=True, comment="使用的模型版本（如适用）"
    )

    # 评分时间
    scored_at: Mapped[datetime] = mapped_column(server_default="now()", comment="评分时间")

    # 关系
    session: Mapped["Session"] = relationship(back_populates="score")

    def __repr__(self) -> str:
        return (
            f"<Score(id={self.id}, session_id={self.session_id}, total_score={self.total_score})>"
        )
