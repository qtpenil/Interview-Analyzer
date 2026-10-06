# pyrefly: ignore [missing-import]
import uuid

from sqlalchemy import (
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as SQLUUID

from app.core.database import Base


class InterviewTopicStats(Base):
    __tablename__ = "topic_stats"

    id = Column(
        SQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic = Column(String(255), nullable=False, index=True)

    average_score = Column(Numeric(5, 2), nullable=False)

    highest_score = Column(Numeric(5, 2), nullable=False)

    lowest_score = Column(Numeric(5, 2), nullable=False)

    highest_score_interview_topic_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("interview_topics.id"),
        nullable=True,
    )

    lowest_score_interview_topic_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("interview_topics.id"),
        nullable=True,
    )

    highest_scored_question_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("interview_questions.id"),
        nullable=True,
    )

    highest_scored_question_score = Column(Numeric(5, 2), nullable=True)

    lowest_scored_question_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("interview_questions.id"),
        nullable=True,
    )

    lowest_scored_question_score = Column(Numeric(5, 2), nullable=True)

    interview_count = Column(Integer, nullable=False, server_default="0")

    last_assessed_at = Column(TIMESTAMP, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_topic_stats_user_topic"),
    )
