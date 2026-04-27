from __future__ import annotations

import logging
from typing import Any

from services.llm.prompts import load_agent_config
from services.llm.schemas import QualitySchema
from services.llm.utils import invoke_structured_llm

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, Any] = {
    "quality_score": None,
    "issues": ["Quality agent failed to produce a result."],
    "suggestions": [],
}


def run_quality_chain(assignment_text: str, student_code: str) -> dict:
    """Assess code quality, style, and best practices."""
    agent = load_agent_config("quality.yaml", "quality_agent")

    logger.info("Running quality chain (model=%s)", agent["model"])
    try:
        return invoke_structured_llm(
            model=agent["model"],
            template=agent["prompt"],
            schema=QualitySchema,
            variables={
                "assignment": assignment_text,
                "student_code": student_code,
            },
        )
    except Exception:
        logger.exception("Quality chain failed — returning fallback")
        return dict(_FALLBACK)