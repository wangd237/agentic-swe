"""Regression tests for the opt-in autonomy experiment."""
from app.core.policy_config import PolicyConfig
from app.core.state import AgentState, ReflectionDecision
from app.tools.policy import ToolPolicy
from app.tools.router import build_tools_for_state, tool_names
from app.llm.prompts import build_system_prompt
from app.agent.reflector import build_reflection_message


def test_strict_default_unchanged():
    assert PolicyConfig(policy_id="test", description="test").harness_mode == "strict"
    state = AgentState()
    assert ToolPolicy().validate(state=state, tool_name="edit_file", tool_input={"relative_path": "x.py"}) is not None
    assert "edit_file" not in tool_names(build_tools_for_state(state))


def test_weak_mode_allows_cross_phase_tools_without_candidate():
    state = AgentState(weak_constraints=True, phase="understand", budget_escalation_active=True)
    names = tool_names(build_tools_for_state(state))
    assert {"read_file", "search_code", "edit_file", "run_tests"} <= set(names)
    assert "search_graph" not in names
    assert "undo" not in names
    assert ToolPolicy().validate(state=state, tool_name="edit_file", tool_input={"relative_path": "x.py"}) is None
    assert ToolPolicy().validate(state=state, tool_name="unknown", tool_input={}) is not None
    assert ToolPolicy().validate(state=state, tool_name="undo", tool_input={}) is not None


def test_weak_mode_has_no_graph_call_cap_or_diff_order_gate():
    state = AgentState(weak_constraints=True, phase="verify", workspace_generation=1, search_graph_calls=3)
    assert ToolPolicy().validate(state=state, tool_name="search_graph", tool_input={}) is None
    assert state.search_graph_calls == 4
    assert "run_tests" in tool_names(build_tools_for_state(state))
    assert ToolPolicy().validate(state=state, tool_name="run_tests", tool_input={}) is None


def test_weak_prompt_and_reflection_are_advisory():
    assert "Choose the order" in build_system_prompt(weak_constraints=True)
    assert "heuristic suggestion" in build_reflection_message(ReflectionDecision(), advisory=True)
    assert "Follow this decision" in build_reflection_message(ReflectionDecision())
