# pyrefly: ignore [unknown-name]
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class HiringDecision(str, Enum):
    STRONG_HIRE = "STRONG_HIRE"
    HIRE = "HIRE"
    BORDERLINE = "BORDERLINE"
    NO_HIRE = "NO_HIRE"


class InterviewStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    TRANSCRIBING = "TRANSCRIBING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# pyrefly: ignore [unknown-name]
class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    claimed_experience_years: Mapped[Decimal | None] = mapped_column(Numeric(4, 1), nullable=True)

    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    technical_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    communication_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    knowledge_depth: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    experience_alignment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    hiring_decision: Mapped[HiringDecision | None] = mapped_column(SQLEnum(HiringDecision), nullable=True)

    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus),
        nullable=False,
        default=InterviewStatus.UPLOADED,
        index=True,
    )

    ai_model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    ai_model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    transcript: Mapped[list[dict] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    audio_fingerprint: Mapped[str | None] = mapped_column(Text, nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="interviews")

    topics: Mapped[list["InterviewTopic"]] = relationship(back_populates="interview", cascade="all, delete-orphan")

    files: Mapped[list["File"]] = relationship(back_populates="interview", cascade="all, delete-orphan")

    # ai_result: Mapped["InterviewAIResult | None"] = relationship(
    #     back_populates="interview", cascade="all, delete-orphan", uselist=False
    # )


# ---------------------------------------------------------------------------
# Import related models at the END of this file so that wherever InterviewModel
# is imported (FastAPI, Celery workers, standalone scripts), the File and
# InterviewTopic classes are already registered in SQLAlchemy's mapper registry
# before the Interview mapper tries to resolve the string references
# "InterviewTopic" and "File" in its relationships.
#
# No circular import: File and InterviewTopic use "Interview" as a string
# reference in their own relationship(), so they do not import this module.
# ---------------------------------------------------------------------------
from app.modules.files.file import File
from app.modules.interviewTopics.interviewTopics import InterviewTopic
from app.modules.user.UserModel import User
