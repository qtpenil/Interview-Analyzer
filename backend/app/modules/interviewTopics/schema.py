from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.interviewQuestions.schema import QuestionOut


class ConceptOut(BaseModel):
    concept: str
    question_ids: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class InterviewTopicCreate(BaseModel):
    interview_id: UUID
    topic: str
    average_score: float | None
    confidence_score: float | None

    strongest_concepts: list[str] | None = None
    weakest_concepts: list[str] | None = None


class InterviewTopicResponse(InterviewTopicCreate):
    id: UUID

    class Config:
        from_attributes = True


class InterviewTopicDetail(BaseModel):
    topic: str
    average_score: Decimal | None = None
    confidence_score: Decimal | None = None
    feedback: str | None = None
    strongest_concepts: list[ConceptOut] | None = None
    weakest_concepts: list[ConceptOut] | None = None
    questions: list[QuestionOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("strongest_concepts", "weakest_concepts", mode="before")
    @classmethod
    def _normalize_concepts(cls, value):
        """Normalize concept entries to the ConceptOut dict shape.

        Handles both the new list-of-dicts shape and the legacy flat
        list-of-strings shape (wrapped with empty question_ids).
        """
        if value is None:
            return None
        normalized: list[dict[str, object]] = []
        for entry in value:
            if isinstance(entry, dict):
                normalized.append(
                    {
                        "concept": entry.get("concept", ""),
                        "question_ids": entry.get("question_ids", []),
                    }
                )
            else:
                normalized.append({"concept": str(entry), "question_ids": []})
        return normalized
