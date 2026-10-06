# pyrefly: ignore [unknown-name]
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.interview.InterviewModel import Interview


# pyrefly: ignore [unknown-name]
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        # pyrefly: ignore [unexpected-keyword]
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # func is SQLAlchemy's way of calling database functions.
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    interviews: Mapped[list["Interview"]] = relationship(back_populates="user")

    # topic_stats: Mapped[list["UserTopicStat"]] = relationship(
    #     back_populates="user",
    #     cascade="all, delete-orphan"
    # )


# When a new row is INSERTED, the database automatically sets the current timestamp if no value is provided.
# Whenever SQLAlchemy updates this row, automatically set updated_at to the current time.
