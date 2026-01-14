"""消息模型。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .sessions import Session


class Message(Base):
    """消息表。

    记录会话中的所有对话消息。
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, comment="消息ID")
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True, comment="会话ID"
    )

    # 消息内容
    role: Mapped[str] = mapped_column(String(20), comment="角色：user/assistant")
    content: Mapped[str] = mapped_column(Text, comment="消息内容")

    # 统计信息
    tokens: Mapped[int | None] = mapped_column(nullable=True, comment="token 数量")
    latency_ms: Mapped[int | None] = mapped_column(nullable=True, comment="响应延迟（毫秒）")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(server_default="now()", comment="创建时间")

    # 关系
    session: Mapped["Session"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, session_id={self.session_id}, role={self.role})>"
