from __future__ import annotations

import logging
from typing import Any

from services.llm.prompts import load_agent_config
from services.llm.schemas import DebuggerSchema
from services.llm.utils import invoke_structured_llm, safe_json_dumps

logger = logging.getLogger(__name__)

_FALLBACK: dict[str, Any] = {
    "error_type": "unknown",
    "explanation": "Debugger agent failed to produce a result.",
    "suggestion": None,
}


def run_debugger_chain(
    student_code: str,
    execution_meta: dict,
    test_inputs: list[str],
) -> dict:
    """Analyse sandbox failures and produce a technical error breakdown."""
    numbered_code = "\n".join(
        f"{index + 1}: {line}"
        for index, line in enumerate(student_code.splitlines())
    )

    test_cases: dict[str, str] = {}
    for index, test_path in enumerate(sorted(test_inputs), start=1):
        with open(test_path, "r", encoding="utf-8") as file_obj:
            test_cases[f"Test Case {index}"] = file_obj.read()

    agent = load_agent_config("debugger.yaml", "debugger-agent")

    logger.info("Running debugger chain (model=%s)", agent["model"])
    try:
        return invoke_structured_llm(
            model=agent["model"],
            template=agent["prompt"],
            schema=DebuggerSchema,
            variables={
                "student_code": numbered_code,
                "sandbox_results": safe_json_dumps(execution_meta),
                "test_cases": safe_json_dumps(test_cases),
            },
        )
    except Exception:
        logger.exception("Debugger chain failed — returning fallback")
        return dict(_FALLBACK)