from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from database.crud import save_plagiarism_results
from database.models import Submission

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JPLAG_JAR = PROJECT_ROOT / "tools" / "jplag.jar"
JPLAG_LANGUAGE = "cpp"
JPLAG_MIN_TOKEN_MATCH = "5"


def prepare_jplag_directory(assignment_id: int, db: Session) -> str:
    jplag_dir = DATA_DIR / "temp_jplag" / str(assignment_id)

    if jplag_dir.exists():
        shutil.rmtree(jplag_dir)
    jplag_dir.mkdir(parents=True, exist_ok=True)

    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id)
        .all()
    )

    if len(submissions) < 2:
        raise ValueError(
            f"Need at least 2 submissions for plagiarism check, found {len(submissions)}"
        )

    for submission in submissions:
        student_dir = jplag_dir / submission.student_id
        student_dir.mkdir(parents=True, exist_ok=True)
        (student_dir / "code.c").write_text(submission.code or "", encoding="utf-8")

    logger.info("Prepared %d submissions for assignment %s", len(submissions), assignment_id)
    return str(jplag_dir)


async def _run_jplag_on_directory(input_dir: Path, output_dir: Path) -> Path:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    result_base = output_dir / "result"
    result_zip = output_dir / "result.zip"

    cmd = [
        "java",
        "-jar",
        str(JPLAG_JAR),
        str(input_dir),
        "-l",
        JPLAG_LANGUAGE,
        "-r",
        str(result_base),
        "-t",
        JPLAG_MIN_TOKEN_MATCH,
    ]

    logger.info("Running JPlag: %s", " ".join(cmd))

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
    )
    stdout, stderr = await process.communicate()

    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")

    if process.returncode != 0:
        raise RuntimeError(
            f"JPlag failed with exit code {process.returncode}. "
            f"stderr: {stderr_text[:2000]}"
        )

    if stdout_text.strip():
        logger.debug("JPlag stdout: %s", stdout_text[:1000])
    if stderr_text.strip():
        logger.debug("JPlag stderr: %s", stderr_text[:1000])

    if result_zip.exists():
        extract_dir = output_dir / "extracted"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(result_zip, "r") as zip_file:
            zip_file.extractall(extract_dir)

    return output_dir


def _extract_comparisons(data: dict[str, Any], student_max: dict[str, dict[str, Any]]) -> None:
    for key in ("comparisons", "top_comparisons", "topComparisons", "matches"):
        comparisons = data.get(key)
        if not isinstance(comparisons, list):
            continue

        for comparison in comparisons:
            if not isinstance(comparison, dict):
                continue

            id1 = comparison.get(
                "first_submission",
                comparison.get("firstSubmission", comparison.get("id1", comparison.get("submission1", ""))),
            )
            id2 = comparison.get(
                "second_submission",
                comparison.get("secondSubmission", comparison.get("id2", comparison.get("submission2", ""))),
            )
            similarity = comparison.get("similarity", comparison.get("avg", 0.0))

            if isinstance(similarity, dict):
                similarity = similarity.get("AVG", similarity.get("avg", 0.0))

            score = float(similarity) if isinstance(similarity, (int, float)) else 0.0
            if score <= 1.0:
                score *= 100.0
            score = round(score, 2)

            student_1 = os.path.basename(str(id1)).strip()
            student_2 = os.path.basename(str(id2)).strip()

            if not student_1 or not student_2:
                continue

            if score > student_max[student_1]["max_score"]:
                student_max[student_1] = {
                    "max_score": score,
                    "most_similar_to": student_2,
                }

            if score > student_max[student_2]["max_score"]:
                student_max[student_2] = {
                    "max_score": score,
                    "most_similar_to": student_1,
                }


def _collect_similarity_results(student_max: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results = [
        {
            "student_id": student_id,
            "max_similarity_score": data["max_score"],
            "most_similar_to": data["most_similar_to"],
        }
        for student_id, data in student_max.items()
    ]
    results.sort(key=lambda item: item["max_similarity_score"], reverse=True)
    return results


def _parse_overview_data(overview: Any) -> list[dict[str, Any]]:
    student_max: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"max_score": 0.0, "most_similar_to": None}
    )

    if isinstance(overview, list):
        for item in overview:
            if isinstance(item, dict):
                _extract_comparisons(item, student_max)
        return _collect_similarity_results(student_max)

    if isinstance(overview, dict):
        if "metrics" in overview and isinstance(overview["metrics"], list):
            for metric in overview["metrics"]:
                if not isinstance(metric, dict):
                    continue

                if "topComparisons" in metric:
                    _extract_comparisons({"comparisons": metric["topComparisons"]}, student_max)
                elif "top_comparisons" in metric:
                    _extract_comparisons({"comparisons": metric["top_comparisons"]}, student_max)
                else:
                    _extract_comparisons(metric, student_max)
        elif "top_comparisons" in overview or "topComparisons" in overview:
            _extract_comparisons(overview, student_max)
        else:
            _extract_comparisons({"comparisons": overview.get("matches", [])}, student_max)

    return _collect_similarity_results(student_max)


def _parse_from_comparisons(extract_dir: Path) -> list[dict[str, Any]]:
    student_max: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"max_score": 0.0, "most_similar_to": None}
    )

    for root, _, files in os.walk(extract_dir):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = Path(root) / filename
            try:
                with file_path.open("r", encoding="utf-8") as file_obj:
                    data = json.load(file_obj)
            except (json.JSONDecodeError, OSError):
                continue

            if isinstance(data, dict):
                _extract_comparisons(data, student_max)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        _extract_comparisons(item, student_max)

    return _collect_similarity_results(student_max)


def parse_jplag_results(assignment_id: int) -> list[dict[str, Any]]:
    extract_dir = DATA_DIR / "jplag_reports" / str(assignment_id) / "extracted"

    overview_path: Path | None = None
    for root, _, files in os.walk(extract_dir):
        for filename in files:
            if filename == "overview.json":
                overview_path = Path(root) / filename
                break
        if overview_path:
            break

    if not overview_path:
        logger.warning("overview.json not found for assignment %s, using fallback parser", assignment_id)
        return _parse_from_comparisons(extract_dir)

    with overview_path.open("r", encoding="utf-8") as file_obj:
        overview = json.load(file_obj)

    results = _parse_overview_data(overview)
    logger.info("Parsed %d plagiarism result rows for assignment %s", len(results), assignment_id)
    return results


async def run_plagiarism_check(assignment_id: int, db: Session) -> list[dict[str, Any]]:
    logger.info("Starting plagiarism check for assignment %s", assignment_id)

    prepare_jplag_directory(assignment_id, db)

    report_dir = await _run_jplag_on_directory(
        DATA_DIR / "temp_jplag" / str(assignment_id),
        DATA_DIR / "jplag_reports" / str(assignment_id),
    )
    report_path = report_dir / "result.zip"

    results = parse_jplag_results(assignment_id)
    if not results:
        logger.warning("No plagiarism results found for assignment %s", assignment_id)
        return []

    relative_report_path = os.path.relpath(report_path, PROJECT_ROOT)
    save_plagiarism_results(
        db,
        assignment_id,
        results,
        report_path=relative_report_path,
    )

    temp_dir = DATA_DIR / "temp_jplag" / str(assignment_id)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    logger.info("Completed plagiarism check for assignment %s", assignment_id)
    return results


async def compare_two_files(code1: str, code2: str) -> float:
    with tempfile.TemporaryDirectory(dir=DATA_DIR) as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"

        (input_dir / "file1").mkdir(parents=True, exist_ok=True)
        (input_dir / "file2").mkdir(parents=True, exist_ok=True)

        (input_dir / "file1" / "code.c").write_text(code1, encoding="utf-8")
        (input_dir / "file2" / "code.c").write_text(code2, encoding="utf-8")

        await _run_jplag_on_directory(input_dir, output_dir)

        extract_dir = output_dir / "extracted"
        overview_path: Path | None = None

        for root, _, files in os.walk(extract_dir):
            for filename in files:
                if filename == "overview.json":
                    overview_path = Path(root) / filename
                    break
            if overview_path:
                break

        if overview_path:
            with overview_path.open("r", encoding="utf-8") as file_obj:
                overview = json.load(file_obj)
            results = _parse_overview_data(overview)
        else:
            results = _parse_from_comparisons(extract_dir)

        for result in results:
            if result["student_id"] == "file1":
                return float(result["max_similarity_score"])
            if result["student_id"] == "file2":
                return float(result["max_similarity_score"])

        return 0.0