from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import (
    AdHocQuestionResult,
    AssignmentQuestion,
    SubmissionQuestionResult,
)


def create_assignment_question(
    db: Session,
    assignment_id: int,
    question_text: str,
) -> AssignmentQuestion:
    question = AssignmentQuestion(
        assignment_id=assignment_id,
        question_text=question_text,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def list_assignment_questions(db: Session, assignment_id: int) -> list[AssignmentQuestion]:
    return (
        db.query(AssignmentQuestion)
        .filter(AssignmentQuestion.assignment_id == assignment_id)
        .order_by(AssignmentQuestion.created_at.asc())
        .all()
    )


def save_submission_question_result(
    db: Session,
    submission_id: int,
    question_text: str,
    answer: str,
    confidence: float | None = None,
    justification: str | None = None,
    evidence: Any = None,
    assignment_question_id: int | None = None,
) -> SubmissionQuestionResult:
    result: Optional[SubmissionQuestionResult] = None

    if assignment_question_id is not None:
        result = (
            db.query(SubmissionQuestionResult)
            .filter(
                SubmissionQuestionResult.submission_id == submission_id,
                SubmissionQuestionResult.assignment_question_id == assignment_question_id,
            )
            .first()
        )

    if result is None:
        result = SubmissionQuestionResult(
            submission_id=submission_id,
            assignment_question_id=assignment_question_id,
        )
        db.add(result)

    result.question_text = question_text
    result.answer = answer
    result.confidence = confidence
    result.justification = justification
    result.evidence = evidence if evidence is not None else []

    db.commit()
    db.refresh(result)
    return result


def save_adhoc_question_result(
    db: Session,
    submission_id: int,
    question_text: str,
    answer: str,
    confidence: float | None = None,
    justification: str | None = None,
    evidence: Any = None,
) -> AdHocQuestionResult:
    result = AdHocQuestionResult(
        submission_id=submission_id,
        question_text=question_text,
        answer=answer,
        confidence=confidence,
        justification=justification,
        evidence=evidence if evidence is not None else [],
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_submission_question_results(
    db: Session,
    submission_id: int,
) -> list[SubmissionQuestionResult]:
    return (
        db.query(SubmissionQuestionResult)
        .filter(SubmissionQuestionResult.submission_id == submission_id)
        .order_by(SubmissionQuestionResult.answered_at.asc())
        .all()
    )


def get_submission_adhoc_results(
    db: Session,
    submission_id: int,
) -> list[AdHocQuestionResult]:
    return (
        db.query(AdHocQuestionResult)
        .filter(AdHocQuestionResult.submission_id == submission_id)
        .order_by(AdHocQuestionResult.asked_at.asc())
        .all()
    )