from typing import Any, Optional
from pydantic import BaseModel, Field


class QuestionAnswerSchema(BaseModel):
    answer: str = Field(description="One of: yes, no, uncertain")
    confidence: Optional[float] = Field(default=None, description="Confidence between 0 and 1")
    justification: Optional[str] = None
    evidence: list[Any] = Field(default_factory=list)


class DebuggerSchema(BaseModel):
    error_type: Optional[str] = None
    explanation: str
    suggestion: Optional[str] = None


class LogicSchema(BaseModel):
    verdict: str
    issues: list[str] = Field(default_factory=list)
    reasoning: Optional[str] = None


class QualitySchema(BaseModel):
    quality_score: Optional[float] = None
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class GraderSchema(BaseModel):
    final_score: Optional[float] = Field(None, description="The overall final score. Must NOT exceed the total_marks parameter.")
    breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Must contain exactly the keys: 'functionality', 'logic', 'efficiency', 'quality'. The sum of these values MUST exactly equal the final_score."
    )
    penalties_applied: list[str] = Field(default_factory=list)
    final_verdict: str