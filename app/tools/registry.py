"""Single index of built-in tools; permissions still belong to ToolPolicy.

Tool definitions and their handler names live in one registration list in
tool_definitions.py. This registry indexes them and produces model-facing
schemas without exposing internal execution metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

from app.tools.definitions import _SINGLE_SOURCE_DATA

RiskLevel = Literal["read", "execute", "modify"]
_VALID_RISK_LEVELS = {"read", "execute", "modify"}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler_name: str
    risk_level: RiskLevel
    is_read_only: bool
    is_concurrency_safe: bool

    def model_definition(self) -> dict[str, Any]:
        """Only fields needed by the model; no handler or risk configuration."""
        return {
            "name": self.name,
            "description": self.description,
            "is_read_only": self.is_read_only,
            "is_concurrency_safe": self.is_concurrency_safe,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    """A name-to-tool index. Registration is NOT execution authorization."""

    def __init__(self, registrations: list[dict[str, Any]]) -> None:
        self._tools: dict[str, ToolSpec] = {}
        for entry in registrations:
            name = entry["name"]
            if not isinstance(name, str) or not name:
                raise ValueError("Tool name must be a non-empty string")
            if name in self._tools:
                raise ValueError(f"Duplicate tool registration: {name}")

            handler_name = entry["handler_name"]
            if not isinstance(handler_name, str) or not handler_name.startswith("_handle_"):
                raise ValueError(f"Invalid handler for tool: {name}")

            risk_level = entry["risk_level"]
            if risk_level not in _VALID_RISK_LEVELS:
                raise ValueError(f"Unknown risk level for tool: {name}")
            if bool(entry["is_read_only"]) != (risk_level == "read"):
                raise ValueError(f"Inconsistent read-only and risk metadata: {name}")

            self._tools[name] = ToolSpec(
                name=name,
                description=entry["description"],
                input_schema=entry["input_schema"],
                handler_name=handler_name,
                risk_level=risk_level,
                is_read_only=entry["is_read_only"],
                is_concurrency_safe=entry["is_concurrency_safe"],
            )

    def get(self, tool_name: str) -> ToolSpec | None:
        return self._tools.get(tool_name)

    def all_specs(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def model_definitions(self) -> list[dict[str, Any]]:
        return [spec.model_definition() for spec in self._tools.values()]


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    return ToolRegistry(_SINGLE_SOURCE_DATA)
