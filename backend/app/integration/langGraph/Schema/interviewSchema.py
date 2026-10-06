from pydantic import BaseModel, Field

from .commonSchema import SpeakerRole


class CandidateMetadata(BaseModel):
    candidate_name: str | None = Field(default=None, description="Candidate's name if explicitly stated.")

    claimed_experience_years: float | None = Field(
        default=None, description="Years of professional experience claimed by the candidate."
    )

    current_role: str | None = Field(default=None, description="Current role/title if mentioned.")

    target_role: str | None = Field(default=None, description="Role being interviewed for if inferable.")

    self_introduction_summary: str = Field(
        default="",
        description=("Concise 2-3 sentence summary of the candidate's background based on the introduction."),
    )


class RawSegment(BaseModel):
    start: float
    end: float
    text: str


class QuestionAnswer(BaseModel):
    question_id: str
    question: str
    answer: str


class MetadataAndQA(BaseModel):
    candidate_name: str | None = None
    claimed_experience_years: float | None = None
    current_role: str | None = None
    target_role: str | None = None
    self_introduction_summary: str | None = None
    question_answers: list[QuestionAnswer]


class ProcessedSegment(BaseModel):
    start_time: float
    end_time: float
    text: str


class ConversationBlock(BaseModel):
    """
    Cleaned interview conversation block.
    """

    speaker_role: SpeakerRole = Field(...)
    speaker_label: str = Field(...)
    text: str = Field(...)

    start_time: float | None = None
    end_time: float | None = None


class ConversationBlockList(BaseModel):
    blocks: list[ConversationBlock]
