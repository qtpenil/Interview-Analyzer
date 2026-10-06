import re
from datetime import UTC, datetime
from uuid import UUID

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.integration.pdf.service import interview_pdf_service
from app.modules.files.file import File
from app.modules.files.schema import FileType
from app.modules.interview.InterviewModel import Interview, InterviewStatus
from app.modules.user.UserModel import User
from app.shared.db.status_updater import is_interview_cancelled, update_interview_status
from app.shared.logger.logger import get_logger
from app.shared.storage.service import save_file

logger = get_logger(__name__)


def _sanitize_filename(name: str) -> str:
    """Remove invalid characters and limit length for safe filenames."""
    if not isinstance(name, str):
        name = str(name)
    safe = re.sub(r'[\\/:*?"<>|]', "_", name)
    return safe[:200]


def _get_user_display_name(session, user_id: UUID) -> str:
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


@celery_app.task(bind=True, max_retries=2)
def generate_pdf_report(self, interview_id: str, state_dict: dict) -> dict:
    """
    Celery task: Generate PDF report from LangGraph state.

    Pipeline step 4/4:
        LangGraph state → PDF file

    We do NOT persist the AI output to the database.

    Final step — sets status to COMPLETED on success.
    """

    try:
        logger.info(f"[{interview_id}] >>> TASK generate_pdf_report STARTED")

        if is_interview_cancelled(interview_id):
            logger.info(f"[{interview_id}] Interview cancelled, aborting PDF generation")
            return {"interview_id": interview_id, "status": "cancelled"}

        logger.info(f"[{interview_id}] Generating PDF report")

        # Generate PDF
        pdf_buffer = interview_pdf_service.generate(interview_id, state_dict)

        logger.info(f"[{interview_id}] PDF generated")

        # Get interview title and user for descriptive filename
        session = SessionLocal()
        try:
            interview = session.query(Interview).filter(Interview.id == UUID(interview_id)).first()
            if interview:
                user_display_name = _get_user_display_name(session, interview.user_id)
                safe_name = _sanitize_filename(user_display_name)
                report_path = f"reports/interview/{interview_id}/interview-report-{safe_name}.pdf"
            else:
                report_path = f"reports/interview/{interview_id}/interview-report-{interview_id}.pdf"
        finally:
            session.close()

        file_size = pdf_buffer.getbuffer().nbytes

        saved_path = save_file(
            file_obj=pdf_buffer,
            path=report_path,
            content_type="application/pdf",
        )

        # Save PDF file metadata
        session = SessionLocal()
        try:
            pdf_file = (
                session.query(File)
                .filter(
                    File.interview_id == UUID(interview_id),
                    File.file_type == FileType.SUMMARY_PDF,
                )
                .first()
            )

            if not pdf_file:
                pdf_file = File(
                    interview_id=UUID(interview_id),  # type: ignore[arg-type]  # uuid.UUID vs sqlalchemy _UUID_RETURN
                    file_type=FileType.SUMMARY_PDF,
                )
                session.add(pdf_file)

            pdf_file.storage_provider = "local"
            pdf_file.storage_path = saved_path
            pdf_file.file_size = file_size

            session.commit()
            logger.info(f"[{interview_id}] PDF report metadata saved to database")
        except Exception as e:
            session.rollback()
            logger.exception(f"[{interview_id}] Failed to save PDF metadata: {e}")
        finally:
            session.close()

        # Update status to COMPLETED
        update_interview_status(
            interview_id,
            InterviewStatus.COMPLETED,
            processing_completed_at=datetime.now(UTC),
        )

        return {
            "interview_id": interview_id,
            "status": "completed",
            "pdf_path": saved_path,
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            update_interview_status(
                interview_id,
                InterviewStatus.FAILED,
            )
        logger.exception(f"[{interview_id}] PDF generation failed: {exc}")
        raise self.retry(exc=exc)
