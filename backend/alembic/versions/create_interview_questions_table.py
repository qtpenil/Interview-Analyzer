"""create interview_questions table

Revision ID: 1b2c3d4e5f6a
Revises: a3f9c4b2e1d7
Create Date: 2026-09-08 15:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b2c3d4e5f6a"
down_revision: Union[str, Sequence[str], None] = "a3f9c4b2e1d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_questions",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "interview_id",
            sa.UUID(),
            sa.ForeignKey("interviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            sa.UUID(),
            sa.ForeignKey("interview_topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(255), nullable=False),
        sa.Column("sub_category", sa.String(255), nullable=True),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum(
                "easy",
                "medium",
                "hard",
                "expert",
                name="difficultylevel",
                native_enum=False,
                create_enum=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "average_score",
            sa.Numeric(5, 2),
            nullable=False,
        ),
        sa.Column(
            "strong_concepts",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "weak_concepts",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "interview_id", "question_number", name="uq_interview_question_number"
        ),
    )
    op.create_index(
        "ix_interview_questions_user_category_score",
        "interview_questions",
        ["user_id", "category", "average_score"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interview_questions_user_category_score",
        table_name="interview_questions",
    )
    op.drop_table("interview_questions")
