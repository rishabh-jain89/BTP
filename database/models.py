from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    plagiarism_status = Column(String, nullable=False, default="not_run")
    last_plagiarism_job_id = Column(
        Integer,
        ForeignKey("evaluation_jobs.id"),
        nullable=True,
    )

    test_cases = relationship(
        "TestCase",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )
    submissions = relationship(
        "Submission",
        back_populates="assignment",
        passive_deletes=True,
    )
    plagiarism_results = relationship(
        "PlagiarismResult",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )
    questions = relationship(
        "AssignmentQuestion",
        back_populates="assignment",
        cascade="all, delete-orphan",
    )


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(
        Integer,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    input_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    order = Column(Integer, nullable=False, default=1)

    assignment = relationship("Assignment", back_populates="test_cases")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    submissions = relationship(
        "Submission",
        primaryjoin="Student.roll_number == foreign(Submission.student_id)",
        viewonly=True,
    )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    assignment_id = Column(
        Integer,
        ForeignKey("assignments.id", ondelete="SET NULL"),
        nullable=True,
    )
    code = Column(Text, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    evaluation_status = Column(String, nullable=False, default="not_queued")
    last_job_id = Column(Integer, ForeignKey("evaluation_jobs.id"), nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship(
        "Student",
        primaryjoin="foreign(Submission.student_id) == Student.roll_number",
        viewonly=True,
    )
    evaluation = relationship(
        "EvaluationResult",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
    )
    execution_runs = relationship(
        "ExecutionRun",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    question_results = relationship(
        "SubmissionQuestionResult",
        back_populates="submission",
        cascade="all, delete-orphan",
    )
    adhoc_question_results = relationship(
        "AdHocQuestionResult",
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False)
    queue_name = Column(String, nullable=False)

    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=True,
    )
    assignment_id = Column(
        Integer,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=True,
    )

    status = Column(String, nullable=False, default="queued")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)

    celery_task_id = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    final_score = Column(Float, nullable=True)
    breakdown = Column(JSONB, nullable=True)
    penalties_applied = Column(JSONB, nullable=True)
    final_verdict = Column(Text, nullable=True)

    debugger_report = Column(JSONB, nullable=True)
    logic_report = Column(JSONB, nullable=True)
    quality_report = Column(JSONB, nullable=True)

    evaluated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    submission = relationship("Submission", back_populates="evaluation")


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_case = Column(String, nullable=False)
    status = Column(String, nullable=False)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="execution_runs")


class PlagiarismResult(Base):
    __tablename__ = "plagiarism_results"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(
        Integer,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id = Column(String, nullable=False)
    max_similarity_score = Column(Float, nullable=False)
    most_similar_to = Column(String, nullable=True)
    report_path = Column(String, nullable=True)
    checked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    assignment = relationship("Assignment", back_populates="plagiarism_results")


class AssignmentQuestion(Base):
    __tablename__ = "assignment_questions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(
        Integer,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    assignment = relationship("Assignment", back_populates="questions")
    results = relationship(
        "SubmissionQuestionResult",
        back_populates="assignment_question",
        cascade="all, delete-orphan",
    )


class SubmissionQuestionResult(Base):
    __tablename__ = "submission_question_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    assignment_question_id = Column(
        Integer,
        ForeignKey("assignment_questions.id", ondelete="CASCADE"),
        nullable=True,
    )

    question_text = Column(Text, nullable=False)
    answer = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    justification = Column(Text, nullable=True)
    evidence = Column(JSONB, nullable=True)
    answered_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    submission = relationship("Submission", back_populates="question_results")
    assignment_question = relationship("AssignmentQuestion", back_populates="results")


class AdHocQuestionResult(Base):
    __tablename__ = "adhoc_question_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_text = Column(Text, nullable=False)
    answer = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    justification = Column(Text, nullable=True)
    evidence = Column(JSONB, nullable=True)
    asked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    submission = relationship("Submission", back_populates="adhoc_question_results")