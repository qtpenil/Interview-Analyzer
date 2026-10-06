import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.database import SessionLocal
from app.modules.interview.InterviewModel import Interview, InterviewStatus
from app.modules.interviewQuestions.model import InterviewQuestion
from app.modules.interviewTopics.interviewTopics import InterviewTopic
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)

_VALID_INTERVIEW_COLUMNS = {c.name for c in Interview.__table__.columns}


def update_interview_status(
    interview_id: str,
    status: InterviewStatus,
    *,
    processing_started_at: datetime | None = None,
    processing_completed_at: datetime | None = None,
) -> None:
    """
    Celery-safe status updater. Opens its own session — never uses
    FastAPI's dependency-injected session.

    This is the single source of truth for all status mutations
    inside Celery tasks.
    """

    session = SessionLocal()

    try:
        interview = session.query(Interview).filter(Interview.id == UUID(interview_id)).first()

        if interview is None:
            logger.error(f"Interview {interview_id} not found for status update")
            return

        interview.status = status

        if processing_started_at is not None:
            interview.processing_started_at = processing_started_at

        if processing_completed_at is not None:
            interview.processing_completed_at = processing_completed_at

        session.commit()

        logger.info(f"Interview {interview_id} status updated to {status.value}")

    except Exception as exc:
        session.rollback()
        logger.exception(f"Failed to update status for interview {interview_id}: {exc}")
        raise

    finally:
        session.close()


def update_interview_fields(interview_id: str, **fields) -> None:
    """
    Celery-safe partial field updater. Only writes fields that exist on the
    Interview model; unknown keywords are skipped (with a warning) so callers
    can pass extra context without breaking the write.
    """
    session = SessionLocal()

    try:
        interview = session.query(Interview).filter(Interview.id == UUID(interview_id)).first()

        if interview is None:
            logger.error(f"Interview {interview_id} not found for field update")
            return

        for field, value in fields.items():
            if field in _VALID_INTERVIEW_COLUMNS and hasattr(interview, field):
                setattr(interview, field, value)
            else:
                logger.warning(f"Skipping unknown interview field: {field}")

        session.commit()
        logger.info(f"Interview {interview_id} fields updated: {', '.join(fields.keys())}")

    except Exception as exc:
        session.rollback()
        logger.exception(f"Failed to update fields for interview {interview_id}: {exc}")
        raise

    finally:
        session.close()


def is_interview_cancelled(interview_id: str) -> bool:
    """
    Check if an interview has been cancelled.
    Used by Celery tasks to abort early when user cancels mid-pipeline.
    """
    session = SessionLocal()
    try:
        interview = session.query(Interview).filter(Interview.id == UUID(interview_id)).first()
        return interview is not None and interview.status == InterviewStatus.CANCELLED
    except Exception as exc:
        logger.warning(f"Failed to check cancellation status for {interview_id}: {exc}")
        return False
    finally:
        session.close()


def _compute_average_score(
    accuracy_score: float,
    depth_score: float,
    completeness_score: float,
    clarity_score: float,
    confidence_score: float,
) -> Decimal:
    """Shared average_score formula: (accuracy + depth + completeness + clarity + confidence) / 5.

    Must stay identical to the formula in topic_aggregation.
    """
    result = (
        float(accuracy_score)
        + float(depth_score)
        + float(completeness_score)
        + float(clarity_score)
        + float(confidence_score)
    ) / 5.0
    return Decimal(str(result))


def _avg_score_from_topic_summary(t_dict: dict) -> Decimal:
    """Extract average_score from a TopicSummary dict, returning Decimal."""
    val = t_dict.get("average_score")
    if val is None:
        return Decimal("0")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def _extract_question_number(question_id) -> int:
    """Extract the trailing ordinal from a pipeline question id like "q12" -> 12."""
    match = re.search(r"(\d+)\s*$", str(question_id or ""))
    return int(match.group(1)) if match else 0


def _incremental_mean(old_avg, old_count, new_val) -> Decimal:
    """Incremental-mean update: new_avg = (old_avg * old_n + new_val) / (old_n + 1)."""
    new_count = int(old_count) + 1
    return Decimal(str((float(old_avg) * float(old_count) + float(new_val)) / float(new_count)))


def _build_concept_to_question_ids(
    strongest_concepts: list[str],
    weakest_concepts: list[str],
    question_evaluations: list,
    local_id_to_uuid: dict[str, UUID],
) -> dict[str, dict[str, set[UUID]]]:
    """Map each topic-level concept to the UUIDs of questions that list it exactly."""
    concept_to_question_ids: dict[str, dict[str, set[UUID]]] = {"strongest": {}, "weakest": {}}

    for concept in strongest_concepts:
        concept_to_question_ids["strongest"][concept] = {
            local_id_to_uuid[q.question_id]
            for q in question_evaluations
            if concept in (q.strong_concepts or [])
        }
    for concept in weakest_concepts:
        concept_to_question_ids["weakest"][concept] = {
            local_id_to_uuid[q.question_id]
            for q in question_evaluations
            if concept in (q.missing_concepts or [])
        }

    return concept_to_question_ids


def _update_question_bounds(db_stats, inserted_questions: list[InterviewQuestion]) -> None:
    """Update highest/lowest scored question pointers on a topic_stats row."""
    if not inserted_questions:
        return

    scores = [(q.id, float(q.average_score)) for q in inserted_questions if q.average_score is not None]
    if not scores:
        return

    high_id, high_score = max(scores, key=lambda item: item[1])
    low_id, low_score = min(scores, key=lambda item: item[1])

    if db_stats.highest_scored_question_score is None or high_score > float(db_stats.highest_scored_question_score):
        db_stats.highest_scored_question_id = high_id
        db_stats.highest_scored_question_score = Decimal(str(high_score))

    if db_stats.lowest_scored_question_score is None or low_score < float(db_stats.lowest_scored_question_score):
        db_stats.lowest_scored_question_id = low_id
        db_stats.lowest_scored_question_score = Decimal(str(low_score))


def _invalidate_dashboard_cache(user_id, touched_topics: set[str]) -> None:
    """Best-effort cache invalidation from a sync (Celery) context."""
    from app.modules.dashboard.cache import invalidate_dashboard_cache_sync

    try:
        invalidate_dashboard_cache_sync(user_id, touched_topics)
    except Exception as exc:  # pragma: no cover - cache is best-effort
        logger.warning(f"Dashboard cache invalidation failed for user {user_id}: {exc}")


def save_interview_analysis_results(
    interview_id: str,
    state_dict: dict,
) -> None:
    """
    Save the LangGraph analysis results (scores, claimed experience, hiring decision,
    and AI model information) into the Interview database record.
    Also persists per-question rows (interview_questions) and incrementally
    updates per-(user, topic) stats (topic_stats).
    """
    from app.core.config import settings
    from app.integration.langGraph.Schema.assessmentSchema import QuestionEvaluation
    from app.modules.dashboard.model import InterviewTopicStats
    from app.modules.interview.InterviewModel import HiringDecision as DBHiringDecision

    session = SessionLocal()
    touched_topics: set[str] = set()
    user_id = None

    try:
        interview = session.query(Interview).filter(Interview.id == UUID(interview_id)).first()

        if interview is None:
            logger.error(f"Interview {interview_id} not found for saving analysis results")
            return

        user_id = interview.user_id

        # Helper to convert to Decimal or None
        def to_decimal(val) -> Decimal | None:
            if val is None or val == "":
                return None
            try:
                return Decimal(str(val))
            except Exception:
                return None

        # Map Hiring Decision
        raw_decision = state_dict.get("hiring_decision")
        mapped_decision = None
        if raw_decision:
            # Extract string value from enum or string
            if hasattr(raw_decision, "value"):
                val_str = str(raw_decision.value)
            else:
                val_str = str(raw_decision)

            # Normalize to uppercase and remove spaces/underscores/dashes
            normalized = val_str.strip().upper().replace(" ", "").replace("_", "").replace("-", "")
            if "." in normalized:
                normalized = normalized.split(".")[-1]

            if "STRONGHIRE" in normalized:
                mapped_decision = DBHiringDecision.STRONG_HIRE
            elif "STRONGREJECT" in normalized or "REJECT" in normalized or "NOHIRE" in normalized:
                mapped_decision = DBHiringDecision.NO_HIRE
            elif "HIRE" in normalized:
                mapped_decision = DBHiringDecision.HIRE
            elif "BORDERLINE" in normalized:
                mapped_decision = DBHiringDecision.BORDERLINE

        # Update fields
        interview.claimed_experience_years = to_decimal(state_dict.get("claimed_experience_years"))
        interview.overall_score = to_decimal(state_dict.get("overall_score"))
        interview.technical_score = to_decimal(state_dict.get("technical_score"))
        interview.communication_score = to_decimal(state_dict.get("communication_score"))
        interview.confidence_score = to_decimal(state_dict.get("confidence_score"))
        interview.knowledge_depth = to_decimal(state_dict.get("knowledge_depth"))
        interview.experience_alignment_score = to_decimal(state_dict.get("experience_alignment_score"))
        interview.hiring_decision = mapped_decision

        # AI processing details
        interview.ai_model_name = "google"
        interview.ai_model_version = settings.GOOGLE_AI_MODEL

        # Group question evaluations by category (TopicSummary.topic == QuestionEvaluation.category).
        # The state_dict carries questions top-level, not nested under each topic.
        raw_evals = state_dict.get("question_evaluations") or []
        evaluations_by_category: dict[str, list[QuestionEvaluation]] = defaultdict(list)
        for ev in raw_evals:
            qe = ev if isinstance(ev, QuestionEvaluation) else QuestionEvaluation.model_validate(ev)
            evaluations_by_category[qe.category].append(qe)

        # Save topics + interview_questions + topic_stats
        topics_list = state_dict.get("topics") or []

        for t_dict in topics_list:
            topic_name = t_dict.get("topic")
            if not topic_name:
                continue

            question_evaluations = evaluations_by_category.get(topic_name) or []
            touched_topics.add(topic_name)

            # -------- Persist InterviewTopic row (existing) --------
            db_topic = (
                session.query(InterviewTopic)
                .filter(InterviewTopic.interview_id == UUID(interview_id), InterviewTopic.topic == topic_name)
                .first()
            )

            if not db_topic:
                db_topic = InterviewTopic(
                    interview_id=UUID(interview_id),
                    topic=topic_name,
                )
                session.add(db_topic)
                # Flush now so db_topic.id is populated before any InterviewQuestion
                # below captures it — otherwise topic_id would be baked in as None.
                session.flush()

            db_topic.average_score = to_decimal(t_dict.get("average_score"))
            db_topic.confidence_score = to_decimal(t_dict.get("confidence_score"))
            raw_strongest = t_dict.get("strongest_concepts") or []
            raw_weakest = t_dict.get("weakest_concepts") or []
            feedback = t_dict.get("feedback")
            if feedback is not None:
                db_topic.feedback = str(feedback) if feedback else None

            # -------- Persist interview_questions for this topic --------
            inserted_questions: list[InterviewQuestion] = []
            for qe in question_evaluations:
                db_question = InterviewQuestion(
                    interview_id=UUID(interview_id),
                    user_id=interview.user_id,
                    topic_id=db_topic.id,
                    category=topic_name,
                    sub_category=qe.sub_category,
                    question_number=_extract_question_number(qe.question_id),
                    question=qe.question,
                    answer=qe.answer,
                    difficulty=qe.difficulty,
                    average_score=_compute_average_score(
                        qe.accuracy_score,
                        qe.depth_score,
                        qe.completeness_score,
                        qe.clarity_score,
                        qe.confidence_score,
                    ),
                    strong_concepts=qe.strong_concepts or [],
                    weak_concepts=qe.missing_concepts or [],
                    feedback=qe.feedback,
                )
                session.add(db_question)
                inserted_questions.append(db_question)

            session.flush()  # Assign DB UUIDs before mapping concepts.

            # Map the local question_id (e.g. "q1") -> the new DB UUID.
            local_id_to_uuid: dict[str, UUID] = {
                qe.question_id: db_question.id for qe, db_question in zip(question_evaluations, inserted_questions)
            }

            # -------- Build concept -> question_ids mapping for this topic --------
            concept_to_question_ids = _build_concept_to_question_ids(
                raw_strongest,
                raw_weakest,
                question_evaluations,
                local_id_to_uuid,
            )

            # New shape: [{"concept": "concept a", "question_ids": ["<uuid>", ...]}]
            db_topic.strongest_concepts = [
                {"concept": concept, "question_ids": sorted(str(qid) for qid in question_ids)}
                for concept, question_ids in concept_to_question_ids["strongest"].items()
            ]
            db_topic.weakest_concepts = [
                {"concept": concept, "question_ids": sorted(str(qid) for qid in question_ids)}
                for concept, question_ids in concept_to_question_ids["weakest"].items()
            ]

            # -------- Fetch-or-create topic_stats row (with row lock) --------
            db_stats = (
                session.query(InterviewTopicStats)
                .filter(
                    InterviewTopicStats.user_id == interview.user_id,
                    InterviewTopicStats.topic == topic_name,
                )
                .with_for_update()
                .first()
            )

            new_topic_score = _avg_score_from_topic_summary(t_dict)

            if not db_stats:
                # New row: seed from this TopicSummary
                db_stats = InterviewTopicStats(
                    user_id=interview.user_id,
                    topic=topic_name,
                    average_score=new_topic_score,
                    highest_score=new_topic_score,
                    lowest_score=new_topic_score,
                    highest_score_interview_topic_id=db_topic.id,
                    lowest_score_interview_topic_id=db_topic.id,
                    interview_count=1,
                    last_assessed_at=datetime.utcnow(),
                )
                session.add(db_stats)
            else:
                # Incremental update
                db_stats.average_score = _incremental_mean(
                    db_stats.average_score,
                    db_stats.interview_count,
                    new_topic_score,
                )
                db_stats.interview_count = int(db_stats.interview_count) + 1

                if new_topic_score > float(db_stats.highest_score):
                    db_stats.highest_score = new_topic_score
                    db_stats.highest_score_interview_topic_id = db_topic.id
                if new_topic_score < float(db_stats.lowest_score):
                    db_stats.lowest_score = new_topic_score
                    db_stats.lowest_score_interview_topic_id = db_topic.id

            # Track highest/lowest scored question among this topic's inserted questions.
            _update_question_bounds(db_stats, inserted_questions)

            db_stats.last_assessed_at = datetime.utcnow()

        session.commit()

        logger.info(f"Interview {interview_id} analysis results saved to database")

    except Exception as exc:
        session.rollback()
        logger.exception(f"Failed to save analysis results for interview {interview_id}: {exc}")
        raise

    finally:
        session.close()

    # Invalidate this user's cached dashboard payload (and touched topic pages).
    # Runs after commit, outside the session. Celery context = no running event loop.
    if user_id is not None and touched_topics:
        _invalidate_dashboard_cache(user_id, touched_topics)
