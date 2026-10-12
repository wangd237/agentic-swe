"""Shared post-edit verification for immediate, stop, and budget-exhausted paths."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Literal

from app.agent.memory import AgentState, FailureSignature
from app.agent.policy import PolicyConfig
from app.agent.reflector import build_reflection_message, reflect_after_failed_verification
from app.agent.tool_executor import ToolExecutor
from app.agent.verification import build_targeted_pytest_command, strength_after_test
from app.schemas.task_schema import Task
from app.schemas.trace_schema import Trace, TraceStep

VerificationSource = Literal[
    "immediate_auto_verification", "auto_verification", "final_pending_verification"
]


@dataclass(frozen=True)
class AutoVerificationOutcome:
    test_exit_code: int | None
    test_summary: str
    verified_generation: int
    latest_failure_summary: dict[str, Any] | None
    message: str


def execute_auto_verification(
    *,
    agent: Any,
    source: VerificationSource,
    tool_executor: ToolExecutor,
    task: Task,
    trace: Trace,
    agent_state: AgentState,
    policy_config: PolicyConfig,
    workspace_generation: int,
    latest_failure_summary: dict[str, Any] | None,
    last_failure_signature_before_patch: FailureSignature | None,
    record_phase_milestone: Callable[..., None],
    refresh_localization_candidates: Callable[[], None],
    run_guided_failure_search: Callable[..., None],
    auto_undo_after_reflection: Callable[[str], dict[str, Any]],
) -> AutoVerificationOutcome:
    """Run diff, optional targeted test, full test, then reflection in trace order.

    The three original paths deliberately differ in tool metadata, trace wording,
    and whether targeted tests and guided failure search are used.
    """
    immediate = source == "immediate_auto_verification"
    final_pending = source == "final_pending_verification"
    diff_input = {"source": source} if (immediate or final_pending) else {}
    diff_execution_input = {} if final_pending else diff_input
    diff_started = perf_counter()
    diff_result = tool_executor.execute("show_diff", diff_execution_input)
    diff_duration = round(perf_counter() - diff_started, 4)
    if diff_result.get("ok"):
        agent_state.remember_diff_observed()

    diff_decision = (
        "写入成功后立即查看 diff，减少模型单独决策验证步骤."
        if immediate else (
            "达到最大迭代次数但仍存在未验证改动，最终兜底先查看 diff。"
            if final_pending else "模型停止前存在未验证改动，先查看 diff 再自动运行测试。"
        )
    )
    # Keep the immediate-path original wording (including Chinese punctuation).
    if immediate:
        diff_decision = "写入成功后立即查看 diff，减少模型单独决策验证步骤。"
    agent._append_tool_trace_step(
        trace=trace, state=agent_state, tool_name="show_diff",
        tool_input=diff_input, tool_result=diff_result,
        duration_sec=diff_duration, decision=diff_decision,
    )

    targeted_result: dict[str, Any] | None = None
    if not final_pending:
        targeted_command = build_targeted_pytest_command(
            base_command=task.test_command,
            failure_summary=latest_failure_summary,
        )
        if targeted_command:
            targeted_input: dict[str, Any] = {
                "timeout_sec": 120,
                "command": targeted_command,
                "verification_scope": "targeted",
            }
            if immediate:
                targeted_input["source"] = source
            targeted_started = perf_counter()
            previous_test_command = tool_executor.test_command
            tool_executor.test_command = targeted_command
            try:
                targeted_result = tool_executor.execute("run_tests", targeted_input)
            finally:
                tool_executor.test_command = previous_test_command
            targeted_duration = round(perf_counter() - targeted_started, 4)
            agent._append_tool_trace_step(
                trace=trace, state=agent_state, tool_name="run_tests",
                tool_input=targeted_input, tool_result=targeted_result,
                duration_sec=targeted_duration,
                decision=(
                    "写入成功后立即运行失败节点的 targeted test。"
                    if immediate else
                    "模型停止前存在未验证改动，先运行失败节点的 targeted test。"
                ),
            )
            agent_state.verification_strength = strength_after_test(
                current=agent_state.verification_strength,
                exit_code=targeted_result.get("data", {}).get("exit_code"),
                workspace_generation=0,
                command_source=str(task.metadata.get("test_command_source", "")),
            )

    full_input: dict[str, Any] = {"timeout_sec": 120, "verification_scope": "full"}
    if immediate or final_pending:
        full_input["source"] = source
    full_started = perf_counter()
    full_result = tool_executor.execute("run_tests", full_input)
    full_duration = round(perf_counter() - full_started, 4)
    test_exit_code = full_result.get("data", {}).get("exit_code")
    test_summary = full_result.get("summary", "")
    agent_state.has_reproduction_evidence = True
    if agent_state.reproduction_evidence_kind != "weak_static":
        agent_state.reproduction_evidence_kind = "test"

    repro_messages = {
        "immediate_auto_verification": "立即自动 run_tests 已提供复现或验证证据。",
        "auto_verification": "自动 run_tests 已提供复现或验证证据。",
        "final_pending_verification": "最终兜底 run_tests 已提供验证证据。",
    }
    record_phase_milestone(
        "reproduce",
        summary=repro_messages[source],
        evidence={
            "exit_code": test_exit_code,
            "workspace_generation": workspace_generation,
            "source": source,
        },
    )
    agent_state.verification_strength = strength_after_test(
        current=agent_state.verification_strength,
        exit_code=test_exit_code,
        workspace_generation=workspace_generation,
        command_source=str(task.metadata.get("test_command_source", "")),
    )
    failure_summary = full_result.get("data", {}).get("failure_summary")
    if failure_summary:
        if immediate and test_exit_code not in {0, None}:
            run_guided_failure_search(failure_summary, source=source)
        latest_failure_summary = failure_summary
        agent_state.failure_signature = FailureSignature.from_failure_summary(failure_summary)
        refresh_localization_candidates()
    if test_exit_code not in {0, None}:
        agent._inject_context_diff_into_failure(
            tool_result=full_result,
            diff_result=diff_result,
            max_chars=agent.llm_config.max_tool_chars,
        )
    if test_exit_code == 0 and workspace_generation > 0:
        verified_messages = {
            "immediate_auto_verification": "立即自动 full run_tests 已通过，具备验证证据。",
            "auto_verification": "自动 full run_tests 已通过，具备验证证据。",
            "final_pending_verification": "最终兜底 full run_tests 已通过，具备验证证据。",
        }
        record_phase_milestone(
            "verify",
            summary=verified_messages[source],
            evidence={
                "exit_code": test_exit_code,
                "workspace_generation": workspace_generation,
                "source": source,
            },
        )
    full_decisions = {
        "immediate_auto_verification": "写入成功后立即运行测试，并把验证结果与写入结果同轮回喂给模型。",
        "auto_verification": "模型停止前存在未验证改动，自动运行测试并把结果回喂给模型。",
        "final_pending_verification": "达到最大迭代次数但仍存在未验证改动，最终兜底运行 full tests。",
    }
    agent._append_tool_trace_step(
        trace=trace, state=agent_state, tool_name="run_tests",
        tool_input=full_input, tool_result=full_result,
        duration_sec=full_duration, decision=full_decisions[source],
    )

    reflection_message = ""
    if test_exit_code not in {0, None}:
        changed_files = diff_result.get("data", {}).get("changed_files", [])
        reflection = reflect_after_failed_verification(
            state=agent_state,
            previous_failure_signature=last_failure_signature_before_patch,
            current_failure_signature=agent_state.failure_signature,
            changed_files=changed_files,
            max_patch_files=policy_config.max_patch_files,
        )
        agent_state.phase = reflection.next_phase
        reflection_message = build_reflection_message(reflection)
        reflection_decisions = {
            "immediate_auto_verification": f"立即自动验证失败后反思，转入 {reflection.next_phase} 阶段。",
            "auto_verification": f"自动验证失败后反思，转入 {reflection.next_phase} 阶段。",
            "final_pending_verification": f"最终兜底验证失败后反思，转入 {reflection.next_phase} 阶段。",
        }
        trace.steps.append(
            TraceStep(
                step_index=len(trace.steps) + 1,
                action_type="reflection",
                tool_name=None,
                tool_input={"changed_files": changed_files, "source": source},
                tool_output_summary=reflection.likely_cause,
                observation=reflection_message,
                decision=reflection_decisions[source],
                timestamp=agent._utc_timestamp(),
                duration_sec=None,
                phase=agent_state.phase,
                state_snapshot=agent_state.snapshot(),
                evidence_ids=[
                    f"reflection:{reflection.likely_cause}",
                    *(f"diff:{path}" for path in changed_files[:5]),
                ],
                reflection_type=reflection.likely_cause,
                verification_strength=agent_state.verification_strength,
                tool_metrics=reflection.model_dump(mode="json"),
            )
        )
        if reflection.should_undo:
            undo_result = auto_undo_after_reflection(reflection.likely_cause)
            if not final_pending:
                reflection_message += (
                    "\n\nAUTO_UNDO_RESULT:\n"
                    f"{ToolExecutor.summarize_for_model(undo_result, max_chars=agent.llm_config.max_tool_chars)}"
                )

    message = ""
    if not final_pending:
        introduction = (
            "IMMEDIATE_AUTO_VERIFICATION: 写入工具成功后，系统已立即执行 show_diff "
            "和 run_tests，以减少模型单独决策验证步骤。"
            if immediate else
            "你刚才停止了，但当前 workspace 存在尚未由模型确认的改动。"
            "系统已自动执行 show_diff 和 run_tests。请根据下面结果继续修正，"
            "或者在测试通过时给出最终结论。"
        )
        parts = [
            introduction,
            "show_diff:\n" + ToolExecutor.summarize_for_model(
                diff_result, max_chars=agent.llm_config.max_tool_chars,
            ),
        ]
        if targeted_result:
            parts.append(
                "targeted_run_tests:\n" + ToolExecutor.summarize_for_model(
                    targeted_result, max_chars=agent.llm_config.max_tool_chars,
                )
            )
        parts.append(
            "run_tests:\n" + ToolExecutor.summarize_for_model(
                full_result, max_chars=agent.llm_config.max_tool_chars,
            )
        )
        if reflection_message:
            parts.append(reflection_message)
        message = ("\n\n" if immediate else "") + "\n\n".join(parts)

    return AutoVerificationOutcome(
        test_exit_code=test_exit_code,
        test_summary=test_summary,
        verified_generation=workspace_generation,
        latest_failure_summary=latest_failure_summary,
        message=message,
    )
