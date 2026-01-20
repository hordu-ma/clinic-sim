"""Add case source fields

Revision ID: 2b0c5f6c7d11
Revises: a33b8a66fd24
Create Date: 2026-01-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2b0c5f6c7d11"
down_revision: str | Sequence[str] | None = "a33b8a66fd24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cases",
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
            server_default="fixed",
            comment="病例来源：fixed（库内病例）/random（LLM 随机生成）",
        ),
    )
    op.add_column(
        "cases",
        sa.Column(
            "generation_meta",
            sa.JSON(),
            nullable=True,
            comment="随机生成元信息（模型版本、提示词版本、生成时间等）",
        ),
    )
    # drop default to keep semantics at application level
    op.alter_column("cases", "source", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cases", "generation_meta")
    op.drop_column("cases", "source")
