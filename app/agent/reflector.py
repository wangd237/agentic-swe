"""Structured reflection helpers for failed repair attempts."""

from __future__ import annotations

import json

from app.agent.memory import AgentState, FailureSignature, ReflectionDecision


def compare_failure_signatures(
    previous: FailureSignature | None,
    current: FailureSignature | None,
) -> str:
    if previous is None or current is None:
        return "unknown"
    return "unchanged" if previous.output_hash == current.output_hash else "changed"


def reflect_after_failed_verification(
    *,
    state: AgentState,
    previous_failure_signature: FailureSignature | None,
    current_failure_signature: FailureSignature | None,
    changed_files: list[str],
    max_patch_files: int,
    min_candidate_confidence: float = 0.4,
) -> ReflectionDecision:
    failure_delta = compare_failure_signatures(previous_failure_signature, current_failure_signature)
    candidate_confidence_by_path = {
        candidate.relative_path: candidate.confidence
        for candidate in state.localization_candidates
    }
    candidate_paths = set(candidate_confidence_by_path)
    changed_file_set = set(changed_files)
    changed_outside_candidates = bool(changed_file_set) and not changed_file_set.issubset(candidate_paths)

    if changed_outside_candidates:
        return ReflectionDecision(
            failure_delta=failure_delta,
            likely_cause="wrong_file",
            next_phase="localize",
            required_actions=[
                "Review the changed file against localization evidence.",
                "Read the failing test and top localization candidates before editing again.",
            ],
            should_undo=failure_delta == "unchanged",
        )

    changed_candidate_confidences = [
        candidate_confidence_by_path[path]
        for path in changed_files
        if path in candidate_confidence_by_path
    ]
    if (
        changed_candidate_confidences
        and max(changed_candidate_confidences) < min_candidate_confidence
    ):
        return ReflectionDecision(
            failure_delta=failure_delta,
            likely_cause="low_confidence_localization",
            next_phase="localize",
            required_actions=[
                "Gather stronger localization evidence before editing again.",
                "Search for issue symbols, read the failing test, or inspect imports from tests to implementation.",
            ],
            should_undo=failure_delta == "unchanged",
        )

    if len(changed_files) > max_patch_files:
        return ReflectionDecision(
            failure_delta=failure_delta,
            likely_cause="overfit",
            next_phase="localize",
            required_actions=[
                "Reduce patch scope.",
                "Prefer a smaller edit in the highest-confidence candidate file.",
            ],
            should_undo=failure_delta == "unchanged",
        )

    if failure_delta == "unchanged":
        return ReflectionDecision(
            failure_delta=failure_delta,
            likely_cause="wrong_hypothesis",
            next_phase="localize",
            required_actions=[
                "Re-check the failure summary and context diff.",
                "Search for another implementation path related to the failing behavior.",
            ],
            should_undo=False,
        )

    if failure_delta == "changed":
        return ReflectionDecision(
            failure_delta=failure_delta,
            likely_cause="partial_fix",
            next_phase="patch",
            required_actions=[
                "Keep useful parts of the patch.",
                "Patch the remaining failing assertion based on the new failure signature.",
            ],
            should_undo=False,
        )

    return ReflectionDecision(
        failure_delta="unknown",
        likely_cause="unknown",
        next_phase="localize",
        required_actions=[
            "Collect clearer verification evidence.",
            "Run tests again or inspect failure output before further edits.",
        ],
        should_undo=False,
    )


def build_reflection_message(decision: ReflectionDecision) -> str:
    payload = decision.model_dump(mode="json")
    return (
        "REFLECTION_DECISION:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
        "Follow this decision before making another patch. If next_phase is localize, gather evidence before editing."
    )
