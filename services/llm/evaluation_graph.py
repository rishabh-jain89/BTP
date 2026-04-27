from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from database.crud import save_evaluation, save_execution_runs
from database.db import SessionLocal
from sandboxed_environment.sandboxNode import runSandbox
from services.llm.debugger_chain import run_debugger_chain
from services.llm.logic_chain import run_logic_chain
from services.llm.quality_chain import run_quality_chain
from services.llm.grader_chain import run_grader_chain

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
#  State definition
# ---------------------------------------------------------------------------


class EvaluationState(TypedDict):
    student_code: str
    student_code_path: str
    test_inputs: list[str]
    execution_meta: dict[str, Any]
    expected_outputs: dict[str, str]
    problem_statement: str
    debugger_report: Any
    logic_report: dict[str, Any] | None
    quality_report: dict[str, Any] | None
    grader_report: dict[str, Any] | None
    needs_debugger: bool
    test_case_results: dict[str, Any] | None


# ---------------------------------------------------------------------------
#  Workspace path resolution
# ---------------------------------------------------------------------------


def get_workspace_paths() -> dict[str, str]:
    workspace_dir = os.environ.get("WORKSPACE_DIR")

    if workspace_dir:
        workspace_path = Path(workspace_dir)
        return {
            "code_path": str(workspace_path / "Code" / "test.c"),
            "input_dir": str(workspace_path / "inputs"),
            "expected_dir": str(workspace_path / "expected"),
            "assignment_path": str(workspace_path / "Assignment" / "assignment.txt"),
        }

    return {
        "code_path": str(PROJECT_ROOT / "Code" / "test.c"),
        "input_dir": str(PROJECT_ROOT / "inputs"),
        "expected_dir": str(PROJECT_ROOT / "expected"),
        "assignment_path": str(PROJECT_ROOT / "Assignment" / "assignment.txt"),
    }


# ---------------------------------------------------------------------------
#  Graph nodes
# ---------------------------------------------------------------------------


def load_data_node(state: EvaluationState) -> EvaluationState:
    """Read student code, test inputs, expected outputs, and the assignment."""
    paths = get_workspace_paths()

    code_path = Path(paths["code_path"])
    input_dir = Path(paths["input_dir"])
    expected_dir = Path(paths["expected_dir"])
    assignment_path = Path(paths["assignment_path"])

    for label, path in [
        ("Code file", code_path),
        ("Input directory", input_dir),
        ("Expected directory", expected_dir),
        ("Assignment file", assignment_path),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"{label} not found: {path}")

    inputs = sorted(str(input_dir / name) for name in os.listdir(input_dir))
    expected_outputs: dict[str, str] = {}

    for index, filename in enumerate(sorted(os.listdir(expected_dir)), start=1):
        with (expected_dir / filename).open("r", encoding="utf-8") as file_obj:
            expected_outputs[f"Expected {index}"] = file_obj.read()

    logger.info(
        "Loaded data: code=%s, inputs=%d, expected=%d",
        code_path.name, len(inputs), len(expected_outputs),
    )

    return {
        **state,
        "student_code": code_path.read_text(encoding="utf-8"),
        "student_code_path": str(code_path),
        "test_inputs": inputs,
        "expected_outputs": expected_outputs,
        "problem_statement": assignment_path.read_text(encoding="utf-8"),
    }


def sandbox_node(state: EvaluationState) -> EvaluationState:
    """Execute student code in the Docker sandbox."""
    logger.info("Running sandbox for %s", state["student_code_path"])

    execution_meta = runSandbox(
        code_path=state["student_code_path"],
        inputs=state["test_inputs"],
    )

    needs_debugger = any(
        test_result.get("exit_code", 1) != 0
        for test_result in execution_meta.values()
    )

    logger.info(
        "Sandbox complete: %d test cases, needs_debugger=%s",
        len(execution_meta), needs_debugger,
    )

    return {
        **state,
        "execution_meta": execution_meta,
        "needs_debugger": needs_debugger,
    }


def debugger_node(state: EvaluationState) -> EvaluationState:
    """Run the debugger chain on failed test cases."""
    logger.info("Entering debugger node")
    debugger_report = run_debugger_chain(
        student_code=state["student_code"],
        execution_meta=state["execution_meta"],
        test_inputs=state["test_inputs"],
    )
    return {
        **state,
        "debugger_report": debugger_report,
    }


def skip_debugger_node(state: EvaluationState) -> EvaluationState:
    """Skip debugging when all test cases pass."""
    logger.info("Skipping debugger — no failures detected")
    return {
        **state,
        "debugger_report": {"message": "No technical errors detected."},
    }


def logic_node(state: EvaluationState) -> EvaluationState:
    """Run the logic evaluation chain."""
    logger.info("Entering logic node")
    logic_report = run_logic_chain(
        assignment_text=state["problem_statement"],
        student_code=state["student_code"],
        execution_meta=state["execution_meta"],
        expected_outputs=state["expected_outputs"],
    )
    return {
        **state,
        "logic_report": logic_report,
    }


def quality_node(state: EvaluationState) -> EvaluationState:
    """Run the code quality chain."""
    logger.info("Entering quality node")
    quality_report = run_quality_chain(
        assignment_text=state["problem_statement"],
        student_code=state["student_code"],
    )
    return {
        **state,
        "quality_report": quality_report,
    }


def compare_outputs_node(state: EvaluationState) -> EvaluationState:
    """Deterministically compare actual stdout against expected outputs.

    This is the AUTHORITATIVE test-case pass/fail check.  We do NOT rely
    on the LLM to do string comparison — it's unreliable.
    """
    execution_meta = state["execution_meta"]
    expected_outputs = state["expected_outputs"]

    results: list[dict[str, Any]] = []
    passed = 0
    total = 0

    for idx, (test_key, test_data) in enumerate(
        sorted(execution_meta.items()), start=1
    ):
        expected_key = f"Expected {idx}"
        expected = expected_outputs.get(expected_key, "").strip()
        actual = (test_data.get("stdout") or "").strip()
        match = actual == expected
        if match:
            passed += 1
        total += 1
        results.append({
            "test_case": test_key,
            "expected": expected,
            "actual": actual,
            "passed": match,
        })

    summary = {
        "passed": passed,
        "total": total,
        "pass_rate": round(passed / total, 2) if total > 0 else 0.0,
        "details": results,
    }

    logger.info(
        "Output comparison: %d/%d test cases passed (%.0f%%)",
        passed, total, summary["pass_rate"] * 100,
    )

    return {
        **state,
        "test_case_results": summary,
    }


def grader_node(state: EvaluationState) -> EvaluationState:
    """Run the grader chain to produce a final score."""
    logger.info("Entering grader node")
    grader_report = run_grader_chain(
        assignment_text=state["problem_statement"],
        debugger_report=state["debugger_report"],
        logic_report=state["logic_report"],
        quality_report=state["quality_report"],
        test_case_results=state.get("test_case_results"),
        total_marks=10,
    )
    return {
        **state,
        "grader_report": grader_report,
    }


# ---------------------------------------------------------------------------
#  Conditional routing
# ---------------------------------------------------------------------------


def debugger_router(state: EvaluationState) -> str:
    route = "debugger" if state.get("needs_debugger") else "skip_debugger"
    logger.info("Debugger router decision: %s", route)
    return route


# ---------------------------------------------------------------------------
#  Graph construction
# ---------------------------------------------------------------------------


def build_graph():
    """Build and compile the evaluation LangGraph."""
    graph = StateGraph(EvaluationState)

    graph.add_node("load_data", load_data_node)
    graph.add_node("sandbox", sandbox_node)
    graph.add_node("debugger", debugger_node)
    graph.add_node("skip_debugger", skip_debugger_node)
    graph.add_node("logic", logic_node)
    graph.add_node("quality", quality_node)
    graph.add_node("grader", grader_node)

    graph.set_entry_point("load_data")
    graph.add_edge("load_data", "sandbox")
    graph.add_conditional_edges(
        "sandbox",
        debugger_router,
        {
            "debugger": "debugger",
            "skip_debugger": "skip_debugger",
        },
    )
    graph.add_edge("debugger", "logic")
    graph.add_edge("skip_debugger", "logic")
    graph.add_node("compare_outputs", compare_outputs_node)

    graph.add_edge("logic", "quality")
    graph.add_edge("quality", "compare_outputs")
    graph.add_edge("compare_outputs", "grader")
    graph.add_edge("grader", END)

    return graph.compile()


# ---------------------------------------------------------------------------
#  Public entry points
# ---------------------------------------------------------------------------


def run_evaluation_graph() -> dict:
    """Execute the full evaluation graph and return the final state."""
    logger.info("Starting evaluation graph")

    graph = build_graph()

    initial_state: EvaluationState = {
        "student_code": "",
        "student_code_path": "",
        "test_inputs": [],
        "execution_meta": {},
        "expected_outputs": {},
        "problem_statement": "",
        "debugger_report": None,
        "logic_report": None,
        "quality_report": None,
        "grader_report": None,
        "needs_debugger": False,
        "test_case_results": None,
    }

    final_state = graph.invoke(initial_state)
    logger.info("Evaluation graph completed successfully")
    return final_state


def persist_results(state: dict) -> None:
    """Save evaluation results to the database."""
    submission_id_env = os.environ.get("SUBMISSION_ID_OVERRIDE")
    if not submission_id_env:
        raise ValueError("SUBMISSION_ID_OVERRIDE is required for evaluation persistence")

    submission_id = int(submission_id_env)

    db = SessionLocal()
    try:
        save_execution_runs(db, submission_id, state["execution_meta"])
        save_evaluation(db, submission_id, state)
        logger.info("Persisted evaluation results for submission_id=%s", submission_id)
    finally:
        db.close()


def main() -> None:
    """CLI entry point: run the full evaluation pipeline and persist results."""
    final_state = run_evaluation_graph()
    persist_results(final_state)


if __name__ == "__main__":
    main()