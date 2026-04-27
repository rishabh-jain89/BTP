import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from database.models import (
    Assignment,
    EvaluationResult,
    ExecutionRun,
    PlagiarismResult,
    Student,
    Submission,
    TestCase,
)


def _serialize_submission_summary(submission: Submission) -> dict[str, Any]:
    evaluation = submission.evaluation
    return {
        "id": submission.id,
        "student_id": submission.student_id,
        "assignment_id": submission.assignment_id,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "final_score": evaluation.final_score if evaluation else None,
        "final_verdict": evaluation.final_verdict if evaluation else None,
        "status": submission.evaluation_status,
    }


def _ensure_json_compatible(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {"raw": value}
    return value


def save_submission(
    db: Session,
    student_id: str,
    code: str,
    assignment_id: int | None = None,
) -> int:
    submission = Submission(
        student_id=student_id,
        code=code,
        assignment_id=assignment_id,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission.id


def save_execution_runs(db: Session, submission_id: int, execution_meta: dict[str, dict[str, Any]]) -> None:
    db.query(ExecutionRun).filter(ExecutionRun.submission_id == submission_id).delete()
    db.flush()

    for test_case, result in execution_meta.items():
        run = ExecutionRun(
            submission_id=submission_id,
            test_case=test_case,
            status=result.get("status", "unknown"),
            exit_code=result.get("exit_code"),
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
        )
        db.add(run)

    db.commit()


def save_evaluation(db: Session, submission_id: int, state: dict[str, Any]) -> EvaluationResult:
    grader_report = state.get("grader_report", {})

    evaluation = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.submission_id == submission_id)
        .first()
    )

    if evaluation is None:
        evaluation = EvaluationResult(submission_id=submission_id)
        db.add(evaluation)

    evaluation.final_score = grader_report.get("final_score")
    evaluation.breakdown = grader_report.get("breakdown")
    evaluation.penalties_applied = grader_report.get("penalties_applied")
    evaluation.final_verdict = grader_report.get("final_verdict")
    evaluation.debugger_report = _ensure_json_compatible(state.get("debugger_report"))
    evaluation.logic_report = _ensure_json_compatible(state.get("logic_report"))
    evaluation.quality_report = _ensure_json_compatible(state.get("quality_report"))

    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_all_submissions(db: Session) -> list[dict[str, Any]]:
    submissions = db.query(Submission).order_by(Submission.submitted_at.desc()).all()
    return [_serialize_submission_summary(submission) for submission in submissions]


def get_submission_detail(db: Session, submission_id: int) -> Optional[dict[str, Any]]:
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        return None

    evaluation = submission.evaluation
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

    return {
        "id": submission.id,
        "student_id": submission.student_id,
        "assignment_id": submission.assignment_id,
        "code": submission.code,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
        "execution_runs": execution_runs,
        "evaluation": (
            {
                "final_score": evaluation.final_score,
                "breakdown": evaluation.breakdown,
                "penalties_applied": evaluation.penalties_applied,
                "final_verdict": evaluation.final_verdict,
                "debugger_report": evaluation.debugger_report,
                "logic_report": evaluation.logic_report,
                "quality_report": evaluation.quality_report,
            }
            if evaluation
            else None
        ),
    }


def get_analytics(db: Session) -> dict[str, Any]:
    submissions = db.query(Submission).all()
    total_submissions = len(submissions)

    scores = [
        submission.evaluation.final_score
        for submission in submissions
        if submission.evaluation and submission.evaluation.final_score is not None
    ]

    average_score = round(sum(scores) / len(scores), 2) if scores else 0
    pass_count = sum(1 for score in scores if score >= 5)

    penalty_counts: dict[str, int] = {}
    for submission in submissions:
        if not submission.evaluation or not submission.evaluation.penalties_applied:
            continue

        for penalty in submission.evaluation.penalties_applied:
            penalty_counts[penalty] = penalty_counts.get(penalty, 0) + 1

    score_distribution = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
    for score in scores:
        if score < 2:
            score_distribution["0-2"] += 1
        elif score < 4:
            score_distribution["2-4"] += 1
        elif score < 6:
            score_distribution["4-6"] += 1
        elif score < 8:
            score_distribution["6-8"] += 1
        else:
            score_distribution["8-10"] += 1

    return {
        "total_submissions": total_submissions,
        "evaluated": len(scores),
        "pending": total_submissions - len(scores),
        "avg_score": average_score,
        "pass_count": pass_count,
        "pass_rate": round((pass_count / len(scores)) * 100, 1) if scores else 0,
        "score_distribution": score_distribution,
        "common_penalties": sorted(
            penalty_counts.items(),
            key=lambda item: -item[1],
        )[:10],
    }


def create_assignment(db: Session, title: str, description: str | None = None) -> Assignment:
    assignment = Assignment(title=title, description=description)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_test_case(
    db: Session,
    assignment_id: int,
    input_text: str,
    expected_output: str,
    order: int = 1,
) -> TestCase:
    test_case = TestCase(
        assignment_id=assignment_id,
        input_text=input_text,
        expected_output=expected_output,
        order=order,
    )
    db.add(test_case)
    db.commit()
    db.refresh(test_case)
    return test_case


def create_assignment_with_test_cases(
    db: Session,
    title: str,
    description: str | None,
    test_cases: list[dict[str, Any]],
) -> Assignment:
    assignment = Assignment(title=title, description=description)
    db.add(assignment)
    db.flush()

    for index, test_case in enumerate(test_cases, start=1):
        db.add(
            TestCase(
                assignment_id=assignment.id,
                input_text=test_case["input_text"],
                expected_output=test_case["expected_output"],
                order=index,
            )
        )

    db.commit()
    db.refresh(assignment)
    return assignment


def get_assignment(db: Session, assignment_id: int) -> Optional[Assignment]:
    return db.query(Assignment).filter(Assignment.id == assignment_id).first()


def get_all_assignments(db: Session) -> list[dict[str, Any]]:
    assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).all()
    return [
        {
            "id": assignment.id,
            "title": assignment.title,
            "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
            "test_case_count": len(assignment.test_cases),
            "submission_count": len(assignment.submissions),
        }
        for assignment in assignments
    ]


def delete_assignment(db: Session, assignment_id: int) -> bool:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return False

    for submission in list(assignment.submissions):
        db.delete(submission)

    db.delete(assignment)
    db.commit()
    return True


def get_or_create_student(db: Session, roll_number: str, name: str | None = None) -> Student:
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if student:
        if name and not student.name:
            student.name = name
            db.commit()
            db.refresh(student)
        return student

    student = Student(roll_number=roll_number, name=name)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student_name(db: Session, roll_number: str, name: str) -> Optional[Student]:
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not student:
        return None

    student.name = name
    db.commit()
    db.refresh(student)
    return student


def get_all_students(db: Session) -> list[Student]:
    return db.query(Student).order_by(Student.roll_number).all()


def delete_student(db: Session, roll_number: str) -> bool:
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not student:
        return False

    submissions = db.query(Submission).filter(Submission.student_id == roll_number).all()
    for submission in submissions:
        db.delete(submission)

    db.delete(student)
    db.commit()
    return True


def get_submissions_by_assignment(db: Session, assignment_id: int) -> list[dict[str, Any]]:
    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id)
        .order_by(Submission.student_id, Submission.submitted_at.desc())
        .all()
    )
    return [_serialize_submission_summary(submission) for submission in submissions]


def get_submission_by_id(db: Session, submission_id: int) -> Optional[Submission]:
    return db.query(Submission).filter(Submission.id == submission_id).first()


def delete_submission(db: Session, submission_id: int) -> bool:
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        return False

    db.delete(submission)
    db.commit()
    return True


def save_plagiarism_results(
    db: Session,
    assignment_id: int,
    results: list[dict[str, Any]],
    report_path: str | None = None,
) -> list[PlagiarismResult]:
    db.query(PlagiarismResult).filter(
        PlagiarismResult.assignment_id == assignment_id
    ).delete()
    db.flush()

    created_results: list[PlagiarismResult] = []
    for result in results:
        plagiarism_result = PlagiarismResult(
            assignment_id=assignment_id,
            student_id=result["student_id"],
            max_similarity_score=result["max_similarity_score"],
            most_similar_to=result.get("most_similar_to"),
            report_path=report_path,
        )
        db.add(plagiarism_result)
        created_results.append(plagiarism_result)

    db.commit()

    for plagiarism_result in created_results:
        db.refresh(plagiarism_result)

    return created_results


def get_plagiarism_results_by_assignment(db: Session, assignment_id: int) -> list[dict[str, Any]]:
    results = (
        db.query(PlagiarismResult)
        .filter(PlagiarismResult.assignment_id == assignment_id)
        .order_by(PlagiarismResult.max_similarity_score.desc())
        .all()
    )

    return [
        {
            "id": result.id,
            "student_id": result.student_id,
            "max_similarity_score": result.max_similarity_score,
            "most_similar_to": result.most_similar_to,
            "report_path": result.report_path,
            "checked_at": result.checked_at.isoformat() if result.checked_at else None,
        }
        for result in results
    ]


def delete_plagiarism_results(db: Session, assignment_id: int) -> int:
    deleted_count = (
        db.query(PlagiarismResult)
        .filter(PlagiarismResult.assignment_id == assignment_id)
        .delete()
    )
    db.commit()
    return deleted_count

def _normalize_issue(raw: str) -> str:
    """Map a verbose LLM-generated issue string to a short standard category.

    The LLM produces unique descriptions for every submission. This function
    normalizes them into ~20 canonical buckets so the analytics charts show
    aggregated, readable categories instead of unique one-off strings.
    """
    s = raw.lower().strip()

    # Memory
    if any(kw in s for kw in ("memory leak", "malloc", "free(", "not freed", "dealloc")):
        return "Memory Leak"
    if any(kw in s for kw in ("buffer overflow", "out of bounds", "array bounds", "overflow")):
        return "Buffer Overflow"
    if any(kw in s for kw in ("null pointer", "null dereference", "segfault", "segmentation")):
        return "Null Pointer"
    if any(kw in s for kw in ("uninitialized", "uninitialised")):
        return "Uninitialized Variable"

    # Input / Output
    if any(kw in s for kw in ("scanf", "input validation", "input handling", "user input")):
        return "Unsafe Input (scanf)"
    if any(kw in s for kw in ("hardcod", "hard-cod", "hard cod")):
        return "Hardcoded Values"
    if any(kw in s for kw in ("edge case", "boundary", "corner case")):
        return "Missing Edge Cases"
    if any(kw in s for kw in ("error handling", "error check", "return value check")):
        return "Missing Error Handling"

    # Logic
    if any(kw in s for kw in ("infinite loop", "infinite recursion")):
        return "Infinite Loop"
    if any(kw in s for kw in ("off-by-one", "off by one", "fencepost")):
        return "Off-by-One Error"
    if any(kw in s for kw in ("wrong output", "incorrect output", "output mismatch")):
        return "Wrong Output"
    if any(kw in s for kw in ("logic error", "logical error", "incorrect logic")):
        return "Logic Error"

    # Code Quality
    if any(kw in s for kw in ("naming", "variable name", "function name", "readability")):
        return "Poor Naming"
    if any(kw in s for kw in ("comment", "documentation", "doc")):
        return "Missing Comments"
    if any(kw in s for kw in ("magic number",)):
        return "Magic Numbers"
    if any(kw in s for kw in ("indentation", "formatting", "whitespace", "style")):
        return "Formatting Issues"
    if any(kw in s for kw in ("modular", "function decomposition", "code structure")):
        return "Poor Structure"

    # Compilation
    if any(kw in s for kw in ("compilation", "compile error", "syntax error", "won't compile")):
        return "Compilation Error"
    if any(kw in s for kw in ("timeout", "time limit", "tle")):
        return "Timeout"
    if any(kw in s for kw in ("runtime error", "crash", "abort")):
        return "Runtime Error"

    # Fallback: take just the first 24 chars
    cleaned = raw.strip()
    if len(cleaned) > 24:
        cleaned = cleaned[:24].rstrip() + "…"
    return cleaned


def get_assignment_analytics(db: Session, assignment_id: int) -> dict:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        return None

    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id)
        .all()
    )

    total = len(submissions)
    evaluated_submissions = [s for s in submissions if s.evaluation is not None]
    scores = [
        s.evaluation.final_score
        for s in evaluated_submissions
        if s.evaluation.final_score is not None
    ]

    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    pass_count = sum(1 for s in scores if s >= 5)

    buckets = {"0-2": 0, "2-4": 0, "4-6": 0, "6-8": 0, "8-10": 0}
    for score in scores:
        if score < 2:
            buckets["0-2"] += 1
        elif score < 4:
            buckets["2-4"] += 1
        elif score < 6:
            buckets["4-6"] += 1
        elif score < 8:
            buckets["6-8"] += 1
        else:
            buckets["8-10"] += 1

    penalty_counts = {}
    verdict_counts = {}
    debugger_counts = {}
    logic_issue_counts = {}
    quality_issue_counts = {}

    for submission in evaluated_submissions:
        ev = submission.evaluation

        if ev.final_verdict:
            verdict_counts[ev.final_verdict] = verdict_counts.get(ev.final_verdict, 0) + 1

        if ev.penalties_applied:
            for penalty in ev.penalties_applied:
                label = _normalize_issue(penalty)
                penalty_counts[label] = penalty_counts.get(label, 0) + 1

        if isinstance(ev.debugger_report, dict):
            err = ev.debugger_report.get("error_type") or ev.debugger_report.get("category")
            if err:
                label = _normalize_issue(str(err))
                debugger_counts[label] = debugger_counts.get(label, 0) + 1

        if isinstance(ev.logic_report, dict):
            issues = ev.logic_report.get("issues", [])
            if isinstance(issues, list):
                for issue in issues:
                    label = _normalize_issue(str(issue))
                    logic_issue_counts[label] = logic_issue_counts.get(label, 0) + 1

        if isinstance(ev.quality_report, dict):
            issues = ev.quality_report.get("issues", [])
            if isinstance(issues, list):
                for issue in issues:
                    label = _normalize_issue(str(issue))
                    quality_issue_counts[label] = quality_issue_counts.get(label, 0) + 1

    return {
        "assignment_id": assignment.id,
        "assignment_title": assignment.title,
        "total_submissions": total,
        "evaluated": len(scores),
        "pending": total - len(scores),
        "avg_score": avg_score,
        "pass_count": pass_count,
        "pass_rate": round(pass_count / len(scores) * 100, 1) if scores else 0,
        "score_distribution": buckets,
        "common_penalties": sorted(penalty_counts.items(), key=lambda x: -x[1])[:10],
        "verdict_breakdown": sorted(verdict_counts.items(), key=lambda x: -x[1]),
        "debugger_mistakes": sorted(debugger_counts.items(), key=lambda x: -x[1])[:10],
        "logic_mistakes": sorted(logic_issue_counts.items(), key=lambda x: -x[1])[:10],
        "quality_mistakes": sorted(quality_issue_counts.items(), key=lambda x: -x[1])[:10],
    }