# pyrefly: ignore [missing-import]
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.interview.InterviewModel import Interview


class InterviewTopic(Base):
    __tablename__ = "interview_topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)

    topic = Column(String(255), nullable=False)

    average_score = Column(Numeric(5, 2), nullable=True)

    confidence_score = Column(Numeric(5, 2), nullable=True)

    strongest_concepts = Column(JSONB, nullable=True)

    weakest_concepts = Column(JSONB, nullable=True)

    feedback = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="topics")

    __table_args__ = (UniqueConstraint("interview_id", "topic", name="uq_interview_topic"),)
