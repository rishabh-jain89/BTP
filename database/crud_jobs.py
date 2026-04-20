from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database.models import Assignment, EvaluationJob, Submission


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_job(db: Session, job_id: int) -> Optional[EvaluationJob]:
    return db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()


def _sync_parent_status(db: Session, job: EvaluationJob) -> None:
    if job.job_type == "evaluation" and job.submission_id:
        submission = db.query(Submission).filter(Submission.id == job.submission_id).first()
        if submission:
            submission.last_job_id = job.id
            if job.status == "queued":
                submission.evaluation_status = "queued"
            elif job.status == "running":
                submission.evaluation_status = "running"
            elif job.status == "completed":
                submission.evaluation_status = "evaluated"
            elif job.status == "failed":
                submission.evaluation_status = "failed"

    elif job.job_type == "plagiarism" and job.assignment_id:
        assignment = db.query(Assignment).filter(Assignment.id == job.assignment_id).first()
        if assignment:
            assignment.last_plagiarism_job_id = job.id
            if job.status == "queued":
                assignment.plagiarism_status = "queued"
            elif job.status == "running":
                assignment.plagiarism_status = "running"
            elif job.status == "completed":
                assignment.plagiarism_status = "completed"
            elif job.status == "failed":
                assignment.plagiarism_status = "failed"


def _create_job(
    db: Session,
    *,
    job_type: str,
    queue_name: str,
    submission_id: int | None = None,
    assignment_id: int | None = None,
) -> EvaluationJob:
    job = EvaluationJob(
        job_type=job_type,
        queue_name=queue_name,
        submission_id=submission_id,
        assignment_id=assignment_id,
        status="queued",
    )
    db.add(job)
    db.flush()

    _sync_parent_status(db, job)

    db.commit()
    db.refresh(job)
    return job


def create_evaluation_job(db: Session, submission_id: int) -> EvaluationJob:
    return _create_job(
        db,
        job_type="evaluation",
        queue_name="evaluation_queue",
        submission_id=submission_id,
    )


def create_plagiarism_job(db: Session, assignment_id: int) -> EvaluationJob:
    return _create_job(
        db,
        job_type="plagiarism",
        queue_name="plagiarism_queue",
        assignment_id=assignment_id,
    )


def mark_job_running(db: Session, job_id: int) -> Optional[EvaluationJob]:
    job = _get_job(db, job_id)
    if not job:
        return None

    now = utcnow()
    job.status = "running"
    job.attempt_count += 1
    job.started_at = now
    job.updated_at = now

    _sync_parent_status(db, job)

    db.commit()
    db.refresh(job)
    return job


def mark_job_completed(db: Session, job_id: int) -> Optional[EvaluationJob]:
    job = _get_job(db, job_id)
    if not job:
        return None

    now = utcnow()
    job.status = "completed"
    job.finished_at = now
    job.updated_at = now
    job.error_message = None

    _sync_parent_status(db, job)

    db.commit()
    db.refresh(job)
    return job


def mark_job_failed(db: Session, job_id: int, error_message: str) -> Optional[EvaluationJob]:
    job = _get_job(db, job_id)
    if not job:
        return None

    now = utcnow()
    job.status = "failed"
    job.finished_at = now
    job.updated_at = now
    job.error_message = error_message[:4000] if error_message else "Unknown failure"

    _sync_parent_status(db, job)

    db.commit()
    db.refresh(job)
    return job


def set_job_celery_task_id(
    db: Session,
    job_id: int,
    celery_task_id: str,
) -> Optional[EvaluationJob]:
    job = _get_job(db, job_id)
    if not job:
        return None

    job.celery_task_id = celery_task_id
    job.updated_at = utcnow()

    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: int) -> Optional[EvaluationJob]:
    return _get_job(db, job_id)