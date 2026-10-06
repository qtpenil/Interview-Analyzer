import os
import shutil
import uuid
from collections import defaultdict
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import SessionLocal
from app.modules.files.file import File, FileType
from app.modules.interview.InterviewModel import (
    Interview,
    InterviewStatus,
)
from app.modules.interview.schemas import InterviewListItem, InterviewListResponse
from app.modules.interviewQuestions.model import InterviewQuestion
from app.shared.logger.logger import get_logger
from app.shared.storage.service import read_file

logger = get_logger(__name__)


def save_video_file(upload_file: UploadFile) -> str:
    uploads_dir = os.path.join("storage", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    suffix = Path(upload_file.filename).suffix if upload_file.filename else ".mp4"
    file_name = f"{uuid.uuid4()}{suffix}"
    file_path = os.path.join(uploads_dir, file_name).replace("\\", "/")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    logger.info(f"Saved uploaded video to {file_path}")
    return file_path


def create_interview(
    video_path: str,
    user_id: UUID | str | int,
    title: str | None = None,
    claimed_experience_years: float | None = None,
) -> Interview:
    session = SessionLocal()
    try:
        interview = Interview(  # type: ignore[call-arg]  # sqlalchemy plugin cannot infer mapped kwargs
            user_id=user_id,
            title=title,
            claimed_experience_years=claimed_experience_years,
            status=InterviewStatus.UPLOADED,
        )

        session.add(interview)
        session.commit()
        session.refresh(interview)
        interview_id = interview.id

        logger.info(f"Created interview {interview_id} with status UPLOADED")

        file_size = None
        try:
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
        except Exception as e:
            logger.warning(f"Failed to get video file size for {video_path}: {e}")

        from app.modules.files.file import File
        from app.modules.files.schema import FileType

        video_file = File(
            interview_id=interview_id,  # type: ignore[arg-type]  # uuid.UUID vs sqlalchemy _UUID_RETURN
            file_type=FileType.VIDEO,
            storage_provider="local",
            storage_path=video_path,
            file_size=file_size,
        )
        session.add(video_file)
        session.commit()

        session.refresh(interview)
        return interview

    except Exception as exc:
        session.rollback()
        logger.exception(f"Failed to create interview: {exc}")
        raise

    finally:
        session.close()


def get_interview_status(interview_id: UUID, user_id: UUID | str | int) -> Interview:
    from app.shared.exceptions.custom_exceptions import ResourceNotFoundException

    session = SessionLocal()
    try:
        interview = session.query(Interview).filter(Interview.id == interview_id, Interview.user_id == user_id).first()

        if interview is None:
            raise ResourceNotFoundException(f"Interview {interview_id} not found")

        return interview

    finally:
        session.close()


def get_interview_report_path(interview_id: UUID, user_id: UUID | str | int) -> bytes:
    from app.shared.exceptions.custom_exceptions import (
        BadRequestException,
        ResourceNotFoundException,
    )

    session = SessionLocal()
    try:
        interview = session.query(Interview).filter(Interview.id == interview_id, Interview.user_id == user_id).first()

        if interview is None:
            raise ResourceNotFoundException(f"Interview {interview_id} not found")

        if interview.status != InterviewStatus.COMPLETED:
            raise BadRequestException(f"Interview is not completed yet. Current status: {interview.status.value}")

        pdf_file = (
            session.query(File)
            .filter(
                File.interview_id == interview_id,
                File.file_type == FileType.SUMMARY_PDF,
            )
            .first()
        )

        if pdf_file is None:
            raise ResourceNotFoundException("PDF report not found")

        if not pdf_file.storage_path:
            raise ResourceNotFoundException("PDF report missing on storage")

        try:
            return read_file(pdf_file.storage_path)
        except Exception as exc:
            logger.warning(f"Storage service read failed for {pdf_file.storage_path}: {exc}")
            if os.path.exists(pdf_file.storage_path):
                with open(pdf_file.storage_path, "rb") as f:
                    return f.read()
            raise ResourceNotFoundException("PDF report file not found on storage") from exc

    finally:
        session.close()


def list_interviews_for_user(
    db: Session,
    user_id: UUID | str | int,
    status: str | None,
    page: int,
    page_size: int,
) -> InterviewListResponse:
    base_query = (
        select(Interview)
        .options(selectinload(Interview.files))
        .where(Interview.user_id == user_id)
        .where(Interview.status != InterviewStatus.CANCELLED)
    )

    if status:
        base_query = base_query.where(Interview.status == status)

    total = db.scalar(select(func.count()).select_from(base_query.subquery()))

    rows = db.scalars(
        base_query.order_by(Interview.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    items = []
    for r in rows:
        item = InterviewListItem.model_validate(r)
        if not item.title and r.files:
            video_file = next(
                (f for f in r.files if getattr(f.file_type, "value", f.file_type) == "VIDEO"),
                r.files[0],
            )
            if video_file and video_file.storage_path:
                item.title = os.path.basename(video_file.storage_path)
        items.append(item)

    return InterviewListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


def get_interview_with_details(db: Session, interview_id: UUID, user_id: UUID | str | int) -> Interview | None:
    interview = db.scalar(
        select(Interview)
        .options(selectinload(Interview.topics))
        .where(Interview.id == interview_id, Interview.user_id == user_id)
    )
    if interview:
        _attach_questions_to_topics(db, interview.topics)
    return interview


def _attach_questions_to_topics(db: Session, topics) -> None:
    """Populate each loaded InterviewTopic with its interview_questions (for the detail embed)."""
    topic_ids = [t.id for t in topics if t.id]
    if not topic_ids:
        return

    rows = db.scalars(
        select(InterviewQuestion)
        .where(InterviewQuestion.topic_id.in_(topic_ids))
        .order_by(InterviewQuestion.topic_id, InterviewQuestion.question_number)
    ).all()

    questions_by_topic: dict[UUID, list[dict]] = defaultdict(list)
    for q in rows:
        questions_by_topic[q.topic_id].append(
            {
                "id": str(q.id) if q.id else None,
                "question_number": q.question_number,
                "question": q.question,
                "answer": q.answer,
                "average_score": float(q.average_score) if q.average_score is not None else None,
                "difficulty": q.difficulty.value if q.difficulty else None,
                "strong_concepts": q.strong_concepts or [],
                "weak_concepts": q.weak_concepts or [],
                "feedback": getattr(q, "feedback", None),
            }
        )

    for topic in topics:
        topic.questions = questions_by_topic.get(topic.id, [])


def cancel_interview(interview_id: UUID, user_id: UUID | str | int) -> Interview:
    """
    Cancel an interview that is still processing.

    Only cancellable in states: UPLOADED, PROCESSING, TRANSCRIBING, ANALYZING.
    If already COMPLETED, FAILED, or CANCELLED, raises BadRequestException.
    """
    from app.shared.exceptions.custom_exceptions import (
        BadRequestException,
        ResourceNotFoundException,
    )

    session = SessionLocal()
    try:
        interview = session.query(Interview).filter(Interview.id == interview_id, Interview.user_id == user_id).first()

        if interview is None:
            raise ResourceNotFoundException(f"Interview {interview_id} not found")

        cancellable_states = {
            InterviewStatus.UPLOADED,
            InterviewStatus.PROCESSING,
            InterviewStatus.TRANSCRIBING,
            InterviewStatus.ANALYZING,
        }

        if interview.status not in cancellable_states:
            raise BadRequestException(
                f"Cannot cancel interview in status '{interview.status.value}'. "
                f"Only in-progress interviews can be cancelled."
            )

        interview.status = InterviewStatus.CANCELLED
        session.commit()

        logger.info(f"Interview {interview_id} cancelled")

        # Clean up temp files if they still exist
        video_file = (
            session.query(File)
            .filter(
                File.interview_id == interview_id,
                File.file_type == FileType.VIDEO,
            )
            .first()
        )
        if video_file and video_file.storage_path:
            try:
                if os.path.exists(video_file.storage_path):
                    os.remove(video_file.storage_path)
                    logger.info(f"Cleaned up video file: {video_file.storage_path}")
            except Exception as exc:
                logger.warning(f"Failed to clean up video file: {exc}")

        session.refresh(interview)
        return interview

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def check_duplicate_interview(
    user_id: UUID | str | int,
    fingerprint: str,
    db: Session,
) -> Interview | None:
    """
    Check if an interview with the same audio fingerprint already exists
    for this user (candidate).

    Args:
        user_id:     The user/candidate UUID to scope the check.
        fingerprint: The chromaprint audio fingerprint to match.
        db:          SQLAlchemy session.

    Returns:
        The matching Interview object if a duplicate is found, else None.
    """

    return (
        db.query(Interview)
        .filter(
            Interview.audio_fingerprint == fingerprint,
            Interview.user_id == user_id,
            Interview.status == InterviewStatus.COMPLETED,
        )
        .first()
    )
