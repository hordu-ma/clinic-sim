"""检查申请模型。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .sessions import Session


class TestRequest(Base):
    """检查申请表。

    记录学生在会话中申请的各类检查。
    """

    __tablename__ = "test_requests"

    id: Mapped[int] = mapped_column(primary_key=True, comment="检查申请ID")
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True, comment="会话ID"
    )

    # 检查信息
    test_type: Mapped[str] = mapped_column(
        String(50), comment="检查类型（如：blood_routine、x_ray）"
    )
    test_name: Mapped[str] = mapped_column(String(100), comment="检查名称")
    result: Mapped[dict] = mapped_column(JSON, comment="检查结果（JSON 格式）")

    # 申请时间
    requested_at: Mapped[datetime] = mapped_column(server_default="now()", comment="申请时间")

    # 关系
    session: Mapped["Session"] = relationship(back_populates="test_requests")

    def __repr__(self) -> str:
        return (
            f"<TestRequest(id={self.id}, session_id={self.session_id}, test_type={self.test_type})>"
        )
