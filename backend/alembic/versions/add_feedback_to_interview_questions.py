"""add feedback column to interview_questions

Revision ID: 9a1d0e2f3c4b
Revises: 7f8e9d0c1b2a
Create Date: 2026-09-09 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a1d0e2f3c4b"
down_revision: Union[str, Sequence[str], None] = "7f8e9d0c1b2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interview_questions",
        sa.Column("feedback", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_questions", "feedback")
