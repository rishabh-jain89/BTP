from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TestCaseIn(BaseModel):
    input_text: str = Field(..., description="Input string for the test case")
    expected_output: str = Field(..., description="Expected output string")


class TestCaseOut(ORMModel):
    id: int
    input_text: str
    expected_output: str
    order: int


class AssignmentCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Assignment title")
    description: str | None = Field(None, description="Assignment description / problem statement")
    test_cases: list[TestCaseIn] = Field(
        ...,
        min_length=1,
        description="At least one test case is required",
    )


class AssignmentOut(ORMModel):
    id: int
    title: str
    description: str | None
    test_cases: list[TestCaseOut]
    created_at: datetime


class AssignmentSummary(ORMModel):
    id: int
    title: str
    created_at: datetime
    test_case_count: int
    submission_count: int


class StudentOut(ORMModel):
    id: int
    roll_number: str
    name: str | None
    created_at: datetime


class StudentCSVRow(BaseModel):
    roll_number: str
    name: str


class SubmissionOut(ORMModel):
    id: int
    student_id: str
    assignment_id: int | None
    submitted_at: datetime
    status: str
    final_score: float | None


class BulkUploadResult(BaseModel):
    total_extracted: int
    submissions_created: int
    errors: list[str] = Field(default_factory=list)


class PlagiarismResultOut(ORMModel):
    id: int
    student_id: str
    max_similarity_score: float
    most_similar_to: str | None
    report_path: str | None
    checked_at: datetime | None


class DashboardStudent(BaseModel):
    student_id: str
    student_name: str | None = None
    submission_id: int | None = None
    submitted_at: str | None = None
    evaluation_status: str = "no_submission"
    final_score: float | None = None
    final_verdict: str | None = None
    plagiarism_score: float | None = None
    most_similar_to: str | None = None
    plagiarism_flag: str = "clean"


class DashboardResponse(BaseModel):
    assignment_id: int
    assignment_title: str
    total_students: int
    total_submissions: int
    evaluated_count: int
    pending_count: int
    plagiarism_checked: bool
    students: list[DashboardStudent]


class CompareRequest(BaseModel):
    code1: str
    code2: str


class CompareResponse(BaseModel):
    similarity_score: float


class AssignmentQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)


class AssignmentQuestionOut(ORMModel):
    id: int
    assignment_id: int
    question_text: str
    created_at: datetime


class AdHocQuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)


class QuestionAnswerOut(ORMModel):
    id: int
    submission_id: int
    question_text: str
    answer: str
    confidence: float | None = None
    justification: str | None = None
    evidence: list[Any] | None = None
    answered_at: datetime | None = None