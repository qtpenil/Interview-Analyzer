from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class QuestionBrief(BaseModel):
    id: UUID | None = None
    question: str | None = None
    average_score: Decimal | None = None
    feedback: str | None = None


class TopicStatsResponse(BaseModel):
    topic: str
    average_score: Decimal | None = None
    highest_score: Decimal | None = None
    lowest_score: Decimal | None = None
    interview_count: int | None = None
    last_assessed_at: str | None = None
    best_feedback: str | None = None
    highest_scored_question: QuestionBrief | None = None
    lowest_scored_question: QuestionBrief | None = None


class DashboardOverviewResponse(BaseModel):
    topics: list[TopicStatsResponse] = Field(default_factory=list)
    strongest_topic: dict | None = None
    weakest_topic: dict | None = None
    best_interview: dict | None = None

    model_config = ConfigDict(from_attributes=True)
