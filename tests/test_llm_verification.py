"""Regression coverage for the three extracted auto-verification paths."""

from types import SimpleNamespace

from app.agent.llm_verification import execute_auto_verification
from app.agent.memory import AgentState
from app.agent.policy import PolicyConfig


class FakeExecutor:
    def __init__(self) -> None:
        self.test_command = "python -m pytest tests/test_app.py -q"
        self.calls: list[tuple[str, dict]] = []

    def execute(self, name: str, params: dict) -> dict:
        self.calls.append((name, dict(params)))
        if name == "show_diff":
            return {
                "ok": True,
                "summary": "diff",
                "data": {"changed_files": ["pkg/app.py"], "diff_text": "+fixed"},
            }
        assert name == "run_tests"
        return {
            "ok": True,
            "summary": "tests passed",
            "data": {"exit_code": 0, "failure_summary": {}},
        }


class FakeAgent:
    llm_config = SimpleNamespace(max_tool_chars=4000)

    def __init__(self) -> None:
        self.trace_calls: list[str] = []

    def _append_tool_trace_step(self, *, tool_name: str, **kwargs) -> None:
        self.trace_calls.append(tool_name)

    @staticmethod
    def _utc_timestamp() -> str:
        return "2026-10-12T00:00:00Z"

    @staticmethod
    def _inject_context_diff_into_failure(**kwargs) -> None:
        raise AssertionError("successful verification must not inject a failure diff")


def _verify(source: str):
    executor = FakeExecutor()
    agent = FakeAgent()
    state = AgentState(phase="verify", workspace_generation=1)
    milestones: list[str] = []
    outcome = execute_auto_verification(
        agent=agent,
        source=source,
        tool_executor=executor,
        task=SimpleNamespace(
            test_command=executor.test_command,
            metadata={},
        ),
        trace=SimpleNamespace(steps=[]),
        agent_state=state,
        policy_config=PolicyConfig(policy_id="test", description="test"),
        workspace_generation=1,
        latest_failure_summary={"failed_tests": ["tests/test_app.py::test_bug"]},
        last_failure_signature_before_patch=None,
        record_phase_milestone=lambda phase, **kwargs: milestones.append(phase),
        refresh_localization_candidates=lambda: None,
        run_guided_failure_search=lambda *args, **kwargs: None,
        auto_undo_after_reflection=lambda cause: {},
    )
    return executor, agent, state, outcome, milestones


def test_immediate_verification_runs_targeted_then_full_and_restores_command() -> None:
    executor, agent, state, result, milestones = _verify("immediate_auto_verification")

    assert [name for name, _ in executor.calls] == [
        "show_diff", "run_tests", "run_tests",
    ]
    assert [name for name, _ in executor.calls] == agent.trace_calls
    assert executor.calls[1][1]["verification_scope"] == "targeted"
    assert executor.calls[1][1]["source"] == "immediate_auto_verification"
    assert executor.calls[2][1]["verification_scope"] == "full"
    assert executor.test_command == "python -m pytest tests/test_app.py -q"
    assert result.test_exit_code == 0
    assert result.verified_generation == 1
    assert result.message.startswith("\n\nIMMEDIATE_AUTO_VERIFICATION")
    assert "targeted_run_tests:" in result.message
    assert state.verification_strength == "full"
    assert milestones == ["reproduce", "verify"]


def test_model_stop_verification_keeps_original_tool_inputs() -> None:
    executor, _, _, result, _ = _verify("auto_verification")

    assert len(executor.calls) == 3
    assert executor.calls[0][1] == {}
    assert "source" not in executor.calls[1][1]
    assert "source" not in executor.calls[2][1]
    assert result.message.startswith("你刚才停止了")


def test_budget_fallback_runs_full_test_without_targeted_test() -> None:
    executor, agent, state, result, milestones = _verify("final_pending_verification")

    assert [name for name, _ in executor.calls] == ["show_diff", "run_tests"]
    assert agent.trace_calls == ["show_diff", "run_tests"]
    assert executor.calls[0][1] == {}
    assert executor.calls[1][1]["source"] == "final_pending_verification"
    assert result.message == ""
    assert result.test_exit_code == 0
    assert state.verification_strength == "full"
    assert milestones == ["reproduce", "verify"]
