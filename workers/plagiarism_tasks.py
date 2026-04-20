import logging

from workers.celery_app import celery_app
from database.db import SessionLocal
from database.crud_jobs import mark_job_completed, mark_job_failed, mark_job_running
from services.plagiarism_runner import run_plagiarism_job


logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="workers.plagiarism_tasks.process_plagiarism_job")
def process_plagiarism_job(self, job_id: int):
    db = SessionLocal()
    try:
        mark_job_running(db, job_id)
        run_plagiarism_job(job_id, db)
        mark_job_completed(db, job_id)

        logger.info("Completed plagiarism job_id=%s", job_id)
        return {"job_id": job_id, "status": "completed"}

    except Exception as exc:
        logger.exception("Plagiarism task failed for job_id=%s", job_id)
        mark_job_failed(db, job_id, str(exc))
        raise
    finally:
        db.close()