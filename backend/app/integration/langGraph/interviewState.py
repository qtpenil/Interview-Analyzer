from datetime import datetime
from typing import TypedDict

from .Schema.assessmentSchema import (
    InterviewSummary,
    QuestionEvaluation,
    TopicSummary,
)
from .Schema.commonSchema import PipelineMetadata, ProcessingStatus
from .Schema.interviewSchema import ConversationBlock, QuestionAnswer


class InterviewGraphState(TypedDict, total=False):
    pipeline_metadata: PipelineMetadata

    """
    Global graph state.

    Node mapping (refactored pipeline):

      Node 0 — metadata_extractor       → candidate_name, claimed_experience_years
      Node 1 — transcript_processor     → conversation_blocks
      Node 2 — qa_assessment_extractor  → question_evaluations
      Node 3 — topic_aggregation        → topic_summaries
      Node 4 — interview_summary        → interview_summary
    """

    # =====================================================
    # INPUTS
    # =====================================================

    interview_id: str

    raw_transcript: str

    # =====================================================
    # NODE 0 — TRANSCRIPT PROCESSING
    # =====================================================

    conversation_blocks: list[ConversationBlock]

    metadata_extraction_status: ProcessingStatus

    # =====================================================
    # NODE 1 — METADATA AND Q/A EXTRACTION
    # =====================================================

    candidate_name: str | None

    claimed_experience_years: float | None

    question_answers: list[QuestionAnswer]

    transcript_processing_status: ProcessingStatus

    # =====================================================
    # NODE 2 — QA ASSESSMENT EXTRACTOR
    # Replaces the former qa_extractor (Node 2) and
    # question_assessment (Node 3) nodes.
    # qa_pairs and qa_extraction_status are removed —
    # QuestionEvaluation objects are produced directly.
    # =====================================================

    question_evaluations: list[QuestionEvaluation]

    assessment_status: ProcessingStatus

    # =====================================================
    # NODE 3 — TOPIC AGGREGATION
    # =====================================================

    topic_summaries: list[TopicSummary]

    topic_aggregation_status: ProcessingStatus

    # =====================================================
    # NODE 4 — INTERVIEW SUMMARY
    # =====================================================

    interview_summary: InterviewSummary

    final_summary_status: ProcessingStatus

    # =====================================================
    # EXECUTION METADATA
    # =====================================================

    current_node: str

    started_at: datetime

    completed_at: datetime | None

    # =====================================================
    # ERROR HANDLING
    # =====================================================

    errors: list[str]

    warnings: list[str]
