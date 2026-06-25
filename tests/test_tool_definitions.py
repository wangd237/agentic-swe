from __future__ import annotations

from app.agent.memory import AgentState
from app.agent.tool_definitions import build_tool_definitions
from app.agent.tool_policy import ALLOWED_TOOLS_BY_PHASE
from app.agent.tool_router import build_tools_for_phase, build_tools_for_state


def test_tool_definitions_include_python_repl_boundaries() -> None:
    tools = build_tool_definitions()
    python_repl_tool = next(tool for tool in tools if tool["name"] == "python_repl")

    assert "expression" in python_repl_tool["input_schema"]["required"]
    assert "import" in python_repl_tool["description"]
    assert "分号" in python_repl_tool["description"]
    assert "dunder" in python_repl_tool["description"]


def test_phase_tool_router_reuses_policy_allowed_tools() -> None:
    all_tool_names = {tool["name"] for tool in build_tool_definitions()}

    for phase, allowed_tool_names in ALLOWED_TOOLS_BY_PHASE.items():
        routed_tool_names = {
            tool["name"]
            for tool in build_tools_for_phase(phase)
        }

        assert allowed_tool_names <= all_tool_names
        assert routed_tool_names == allowed_tool_names


def test_state_tool_router_hides_undo_before_workspace_changes() -> None:
    state = AgentState(phase="patch", workspace_generation=0)

    routed_tool_names = {
        tool["name"]
        for tool in build_tools_for_state(state)
    }

    assert "undo" not in routed_tool_names
    assert "grep" in routed_tool_names
    assert "search_code" in routed_tool_names
    assert "edit_file" in routed_tool_names
    assert "write_file" in routed_tool_names


def test_state_tool_router_exposes_read_only_search_during_reproduce() -> None:
    state = AgentState(phase="reproduce")

    routed_tool_names = {
        tool["name"]
        for tool in build_tools_for_state(state)
    }

    assert "grep" in routed_tool_names
    assert "search_code" in routed_tool_names
    assert "edit_file" not in routed_tool_names
    assert "write_file" not in routed_tool_names


def test_state_tool_router_hides_verify_tests_until_current_diff_is_observed() -> None:
    state = AgentState(
        phase="verify",
        workspace_generation=1,
        diff_observed_generation=None,
    )

    routed_tool_names = {
        tool["name"]
        for tool in build_tools_for_state(state)
    }

    assert "run_tests" not in routed_tool_names
    assert "show_diff" in routed_tool_names


def test_state_tool_router_allows_verify_tests_after_current_diff_is_observed() -> None:
    state = AgentState(
        phase="verify",
        workspace_generation=1,
        diff_observed_generation=1,
    )

    routed_tool_names = {
        tool["name"]
        for tool in build_tools_for_state(state)
    }

    assert "run_tests" in routed_tool_names
    assert "show_diff" in routed_tool_names


def test_state_tool_router_exposes_write_tools_during_patch_recovery() -> None:
    state = AgentState(
        phase="localize",
        has_reproduction_evidence=True,
        workspace_generation=1,
    )
    state.remember_candidate(
        "pkg/app.py",
        reason="failed_patch_file",
        evidence="previous patch verification failed in this file",
        confidence=0.8,
    )

    routed_tool_names = {
        tool["name"]
        for tool in build_tools_for_state(state)
    }

    assert "edit_file" in routed_tool_names
    assert "write_file" in routed_tool_names
    assert "show_diff" in routed_tool_names
    assert "undo" in routed_tool_names
