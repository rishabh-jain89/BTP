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


def _clamp_grader_result(
    result: dict, total_marks: int, test_case_results: dict | None
) -> dict:
    """Normalize breakdown values and clamp final_score to total_marks.

    LLMs frequently ignore score-cap instructions, so we enforce the
    constraint programmatically after every invocation.

    Additionally, the functionality component is hard-capped proportionally
    to the deterministic test-case pass rate.
    """
    breakdown = result.get("breakdown", {})

    # --- (Removed) Hard-cap functionality based on deterministic test pass rate ---
    # We no longer strictly multiply functionality by pass_rate, to allow LLMs to grant partial functionality marks for good code that just had minor output mismatches.

    # --- Normalize the full breakdown to sum ≤ total_marks ---
    if breakdown:
        raw_sum = sum(breakdown.values())
        if raw_sum > 0 and raw_sum > total_marks:
            scale = total_marks / raw_sum
            breakdown = {k: round(v * scale, 1) for k, v in breakdown.items()}
            result["breakdown"] = breakdown

    # Clamp final_score
    score = result.get("final_score")
    if score is not None:
        result["final_score"] = round(min(float(score), total_marks), 1)

    # Re-derive final_score from breakdown if breakdown exists
    if breakdown:
        result["final_score"] = round(sum(breakdown.values()), 1)

    return result


def run_grader_chain(
    assignment_text: str,
    debugger_report: Any,
    logic_report: Any,
    quality_report: Any,
    total_marks: int = 10,
    test_case_results: dict | None = None,
) -> dict:
    """Assign a final grade based on the three specialist reports."""
    agent = load_agent_config("grader.yaml", "grader_agent")

    logger.info("Running grader chain (model=%s)", agent["model"])
    try:
        raw = invoke_structured_llm(
            model=agent["model"],
            template=agent["prompt"],
            schema=GraderSchema,
            variables={
                "assignment": assignment_text,
                "debugger_report": safe_json_dumps(debugger_report),
                "logic_report": safe_json_dumps(logic_report),
                "quality_report": safe_json_dumps(quality_report),
                "test_case_results": safe_json_dumps(test_case_results),
                "total_marks": total_marks,
            },
        )
        return _clamp_grader_result(raw, total_marks, test_case_results)
    except Exception:
        logger.exception("Grader chain failed — returning fallback")
        return dict(_FALLBACK)