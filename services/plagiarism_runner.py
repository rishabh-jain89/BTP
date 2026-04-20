from __future__ import annotations

import asyncio

from database.models import EvaluationJob
from api.plagiarism_service import run_plagiarism_check


def run_plagiarism_job(job_id: int, db) -> None:
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if job is None or job.assignment_id is None:
        raise ValueError(f"Invalid plagiarism job: {job_id}")

    asyncio.run(run_plagiarism_check(job.assignment_id, db))