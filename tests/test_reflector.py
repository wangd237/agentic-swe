from __future__ import annotations

from app.agent.memory import AgentState, FailureSignature
from app.agent.reflector import (
    build_reflection_message,
    compare_failure_signatures,
    reflect_after_failed_verification,
)


def make_signature(output_hash: str) -> FailureSignature:
    return FailureSignature(
        failed_tests=["tests/test_app.py::test_value"],
        assertion_lines=["assert value() == 1"],
        locations=[{"path": "tests/test_app.py", "line": 4, "error": "AssertionError"}],
        output_hash=output_hash,
    )


def test_compare_failure_signatures_detects_delta() -> None:
    assert compare_failure_signatures(make_signature("a"), make_signature("a")) == "unchanged"
    assert compare_failure_signatures(make_signature("a"), make_signature("b")) == "changed"
    assert compare_failure_signatures(None, make_signature("b")) == "unknown"


def test_reflect_after_failed_verification_marks_partial_fix_when_failure_changed() -> None:
    state = AgentState(phase="verify", has_reproduction_evidence=True)
    state.remember_candidate(
        "demo_pkg/app.py",
        reason="task_hint",
        evidence="candidate",
        confidence=0.8,
    )

    decision = reflect_after_failed_verification(
        state=state,
        previous_failure_signature=make_signature("before"),
        current_failure_signature=make_signature("after"),
        changed_files=["demo_pkg/app.py"],
        max_patch_files=1,
    )

    assert decision.failure_delta == "changed"
    assert decision.likely_cause == "partial_fix"
    assert decision.next_phase == "patch"
    assert decision.should_undo is False


def test_reflect_after_failed_verification_marks_wrong_file_for_candidate_mismatch() -> None:
    state = AgentState(phase="verify", has_reproduction_evidence=True)
    state.remember_candidate(
        "demo_pkg/parser.py",
        reason="failure_location",
        evidence="candidate",
        confidence=0.8,
    )

    decision = reflect_after_failed_verification(
        state=state,
        previous_failure_signature=make_signature("same"),
        current_failure_signature=make_signature("same"),
        changed_files=["demo_pkg/app.py"],
        max_patch_files=1,
    )

    assert decision.failure_delta == "unchanged"
    assert decision.likely_cause == "wrong_file"
    assert decision.next_phase == "localize"
    assert decision.should_undo is True


def test_reflect_after_failed_verification_marks_overfit_for_too_many_files() -> None:
    state = AgentState(phase="verify", has_reproduction_evidence=True)
    for path in ["demo_pkg/app.py", "demo_pkg/parser.py"]:
        state.remember_candidate(
            path,
            reason="task_hint",
            evidence="candidate",
            confidence=0.8,
        )

    decision = reflect_after_failed_verification(
        state=state,
        previous_failure_signature=make_signature("same"),
        current_failure_signature=make_signature("same"),
        changed_files=["demo_pkg/app.py", "demo_pkg/parser.py"],
        max_patch_files=1,
    )

    assert decision.failure_delta == "unchanged"
    assert decision.likely_cause == "overfit"
    assert decision.next_phase == "localize"
    assert decision.should_undo is True


def test_reflect_after_failed_verification_marks_low_confidence_localization() -> None:
    state = AgentState(phase="verify", has_reproduction_evidence=True)
    state.remember_candidate(
        "demo_pkg/app.py",
        reason="weak_keyword_match",
        evidence="only a weak keyword matched this file",
        confidence=0.2,
    )

    decision = reflect_after_failed_verification(
        state=state,
        previous_failure_signature=make_signature("same"),
        current_failure_signature=make_signature("same"),
        changed_files=["demo_pkg/app.py"],
        max_patch_files=1,
    )

    assert decision.failure_delta == "unchanged"
    assert decision.likely_cause == "low_confidence_localization"
    assert decision.next_phase == "localize"
    assert "stronger localization evidence" in decision.required_actions[0]
    assert decision.should_undo is True


def test_build_reflection_message_is_structured() -> None:
    decision = reflect_after_failed_verification(
        state=AgentState(phase="verify"),
        previous_failure_signature=None,
        current_failure_signature=None,
        changed_files=[],
        max_patch_files=1,
    )

    message = build_reflection_message(decision)

    assert "REFLECTION_DECISION" in message
    assert "next_phase" in message
    assert "required_actions" in message
