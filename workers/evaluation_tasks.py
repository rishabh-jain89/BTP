import logging

from workers.celery_app import celery_app
from database.db import SessionLocal
from database.models import EvaluationJob
from database.crud import get_submission_by_id
from database.crud_jobs import mark_job_completed, mark_job_failed, mark_job_running
from database.crud_questions import list_assignment_questions
from services.evaluation_service import run_evaluation_job
from workers.question_tasks import process_assignment_question


logger = logging.getLogger(__name__)


def _enqueue_assignment_questions_for_submission(db, submission_id: int) -> int:
    submission = get_submission_by_id(db, submission_id)
    if submission is None or submission.assignment_id is None:
        return 0

    questions = list_assignment_questions(db, submission.assignment_id)
    queued_count = 0

    for question in questions:
        process_assignment_question.apply_async(
            args=[submission.id, question.id, question.question_text],
            queue="question_queue",
        )
        queued_count += 1

    return queued_count


@celery_app.task(bind=True, name="workers.evaluation_tasks.process_evaluation_job")
def process_evaluation_job(self, job_id: int):
    db = SessionLocal()
    try:
        job = mark_job_running(db, job_id)
        if job is None:
            logger.warning("Skipping evaluation job_id=%s (not found)", job_id)
            return {
                "job_id": job_id,
                "status": "skipped",
                "reason": "job_not_found",
            }

        run_evaluation_job(job_id, db)

        job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
        queued_questions = 0

        if job and job.submission_id:
            try:
                queued_questions = _enqueue_assignment_questions_for_submission(db, job.submission_id)
            except Exception:
                logger.exception(
                    "Evaluation succeeded but assignment-question enqueue failed for job_id=%s",
                    job_id,
                )
                raise

        mark_job_completed(db, job_id)

        logger.info(
            "Completed evaluation job_id=%s, queued_questions=%s",
            job_id,
            queued_questions,
        )
        return {
            "job_id": job_id,
            "status": "completed",
            "queued_questions": queued_questions,
        }

    except ValueError as exc:
        logger.warning("Evaluation task failed for job_id=%s: %s", job_id, exc)
        mark_job_failed(db, job_id, str(exc))
        return {
            "job_id": job_id,
            "status": "failed",
            "reason": str(exc),
        }
    except Exception as exc:
        logger.exception("Evaluation task failed for job_id=%s", job_id)
        mark_job_failed(db, job_id, str(exc))
        raise
    finally:
        db.close()