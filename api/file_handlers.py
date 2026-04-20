from __future__ import annotations

import csv
import io
import os
import zipfile
from pathlib import Path
from typing import Any


ALLOWED_DESCRIPTION_EXTENSIONS = {".pdf", ".txt"}
C_SOURCE_EXTENSION = ".c"


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

    return "\n\n".join(part for part in text_parts if part)


def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def extract_description_from_upload(filename: str, file_bytes: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return extract_text_from_pdf(file_bytes)
    if suffix == ".txt":
        return extract_text_from_txt(file_bytes)

    allowed = ", ".join(sorted(ALLOWED_DESCRIPTION_EXTENSIONS))
    raise ValueError(f"Unsupported file type: {filename}. Supported types: {allowed}.")


def save_submission_file(
    data_dir: str,
    assignment_id: int,
    roll_number: str,
    file_bytes: bytes,
) -> str:
    target_dir = Path(data_dir) / "assignments" / str(assignment_id) / "students" / roll_number
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / "test.c"
    target_path.write_bytes(file_bytes)
    return str(target_path.resolve())


def process_zip_upload(
    zip_bytes: bytes,
    assignment_id: int,
    data_dir: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    submissions: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_roll_numbers: set[str] = set()

    try:
        zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes), "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid ZIP file.") from exc

    with zip_file as zf:
        for entry in zf.infolist():
            entry_name = entry.filename

            if entry.is_dir():
                continue

            basename = os.path.basename(entry_name)
            if not basename:
                continue

            if basename.startswith(".") or entry_name.startswith("__MACOSX/"):
                continue

            if Path(basename).suffix.lower() != C_SOURCE_EXTENSION:
                errors.append(f"Skipped non-.c file: {entry_name}")
                continue

            roll_number = Path(basename).stem.strip()
            if not roll_number:
                errors.append(f"Empty roll number from file: {entry_name}")
                continue

            if roll_number in seen_roll_numbers:
                errors.append(f"Duplicate roll number file skipped: {entry_name}")
                continue

            try:
                code_bytes = zf.read(entry)
                code_text = code_bytes.decode("utf-8", errors="replace")
                file_path = save_submission_file(data_dir, assignment_id, roll_number, code_bytes)

                submissions.append(
                    {
                        "roll_number": roll_number,
                        "code": code_text,
                        "file_path": file_path,
                    }
                )
                seen_roll_numbers.add(roll_number)
            except Exception as exc:
                errors.append(f"Error processing {entry_name}: {exc}")

    return submissions, errors


def parse_student_csv(file_bytes: bytes) -> list[dict[str, str | None]]:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV file is empty or has no header row.")

    normalized_field_map = {field.strip().lower(): field for field in reader.fieldnames if field}
    required_fields = {"roll_number", "name"}

    if not required_fields.issubset(normalized_field_map):
        raise ValueError(
            f"CSV must have 'roll_number' and 'name' columns. Found: {reader.fieldnames}"
        )

    results: list[dict[str, str | None]] = []

    for row in reader:
        normalized_row = {
            (key.strip().lower() if key else ""): (value.strip() if value else "")
            for key, value in row.items()
        }

        roll_number = normalized_row.get("roll_number", "")
        name = normalized_row.get("name", "")

        if not roll_number:
            continue

        results.append(
            {
                "roll_number": roll_number,
                "name": name or None,
            }
        )

    return results