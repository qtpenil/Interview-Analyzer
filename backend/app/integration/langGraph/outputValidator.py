from typing import Any

from pydantic import BaseModel

from app.integration.langGraph.Schema.assessmentSchema import (
    InterviewSummary,
    QuestionEvaluation,
    TopicSummary,
)
from app.integration.langGraph.Schema.commonSchema import (
    DifficultyLevel,
    HiringDecision,
    SpeakerRole,
)
from app.integration.langGraph.Schema.interviewSchema import ConversationBlock, MetadataAndQA


class ValidationResult(BaseModel):
    is_valid: bool
    error_message: str | None = None


def validate_conversation_blocks(blocks: Any) -> ValidationResult:
    """Validate ConversationBlockList output from transcript_structuring node."""
    if not isinstance(blocks, list):
        return ValidationResult(is_valid=False, error_message="Expected blocks to be a list")

    if len(blocks) == 0:
        return ValidationResult(is_valid=False, error_message="Blocks list is empty")

    for idx, block in enumerate(blocks):
        if not isinstance(block, ConversationBlock):
            return ValidationResult(
                is_valid=False, error_message=f"Block at index {idx} is not a ConversationBlock instance"
            )

        if not block.speaker_role or block.speaker_role not in SpeakerRole.__members__.values():
            return ValidationResult(
                is_valid=False, error_message=f"Block {idx} has invalid speaker_role: {block.speaker_role}"
            )

        if not block.speaker_label or not block.speaker_label.strip():
            return ValidationResult(is_valid=False, error_message=f"Block {idx} has empty speaker_label")

        if not block.text or not block.text.strip():
            return ValidationResult(is_valid=False, error_message=f"Block {idx} has empty text")

    return ValidationResult(is_valid=True)


def validate_metadata_qa(result: Any) -> ValidationResult:
    """Validate MetadataAndQA output from metadata_qa_extractor node."""
    if not isinstance(result, MetadataAndQA):
        return ValidationResult(is_valid=False, error_message="Result is not a MetadataAndQA instance")

    qas = result.question_answers
    if not isinstance(qas, list) or len(qas) == 0:
        return ValidationResult(is_valid=False, error_message="No question answers extracted")

    seen_ids = set()
    for idx, qa in enumerate(qas):
        if not qa.question_id or not qa.question_id.strip():
            return ValidationResult(
                is_valid=False, error_message=f"QuestionAnswer at index {idx} has empty question_id"
            )

        if not qa.question or not qa.question.strip():
            return ValidationResult(
                is_valid=False, error_message=f"QuestionAnswer '{qa.question_id}' has empty question text"
            )

        if not qa.answer or not qa.answer.strip():
            return ValidationResult(
                is_valid=False, error_message=f"QuestionAnswer '{qa.question_id}' has empty answer text"
            )

        if qa.question_id in seen_ids:
            return ValidationResult(is_valid=False, error_message=f"Duplicate question_id detected: {qa.question_id}")
        seen_ids.add(qa.question_id)

    return ValidationResult(is_valid=True)


def validate_question_evaluations(evals: Any, expected_count: int) -> ValidationResult:
    """Validate QuestionEvaluationList output from batched_qa_assessment node."""
    if not isinstance(evals, list):
        return ValidationResult(is_valid=False, error_message="Expected evaluations to be a list")

    if len(evals) != expected_count:
        return ValidationResult(
            is_valid=False,
            error_message=f"Question count mismatch. Expected {expected_count} evaluations, got {len(evals)}",
        )

    seen_ids = set()
    for idx, ev in enumerate(evals):
        if not isinstance(ev, QuestionEvaluation):
            return ValidationResult(
                is_valid=False, error_message=f"Evaluation at index {idx} is not a QuestionEvaluation instance"
            )

        qid = ev.question_id
        if not qid or not qid.strip():
            return ValidationResult(is_valid=False, error_message=f"Evaluation {idx} has empty question_id")

        if qid in seen_ids:
            return ValidationResult(is_valid=False, error_message=f"Duplicate question_id in evaluations: {qid}")
        seen_ids.add(qid)

        if not ev.question or not ev.question.strip():
            return ValidationResult(is_valid=False, error_message=f"Evaluation '{qid}' has empty question text")

        if not ev.answer or not ev.answer.strip():
            return ValidationResult(is_valid=False, error_message=f"Evaluation '{qid}' has empty answer text")

        if not ev.expected_answer or not ev.expected_answer.strip():
            return ValidationResult(is_valid=False, error_message=f"Evaluation '{qid}' has empty expected_answer text")

        if ev.difficulty not in DifficultyLevel.__members__.values():
            return ValidationResult(
                is_valid=False, error_message=f"Evaluation '{qid}' has invalid difficulty: {ev.difficulty}"
            )

        # Bounds checks for scores (0 to 10)
        scores = {
            "accuracy_score": ev.accuracy_score,
            "depth_score": ev.depth_score,
            "completeness_score": ev.completeness_score,
            "clarity_score": ev.clarity_score,
            "confidence_score": ev.confidence_score,
            "experience_alignment_score": ev.experience_alignment_score,
        }
        for name, score in scores.items():
            if score < 0 or score > 10:
                return ValidationResult(
                    is_valid=False, error_message=f"Evaluation '{qid}' score {name} out of bounds: {score}"
                )

        if not ev.feedback or not ev.feedback.strip():
            return ValidationResult(is_valid=False, error_message=f"Evaluation '{qid}' has empty feedback")

    return ValidationResult(is_valid=True)


def validate_topic_summaries(topics: Any, evaluations: list[QuestionEvaluation]) -> ValidationResult:
    """Validate TopicSummary outputs from topic_aggregation node."""
    if not isinstance(topics, list):
        return ValidationResult(is_valid=False, error_message="Expected topic summaries to be a list")

    if len(topics) == 0:
        return ValidationResult(is_valid=False, error_message="Topic summaries list is empty")

    valid_categories = {ev.category for ev in evaluations}

    for idx, t in enumerate(topics):
        if not isinstance(t, TopicSummary):
            return ValidationResult(
                is_valid=False, error_message=f"Topic summary at index {idx} is not a TopicSummary instance"
            )

        if not t.topic or not t.topic.strip():
            return ValidationResult(is_valid=False, error_message=f"Topic summary {idx} has empty topic name")

        # Orphaned topic check
        if t.topic not in valid_categories:
            return ValidationResult(
                is_valid=False,
                error_message=f"Orphaned topic: '{t.topic}' does not match any category in evaluations: {valid_categories}",
            )

        if t.average_score < 0 or t.average_score > 10:
            return ValidationResult(
                is_valid=False, error_message=f"Topic '{t.topic}' average_score out of bounds: {t.average_score}"
            )

        if t.confidence_score < 0 or t.confidence_score > 10:
            return ValidationResult(
                is_valid=False, error_message=f"Topic '{t.topic}' confidence_score out of bounds: {t.confidence_score}"
            )

        if not t.feedback or not t.feedback.strip():
            return ValidationResult(is_valid=False, error_message=f"Topic '{t.topic}' has empty feedback")

    return ValidationResult(is_valid=True)


def validate_interview_summary(summary: Any) -> ValidationResult:
    """Validate InterviewSummary output from interview_summary node."""
    if not isinstance(summary, InterviewSummary):
        return ValidationResult(is_valid=False, error_message="Result is not an InterviewSummary instance")

    scores = {
        "overall_score": summary.overall_score,
        "technical_score": summary.technical_score,
        "communication_score": summary.communication_score,
        "confidence_score": summary.confidence_score,
        "knowledge_depth": summary.knowledge_depth,
        "experience_alignment_score": summary.experience_alignment_score,
    }
    for name, score in scores.items():
        if score < 0 or score > 10:
            return ValidationResult(is_valid=False, error_message=f"InterviewSummary {name} out of bounds: {score}")

    if summary.hiring_decision not in HiringDecision.__members__.values():
        return ValidationResult(
            is_valid=False, error_message=f"InterviewSummary has invalid hiring_decision: {summary.hiring_decision}"
        )

    if not summary.final_feedback or not summary.final_feedback.strip():
        return ValidationResult(is_valid=False, error_message="InterviewSummary has empty final_feedback")

    return ValidationResult(is_valid=True)
