from __future__ import annotations

import logging

from workers.celery_app import celery_app
from database.db import SessionLocal
from database.crud import get_submission_by_id
from database.crud_questions import (
    save_adhoc_question_result,
    save_submission_question_result,
)
from services.llm.question_chain import ask_llm_question

logger = logging.getLogger(__name__)


def _get_submission(db, submission_id: int):
    return get_submission_by_id(db, submission_id)


@celery_app.task(bind=True, name="workers.question_tasks.process_assignment_question")
def process_assignment_question(self, submission_id: int, question_id: int, question_text: str):
    db = SessionLocal()
    try:
        submission = _get_submission(db, submission_id)
        if submission is None:
            logger.warning(
                "Skipping assignment question: submission_id=%s not found",
                submission_id,
            )
            return {
                "submission_id": submission_id,
                "question_id": question_id,
                "status": "skipped",
                "reason": "submission_not_found",
            }

        result = ask_llm_question(db, submission_id, question_text)

        save_submission_question_result(
            db=db,
            submission_id=submission_id,
            assignment_question_id=question_id,
            question_text=question_text,
            answer=result["answer"],
            confidence=result.get("confidence"),
            justification=result.get("justification"),
            evidence=result.get("evidence"),
        )

        logger.info(
            "Completed assignment question processing for submission_id=%s, question_id=%s",
            submission_id,
            question_id,
        )
        return {
            "submission_id": submission_id,
            "question_id": question_id,
            "status": "completed",
        }
    except Exception as exc:
        logger.exception(
            "Assignment question task failed for submission_id=%s, question_id=%s",
            submission_id,
            question_id,
        )
        raise exc
    finally:
        db.close()


@celery_app.task(bind=True, name="workers.question_tasks.process_adhoc_question")
def process_adhoc_question(self, submission_id: int, question_text: str):
    db = SessionLocal()
    try:
        submission = _get_submission(db, submission_id)
        if submission is None:
            logger.warning(
                "Skipping ad-hoc question: submission_id=%s not found",
                submission_id,
            )
            return {
                "submission_id": submission_id,
                "status": "skipped",
                "reason": "submission_not_found",
            }

        result = ask_llm_question(db, submission_id, question_text)

        saved_result = save_adhoc_question_result(
            db=db,
            submission_id=submission_id,
            question_text=question_text,
            answer=result["answer"],
            confidence=result.get("confidence"),
            justification=result.get("justification"),
            evidence=result.get("evidence"),
        )

        logger.info(
            "Completed ad-hoc question processing for submission_id=%s, result_id=%s",
            submission_id,
            saved_result.id,
        )
        return {
            "submission_id": submission_id,
            "result_id": saved_result.id,
            "status": "completed",
        }
    except Exception as exc:
        logger.exception(
            "Ad-hoc question task failed for submission_id=%s",
            submission_id,
        )
        raise exc
    finally:
        db.close()