"""Finish an Agent run: classify, report, persist evidence and strategy memory."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.agent.run_metrics import compute_agent_run_metrics
from app.agent.strategy_memory import append_strategy_memory, distill_strategy_memory_entry
from app.agent.tool_router import SCHEMA_STRATEGY_PHASE_STATE_FILTERED
from app.agent.verification import adjust_final_status_for_verification
from app.agent.verifier import (
    accepted_final_status_from_report,
    build_verification_evidence,
    build_verifier_report,
)
from app.runtime.logger import write_json, write_text
from app.schemas.result_schema import Result
from app.schemas.trace_schema import TraceStep


class AgentFinalizationMixin:
    """Final result assembly and artifact persistence; no Agent loop decisions."""

    def _finalize_run(
        self,
        *,
        tool_executor: Any,
        run_paths: Any,
        agent_state: Any,
        task: Any,
        trace: Any,
        policy_config: Any,
        started_at: float,
        last_test_exit_code: int | None,
        pre_test_exit_code: int | None,
        post_test_exit_code: int | None,
        pre_test_summary: str,
        post_test_summary: str,
        last_test_summary: str,
        verified_generation: int | None,
        workspace_generation: int,
        ever_used_tool: bool,
        max_iterations_reached: bool,
        final_summary: str,
        latest_failure_summary: Any,
        successful_write_before_repro_count: int,
        code_intelligence_result: Any,
        code_intelligence_backend: Any,
        llm_call_count: int,
        llm_total_tokens: int,
        llm_prompt_tokens: int,
        llm_missing_usage_count: int,
        llm_missing_prompt_usage_count: int,
        total_tool_schema_sent: int,
        tools_by_phase: Any,
        strategy_memory_path: Any,
        run_id: str,
    ) -> dict[str, Any]:
        diff_result = tool_executor.execute("show_diff", {})
        if diff_result.get("ok"):
            agent_state.remember_diff_observed()
        patch_text = diff_result.get("data", {}).get("diff_text", "")
        write_text(run_paths.patch_diff_path, patch_text)
        patch_applied = bool(diff_result.get("data", {}).get("changed_files"))
        final_status, incomplete_reason = self._classify_final_state(
            patch_applied=patch_applied,
            last_test_exit_code=last_test_exit_code,
            verified_generation=verified_generation,
            workspace_generation=workspace_generation,
            ever_used_tool=ever_used_tool,
            max_iterations_reached=max_iterations_reached,
            model_reported_incomplete=self._model_reported_incomplete(final_summary),
            reproduction_evidence_kind=agent_state.reproduction_evidence_kind,
            verification_strength=agent_state.verification_strength,
        )
        final_status, incomplete_reason = adjust_final_status_for_verification(
            final_status=final_status,
            incomplete_reason=incomplete_reason,
            verification_strength=agent_state.verification_strength,
            patch_applied=patch_applied,
        )
        modified_files = diff_result.get("data", {}).get("changed_files", [])
        observed_failure = ""
        if latest_failure_summary:
            failure_type = str(latest_failure_summary.get("type", "")).strip()
            failure_message = str(latest_failure_summary.get("message", "")).strip()
            observed_failure = ": ".join(
                part for part in [failure_type, failure_message] if part
            )
        verification_evidence = build_verification_evidence(
            patch_applied=patch_applied,
            modified_files=modified_files,
            verification_strength=agent_state.verification_strength,
            test_command=task.test_command,
            pre_test_exit_code=pre_test_exit_code,
            post_test_exit_code=post_test_exit_code,
            pre_test_summary=pre_test_summary,
            post_test_summary=post_test_summary,
            observed_failure=observed_failure,
            source_type=task.source_type,
            task_metadata=task.metadata,
        )
        verifier_report = build_verifier_report(
            final_status=final_status,
            verification_strength=agent_state.verification_strength,
            patch_applied=patch_applied,
            modified_files=modified_files,
            pre_test_exit_code=pre_test_exit_code,
            post_test_exit_code=post_test_exit_code,
            source_type=task.source_type,
            task_metadata=task.metadata,
            verification_evidence=verification_evidence,
        )
        accepted_final_status = accepted_final_status_from_report(verifier_report)

        duration_sec = round(perf_counter() - started_at, 4)
        if incomplete_reason == "weak_verification":
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="verification_audit",
                    tool_name=None,
                    tool_input={
                        "final_status": final_status,
                        "verification_strength": agent_state.verification_strength,
                        "patch_applied": patch_applied,
                        "verified_generation": verified_generation,
                        "workspace_generation": workspace_generation,
                    },
                    tool_output_summary="最终结果缺少 full verification，已记录弱验证审计。",
                    observation=(
                        "VERIFICATION_AUDIT: final result is downgraded because verification "
                        f"strength is `{agent_state.verification_strength}`, not `full`."
                    ),
                    decision="保留补丁结果，但禁止把弱验证报告为普通成功。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=None,
                    phase=agent_state.phase,
                    state_snapshot=agent_state.snapshot(),
                    evidence_ids=[
                        f"verification:{agent_state.verification_strength}",
                        "audit:weak_verification",
                    ],
                    reflection_type="weak_verification",
                    verification_strength=agent_state.verification_strength,
                    tool_metrics={
                        "final_status": final_status,
                        "incomplete_reason": incomplete_reason,
                        "requires_full_verification": True,
                    },
                )
            )
        agent_state.phase = "final"
        trace.steps.append(
            TraceStep(
                step_index=len(trace.steps) + 1,
                action_type="finalize",
                tool_name=None,
                tool_input={},
                tool_output_summary=final_status,
                observation=final_summary or "LLM agent 运行结束。",
                decision=(
                    "根据补丁、验证强度和最终测试结果生成可审计的运行结论。"
                ),
                timestamp=self._utc_timestamp(),
                duration_sec=None,
                phase=agent_state.phase,
                state_snapshot=agent_state.snapshot(),
                evidence_ids=[
                    f"final:{final_status}",
                    f"accepted:{accepted_final_status}",
                    f"verification:{agent_state.verification_strength}",
                    f"verifier:{verifier_report.verification_level}",
                ],
                verification_strength=agent_state.verification_strength,
                tool_metrics={
                    "final_status": final_status,
                    "accepted_final_status": accepted_final_status,
                    "incomplete_reason": incomplete_reason,
                    "patch_applied": patch_applied,
                    "verified_generation": verified_generation,
                    "workspace_generation": workspace_generation,
                    "verifier_report": verifier_report.to_dict(),
                    "verification_evidence": verification_evidence.to_dict(),
                },
            )
        )
        trace.final_status = final_status
        trace.finished_at = self._utc_timestamp()
        context_compression_steps = [
            step for step in trace.steps
            if step.action_type == "context_compression"
        ]
        run_metrics = compute_agent_run_metrics(
            trace=trace,
            final_status=final_status,
            verification_strength=agent_state.verification_strength,
            patch_applied=patch_applied,
            workspace_generation=workspace_generation,
            verified_generation=verified_generation,
            write_before_repro_count=successful_write_before_repro_count,
            modified_files=modified_files,
            localization_candidate_paths=[
                candidate.relative_path
                for candidate in agent_state.localization_candidates
            ],
        )

        result = Result(
            task_id=task.task_id,
            run_id=run_id,
            final_status=final_status,
            accepted_final_status=accepted_final_status,
            incomplete_reason=incomplete_reason,
            summary=final_summary or "LLM agent 运行结束。",
            test_command=task.test_command,
            test_exit_code=last_test_exit_code,
            pre_test_exit_code=pre_test_exit_code,
            post_test_exit_code=post_test_exit_code,
            pre_test_summary=pre_test_summary,
            post_test_summary=post_test_summary,
            test_summary=last_test_summary or final_summary or "",
            patch_applied=patch_applied,
            patch_summary=diff_result.get("summary", ""),
            modified_files=modified_files,
            duration_sec=duration_sec,
            tool_stats={
                "policy_id": policy_config.policy_id,
                "agent_type": policy_config.agent_type,
                "llm_provider": self.llm_config.provider,
                "llm_model": self.llm_config.model,
                "total_tool_calls": trace.total_tool_calls,
                "max_iterations": self.llm_config.max_iterations,
                "max_iterations_reached": max_iterations_reached,
                "workspace_generation": workspace_generation,
                "verified_generation": verified_generation,
                "incomplete_reason": incomplete_reason,
                "accepted_final_status": accepted_final_status,
                "context_compression_count": len(context_compression_steps),
                "final_phase": agent_state.phase,
                "verification_strength": agent_state.verification_strength,
                "verifier_report": verifier_report.to_dict(),
                "verification_evidence": verification_evidence.to_dict(),
                "write_before_repro_count": successful_write_before_repro_count,
                "localization_candidate_count": len(agent_state.localization_candidates),
                "code_intelligence": code_intelligence_result.to_dict(),
                "llm_usage": {
                    "call_count": llm_call_count,
                    "total_tokens": llm_total_tokens,
                    "prompt_tokens": llm_prompt_tokens,
                    "missing_usage_count": llm_missing_usage_count,
                    "missing_prompt_usage_count": llm_missing_prompt_usage_count,
                },
                "tool_routing": {
                    "schema_strategy": SCHEMA_STRATEGY_PHASE_STATE_FILTERED,
                    "total_tool_schema_sent": total_tool_schema_sent,
                    "avg_tool_schema_count": round(
                        total_tool_schema_sent / llm_call_count,
                        2,
                    ) if llm_call_count else 0.0,
                    "tools_by_phase": tools_by_phase,
                },
                "agent_core_metrics": run_metrics.to_dict(),
                "strategy_memory_path": str(strategy_memory_path),
                "verification_records": {
                    "pre": {
                        "exit_code": pre_test_exit_code,
                        "summary": pre_test_summary,
                    },
                    "post": {
                        "exit_code": post_test_exit_code,
                        "summary": post_test_summary,
                    },
                },
            },
            recommended_files=trace.read_files[:],
            verifier_report=verifier_report.to_dict(),
            verification_evidence=verification_evidence.to_dict(),
        )

        memory_entry = distill_strategy_memory_entry(
            state=agent_state,
            trace=trace,
            result=result,
            trace_path=run_paths.trace_json_path,
            result_path=run_paths.result_json_path,
        )
        append_strategy_memory(strategy_memory_path, memory_entry)

        code_intelligence_backend.cleanup()

        write_json(run_paths.trace_json_path, trace)
        write_json(run_paths.result_json_path, result)
        write_text(
            run_paths.summary_md_path,
            (
                "# LLM Agent Run Summary\n\n"
                f"- task_id: `{task.task_id}`\n"
                f"- run_id: `{run_id}`\n"
                f"- final_status: `{final_status}`\n"
                f"- accepted_final_status: `{accepted_final_status}`\n"
                f"- agent_type: `{policy_config.agent_type}`\n"
                f"- policy_id: `{policy_config.policy_id}`\n"
                f"- llm_provider: `{self.llm_config.provider}`\n"
                f"- llm_model: `{self.llm_config.model}`\n"
                f"- total_tool_calls: `{trace.total_tool_calls}`\n"
                f"- incomplete_reason: `{incomplete_reason or 'none'}`\n"
                f"- final_phase: `{agent_state.phase}`\n"
                f"- verification_strength: `{agent_state.verification_strength}`\n"
                f"- verification_level: `{verifier_report.verification_level}`\n"
                f"- evidence_quality: `{verifier_report.evidence_quality}`\n"
                f"- missing_evidence: `{', '.join(verifier_report.missing_evidence) or 'none'}`\n"
                f"- verifier_accepted: `{verifier_report.accepted}`\n"
                f"- risk_level: `{verifier_report.risk_level}`\n"
                f"- evidence_scope: `{verification_evidence.verification_scope}`\n"
                f"- evidence_pre_exit_code: `{verification_evidence.pre_test.get('exit_code')}`\n"
                f"- evidence_post_exit_code: `{verification_evidence.post_test.get('exit_code')}`\n"
                f"- evidence_official_harness_required: `{verification_evidence.official_harness.get('required')}`\n"
                f"- summary: {final_summary or '无'}\n"
            ),
        )

        return {
            "task": task.to_dict(),
            "result": result.to_dict(),
            "trace": trace.to_dict(),
            "run_paths": run_paths.to_dict(),
        }

