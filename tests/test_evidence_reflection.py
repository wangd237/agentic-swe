from app.core.policy_config import PolicyConfig
from app.core.state import AgentState
from app.tools.policy import ToolPolicy
from app.tools.router import build_tools_for_state
from app.verification.test_feedback import record_test_evidence, evidence_message, is_non_product_signal


def observation(state, output, code=1, scope="full", command="pytest -q", error=None, generation=1):
    return record_test_evidence(state, {
        "ok": code == 0, "data": {"command": command, "exit_code": code, "stdout": output},
        "error": error,
    }, scope=scope, generation=generation)


def test_default_stays_rule_based():
    assert PolicyConfig(policy_id="test", description="test").reflection_mode == "rules"


def test_startup_is_not_evidence_of_product_failure():
    state = AgentState(evidence_reflection=True)
    evidence = observation(state, "ValueError: Plugin already registered under a different name")
    assert is_non_product_signal(evidence)
    assert evidence["collection_completed"] is False
    assert evidence["test_delta"] is None
    assert state.recovery_active
    assert "wrong_hypothesis" not in evidence_message(evidence)


def test_timeout_partial_output_is_not_a_pass():
    state = AgentState(evidence_reflection=True)
    evidence = observation(state, b"tests/test_a.py::test_a PASSED", code=None,
                           error={"type": "timeout"})
    assert evidence["timed_out"]
    assert evidence["test_delta"] is None
    assert is_non_product_signal(evidence)


def test_delta_compares_explicit_outcomes_only():
    state = AgentState(evidence_reflection=True)
    observation(state, "FAILED tests/test_a.py::test_a - assert 1\nFAILED tests/test_a.py::test_b\nPASSED tests/test_a.py::test_c")
    evidence = observation(state, "PASSED tests/test_a.py::test_a\nFAILED tests/test_a.py::test_c", generation=2)
    delta = evidence["test_delta"]
    assert delta["fixed_tests"] == ["tests/test_a.py::test_a"]
    assert delta["newly_failed_tests"] == ["tests/test_a.py::test_c"]
    assert delta["previously_observed_not_reported"] == ["tests/test_a.py::test_b"]
    assert not delta["still_failing_tests"]


def test_scope_and_missing_outcomes_are_not_comparable():
    state = AgentState(evidence_reflection=True)
    observation(state, "FAILED tests/test_a.py::test_a")
    assert observation(state, "PASSED tests/test_a.py::test_a", code=0, scope="targeted")["test_delta"] is None
    assert observation(state, "1 passed", code=0)["test_delta"] is None
    assert not state.recovery_active


def test_recovery_route_keeps_candidate_and_diff_gates():
    state = AgentState(phase="verify", evidence_reflection=True, recovery_active=True,
                       has_reproduction_evidence=True, workspace_generation=1)
    state.remember_candidate("pkg/app.py", reason="read", evidence="read")
    names = {tool["name"] for tool in build_tools_for_state(state)}
    assert {"python_repl", "grep", "undo", "edit_file"} <= names
    assert "search_graph" not in names
    policy = ToolPolicy()
    assert policy.validate(state=state, tool_name="edit_file", tool_input={"relative_path": "pkg/app.py"}) is None
    assert policy.validate(state=state, tool_name="edit_file", tool_input={"relative_path": "pkg/other.py"}) is not None
    assert policy.validate(state=state, tool_name="run_tests", tool_input={}) is not None
    state.recovery_active = False
    assert policy.validate(state=state, tool_name="edit_file", tool_input={"relative_path": "pkg/app.py"}) is not None
