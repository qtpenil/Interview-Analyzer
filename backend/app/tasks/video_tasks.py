import asyncio
import os
from datetime import datetime
from uuid import UUID

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.integration.ffmpeg.manager import ffmpeg_manager
from app.integration.ffmpeg.utils import generate_audio_fingerprint
from app.modules.interview.interview_media_service import interview_media_service
from app.modules.interview.InterviewModel import Interview, InterviewStatus
from app.modules.interview.service import check_duplicate_interview
from app.shared.db.status_updater import (
    is_interview_cancelled,
    update_interview_fields,
    update_interview_status,
)
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


def run_async_safe(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    return asyncio.run_coroutine_threadsafe(coro, loop).result()


def copy_interview_results(from_id: UUID, to_id: UUID, db) -> None:
    """Copy all scored fields and topic rows from source interview to dest."""
    from app.modules.interview.InterviewModel import Interview, InterviewStatus
    from app.modules.interviewTopics.interviewTopics import InterviewTopic

    src = db.query(Interview).filter(Interview.id == from_id).first()
    dest = db.query(Interview).filter(Interview.id == to_id).first()
    if not src or not dest:
        return

    dest.claimed_experience_years = src.claimed_experience_years
    dest.overall_score = src.overall_score
    dest.technical_score = src.technical_score
    dest.communication_score = src.communication_score
    dest.confidence_score = src.confidence_score
    dest.knowledge_depth = src.knowledge_depth
    dest.experience_alignment_score = src.experience_alignment_score
    dest.hiring_decision = src.hiring_decision
    dest.ai_model_name = src.ai_model_name
    dest.ai_model_version = src.ai_model_version
    dest.transcript = src.transcript
    dest.status = InterviewStatus.COMPLETED
    dest.processing_completed_at = datetime.utcnow()

    # Copy topics
    db.query(InterviewTopic).filter(InterviewTopic.interview_id == to_id).delete()
    for t in src.topics:
        db_topic = InterviewTopic(
            interview_id=to_id,  # type: ignore[arg-type]  # uuid.UUID vs sqlalchemy _UUID_RETURN
            topic=t.topic,
            average_score=t.average_score,
            confidence_score=t.confidence_score,
            strongest_concepts=t.strongest_concepts,
            weakest_concepts=t.weakest_concepts,
            feedback=t.feedback,
        )
        db.add(db_topic)

    db.commit()


def build_state_dict_for_duplicate(src_interview, dest_interview_id: str) -> dict:
    """
    Build a fully-populated state_dict for PDF generation from the original
    (already-completed) interview, using its checkpoint data when available.

    Priority:
        1. Checkpoint from Redis/local backend  →  full pipeline state
        2. DB fields + topic rows               →  flat reconstructed dict
    """
    from app.core.config import settings
    from app.integration.langGraph.concurrency import get_concurrency_manager
    from app.integration.langGraph.interviewGraph import interview_graph_runner

    src_id = str(src_interview.id)

    # 1. Try checkpoint of the *original* interview — richest data
    if settings.ENABLE_CHECKPOINTING:
        try:
            concurrency_mgr = get_concurrency_manager()
            checkpoint = run_async_safe(concurrency_mgr.backend.get_checkpoint(f"checkpoint:{src_id}"))
            if checkpoint:
                logger.info(f"[{dest_interview_id}] Using checkpoint from original interview {src_id}")
                state_dict = interview_graph_runner._format_output(checkpoint)
                # Stamp with the new interview_id so the PDF task is correct
                state_dict["interview_id"] = dest_interview_id
                return state_dict
        except Exception as exc:
            logger.warning(
                f"[{dest_interview_id}] Could not load checkpoint for {src_id}: {exc}. Falling back to DB fields."
            )

    # 2. Fallback: reconstruct from flat DB fields + topic rows
    logger.info(f"[{dest_interview_id}] Reconstructing state_dict from DB fields of {src_id}")
    topics = [
        {
            "topic": t.topic,
            "average_score": float(t.average_score or 0),
            "confidence_score": float(t.confidence_score or 0),
            "strongest_concepts": t.strongest_concepts or [],
            "weakest_concepts": t.weakest_concepts or [],
            "feedback": getattr(t, "feedback", ""),
        }
        for t in src_interview.topics
    ]

    hiring_decision = src_interview.hiring_decision.value if src_interview.hiring_decision else "borderline"

    summary_data: dict[str, object] = {
        "candidate_name": src_interview.title or "Candidate",
        "hiring_decision": hiring_decision,
        "overall_score": float(src_interview.overall_score or 0),
        "technical_score": float(src_interview.technical_score or 0),
        "communication_score": float(src_interview.communication_score or 0),
        "confidence_score": float(src_interview.confidence_score or 0),
        "knowledge_depth": float(src_interview.knowledge_depth or 0),
        "experience_alignment_score": float(src_interview.experience_alignment_score or 0),
        "final_feedback": "",
        "strengths": [],
        "weaknesses": [],
        "risk_factors": [],
    }

    return {
        "interview_id": dest_interview_id,
        "candidate_name": summary_data["candidate_name"],
        "claimed_experience_years": float(src_interview.claimed_experience_years or 0),
        "hiring_decision": hiring_decision,
        "overall_score": summary_data["overall_score"],
        "technical_score": summary_data["technical_score"],
        "communication_score": summary_data["communication_score"],
        "confidence_score": summary_data["confidence_score"],
        "knowledge_depth": summary_data["knowledge_depth"],
        "experience_alignment_score": summary_data["experience_alignment_score"],
        "summary": "",
        "final_feedback": "",
        "strengths": [],
        "weaknesses": [],
        "risk_factors": [],
        "interview_summary": summary_data,
        "question_evaluations": [],
        "topics": topics,
        "questions": [],
    }


@celery_app.task(bind=True, max_retries=3)
def process_video_to_audio(self, interview_id: str, video_path: str) -> dict:
    """
    Celery task: Convert uploaded video to cleaned WAV audio.

    Pipeline step 1/4:
        video → extract audio → silence removal → cleaned .wav

    After audio is ready, generates an audio fingerprint and checks
    for duplicate interviews before chaining to transcription.
    """

    try:
        logger.info(f"[{interview_id}] >>> TASK process_video_to_audio STARTED (video_path={video_path})")

        # Check if cancelled before starting work
        if is_interview_cancelled(interview_id):
            logger.info(f"[{interview_id}] Interview cancelled, aborting video processing")
            # Clean up video file if it exists
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                pass
            return {"interview_id": interview_id, "status": "cancelled"}

        duration = ffmpeg_manager.get_duration(video_path)
        if duration < 60:
            logger.info(f"[{interview_id}] Video too short ({duration}s), rejecting")
            update_interview_status(interview_id, InterviewStatus.FAILED)
            update_interview_fields(
                interview_id,
                failure_reason="Video is too short to be an interview (under 60 seconds)",
            )
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                pass
            return {"interview_id": interview_id, "status": "too_short", "duration": duration}

        if duration > 7200:
            logger.info(f"[{interview_id}] Video too long ({duration}s), rejecting")
            update_interview_status(interview_id, InterviewStatus.FAILED)
            update_interview_fields(
                interview_id,
                failure_reason="Video exceeds maximum duration of 2 hours",
            )
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
            except Exception:
                pass
            return {"interview_id": interview_id, "status": "too_long", "duration": duration}

        update_interview_status(
            interview_id,
            InterviewStatus.PROCESSING,
            processing_started_at=datetime.utcnow(),
        )

        logger.info(f"[{interview_id}] Starting video-to-audio processing: {video_path}")

        audio_prep_mode = getattr(
            __import__("app.core.config", fromlist=["settings"]).settings,
            "AUDIO_PREP_MODE",
            "trimmed",
        )

        audio_result = interview_media_service.prepare_audio_for_transcription(
            video_path=video_path,
            audio_prep_mode=audio_prep_mode,
        )

        logger.info(f"[{interview_id}] Audio prepared: {audio_result.audio_path} (mode={audio_result.mode})")

        # Clean up original video file — no longer needed
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"[{interview_id}] Cleaned up video file: {video_path}")
        except Exception as exc:
            logger.warning(f"[{interview_id}] Failed to clean up video file {video_path}: {exc}")

        # ── Audio fingerprinting & duplicate detection ──────────────────

        fingerprint = generate_audio_fingerprint(audio_result.audio_path)

        if fingerprint:
            # Check for a duplicate interview for the same user

            session = SessionLocal()
            try:
                # Retrieve the current interview to get its user_id
                interview = (
                    session.query(Interview)
                    .filter(
                        Interview.id == UUID(interview_id),
                    )
                    .first()
                )

                if interview is None:
                    logger.error(f"[{interview_id}] Interview not found during duplicate check")
                else:
                    duplicate = check_duplicate_interview(
                        user_id=interview.user_id,
                        fingerprint=fingerprint,
                        db=session,
                    )

                    if duplicate and str(duplicate.id) != interview_id:
                        logger.warning(
                            f"[{interview_id}] >>> DUPLICATE PATH: skipping LangGraph pipeline. "
                            f"Reusing analysis from existing interview {duplicate.id} "
                            f"for user {interview.user_id}"
                        )

                        # 1. Persist fingerprint + transcript on the new row
                        interview.audio_fingerprint = fingerprint
                        interview.transcript = duplicate.transcript
                        session.commit()
                        logger.info(f"[{interview_id}] Fingerprint + transcript saved (duplicate)")

                        # 2. Copy all scored DB fields and topic rows
                        copy_interview_results(duplicate.id, interview.id, session)

                        # 3. Build a fully-populated state_dict from the original
                        #    interview's checkpoint (or DB fields as fallback).
                        #    This is the payload the PDF service needs to render
                        #    scores, topics, questions and the narrative summary.
                        state_dict = build_state_dict_for_duplicate(
                            src_interview=duplicate,
                            dest_interview_id=interview_id,
                        )

                        # 4. Fire PDF generation directly — no LangGraph re-run
                        from app.tasks.pdf_tasks import generate_pdf_report

                        generate_pdf_report.delay(interview_id, state_dict)

                        logger.info(
                            f"[{interview_id}] PDF task queued from duplicate state_dict (source: {duplicate.id})"
                        )

                        return {
                            "interview_id": interview_id,
                            "status": "duplicate",
                            "duplicate_of": str(duplicate.id),
                        }

            finally:
                session.close()

            # No duplicate — save fingerprint to DB
            update_interview_fields(
                interview_id,
                audio_fingerprint=fingerprint,
            )
            logger.info(f"[{interview_id}] Audio fingerprint saved")

        else:
            logger.warning(f"[{interview_id}] Could not generate audio fingerprint, skipping duplicate check")

        # ── Chain to next task ──────────────────────────────────────────
        from app.tasks.transcription_tasks import transcribe_audio

        transcribe_audio.delay(
            interview_id,
            audio_result.audio_path,
            audio_result.chunk_boundaries,
            audio_result.mode,
        )

        return {
            "interview_id": interview_id,
            "audio_path": audio_result.audio_path,
            "status": "audio_ready",
            "audio_prep_mode": audio_result.mode,
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            update_interview_status(
                interview_id,
                InterviewStatus.FAILED,
            )
        logger.exception(f"[{interview_id}] Video processing failed: {exc}")
        raise self.retry(exc=exc)
