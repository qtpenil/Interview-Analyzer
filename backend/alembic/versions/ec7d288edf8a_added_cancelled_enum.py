"""Added Cancelled Enum

Revision ID: ec7d288edf8a
Revises: dd2d833f143e
Create Date: 2026-07-21 12:47:40.573882
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ec7d288edf8a"
down_revision: str | Sequence[str] | None = "dd2d833f143e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE interviewstatus ADD VALUE IF NOT EXISTS 'CANCELLED';")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values.
    # Intentionally left as a no-op.
    pass
