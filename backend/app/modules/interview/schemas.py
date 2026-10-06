from __future__ import annotations  # if present, keep it

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.interviewTopics.schema import InterviewTopicDetail


class InterviewListItem(BaseModel):
    id: UUID
    title: str | None
    status: str
    hiring_decision: str | None
    overall_score: Decimal | None
    claimed_experience_years: Decimal | None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InterviewListItem]


class InterviewCancelResponse(BaseModel):
    """Response schema for interview cancel endpoint."""

    interview_id: str
    status: str
    message: str


class InterviewUploadResponse(BaseModel):
    """Response schema for interview upload endpoint."""

    interview_id: str
    status: str


class InterviewStatusResponse(BaseModel):
    """Response schema for interview status endpoint."""

    interview_id: str
    status: str
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None
    claimed_experience_years: float | None = None
    overall_score: float | None = None
    technical_score: float | None = None
    communication_score: float | None = None
    confidence_score: float | None = None
    knowledge_depth: float | None = None
    experience_alignment_score: float | None = None
    hiring_decision: str | None = None
    ai_model_name: str | None = None
    ai_model_version: str | None = None
    # transcript: str | None = None
    audio_fingerprint: str | None = None
    failure_reason: str | None = None


class InterviewDetailResponse(BaseModel):
    id: UUID
    title: str | None
    status: str
    hiring_decision: str | None
    claimed_experience_years: Decimal | None
    overall_score: Decimal | None
    technical_score: Decimal | None
    communication_score: Decimal | None
    confidence_score: Decimal | None
    knowledge_depth: Decimal | None
    experience_alignment_score: Decimal | None
    # transcript: str | None = None
    audio_fingerprint: str | None = None
    created_at: datetime
    topics: list[InterviewTopicDetail]

    model_config = ConfigDict(from_attributes=True)


InterviewDetailResponse.model_rebuild()
InterviewStatusResponse.model_rebuild()
InterviewListItem.model_rebuild()
InterviewListResponse.model_rebuild()
