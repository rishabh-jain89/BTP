from __future__ import annotations

import logging
from typing import Any

from services.llm.prompts import load_agent_config
from services.llm.schemas import GraderSchema
from services.llm.utils import invoke_structured_llm, safe_json_dumps

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, Any] = {
    "final_score": None,
    "breakdown": {},
    "penalties_applied": [],
    "final_verdict": "Grader agent failed to produce a result.",
}


def run_grader_chain(
    assignment_text: str,
    debugger_report: Any,
    logic_report: Any,
    quality_report: Any,
    total_marks: int = 10,
) -> dict:
    """Assign a final grade based on the three specialist reports."""
    agent = load_agent_config("grader.yaml", "grader_agent")

    logger.info("Running grader chain (model=%s)", agent["model"])
    try:
        return invoke_structured_llm(
            model=agent["model"],
            template=agent["prompt"],
            schema=GraderSchema,
            variables={
                "assignment": assignment_text,
                "debugger_report": safe_json_dumps(debugger_report),
                "logic_report": safe_json_dumps(logic_report),
                "quality_report": safe_json_dumps(quality_report),
                "total_marks": total_marks,
            },
        )
    except Exception:
        logger.exception("Grader chain failed — returning fallback")
        return dict(_FALLBACK)