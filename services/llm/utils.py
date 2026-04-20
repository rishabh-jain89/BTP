from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Type

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from services.llm.client import get_llm

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_RETRY_DELAY_SECONDS = 2

# ---------------------------------------------------------------------------
#  JSON extraction helpers
# ---------------------------------------------------------------------------

_FENCED_JSON_RE = re.compile(
    r"```(?:json)?\s*\n?(.*?)\n?\s*```",
    re.DOTALL,
)


def _extract_json_from_text(text: str) -> str | None:
    """Try to pull a JSON object from fenced code blocks or raw braces."""
    match = _FENCED_JSON_RE.search(text)
    if match:
        return match.group(1).strip()

    # Fallback: find the first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return None


# ---------------------------------------------------------------------------
#  Core structured LLM invocation
# ---------------------------------------------------------------------------


def invoke_structured_llm(
    *,
    model: str,
    template: str,
    schema: Type[BaseModel],
    variables: dict[str, Any],
) -> dict[str, Any]:
    """
    Invoke an LLM with a prompt template and parse the response into a
    Pydantic schema.  Includes retry logic and a JSON-extraction fallback.
    """
    parser = PydanticOutputParser(pydantic_object=schema)

    prompt = ChatPromptTemplate.from_template(
        template + "\n\nReturn output in this format:\n{format_instructions}"
    )

    chain = prompt | get_llm(model)

    merged_vars = {
        **variables,
        "format_instructions": parser.get_format_instructions(),
    }

    last_error: Exception | None = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            raw_response = chain.invoke(merged_vars)
            content = _response_to_text(raw_response)

            # Primary path: strict Pydantic parse
            try:
                parsed = parser.parse(content)
                logger.debug(
                    "LLM invocation succeeded (attempt %d, model=%s, schema=%s)",
                    attempt, model, schema.__name__,
                )
                return parsed.model_dump()
            except Exception as parse_err:
                logger.warning(
                    "Pydantic parse failed (attempt %d, schema=%s): %s  — trying JSON fallback",
                    attempt, schema.__name__, parse_err,
                )
                return _json_fallback_parse(content, schema, parse_err)

        except Exception as exc:
            last_error = exc
            logger.warning(
                "LLM invocation error (attempt %d/%d, model=%s): %s",
                attempt, _MAX_RETRIES, model, exc,
            )
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_DELAY_SECONDS)

    # All retries exhausted
    logger.error(
        "LLM invocation failed after %d attempts (model=%s, schema=%s): %s",
        _MAX_RETRIES, model, schema.__name__, last_error,
    )
    raise RuntimeError(
        f"LLM invocation failed after {_MAX_RETRIES} attempts: {last_error}"
    ) from last_error


# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------


def _response_to_text(raw_response: Any) -> str:
    """Normalise a LangChain response object to a plain string."""
    content = getattr(raw_response, "content", raw_response)

    if isinstance(content, list):
        content = "\n".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in content
        )

    if not isinstance(content, str):
        raise ValueError("LLM returned non-text content")

    return content


def _json_fallback_parse(
    content: str,
    schema: Type[BaseModel],
    original_error: Exception,
) -> dict[str, Any]:
    """
    Last-resort parser: extract a JSON object from the raw LLM text and
    validate it against the Pydantic schema with lenient defaults.
    """
    extracted = _extract_json_from_text(content)
    if extracted is None:
        raise original_error

    try:
        raw_dict = json.loads(extracted)
    except json.JSONDecodeError:
        raise original_error

    if not isinstance(raw_dict, dict):
        raise original_error

    try:
        parsed = schema.model_validate(raw_dict)
        logger.info("JSON fallback parse succeeded for schema=%s", schema.__name__)
        return parsed.model_dump()
    except Exception:
        raise original_error


# ---------------------------------------------------------------------------
#  Reusable tiny helpers
# ---------------------------------------------------------------------------


def safe_json_dumps(value: Any) -> str:
    """JSON-serialise a value with sensible defaults."""
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def clamp_confidence(value: Any) -> float | None:
    """Clamp a raw confidence value to [0, 1] or return None."""
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, value))