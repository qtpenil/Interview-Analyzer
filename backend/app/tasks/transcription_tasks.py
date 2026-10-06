import os

from app.core.config import settings
from app.celery_app import celery_app
from app.integration.interview_classifier.classifier import (
    classify_transcript_with_context,
)
from app.integration.transcription.manager import transcription_manager
from app.modules.interview.InterviewModel import InterviewStatus
from app.shared.db.status_updater import (
    is_interview_cancelled,
    update_interview_fields,
    update_interview_status,
)
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


def cleanup_audio_file(audio_path: str) -> None:
    """
    Delete the intermediate .wav file after successful transcription.

    Never raises — cleanup failure must not fail the pipeline.
    """

    try:
        os.remove(audio_path)
        logger.info(f"Cleaned up audio file: {audio_path}")

    except Exception as exc:
        logger.warning(f"Failed to cleanup audio file {audio_path}: {exc}")


@celery_app.task(bind=True, max_retries=3)
def transcribe_audio(
    self,
    interview_id: str,
    audio_path: str,
    chunk_boundaries: list[dict] | None = None,
    audio_prep_mode: str = "trimmed",
) -> dict:
    """
    Celery task: Transcribe cleaned audio via Groq Whisper.

    Pipeline step 2/4:
        .wav → chunk + parallel transcription → merged segments + full text

    On success, cleans up audio file and chains to analysis task.

    Args:
        interview_id: The interview ID.
        audio_path: Path to the cleaned .wav file.
        chunk_boundaries: Pre-computed chunk boundaries for
            `silence_aware` mode (passed to split_audio_to_memory).
        audio_prep_mode: One of "trimmed", "raw", or
            "silence_aware" — recorded for A/B testing.
    """

    try:
        logger.info(
            f"[{interview_id}] >>> TASK transcribe_audio STARTED "
            f"(audio_path={audio_path}, mode={audio_prep_mode})"
        )

        if is_interview_cancelled(interview_id):
            logger.info(f"[{interview_id}] Interview cancelled, aborting transcription")
            cleanup_audio_file(audio_path)
            return {"interview_id": interview_id, "status": "cancelled"}

        update_interview_status(
            interview_id,
            InterviewStatus.TRANSCRIBING,
        )

        logger.info(f"[{interview_id}] Starting transcription: {audio_path}")

        transcript_result = transcription_manager.transcribe(
            audio_path,
            chunk_boundaries=chunk_boundaries,
        )

        logger.info(
            f"[{interview_id}] Transcription complete: "
            f"{transcript_result['chunks_processed']} chunks, "
            f"{len(transcript_result['segments'])} segments, "
            f"{transcript_result['processing_time']}s"
        )

        # Save transcript text to DB
        segments = transcript_result.get("segments")
        full_text = transcript_result.get("full_text", "")

        if segments:
            update_interview_fields(
                interview_id,
                transcript=segments,
            )

            logger.info(f"[{interview_id}] Transcript saved to database")

        # Cleanup intermediate audio file
        cleanup_audio_file(audio_path)

        # ── Interview classifier ──────────────────────────────────────────
        if full_text:
            segments = transcript_result.get("segments", [])
            duration = transcript_result.get("audio_duration_seconds", 0.0)
            classification = classify_transcript_with_context(
                full_text, segments, duration, interview_id
            )
            if not classification.get("is_interview", True):
                reason = classification.get("reason", "Uploaded video does not appear to be an interview")
                logger.warning(f"[{interview_id}] Not an interview: {reason}")
                update_interview_status(interview_id, InterviewStatus.FAILED)
                update_interview_fields(interview_id, failure_reason=reason)
                return {
                    "interview_id": interview_id,
                    "status": "not_an_interview",
                    "reason": reason,
                }

        # Chain to next task
        from app.tasks.analysis_tasks import analyze_transcript

        analyze_transcript.delay(interview_id, transcript_result)

        return {
            "interview_id": interview_id,
            "status": "transcription_complete",
            "segments_count": len(transcript_result["segments"]),
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            update_interview_status(
                interview_id,
                InterviewStatus.FAILED,
            )
        logger.exception(f"[{interview_id}] Transcription failed: {exc}")
        raise self.retry(exc=exc)
