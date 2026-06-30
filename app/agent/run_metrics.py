"""Derived behavior metrics for a single agent repair run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.tool_definitions import write_tool_names
from app.schemas.trace_schema import Trace


PHASE_ORDER = ["understand", "reproduce", "localize", "patch", "verify", "final"]
WRITE_TOOLS = write_tool_names()
REPRO_EVIDENCE_TOOLS = {"run_tests"}


@dataclass(frozen=True)
class AgentRunMetrics:
    """Small set of metrics that measure whether the agent followed repair discipline."""

    phase_completion_rate: float
    pre_repro_rate: float
    write_before_repro_count: int
    policy_violation_count: int
    patch_changed_file_count: int
    unverified_patch_rate: float
    success_full_verify_rate: float
    weak_success_rate: float
    undo_recovery_rate: float
    localization_precision_at_3: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_completion_rate": self.phase_completion_rate,
            "pre_repro_rate": self.pre_repro_rate,
            "write_before_repro_count": self.write_before_repro_count,
            "policy_violation_count": self.policy_violation_count,
            "patch_changed_file_count": self.patch_changed_file_count,
            "unverified_patch_rate": self.unverified_patch_rate,
            "success_full_verify_rate": self.success_full_verify_rate,
            "weak_success_rate": self.weak_success_rate,
            "undo_recovery_rate": self.undo_recovery_rate,
            "localization_precision_at_3": self.localization_precision_at_3,
        }


def _step_ok(step: Any) -> bool:
    return bool(getattr(step, "tool_metrics", {}).get("ok", False))


def _is_reproduction_evidence(step: Any) -> bool:
    if step.tool_name not in REPRO_EVIDENCE_TOOLS:
        return False
    if getattr(step, "tool_metrics", {}).get("policy_blocked"):
        return False
    if getattr(step, "tool_metrics", {}).get("error_type") == "tool_policy_violation":
        return False
    return True


def _round_rate(value: float) -> float:
    return round(value, 4)


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def compute_agent_run_metrics(
    *,
    trace: Trace,
    final_status: str,
    verification_strength: str,
    patch_applied: bool,
    workspace_generation: int,
    verified_generation: int | None,
    write_before_repro_count: int,
    modified_files: list[str] | None = None,
    localization_candidate_paths: list[str] | None = None,
) -> AgentRunMetrics:
    """Compute currentTask.md behavior metrics from authoritative run state."""

    phases_seen = {
        step.phase
        for step in trace.steps
        if step.phase in PHASE_ORDER
    }
    phase_completion_rate = len(phases_seen) / len(PHASE_ORDER)

    write_steps = [
        step
        for step in trace.steps
        if step.tool_name in WRITE_TOOLS and _step_ok(step)
    ]
    first_successful_write_index = min(
        (step.step_index for step in write_steps),
        default=None,
    )
    repro_before_write = any(
        _is_reproduction_evidence(step)
        and (
            first_successful_write_index is None
            or step.step_index < first_successful_write_index
        )
        for step in trace.steps
    )
    pre_repro_rate = 1.0 if repro_before_write else 0.0

    unverified_patch = (
        patch_applied
        and workspace_generation > 0
        and verified_generation != workspace_generation
    )
    success_full_verify = final_status == "success" and verification_strength == "full"
    weak_success = final_status == "success_weak_verification"
    undo_recovery = any(
        step.tool_name == "undo"
        and _step_ok(step)
        and bool(step.tool_input.get("automatic"))
        for step in trace.steps
    )
    policy_violation_count = sum(
        1
        for step in trace.steps
        if bool(getattr(step, "tool_metrics", {}).get("policy_blocked"))
        or getattr(step, "tool_metrics", {}).get("error_type") == "tool_policy_violation"
    )
    normalized_modified_files = {
        normalized
        for path in (modified_files or [])
        if (normalized := _normalize_path(path))
    }
    top_localization_candidates = {
        normalized
        for path in (localization_candidate_paths or [])[:3]
        if (normalized := _normalize_path(path))
    }
    localization_hits = normalized_modified_files & top_localization_candidates
    localization_precision_at_3 = (
        len(localization_hits) / len(normalized_modified_files)
        if normalized_modified_files
        else 0.0
    )

    return AgentRunMetrics(
        phase_completion_rate=_round_rate(phase_completion_rate),
        pre_repro_rate=1.0 if pre_repro_rate else 0.0,
        write_before_repro_count=write_before_repro_count,
        policy_violation_count=policy_violation_count,
        patch_changed_file_count=len(normalized_modified_files),
        unverified_patch_rate=1.0 if unverified_patch else 0.0,
        success_full_verify_rate=1.0 if success_full_verify else 0.0,
        weak_success_rate=1.0 if weak_success else 0.0,
        undo_recovery_rate=1.0 if undo_recovery else 0.0,
        localization_precision_at_3=_round_rate(localization_precision_at_3),
    )
