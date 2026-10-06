from app.celery_app import celery_app
from app.integration.langGraph.interviewGraph import interview_graph_runner
from app.modules.interview.InterviewModel import InterviewStatus
from app.shared.db.status_updater import (
    is_interview_cancelled,
    save_interview_analysis_results,
    update_interview_status,
)
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=2)
def analyze_transcript(self, interview_id: str, transcript: list[dict] | dict | None) -> dict:
    """
    Celery task: Analyze transcript via LangGraph pipeline.

    Pipeline step 3/4:
        transcript → metadata extraction → QA assessment →
        topic aggregation → interview summary

    On success, chains to PDF generation task.
    """

    try:
        logger.info(f"[{interview_id}] >>> TASK analyze_transcript STARTED")

        if is_interview_cancelled(interview_id):
            logger.info(f"[{interview_id}] Interview cancelled, aborting analysis")
            return {"interview_id": interview_id, "status": "cancelled"}

        update_interview_status(
            interview_id,
            InterviewStatus.ANALYZING,
        )

        logger.info(f"[{interview_id}] Starting LangGraph analysis")

        state_dict = interview_graph_runner.run(transcript, interview_id=interview_id)

        logger.info(
            f"[{interview_id}] LangGraph analysis complete. Decision: {state_dict.get('hiring_decision', 'N/A')}"
        )

        # Save analysis results to database
        save_interview_analysis_results(interview_id, state_dict)

        # Chain to next task
        from app.tasks.pdf_tasks import generate_pdf_report

        generate_pdf_report.delay(interview_id, state_dict)

        return {
            "interview_id": interview_id,
            "status": "analysis_complete",
            "hiring_decision": state_dict.get("hiring_decision"),
        }

    except Exception as exc:
        if self.request.retries >= self.max_retries:
            update_interview_status(
                interview_id,
                InterviewStatus.FAILED,
            )
        logger.exception(f"[{interview_id}] Analysis failed: {exc}")
        raise self.retry(exc=exc)
