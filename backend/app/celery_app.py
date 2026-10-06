from celery import Celery
from celery.signals import worker_process_init

from app.core.config import settings
from app.shared.logger.logger import setup_logging

# Use the PostgreSQL database as a persistent backend so any connection can query task status
db_url = settings.DATABASE_URL
if not db_url.startswith("postgresql"):
    raise RuntimeError("DATABASE_URL must be a PostgreSQL connection string for the Celery result backend")

result_backend = "db+" + db_url

celery_app = Celery("interview_ai", broker=settings.BROKER_URL, backend=result_backend)

celery_app.conf.update(
    task_track_started=True,
    # Prevent celery_taskmeta from growing unboundedly
    result_expires=86400,  # 1 day
    # Hard per-task execution limits so a hung task cannot block a worker forever
    task_time_limit=3600,
    task_soft_time_limit=3540,
    imports=[
        "app.tasks.video_tasks",
        "app.tasks.transcription_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.pdf_tasks",
        "app.tasks.email_tasks",
    ],
)

celery_app.autodiscover_tasks(["app"])


@worker_process_init.connect
def configure_worker_logging(**kwargs):
    setup_logging()
