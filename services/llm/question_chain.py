from __future__ import annotations

import logging
from typing import Any

from database.crud import get_assignment
from database.models import Submission

from services.llm.prompts import load_agent_config
from services.llm.schemas import QuestionAnswerSchema
from services.llm.utils import clamp_confidence, invoke_structured_llm, safe_json_dumps

logger = logging.getLogger(__name__)

VALID_ANSWERS = {"yes", "no", "uncertain"}

_FALLBACK: dict[str, Any] = {
    "answer": "uncertain",
    "confidence": None,
    "justification": "Question agent failed to produce a result.",
    "evidence": [],
}


def build_submission_context(db, submission_id: int) -> dict:
    """Load all relevant context for a submission from the database."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is None:
        raise ValueError(f"Submission {submission_id} not found")

    assignment = get_assignment(db, submission.assignment_id) if submission.assignment_id else None

    execution_runs = [
        {
            "test_case": run.test_case,
            "status": run.status,
            "exit_code": run.exit_code,
            "stdout": run.stdout,
            "stderr": run.stderr,
        }
        for run in submission.execution_runs
    ]

    evaluation_summary = None
    if submission.evaluation:
        evaluation_summary = {
            "final_score": submission.evaluation.final_score,
            "final_verdict": submission.evaluation.final_verdict,
            "debugger_report": submission.evaluation.debugger_report,
            "logic_report": submission.evaluation.logic_report,
            "quality_report": submission.evaluation.quality_report,
        }

    return {
        "assignment_text": (assignment.description or assignment.title) if assignment else "No assignment available",
        "student_code": submission.code or "",
        "execution_meta": execution_runs,
        "evaluation_summary": evaluation_summary,
    }


def ask_llm_question(db, submission_id: int, question_text: str) -> dict:
    """
    Answer a teacher's question about a student submission using the LLM.

    Returns a dict with keys: answer, confidence, justification, evidence.
    Always returns a stable shape even on LLM failure.
    """
    ctx = build_submission_context(db, submission_id)
    agent = load_agent_config("question.yaml", "question_agent")

    logger.info(
        "Running question chain (model=%s, submission_id=%s)",
        agent["model"], submission_id,
    )

    try:
        result = invoke_structured_llm(
            model=agent["model"],
            template=agent["prompt"],
            schema=QuestionAnswerSchema,
            variables={
                "assignment": ctx["assignment_text"],
                "student_code": ctx["student_code"],
                "execution_meta": safe_json_dumps(ctx["execution_meta"]),
                "evaluation_summary": safe_json_dumps(ctx["evaluation_summary"]),
                "question_text": question_text,
            },
        )
    except Exception:
        logger.exception(
            "Question chain failed for submission_id=%s — returning fallback",
            submission_id,
        )
        return dict(_FALLBACK)

    answer = str(result.get("answer", "uncertain")).strip().lower()
    if answer not in VALID_ANSWERS:
        answer = "uncertain"

    return {
        "answer": answer,
        "confidence": clamp_confidence(result.get("confidence")),
        "justification": result.get("justification"),
        "evidence": result.get("evidence", []),
    }