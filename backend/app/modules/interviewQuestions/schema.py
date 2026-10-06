from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.integration.langGraph.Schema.commonSchema import DifficultyLevel


class InterviewQuestionCreate(BaseModel):
    interview_id: UUID
    topic_id: UUID
    category: str
    sub_category: str | None = None
    question_number: int
    question: str
    answer: str
    difficulty: DifficultyLevel
    average_score: Decimal | None = None
    strong_concepts: list[str] | None = None
    weak_concepts: list[str] | None = None
    feedback: str | None = None


class InterviewQuestionResponse(InterviewQuestionCreate):
    id: UUID
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class InterviewQuestionDetail(BaseModel):
    id: UUID
    question_number: int
    question: str
    answer: str
    average_score: Decimal | None = None
    difficulty: DifficultyLevel | None = None
    strong_concepts: list[str] | None = None
    weak_concepts: list[str] | None = None
    feedback: str | None = None

    model_config = ConfigDict(from_attributes=True)


class QuestionOut(InterviewQuestionDetail):
    """Question payload embedded in interview-detail topic objects / dashboard briefs."""

    model_config = ConfigDict(from_attributes=True)
