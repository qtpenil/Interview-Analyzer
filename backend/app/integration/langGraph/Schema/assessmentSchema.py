from pydantic import BaseModel, Field

from .commonSchema import DifficultyLevel, HiringDecision


class QuestionEvaluation(BaseModel):
    """
    Combined extraction + assessment for a single interview question.
    Produced directly by qa_assessment_extractor — no intermediate QA pair needed.
    """

    question_id: str

    question: str

    answer: str
    expected_answer: str

    category: str
    sub_category: str

    difficulty: DifficultyLevel

    expected_experience: float

    accuracy_score: float = Field(..., ge=0, le=10)
    depth_score: float = Field(..., ge=0, le=10)
    completeness_score: float = Field(..., ge=0, le=10)
    clarity_score: float = Field(..., ge=0, le=10)
    confidence_score: float = Field(..., ge=0, le=10)
    experience_alignment_score: float = Field(..., ge=0, le=10)

    strong_concepts: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    feedback: str


class QuestionEvaluationList(BaseModel):
    """
    Wrapper returned by the qa_assessment_extractor node.
    """

    evaluations: list[QuestionEvaluation]


class TopicSummary(BaseModel):
    """
    Topic-level aggregation.  All numeric fields are computed deterministically
    in topic_aggregation — the LLM never touches these values.
    """

    topic: str

    total_questions: int

    average_score: float = Field(..., ge=0, le=10)

    strongest_concepts: list[str] = Field(default_factory=list)
    weakest_concepts: list[str] = Field(default_factory=list)

    confidence_score: float = Field(..., ge=0, le=10)

    feedback: str


class InterviewSummary(BaseModel):
    """
    Final interview assessment.
    """

    candidate_name: str | None = None

    claimed_experience_years: float | None = None

    overall_score: float = Field(..., ge=0, le=10)

    technical_score: float = Field(..., ge=0, le=10)

    communication_score: float = Field(..., ge=0, le=10)

    confidence_score: float = Field(..., ge=0, le=10)

    knowledge_depth: float = Field(..., ge=0, le=10)

    experience_alignment_score: float = Field(..., ge=0, le=10)

    skills_assessed: list[str] = Field(default_factory=list)

    strongest_topics: list[str] = Field(default_factory=list)
    weakest_topics: list[str] = Field(default_factory=list)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    risk_factors: list[str] = Field(default_factory=list)

    hiring_decision: HiringDecision

    final_feedback: str
