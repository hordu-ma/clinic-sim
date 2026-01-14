"""数据库基类和公共字段定义。"""

from datetime import datetime
from typing import Any

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 命名约定，用于自动生成约束名称
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """数据库模型基类。"""

    metadata = metadata

    # 类型注解，供子类使用
    __tablename__: str


class TimestampMixin:
    """时间戳混入类，提供创建和更新时间字段。"""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )


def to_dict(obj: Any) -> dict[str, Any]:
    """将 SQLAlchemy 模型对象转换为字典。

    Args:
        obj: SQLAlchemy 模型实例

    Returns:
        字典表示
    """
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
