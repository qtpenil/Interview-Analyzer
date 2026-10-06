# pyrefly: ignore [missing-import]
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.modules.files.schema import FileType

if TYPE_CHECKING:
    from app.modules.interview.InterviewModel import Interview


class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    interview_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_type = Column(SQLEnum(FileType), nullable=True)

    storage_provider = Column(String(50), nullable=True)

    storage_path = Column(Text, nullable=True)

    file_size = Column(BigInteger, nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="files")
