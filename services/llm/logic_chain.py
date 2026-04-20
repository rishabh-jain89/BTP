from __future__ import annotations

import logging
from typing import Any

from services.llm.prompts import load_agent_config
from services.llm.schemas import LogicSchema
from services.llm.utils import invoke_structured_llm, safe_json_dumps

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, Any] = {
    "verdict": "uncertain",
    "issues": ["Logic agent failed to produce a result."],
    "reasoning": None,
}


def run_logic_chain(
    assignment_text: str,
    student_code: str,
    execution_meta: dict,
    expected_outputs: dict,
) -> dict:
    """Evaluate logical correctness of the student submission."""
    agent = load_agent_config("logic.yaml", "logic_agent")

    logger.info("Running logic chain (model=%s)", agent["model"])
    try:
        return invoke_structured_llm(
            model=agent["model"],
            template=agent["prompt"],
            schema=LogicSchema,
            variables={
                "assignment": assignment_text,
                "student_code": student_code,
                "actual_output": safe_json_dumps(execution_meta),
                "expected_output": safe_json_dumps(expected_outputs),
            },
        )
    except Exception:
        logger.exception("Logic chain failed — returning fallback")
        return dict(_FALLBACK)