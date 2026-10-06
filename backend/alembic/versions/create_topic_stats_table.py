"""create topic_stats table

Revision ID: 7f8e9d0c1b2a
Revises: 1b2c3d4e5f6a
Create Date: 2026-09-08 15:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f8e9d0c1b2a"
down_revision: Union[str, Sequence[str], None] = "1b2c3d4e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "topic_stats",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "average_score",
            sa.Numeric(5, 2),
            nullable=False,
        ),
        sa.Column(
            "highest_score",
            sa.Numeric(5, 2),
            nullable=False,
        ),
        sa.Column(
            "lowest_score",
            sa.Numeric(5, 2),
            nullable=False,
        ),
        sa.Column(
            "highest_score_interview_topic_id",
            sa.UUID(),
            sa.ForeignKey("interview_topics.id"),
            nullable=True,
        ),
        sa.Column(
            "lowest_score_interview_topic_id",
            sa.UUID(),
            sa.ForeignKey("interview_topics.id"),
            nullable=True,
        ),
        sa.Column(
            "highest_scored_question_id",
            sa.UUID(),
            sa.ForeignKey("interview_questions.id"),
            nullable=True,
        ),
        sa.Column(
            "highest_scored_question_score",
            sa.Numeric(5, 2),
            nullable=True,
        ),
        sa.Column(
            "lowest_scored_question_id",
            sa.UUID(),
            sa.ForeignKey("interview_questions.id"),
            nullable=True,
        ),
        sa.Column(
            "lowest_scored_question_score",
            sa.Numeric(5, 2),
            nullable=True,
        ),
        sa.Column(
            "interview_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "last_assessed_at",
            sa.TIMESTAMP(),
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
        sa.UniqueConstraint("user_id", "topic", name="uq_topic_stats_user_topic"),
    )


def downgrade() -> None:
    op.drop_table("topic_stats")
