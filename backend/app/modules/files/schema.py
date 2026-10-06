from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class FileType(str, Enum):
    SUMMARY_PDF = "SUMMARY_PDF"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    TRANSCRIPT = "TRANSCRIPT"


class FileCreate(BaseModel):
    interview_id: UUID
    file_type: FileType | None
    storage_provider: str | None
    storage_path: str | None
    file_size: int | None


class FileResponse(FileCreate):
    id: UUID

    class Config:
        from_attributes = True
