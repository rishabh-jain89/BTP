import os
import shutil
import asyncio
from typing import List, Optional

from fastapi import (
    FastAPI, HTTPException, Depends,
    UploadFile, File, Form, BackgroundTasks, Query,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.crud_jobs import (
    create_evaluation_job,
    create_plagiarism_job,
    set_job_celery_task_id,
)
from workers.evaluation_tasks import process_evaluation_job
from workers.plagiarism_tasks import process_plagiarism_job

from database.crud_questions import (
    create_assignment_question,
    list_assignment_questions,
    get_submission_question_results,
    get_submission_adhoc_results,
)
from workers.question_tasks import (
    process_assignment_question,
    process_adhoc_question,
)

from database.crud_jobs import get_job
from database.db import engine, get_db
from database import models
from database.crud import (
    get_all_submissions,
    get_submission_detail,
    get_analytics,
    get_assignment_analytics,
    save_submission,
    save_execution_runs,
    save_evaluation,
    create_assignment_with_test_cases,
    get_assignment,
    get_all_assignments,
    get_or_create_student,
    update_student_name,
    get_all_students,
    delete_student,
    get_submissions_by_assignment,
    get_submission_by_id,
    delete_assignment,
    delete_submission,
    get_plagiarism_results_by_assignment,
    save_plagiarism_results,
)
from api.schemas import (
    AssignmentCreate,
    AssignmentOut,
    TestCaseOut,
    BulkUploadResult,
    StudentOut,
    PlagiarismResultOut,
    DashboardStudent,
    DashboardResponse,
    CompareRequest,
    CompareResponse,
    AssignmentQuestionCreate,
    AssignmentQuestionOut,
    AdHocQuestionCreate,
)
from api.file_handlers import (
    extract_description_from_upload,
    process_zip_upload,
    save_submission_file,
    parse_student_csv,
)
from api.plagiarism_service import run_plagiarism_check, compare_two_files

# Create all tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="BTP Evaluation Lab API", version="2.0.0")

# Allow the React dev server (and any localhost port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════
#  Health
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
def health():
    return {"status": "ok", "message": "BTP Evaluation Lab API is running"}


# ═══════════════════════════════════════════════════════════════════════════
#  Analytics (original)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    """Class-wide aggregate stats for the dashboard."""
    return get_analytics(db)


# ═══════════════════════════════════════════════════════════════════════════
#  Submissions (original)
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/submissions")
def list_submissions(db: Session = Depends(get_db)):
    """Paginated list of all submissions with their grader summary."""
    return get_all_submissions(db)


@app.get("/submissions/{submission_id}")
def submission_detail(submission_id: int, db: Session = Depends(get_db)):
    """Full evaluation report (all 4 agent outputs) for a single submission."""
    detail = get_submission_detail(db, submission_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Submission not found")
    return detail


# ── Original /evaluate endpoint (backward compatible) ───────────────────

@app.post("/evaluate", status_code=202)
async def evaluate(
    student_id: str = Form(...),
    code: UploadFile = File(...),
    assignment: UploadFile = File(...),
    test_inputs: List[UploadFile] = File(...),
    expected_outputs: List[UploadFile] = File(...),
    assignment_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Handle single file uploads. Saves everything to DB and queues for evaluation.
    This replaces the 'standalone' behavior with a DB-backed one that syncs with the dashboard.
    """
    code_bytes = await code.read()
    code_str = code_bytes.decode()

    # 1. Create submission record
    sub_id = save_submission(
        db, 
        student_id=student_id, 
        code=code_str, 
        assignment_id=assignment_id
    )

    # 2. If no assignment_id provided, we still need to store the provided assignment/test files
    #    so the worker can find them. For now, we'll write them to legacy folders 
    #    BUT the plan is to link everything to dashboard assignments eventually.
    if not assignment_id:
        # Fallback to legacy file saving for non-linked evaluations
        code_dir = os.path.join(PROJECT_ROOT, "Code")
        os.makedirs(code_dir, exist_ok=True)
        with open(os.path.join(code_dir, "test.c"), "wb") as f:
            f.write(code_bytes)

        assignment_dir = os.path.join(PROJECT_ROOT, "Assignment")
        os.makedirs(assignment_dir, exist_ok=True)
        with open(os.path.join(assignment_dir, "assignment.txt"), "wb") as f:
            f.write(await assignment.read())

        inputs_dir = os.path.join(PROJECT_ROOT, "inputs")
        shutil.rmtree(inputs_dir, ignore_errors=True)
        os.makedirs(inputs_dir)
        for i, inp in enumerate(test_inputs, start=1):
            with open(os.path.join(inputs_dir, f"test{i}.txt"), "wb") as f:
                f.write(await inp.read())

        expected_dir = os.path.join(PROJECT_ROOT, "expected")
        shutil.rmtree(expected_dir, ignore_errors=True)
        os.makedirs(expected_dir)
        for i, exp in enumerate(expected_outputs, start=1):
            with open(os.path.join(expected_dir, f"expected{i}.txt"), "wb") as f:
                f.write(await exp.read())

    job = create_evaluation_job(db, sub_id)
    task = process_evaluation_job.apply_async(
        args=[job.id],
        queue="evaluation_queue",
        countdown=1
    )
    set_job_celery_task_id(db, job.id, task.id)

    return {
        "status": "queued",
        "message": f"Evaluation queued for '{student_id}'",
        "submission_id": sub_id,
        "job_id": job.id,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Assignments — CRUD
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/assignments", status_code=201)
def create_assignment_json(payload: AssignmentCreate, db: Session = Depends(get_db)):
    """
    Create a new assignment with inline test cases (JSON body).

    Example:
    {
      "title": "Linked List Assignment",
      "description": "Implement a singly-linked list...",
      "test_cases": [
        {"input_text": "1 2 3", "expected_output": "3 2 1"},
        {"input_text": "5", "expected_output": "5"}
      ]
    }
    """
    assignment = create_assignment_with_test_cases(
        db,
        title=payload.title,
        description=payload.description,
        test_cases=[tc.dict() for tc in payload.test_cases],
    )
    return _assignment_to_dict(assignment)


@app.post("/assignments/upload", status_code=201)
async def create_assignment_upload(
    title: str = Form(...),
    description_file: Optional[UploadFile] = File(None),
    description_text: Optional[str] = Form(None),
    test_inputs: List[str] = Form(...),
    test_outputs: List[str] = Form(...),
    db: Session = Depends(get_db),
):
    """
    Create an assignment with description from an uploaded PDF/TXT file or inline text,
    plus test cases as form fields.

    - `title`: Assignment title (required)
    - `description_file`: PDF or TXT file with the assignment prompt (optional)
    - `description_text`: Plain text description (optional, used if no file uploaded)
    - `test_inputs`: List of input strings
    - `test_outputs`: List of expected output strings (must match test_inputs length)
    """
    # Resolve description
    description = None
    if description_file:
        file_bytes = await description_file.read()
        description = extract_description_from_upload(description_file.filename, file_bytes)
    elif description_text:
        description = description_text

    if len(test_inputs) != len(test_outputs):
        raise HTTPException(
            status_code=400,
            detail=f"Mismatch: {len(test_inputs)} inputs vs {len(test_outputs)} outputs",
        )

    if len(test_inputs) == 0:
        raise HTTPException(status_code=400, detail="At least one test case is required")

    test_cases = [
        {"input_text": inp, "expected_output": out}
        for inp, out in zip(test_inputs, test_outputs)
    ]

    assignment = create_assignment_with_test_cases(
        db, title=title, description=description, test_cases=test_cases
    )
    return _assignment_to_dict(assignment)


@app.get("/assignments")
def list_assignments(db: Session = Depends(get_db)):
    """List all assignments with summary counts."""
    return get_all_assignments(db)


@app.get("/assignments/{assignment_id}")
def get_assignment_detail(assignment_id: int, db: Session = Depends(get_db)):
    """Get full assignment details including test cases."""
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return _assignment_to_dict(assignment)


def _assignment_to_dict(a) -> dict:
    """Convert Assignment ORM object to a JSON-safe dict."""
    return {
        "id": a.id,
        "title": a.title,
        "description": a.description,
        "created_at": a.created_at.isoformat(),
        "test_cases": [
            {
                "id": tc.id,
                "input_text": tc.input_text,
                "expected_output": tc.expected_output,
                "order": tc.order,
            }
            for tc in sorted(a.test_cases, key=lambda t: t.order)
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Bulk Upload — ZIP of roll_number.c files
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/assignments/{assignment_id}/upload-bulk", status_code=201)
async def upload_bulk(
    assignment_id: int,
    zip_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Accept a .zip file containing student submissions.

    Expected ZIP structure (flat):
    ```
    submissions.zip
    ├── 2021001.c
    ├── 2021002.c
    └── 2021003.c
    ```

    Each `.c` filename (without extension) is treated as the student's roll number.
    Files are stored under: /data/assignments/{id}/students/{roll_number}/test.c
    """
    # Validate assignment exists
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Validate file type
    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")

    zip_bytes = await zip_file.read()
    submissions, errors = process_zip_upload(zip_bytes, assignment_id, DATA_DIR)

    created_ids = []
    print(f"[Bulk Upload] Created submission IDs: {created_ids}")
    for sub in submissions:
        # Create or update student profile
        get_or_create_student(db, roll_number=sub["roll_number"])

        # Create submission record
        sub_id = save_submission(
            db,
            student_id=sub["roll_number"],
            code=sub["code"],
            assignment_id=assignment_id,
        )
        created_ids.append(sub_id)

    # Automatically queue all new submissions for sequential evaluation
    job_ids = []
    for sid in created_ids:
        print(f"[Bulk Upload] Queueing submission {sid}")
        job = create_evaluation_job(db, sid)
        task = process_evaluation_job.apply_async(
            args=[job.id],
            queue="evaluation_queue",
            countdown=1
        )
        set_job_celery_task_id(db, job.id, task.id)
        job_ids.append(job.id)

    return BulkUploadResult(
        total_extracted=len(submissions) + len(errors),
        submissions_created=len(created_ids),
        errors=errors,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Submissions by Assignment
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/assignments/{assignment_id}/submissions")
def assignment_submissions(assignment_id: int, db: Session = Depends(get_db)):
    """Retrieve all student submissions for a specific assignment."""
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = get_submissions_by_assignment(db, assignment_id)
    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "total": len(submissions),
        "submissions": submissions,
    }



@app.post("/assignments/{assignment_id}/run-plagiarism", status_code=202)
async def trigger_plagiarism_check(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Trigger a JPlag plagiarism check for all submissions in an assignment.
    The check runs in the background via the plagiarism queue.
    """
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    subs = get_submissions_by_assignment(db, assignment_id)
    if len(subs) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 2 submissions for plagiarism check, found {len(subs)}"
        )

    job = create_plagiarism_job(db, assignment_id)
    task = process_plagiarism_job.apply_async(
        args=[job.id],
        queue="plagiarism_queue"
    )
    set_job_celery_task_id(db, job.id, task.id)

    return {
        "status": "queued",
        "message": f"Plagiarism check queued for assignment {assignment_id}",
        "assignment_id": assignment_id,
        "job_id": job.id,
    }


@app.get("/assignments/{assignment_id}/plagiarism")
def get_plagiarism_results(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve plagiarism check results for an assignment.
    Returns per-student max similarity scores.
    """
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    results = get_plagiarism_results_by_assignment(db, assignment_id)
    return {
        "assignment_id": assignment_id,
        "assignment_title": assignment.title,
        "total_results": len(results),
        "results": results,
    }


@app.post("/plagiarism/compare", response_model=CompareResponse)
async def compare_two_snippets(payload: CompareRequest):
    """
    Compare two arbitrary code snippets using JPlag and return their similarity percentage.
    """
    try:
        similarity = await compare_two_files(payload.code1, payload.code2)
        return CompareResponse(similarity_score=similarity)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Plagiarism comparison failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
#  Assignment Dashboard — Grouped View
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/assignments/{assignment_id}/dashboard")
def assignment_dashboard(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Grouped view: all student profiles, evaluation status, scores,
    and plagiarism flags in one response.
    """
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = get_submissions_by_assignment(db, assignment_id)
    plagiarism = get_plagiarism_results_by_assignment(db, assignment_id)

    # Index plagiarism by student_id
    plag_map = {p["student_id"]: p for p in plagiarism}

    # Build student entries
    students = []
    evaluated_count = 0
    pending_count = 0

    # Also look up student names
    all_students = get_all_students(db)
    name_map = {s.roll_number: s.name for s in all_students}

    for sub in submissions:
        plag = plag_map.get(sub["student_id"])
        plag_score = plag["max_similarity_score"] if plag else None
        most_similar = plag["most_similar_to"] if plag else None

        # Determine plagiarism flag
        if plag_score is not None:
            if plag_score >= 70:
                plag_flag = "flagged"
            elif plag_score >= 40:
                plag_flag = "warning"
            else:
                plag_flag = "clean"
        else:
            plag_flag = "clean"

        is_evaluated = sub["status"] == "evaluated"
        if is_evaluated:
            evaluated_count += 1
        else:
            pending_count += 1

        students.append(DashboardStudent(
            student_id=sub["student_id"],
            student_name=name_map.get(sub["student_id"]),
            submission_id=sub["id"],
            submitted_at=sub["submitted_at"],
            evaluation_status=sub["status"],
            final_score=sub.get("final_score"),
            final_verdict=sub.get("final_verdict"),
            plagiarism_score=plag_score,
            most_similar_to=most_similar,
            plagiarism_flag=plag_flag,
        ))

    return DashboardResponse(
        assignment_id=assignment_id,
        assignment_title=assignment.title,
        total_students=len(students),
        total_submissions=len(submissions),
        evaluated_count=evaluated_count,
        pending_count=pending_count,
        plagiarism_checked=len(plagiarism) > 0,
        students=students,
    )


# ═══════════════════════════════════════════════════════════════════════════
#  Individual Evaluation Trigger
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/evaluate/individual/{submission_id}", status_code=202)
async def evaluate_individual(
    submission_id: int,
    db: Session = Depends(get_db),
):
    """
    Manually trigger the evaluation for a single submission using the sequential queue.
    """
    submission = get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    job = create_evaluation_job(db, submission_id)
    task = process_evaluation_job.apply_async(
        args=[job.id],
        queue="evaluation_queue",
        countdown=1
    )
    set_job_celery_task_id(db, job.id, task.id)

    return {
        "status": "queued",
        "message": f"Evaluation added to queue for submission {submission_id}",
        "submission_id": submission_id,
        "job_id": job.id,
    }


@app.post("/assignments/{assignment_id}/re-evaluate", status_code=202)
async def re_evaluate_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """
    Re-evaluate ALL submissions for an assignment.
    Creates fresh evaluation jobs and queues them sequentially.
    """
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    submissions = get_submissions_by_assignment(db, assignment_id)
    if not submissions:
        raise HTTPException(status_code=400, detail="No submissions found for this assignment")

    queued = []
    for sub in submissions:
        job = create_evaluation_job(db, sub["id"])
        task = process_evaluation_job.apply_async(
            args=[job.id],
            queue="evaluation_queue",
            countdown=1
        )
        set_job_celery_task_id(db, job.id, task.id)
        queued.append({"submission_id": sub["id"], "job_id": job.id})

    return {
        "status": "queued",
        "message": f"Re-evaluation queued for {len(queued)} submissions in assignment {assignment_id}",
        "assignment_id": assignment_id,
        "queued": queued,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Deletion — Assignments & Submissions
# ═══════════════════════════════════════════════════════════════════════════

@app.delete("/assignments/{assignment_id}/delete", status_code=200)
def delete_assignment_endpoint(assignment_id: int, db: Session = Depends(get_db)):
    """
    Delete an assignment, its test cases, all student submissions for it,
    and associated files on disk.
    """
    # 1. Remove files from disk
    assignment_path = os.path.join(DATA_DIR, "assignments", str(assignment_id))
    if os.path.exists(assignment_path):
        shutil.rmtree(assignment_path)

    # 2. Delete from database
    success = delete_assignment(db, assignment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")

    return {
        "status": "deleted",
        "message": f"Assignment {assignment_id} and all submission data removed.",
        "assignment_id": assignment_id,
    }


@app.delete("/submissions/{submission_id}/delete", status_code=200)
def delete_submission_endpoint(submission_id: int, db: Session = Depends(get_db)):
    """
    Delete a single submission and its files on disk.
    """
    submission = get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # 1. Remove files from organized storage if exists
    if submission.assignment_id:
        sub_path = os.path.join(
            DATA_DIR, "assignments", str(submission.assignment_id),
            "students", submission.student_id
        )
        if os.path.exists(sub_path):
            shutil.rmtree(sub_path)

    # 2. Delete from DB
    delete_submission(db, submission_id)

    return {
        "status": "deleted",
        "message": f"Submission {submission_id} removed.",
        "submission_id": submission_id,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Students — Management & Cleanup
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/students")
def list_students(db: Session = Depends(get_db)):
    """List all student profiles."""
    students = get_all_students(db)
    return [
        {
            "id": s.id,
            "roll_number": s.roll_number,
            "name": s.name,
            "created_at": s.created_at.isoformat(),
        }
        for s in students
    ]


@app.delete("/students/{roll_number}/delete", status_code=200)
def delete_student_endpoint(roll_number: str, db: Session = Depends(get_db)):
    """
    Delete a student and all their associated submissions, evaluations,
    execution runs, and files on disk.
    """
    # Remove files from organized storage
    student_data_pattern = os.path.join(DATA_DIR, "assignments")
    if os.path.exists(student_data_pattern):
        for assignment_dir in os.listdir(student_data_pattern):
            student_dir = os.path.join(
                student_data_pattern, assignment_dir, "students", roll_number
            )
            if os.path.exists(student_dir):
                shutil.rmtree(student_dir)

    # Delete from database (cascades to submissions → evaluations → runs)
    deleted = delete_student(db, roll_number)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Student '{roll_number}' not found")

    return {
        "status": "deleted",
        "message": f"Student '{roll_number}' and all associated data have been removed.",
        "roll_number": roll_number,
    }


@app.post("/students/upload-csv", status_code=200)
async def upload_student_csv(
    csv_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file with columns: roll_number, name.
    Updates existing student names or creates new profiles.

    Example CSV:
    ```
    roll_number,name
    2021001,Alice Johnson
    2021002,Bob Smith
    ```
    """
    if not csv_file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    file_bytes = await csv_file.read()
    try:
        rows = parse_student_csv(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    updated = 0
    created = 0
    for row in rows:
        existing = update_student_name(db, row["roll_number"], row["name"])
        if existing:
            updated += 1
        else:
            get_or_create_student(db, roll_number=row["roll_number"], name=row["name"])
            created += 1

    return {
        "status": "success",
        "total_processed": len(rows),
        "created": created,
        "updated": updated,
    }

@app.get("/jobs/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "job_type": job.job_type,
        "queue_name": job.queue_name,
        "submission_id": job.submission_id,
        "assignment_id": job.assignment_id,
        "status": job.status,
        "attempt_count": job.attempt_count,
        "max_attempts": job.max_attempts,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }

@app.post("/assignments/{assignment_id}/questions", status_code=201)
def add_assignment_question(
    assignment_id: int,
    payload: AssignmentQuestionCreate,
    db: Session = Depends(get_db),
):
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    q = create_assignment_question(db, assignment_id, payload.question_text)

    # Backfill for existing submissions
    submissions = get_submissions_by_assignment(db, assignment_id)
    queued_for = 0

    for sub in submissions:
        process_assignment_question.apply_async(
            args=[sub["id"], q.id, q.question_text],
            queue="question_queue",
        )
        queued_for += 1

    return {
        "id": q.id,
        "assignment_id": q.assignment_id,
        "question_text": q.question_text,
        "created_at": q.created_at.isoformat(),
        "queued_for_existing_submissions": queued_for,
    }

@app.get("/assignments/{assignment_id}/questions")
def get_assignment_questions(assignment_id: int, db: Session = Depends(get_db)):
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    questions = list_assignment_questions(db, assignment_id)
    return [
        {
            "id": q.id,
            "assignment_id": q.assignment_id,
            "question_text": q.question_text,
            "created_at": q.created_at.isoformat(),
        }
        for q in questions
    ]

@app.post("/submissions/{submission_id}/ask", status_code=202)
def ask_submission_question(
    submission_id: int,
    payload: AdHocQuestionCreate,
):
    task = process_adhoc_question.apply_async(
        args=[submission_id, payload.question_text],
        queue="question_queue",
    )
    return {
        "status": "queued",
        "submission_id": submission_id,
        "question_text": payload.question_text,
        "task_id": task.id,
    }

@app.get("/submissions/{submission_id}/questions")
def get_submission_questions(submission_id: int, db: Session = Depends(get_db)):
    results = get_submission_question_results(db, submission_id)
    return [
        {
            "id": r.id,
            "submission_id": r.submission_id,
            "question_text": r.question_text,
            "answer": r.answer,
            "confidence": r.confidence,
            "justification": r.justification,
            "evidence": r.evidence,
            "answered_at": r.answered_at.isoformat() if r.answered_at else None,
        }
        for r in results
    ]

@app.get("/submissions/{submission_id}/ask-history")
def get_submission_ask_history(submission_id: int, db: Session = Depends(get_db)):
    results = get_submission_adhoc_results(db, submission_id)
    return [
        {
            "id": r.id,
            "submission_id": r.submission_id,
            "question_text": r.question_text,
            "answer": r.answer,
            "confidence": r.confidence,
            "justification": r.justification,
            "evidence": r.evidence,
            "asked_at": r.asked_at.isoformat() if r.asked_at else None,
        }
        for r in results
    ]

@app.get("/assignments/{assignment_id}/analytics")
def assignment_analytics(assignment_id: int, db: Session = Depends(get_db)):
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    analytics = get_assignment_analytics(db, assignment_id)
    return analytics