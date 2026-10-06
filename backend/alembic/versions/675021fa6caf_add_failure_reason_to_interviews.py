"""add failure_reason to interviews

Revision ID: 675021fa6caf
Revises: ec7d288edf8a
Create Date: 2026-07-30 12:04:17.913648

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "675021fa6caf"
down_revision: Union[str, Sequence[str], None] = "ec7d288edf8a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("interviews", sa.Column("failure_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("interviews", "failure_reason")
