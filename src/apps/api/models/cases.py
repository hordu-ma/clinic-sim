"""病例模型。"""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .sessions import Session


class Case(Base, TimestampMixin):
    """病例表。

    存储教学病例信息，包括病史、体征、检查项、标准答案等。
    """

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True, comment="病例ID")
    title: Mapped[str] = mapped_column(String(200), comment="病例标题")
    difficulty: Mapped[str] = mapped_column(String(20), comment="难度：easy/medium/hard")
    department: Mapped[str] = mapped_column(String(50), comment="科室")

    # 病例数据（JSON 格式存储）
    patient_info: Mapped[dict] = mapped_column(JSON, comment="患者基本信息（年龄、性别、职业等）")
    chief_complaint: Mapped[str] = mapped_column(Text, comment="主诉")
    present_illness: Mapped[str] = mapped_column(Text, comment="现病史")
    past_history: Mapped[dict] = mapped_column(JSON, comment="既往史（疾病、过敏、用药等）")
    physical_exam: Mapped[dict] = mapped_column(
        JSON, comment="体格检查（可见体征和按需提供的体征）"
    )
    available_tests: Mapped[list] = mapped_column(JSON, comment="可申请的检查项及结果")

    # 标准答案（仅教师端可见）
    standard_diagnosis: Mapped[dict] = mapped_column(JSON, comment="标准诊断（主要诊断、鉴别诊断）")
    key_points: Mapped[list] = mapped_column(JSON, comment="关键问诊点列表")
    recommended_tests: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="推荐检查项列表"
    )

    # 病例来源
    source: Mapped[str] = mapped_column(
        String(20),
        default="fixed",
        comment="病例来源：fixed（库内病例）/random（LLM 随机生成）",
    )
    generation_meta: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="随机生成元信息（模型版本、提示词版本、生成时间等）",
    )

    # 是否启用
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")

    # 关系
    sessions: Mapped[list["Session"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Case(id={self.id}, title={self.title}, difficulty={self.difficulty})>"
