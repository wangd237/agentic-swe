from __future__ import annotations

from app.agent.run_metrics import compute_agent_run_metrics
from app.schemas.trace_schema import Trace, TraceStep


def make_step(
    index: int,
    *,
    phase: str,
    tool_name: str | None = None,
    ok: bool = True,
    tool_input: dict | None = None,
) -> TraceStep:
    return TraceStep(
        step_index=index,
        action_type="tool_call" if tool_name else "planning",
        tool_name=tool_name,
        tool_input=tool_input or {},
        phase=phase,
        tool_metrics={"ok": ok} if tool_name else {},
    )


def test_compute_agent_run_metrics_rewards_disciplined_full_verification() -> None:
    trace = Trace(
        task_id="task",
        run_id="run",
        steps=[
            make_step(1, phase="understand"),
            make_step(2, phase="reproduce", tool_name="run_tests"),
            make_step(3, phase="localize", tool_name="read_file"),
            make_step(4, phase="patch", tool_name="write_file"),
            make_step(5, phase="verify", tool_name="run_tests"),
            make_step(6, phase="final", tool_name="show_diff"),
        ],
    )

    metrics = compute_agent_run_metrics(
        trace=trace,
        final_status="success",
        verification_strength="full",
        patch_applied=True,
        workspace_generation=1,
        verified_generation=1,
        write_before_repro_count=0,
        modified_files=["demo_pkg/app.py"],
        localization_candidate_paths=["demo_pkg/app.py", "tests/test_app.py"],
    )

    assert metrics.to_dict() == {
        "phase_completion_rate": 1.0,
        "pre_repro_rate": 1.0,
        "write_before_repro_count": 0,
        "policy_violation_count": 0,
        "patch_changed_file_count": 1,
        "unverified_patch_rate": 0.0,
        "success_full_verify_rate": 1.0,
        "weak_success_rate": 0.0,
        "undo_recovery_rate": 0.0,
        "localization_precision_at_3": 1.0,
    }


def test_compute_agent_run_metrics_flags_weak_unverified_and_auto_undo() -> None:
    trace = Trace(
        task_id="task",
        run_id="run",
        steps=[
            make_step(1, phase="understand", tool_name="write_file"),
            make_step(2, phase="verify", tool_name="undo", tool_input={"automatic": True}),
        ],
    )
    trace.steps[0].tool_metrics["policy_blocked"] = True

    metrics = compute_agent_run_metrics(
        trace=trace,
        final_status="success_weak_verification",
        verification_strength="weak",
        patch_applied=True,
        workspace_generation=2,
        verified_generation=1,
        write_before_repro_count=1,
        modified_files=["demo_pkg/app.py", "demo_pkg/extra.py"],
        localization_candidate_paths=["tests/test_app.py", "demo_pkg/app.py"],
    )

    assert metrics.phase_completion_rate == 0.3333
    assert metrics.pre_repro_rate == 0.0
    assert metrics.write_before_repro_count == 1
    assert metrics.policy_violation_count == 1
    assert metrics.patch_changed_file_count == 2
    assert metrics.unverified_patch_rate == 1.0
    assert metrics.success_full_verify_rate == 0.0
    assert metrics.weak_success_rate == 1.0
    assert metrics.undo_recovery_rate == 1.0
    assert metrics.localization_precision_at_3 == 0.5


def test_compute_agent_run_metrics_counts_failed_pre_patch_test_as_reproduction() -> None:
    trace = Trace(
        task_id="task",
        run_id="run",
        steps=[
            make_step(1, phase="reproduce", tool_name="run_tests", ok=False),
            make_step(2, phase="patch", tool_name="write_file"),
        ],
    )
    trace.steps[0].tool_metrics["error_type"] = "test_failure"

    metrics = compute_agent_run_metrics(
        trace=trace,
        final_status="incomplete",
        verification_strength="none",
        patch_applied=True,
        workspace_generation=1,
        verified_generation=None,
        write_before_repro_count=0,
        modified_files=["demo_pkg/app.py"],
        localization_candidate_paths=["demo_pkg/app.py"],
    )

    assert metrics.pre_repro_rate == 1.0


def test_compute_agent_run_metrics_normalizes_localization_paths() -> None:
    trace = Trace(task_id="task", run_id="run", steps=[])

    metrics = compute_agent_run_metrics(
        trace=trace,
        final_status="incomplete",
        verification_strength="none",
        patch_applied=False,
        workspace_generation=0,
        verified_generation=None,
        write_before_repro_count=0,
        modified_files=[r"demo_pkg\app.py"],
        localization_candidate_paths=["demo_pkg/app.py"],
    )

    assert metrics.localization_precision_at_3 == 1.0
