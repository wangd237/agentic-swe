from __future__ import annotations

from app.agent.memory import AgentState
from app.agent.tool_policy import ToolPolicy


def test_tool_policy_blocks_write_before_patch_gate() -> None:
    state = AgentState(phase="understand")
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="edit_file",
        tool_input={
            "relative_path": "pkg/app.py",
            "old_string": "return 1",
            "new_string": "return 2",
        },
    )

    assert result is not None
    assert result["ok"] is False
    assert result["error"]["type"] == "tool_policy_violation"
    assert "not allowed" in result["error"]["message"]


def test_tool_policy_allows_patch_after_evidence_and_read_candidate() -> None:
    state = AgentState(phase="patch", has_reproduction_evidence=True)
    state.remember_read_file("pkg/app.py")
    state.remember_candidate(
        "pkg/app.py",
        reason="test_failure_location",
        evidence="tests point to pkg/app.py",
        confidence=0.8,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="edit_file",
        tool_input={
            "relative_path": "pkg/app.py",
            "old_string": "return 1",
            "new_string": "return 2",
        },
    )

    assert result is None


def test_tool_policy_allows_patch_with_explicit_weak_static_evidence() -> None:
    state = AgentState(
        phase="patch",
        has_reproduction_evidence=True,
        reproduction_evidence_kind="weak_static",
        verification_strength="weak",
    )
    state.remember_candidate(
        "pkg/app.py",
        reason="task_hint",
        evidence="task explicitly allows weak/static repair evidence",
        confidence=0.5,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="write_file",
        tool_input={
            "relative_path": "pkg/app.py",
            "content": "VALUE = 1\n",
        },
    )

    assert result is None


def test_tool_policy_requires_candidate_before_write() -> None:
    state = AgentState(phase="patch", has_reproduction_evidence=True)
    state.remember_candidate(
        "pkg/other.py",
        reason="task_hint",
        evidence="task hinted a different file",
        confidence=0.6,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="write_file",
        tool_input={
            "relative_path": "pkg/app.py",
            "content": "VALUE = 1\n",
        },
    )

    assert result is not None
    assert result["ok"] is False
    assert "must be a localization candidate" in result["error"]["message"]


def test_tool_policy_allows_candidate_override_with_specific_reason() -> None:
    state = AgentState(phase="patch", has_reproduction_evidence=True)
    state.remember_candidate(
        "pkg/other.py",
        reason="task_hint",
        evidence="task hinted a different file",
        confidence=0.6,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="write_file",
        tool_input={
            "relative_path": "pkg/app.py",
            "content": "VALUE = 1\n",
            "localization_override_reason": (
                "Failure traceback imports pkg.app through pkg.other, so this implementation file must change."
            ),
        },
    )

    assert result is None


def test_tool_policy_rejects_empty_candidate_override_reason() -> None:
    state = AgentState(phase="patch", has_reproduction_evidence=True)
    state.remember_candidate(
        "pkg/other.py",
        reason="task_hint",
        evidence="task hinted a different file",
        confidence=0.6,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="edit_file",
        tool_input={
            "relative_path": "pkg/app.py",
            "old_string": "return 1",
            "new_string": "return 2",
            "localization_override_reason": "needed",
        },
    )

    assert result is not None
    assert result["ok"] is False
    assert "localization_override_reason" in result["error"]["message"]


def test_tool_policy_requires_show_diff_before_patch_verification_tests() -> None:
    state = AgentState(
        phase="verify",
        has_reproduction_evidence=True,
        workspace_generation=1,
        diff_observed_generation=None,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="run_tests",
        tool_input={"timeout_sec": 30},
    )

    assert result is not None
    assert result["ok"] is False
    assert "show_diff" in result["error"]["message"]


def test_tool_policy_allows_tests_after_current_diff_is_observed() -> None:
    state = AgentState(
        phase="verify",
        has_reproduction_evidence=True,
        workspace_generation=1,
        diff_observed_generation=1,
    )
    policy = ToolPolicy()

    result = policy.validate(
        state=state,
        tool_name="run_tests",
        tool_input={"timeout_sec": 30},
    )

    assert result is None
