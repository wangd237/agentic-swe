"""Validate model-generated tool arguments against the advertised JSON Schemas."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from jsonschema import Draft202012Validator

from app.tools.definitions import build_tool_definitions


@lru_cache(maxsize=1)
def _validators() -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}
    for tool in build_tool_definitions():
        # The existing input_schema is also the model-facing contract.
        # Reject unknown arguments rather than silently discarding them.
        schema = {**tool["input_schema"], "additionalProperties": False}
        Draft202012Validator.check_schema(schema)
        validators[tool["name"]] = Draft202012Validator(schema)
    return validators


def validate_tool_call(tool_name: str, tool_input: Any) -> dict[str, Any] | None:
    """Return an ordinary tool error for invalid input; None means valid.

    Call only for model-generated tool calls. Internal verification calls pass
    additional runtime metadata and must not be subject to the public schema.
    """
    validator = _validators().get(tool_name)
    if validator is None:
        message = f"Unknown tool: {tool_name}"
    else:
        errors = list(validator.iter_errors(tool_input))
        if not errors:
            return None
        error = min(errors, key=lambda item: (len(item.absolute_path), str(item.message)))
        location = ".".join(str(part) for part in error.absolute_path)
        message = f"{location}: {error.message}" if location else error.message

    return {
        "ok": False,
        "tool_name": tool_name,
        "summary": f"Tool argument schema validation failed: {message}",
        "data": {"validation_failed": True},
        "error": {"type": "schema_validation_error", "message": message},
    }
