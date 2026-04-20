from __future__ import annotations

import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.PROJECT_ROOT = Path(__file__).resolve().parent.parent

        self.DATABASE_URL = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/btp_eval",
        )
        self.REDIS_URL = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        )

        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.TEMP_DIR = self.DATA_DIR / "tmp_jobs"

        self.EVALUATION_QUEUE = "evaluation_queue"
        self.PLAGIARISM_QUEUE = "plagiarism_queue"
        self.QUESTION_QUEUE = "question_queue"


settings = Settings()