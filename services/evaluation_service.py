from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from database.crud import get_assignment
from database.models import EvaluationJob, Submission
from services.workspace_service import build_evaluation_workspace, cleanup_workspace


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _write_workspace_files(workspace_root: str, submission: Submission, assignment: Any) -> None:
    workspace_path = Path(workspace_root)

    (workspace_path / "Code" / "test.c").write_text(
        submission.code or "",
        encoding="utf-8",
    )

    assignment_text = "No assignment provided"
    if assignment is not None:
        assignment_text = assignment.description or assignment.title or ""

    (workspace_path / "Assignment" / "assignment.txt").write_text(
        assignment_text,
        encoding="utf-8",
    )

    if assignment is None:
        return

    for test_case in sorted(assignment.test_cases, key=lambda item: item.order):
        (workspace_path / "inputs" / f"test{test_case.order}.txt").write_text(
            test_case.input_text or "",
            encoding="utf-8",
        )
        (workspace_path / "expected" / f"expected{test_case.order}.txt").write_text(
            test_case.expected_output or "",
            encoding="utf-8",
        )


def run_evaluation_job(job_id: int, db) -> None:
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if job is None or job.submission_id is None:
        raise ValueError(f"Invalid evaluation job: {job_id}")

    submission = db.query(Submission).filter(Submission.id == job.submission_id).first()
    if submission is None:
        raise ValueError(f"Submission not found for job {job_id}")

    assignment = get_assignment(db, submission.assignment_id) if submission.assignment_id else None
    workspace_root = build_evaluation_workspace(str(PROJECT_ROOT), job_id)

    process: subprocess.CompletedProcess[str] | None = None

    try:
        _write_workspace_files(workspace_root, submission, assignment)

        env = {
            **os.environ,
            "SUBMISSION_ID_OVERRIDE": str(submission.id),
            "WORKSPACE_DIR": workspace_root,
        }

        process = subprocess.run(
            ["python3", "-m", "Agents.state"],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.stdout:
            logger.info("Evaluation stdout for submission %s:\n%s", submission.id, process.stdout[:4000])
        if process.stderr:
            logger.warning("Evaluation stderr for submission %s:\n%s", submission.id, process.stderr[:4000])

        if process.returncode != 0:
            raise RuntimeError(
                f"Evaluator failed for submission {submission.id}. "
                f"stderr: {process.stderr[:4000]}"
            )

    finally:
        keep_failed_workspace = os.environ.get("KEEP_FAILED_WORKSPACE", "0") == "1"
        should_cleanup = (
            process is None
            or process.returncode == 0
            or not keep_failed_workspace
        )

        if should_cleanup:
            cleanup_workspace(workspace_root)
        else:
            logger.warning("Preserving failed workspace: %s", workspace_root)