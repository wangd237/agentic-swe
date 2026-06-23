"""Verification strength and final-result policy for repair runs."""

from __future__ import annotations

import re
import shlex
from typing import Any

from app.agent.memory import VerificationStrength


WEAK_VERIFICATION_METADATA_VALUES = {"weak", "none"}
FAILED_TEST_DETAIL_SEPARATOR = " - "
PYTEST_NODE_PATTERN = re.compile(r"(?P<node>[^\s]+\.py(?:::[^\s]+)+)")


def initial_verification_strength(task_metadata: dict[str, Any]) -> VerificationStrength:
    """Infer the starting verification quality from task construction metadata."""

    metadata_value = str(task_metadata.get("verification_strength", "")).strip().lower()
    test_source = str(task_metadata.get("test_command_source", "")).strip().lower()
    if metadata_value in WEAK_VERIFICATION_METADATA_VALUES or test_source == "pytest_fallback":
        return "weak"
    return "none"


def strength_after_test(
    *,
    current: VerificationStrength,
    exit_code: int | None,
    workspace_generation: int,
    command_source: str = "",
) -> VerificationStrength:
    """Update verification strength after a test run."""

    if exit_code is None:
        return current

    if command_source == "pytest_fallback":
        return "weak"

    if exit_code == 0 and workspace_generation > 0:
        return "full"
    if exit_code == 0:
        return "targeted"
    return "targeted" if current != "weak" else "weak"


def adjust_final_status_for_verification(
    *,
    final_status: str,
    incomplete_reason: str,
    verification_strength: VerificationStrength,
    patch_applied: bool,
) -> tuple[str, str]:
    """Prevent weak or missing verification from being reported as ordinary success."""

    if final_status != "success":
        return final_status, incomplete_reason
    if verification_strength == "full":
        return final_status, incomplete_reason
    if verification_strength in {"weak", "targeted"} and patch_applied:
        return "success_weak_verification", "weak_verification"
    return "incomplete", "weak_verification"


def extract_pytest_node_ids(failure_summary: dict[str, Any] | None) -> list[str]:
    """Extract pytest node ids from a run_tests failure summary."""

    if not failure_summary:
        return []

    node_ids: list[str] = []
    for failed_test in failure_summary.get("failed_tests", []) or []:
        candidate = str(failed_test).split(FAILED_TEST_DETAIL_SEPARATOR, 1)[0].strip()
        match = PYTEST_NODE_PATTERN.search(candidate)
        node_id = match.group("node") if match else candidate
        node_id = node_id.replace("\\", "/")
        if ".py::" not in node_id:
            continue
        if node_id not in node_ids:
            node_ids.append(node_id)
    return node_ids


def build_targeted_pytest_command(
    *,
    base_command: str,
    failure_summary: dict[str, Any] | None,
    max_nodes: int = 3,
) -> str | None:
    """Build a focused pytest command for the failing node ids when possible."""

    if "pytest" not in base_command:
        return None

    node_ids = extract_pytest_node_ids(failure_summary)[:max_nodes]
    if not node_ids:
        return None

    prefix = _pytest_command_prefix(base_command)
    return f"{prefix} {' '.join(node_ids)} -q"


def _pytest_command_prefix(base_command: str) -> str:
    try:
        parts = shlex.split(base_command, posix=False)
    except ValueError:
        return "python -m pytest" if " -m pytest" in base_command else "pytest"

    for index, part in enumerate(parts):
        normalized_part = part.strip("\"'")
        if normalized_part == "pytest":
            if index >= 2 and parts[index - 1] == "-m":
                return " ".join(parts[: index + 1])
            return part
    return "python -m pytest" if " -m pytest" in base_command else "pytest"
