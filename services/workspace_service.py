from __future__ import annotations

import shutil
from pathlib import Path


def build_evaluation_workspace(project_root: str, job_id: int) -> str:
    workspace_root = Path(project_root) / "data" / "tmp_jobs" / f"eval_{job_id}"

    if workspace_root.exists():
        shutil.rmtree(workspace_root)

    for folder_name in ("Code", "Assignment", "inputs", "expected", "output"):
        (workspace_root / folder_name).mkdir(parents=True, exist_ok=True)

    return str(workspace_root)


def cleanup_workspace(workspace_root: str) -> None:
    workspace_path = Path(workspace_root)
    if workspace_path.exists():
        shutil.rmtree(workspace_path)