# pyrefly: ignore [missing-import]
import uuid

from sqlalchemy import TIMESTAMP, Column, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as SQLUUID

from app.core.database import Base
from app.integration.langGraph.Schema.commonSchema import DifficultyLevel


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(
        SQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    interview_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("interview_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    category = Column(String(255), nullable=False, index=True)

    sub_category = Column(String(255), nullable=True)

    question_number = Column(Integer, nullable=False)

    question = Column(Text, nullable=False)

    answer = Column(Text, nullable=False)

    difficulty = Column(
        Enum(DifficultyLevel, native_enum=False, create_enum=True),
        nullable=False,
    )

    average_score = Column(Numeric(5, 2), nullable=False)

    strong_concepts = Column(JSONB, nullable=True)

    weak_concepts = Column(JSONB, nullable=True)

    feedback = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("interview_id", "question_number", name="uq_interview_question_number"),
    )
