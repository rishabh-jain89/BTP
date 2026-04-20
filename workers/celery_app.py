from celery import Celery
from kombu import Queue

from core.config import settings


celery_app = Celery(
    "btp_eval",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("evaluation_queue"),
        Queue("plagiarism_queue"),
        Queue("question_queue"),
    ),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)