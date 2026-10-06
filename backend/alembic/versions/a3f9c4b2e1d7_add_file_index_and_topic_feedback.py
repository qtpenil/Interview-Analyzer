"""add index on files.interview_id and feedback on interview_topics

Revision ID: a3f9c4b2e1d7
Revises: 675021fa6caf
Create Date: 2026-08-07 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f9c4b2e1d7"
down_revision: Union[str, Sequence[str], None] = "675021fa6caf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_files_interview_id", "files", ["interview_id"])
    op.add_column("interview_topics", sa.Column("feedback", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("interview_topics", "feedback")
    op.drop_index("ix_files_interview_id", table_name="files")
