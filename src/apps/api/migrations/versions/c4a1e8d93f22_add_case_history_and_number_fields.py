"""Add case history and number fields

Revision ID: c4a1e8d93f22
Revises: 2b0c5f6c7d11
Create Date: 2026-02-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4a1e8d93f22"
down_revision: str | Sequence[str] | None = "2b0c5f6c7d11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "cases",
        sa.Column(
            "marriage_childbearing_history",
            sa.Text(),
            nullable=True,
            comment="婚育个人史",
        ),
    )
    op.add_column(
        "cases",
        sa.Column(
            "family_history",
            sa.Text(),
            nullable=True,
            comment="家族史",
        ),
    )
    op.add_column(
        "cases",
        sa.Column(
            "case_number",
            sa.Integer(),
            nullable=True,
            comment="随机病例序号（1-106）",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cases", "case_number")
    op.drop_column("cases", "family_history")
    op.drop_column("cases", "marriage_childbearing_history")
