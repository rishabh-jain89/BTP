"""
services.question_service — compatibility re-export.

The real implementation lives in services.llm.question_chain.
This module re-exports ``ask_llm_question`` so that any legacy imports like
``from services.question_service import ask_llm_question`` continue to work.
"""
from __future__ import annotations

from services.llm.question_chain import ask_llm_question, build_submission_context

__all__ = ["ask_llm_question", "build_submission_context"]