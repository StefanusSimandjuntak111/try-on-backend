"""Celery application configuration."""

from celery import Celery

from app.config import settings
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "tryon_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Task routing
    task_routes={
        "app.workers.tasks.preprocess_model_task": {"queue": "preprocessing"},
        "app.workers.tasks.preprocess_garment_task": {"queue": "preprocessing"},
        "app.workers.tasks.tryon_inference_task": {"queue": "inference"},
        "app.workers.tasks.cleanup_old_files_task": {"queue": "maintenance"},
    },
    # Task retry configuration
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3, "countdown": 60},
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes
    task_retry_jitter=True,
)

logger.info("Celery app configured", broker=settings.CELERY_BROKER_URL)

