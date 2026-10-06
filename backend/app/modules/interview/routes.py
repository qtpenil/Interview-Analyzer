import io
import re
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.rate_limiter import limiter
from app.core.security import get_current_user
from app.modules.interview import service as interview_service
from app.modules.interview.schemas import (
    InterviewCancelResponse,
    InterviewDetailResponse,
    InterviewListResponse,
    InterviewStatusResponse,
    InterviewUploadResponse,
)
from app.modules.user.UserModel import User
from app.shared.exceptions.custom_exceptions import ResourceNotFoundException
from app.shared.logger.logger import get_logger
from app.shared.response_handler.responseSchema import SuccessResponse
from app.tasks.video_tasks import process_video_to_audio

logger = get_logger(__name__)

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _sanitize_filename(name: str) -> str:
    """Remove invalid characters and limit length for safe filenames."""
    # Remove path separators and other problematic characters
    safe = re.sub(r'[\\/:*?"<>|]', "_", name)
    # Limit length (keep reasonable for filesystem compatibility)
    return safe[:200]


def _get_user_display_name(session: Session, user_id: str | int) -> str:
    """Get a user-friendly display name for the PDF filename.

    Prefers user.name, falls back to email prefix (before @).
    """
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            if user.name:
                return user.name.strip()
            if user.email:
                return user.email.split("@")[0]
    except Exception:
        pass
    return "interview"


@router.get(
    "/{interview_id}/report",
    summary="Download PDF report",
)
@limiter.limit("30/minute")
async def get_interview_report(
    request: Request,
    interview_id: str,
    current_user_id: str | int = Depends(get_current_user),
):
    """
    Download the generated PDF report for a completed interview.
    """
    pdf_bytes = interview_service.get_interview_report_path(
        UUID(interview_id),
        current_user_id,
    )

    # Fetch the user to build a username-based filename
    session = SessionLocal()
    try:
        safe_name = _sanitize_filename(_get_user_display_name(session, current_user_id))
    finally:
        session.close()

    filename = f"interview-report-{safe_name}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/upload",
    response_model=SuccessResponse[InterviewUploadResponse],
)
@limiter.limit("10/hour")
async def upload_interview(
    request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    claimed_experience_years: float | None = Form(default=None),
    current_user_id: str | int = Depends(get_current_user),
):
    """
    Upload an interview video and start the processing pipeline.

    1. Saves the video to storage/uploads/ (cleaned after processing)
    2. Creates an Interview record (status = UPLOADED)
    3. Dispatches the Celery pipeline task
    4. Returns immediately with interview_id for polling
    """

    # Save uploaded video to disk
    video_path = interview_service.save_video_file(file)

    if not title and file.filename:
        title = file.filename

    # Create interview record in DB
    interview = interview_service.create_interview(
        video_path=video_path,
        user_id=current_user_id,
        title=title,
        claimed_experience_years=claimed_experience_years,
    )

    # Dispatch Celery pipeline
    process_video_to_audio.delay(
        str(interview.id),
        video_path,
    )

    logger.info(f"Interview {interview.id} uploaded, pipeline dispatched")

    return SuccessResponse(
        message="Interview uploaded successfully",
        data=InterviewUploadResponse(
            interview_id=str(interview.id),
            status=interview.status.value,
        ),
    )


@router.post(
    "/{interview_id}/cancel",
    response_model=SuccessResponse[InterviewCancelResponse],
)
@limiter.limit("10/minute")
async def cancel_interview(
    request: Request,
    interview_id: str,
    current_user_id: str | int = Depends(get_current_user),
):
    """
    Cancel an interview that is still processing.

    Sets status to CANCELLED and cleans up temp files.
    Only works for interviews in: UPLOADED, PROCESSING, TRANSCRIBING, ANALYZING.
    """

    interview = interview_service.cancel_interview(
        UUID(interview_id),
        current_user_id,
    )

    logger.info(f"Interview {interview_id} cancelled by user")

    return SuccessResponse(
        message="Interview cancelled successfully",
        data=InterviewCancelResponse(
            interview_id=str(interview.id),
            status=interview.status.value,
            message="Interview cancelled successfully",
        ),
    )


@router.get(
    "/{interview_id}/status",
    response_model=SuccessResponse[InterviewStatusResponse],
)
@limiter.limit("120/minute")
async def get_interview_status(
    request: Request,
    interview_id: str,
    current_user_id: str | int = Depends(get_current_user),
):
    """
    Get the current processing status of an interview.
    """

    interview = interview_service.get_interview_status(
        UUID(interview_id),
        current_user_id,
    )

    return SuccessResponse(
        message="Interview status retrieved successfully",
        data=InterviewStatusResponse(
            interview_id=str(interview.id),
            status=interview.status.value,
            processing_started_at=interview.processing_started_at,
            processing_completed_at=interview.processing_completed_at,
            claimed_experience_years=(
                float(interview.claimed_experience_years) if interview.claimed_experience_years is not None else None
            ),
            overall_score=(float(interview.overall_score) if interview.overall_score is not None else None),
            technical_score=(float(interview.technical_score) if interview.technical_score is not None else None),
            communication_score=(
                float(interview.communication_score) if interview.communication_score is not None else None
            ),
            confidence_score=(float(interview.confidence_score) if interview.confidence_score is not None else None),
            knowledge_depth=(float(interview.knowledge_depth) if interview.knowledge_depth is not None else None),
            experience_alignment_score=(
                float(interview.experience_alignment_score)
                if interview.experience_alignment_score is not None
                else None
            ),
            hiring_decision=(interview.hiring_decision.value if interview.hiring_decision is not None else None),
            ai_model_name=interview.ai_model_name,
            ai_model_version=interview.ai_model_version,
            failure_reason=interview.failure_reason,
        ),
    )


@router.get("/list", response_model=SuccessResponse[InterviewListResponse])
@limiter.limit("60/minute")
async def list_interviews(
    request: Request,
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: str | int = Depends(get_current_user),
):
    result = interview_service.list_interviews_for_user(
        db=db,
        user_id=current_user_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return SuccessResponse(message="Interviews fetched successfully", data=result)


@router.get("/{interview_id}", response_model=SuccessResponse[InterviewDetailResponse])
@limiter.limit("60/minute")
async def get_interview_detail(
    request: Request,
    interview_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str | int = Depends(get_current_user),
):
    interview = interview_service.get_interview_with_details(db, interview_id, current_user_id)

    if not interview:
        raise ResourceNotFoundException("Interview not found")
    return SuccessResponse(
        message="Interview details fetched successfully",
        data=InterviewDetailResponse.model_validate(interview),
    )
