"""Run-local state for a single agent repair invocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agent.code_intelligence import CodeIntelligenceBackend
from app.agent.memory import AgentState, FailureSignature
from app.agent.policy import PolicyConfig
from app.runtime.harness import RunPaths
from app.schemas.task_schema import Task
from app.schemas.trace_schema import Trace


@dataclass
class RunContext:
    """Encapsulates all mutable state for one agent run() invocation.

    Replaces 17 local variables + 11 inner closures that previously
    captured them via ``nonlocal``. After migration, ``run()`` becomes
    a thin orchestration layer: build context -> loop -> finalize.
    """

    # --- injected at construction ---
    task: Task
    policy_config: PolicyConfig
    agent_state: AgentState
    trace: Trace
    run_paths: RunPaths
    code_intelligence_backend: CodeIntelligenceBackend
    tool_executor: Any       # ToolExecutor – avoid circular import at module level
    tool_policy: Any         # ToolPolicy
    repository_root: Path
    source_repo_path: Path
    system_prompt: str
    strategy_memory_path: Path

    # --- mutable run state (formerly local variables in run()) ---
    messages: list[dict[str, Any]] = field(default_factory=list)
    latest_failure_summary: dict[str, Any] | None = None
    search_match_files: list[str] = field(default_factory=list)
    searched_queries: set[str] = field(default_factory=set)

    final_summary: str = ""
    final_status: str = "incomplete"
    last_test_exit_code: int | None = None
    last_test_summary: str = ""
    pre_test_exit_code: int | None = None
    pre_test_summary: str = ""
    post_test_exit_code: int | None = None
    post_test_summary: str = ""
    workspace_generation: int = 0
    verified_generation: int | None = None
    last_full_verified_generation: int | None = None
    last_full_verified_exit_code: int | None = None
    ever_used_tool: bool = False
    pending_auto_verification: bool = False
    max_iterations_reached: bool = True
    write_history: list[dict[str, str]] = field(default_factory=list)
    anti_loop_injected: bool = False
    successful_write_before_repro_count: int = 0
    last_failure_signature_before_patch: FailureSignature | None = None
    recorded_phase_milestones: set[str] = field(default_factory=lambda: {"understand"})
    llm_call_count: int = 0
    llm_total_tokens: int = 0
    llm_missing_usage_count: int = 0
    total_tool_schema_sent: int = 0
    tools_by_phase: dict[str, list[str]] = field(default_factory=dict)
    llm_config: Any = None  # LLMConfig – avoid circular import
    client: Any = None

    # --- migrated closures ---

    def already_full_verified_current_generation(self) -> bool:
        return (
            self.workspace_generation > 0
            and self.verified_generation == self.workspace_generation
            and self.last_full_verified_generation == self.workspace_generation
            and self.last_full_verified_exit_code == 0
        )

    def can_auto_finalize_current_generation(self) -> bool:
        return (
            self.already_full_verified_current_generation()
            and self.agent_state.workspace_generation == self.workspace_generation
            and self.agent_state.diff_observed_generation == self.workspace_generation
            and not self.pending_auto_verification
        )

    def record_phase_milestone(self, phase: str, *, summary: str, evidence: dict | None = None) -> None:
        if phase in self.recorded_phase_milestones:
            return
        self.recorded_phase_milestones.add(phase)
        self.trace.steps.append(
            {
                "step_index": len(self.trace.steps) + 1,
                "action_type": "phase_milestone",
                "tool_name": None,
                "tool_input": evidence or {},
                "tool_output_summary": summary,
                "observation": summary,
                "decision": f"Phase evidence satisfied, recording {phase.upper()} milestone.",
                "phase": phase,
                "state_snapshot": self.agent_state.snapshot(),
                "evidence_ids": [f"phase:{phase}"],
                "verification_strength": self.agent_state.verification_strength,
                "tool_metrics": {"phase": phase},
            }
        )

    def refresh_localization_candidates(self) -> None:
        from app.agent.code_locator import rank_candidates

        self.agent_state.set_localization_candidates(
            rank_candidates(
                repo_path=self.run_paths.workspace_dir,
                issue_text=self.agent_state.issue_summary,
                target_files_hint=self.task.target_files_hint,
                failure_summary=self.latest_failure_summary,
                search_match_files=self.search_match_files,
                existing_candidates=self.agent_state.localization_candidates,
            )
        )

    def run_immediate_auto_verification(self) -> str:
        from time import perf_counter
        from app.agent.verification import build_targeted_pytest_command, strength_after_test
        from app.agent.reflector import reflect_after_failed_verification, build_reflection_message
        from app.agent.memory import FailureSignature
        from app.agent.tool_executor import ToolExecutor

        diff_input = {"source": "immediate_auto_verification"}
        diff_started_at = perf_counter()
        diff_result_for_model = self.tool_executor.execute("show_diff", diff_input)
        diff_duration_sec = round(perf_counter() - diff_started_at, 4)
        if diff_result_for_model.get("ok"):
            self.agent_state.remember_diff_observed()
        self._append_tool_trace_step(
            tool_name="show_diff",
            tool_input=diff_input,
            tool_result=diff_result_for_model,
            duration_sec=diff_duration_sec,
            decision="Show diff immediately after write.",
        )

        targeted_result_for_model: dict[str, Any] | None = None
        targeted_command = build_targeted_pytest_command(
            base_command=self.task.test_command,
            failure_summary=self.latest_failure_summary,
        )
        if targeted_command:
            targeted_input = {
                "timeout_sec": 120,
                "command": targeted_command,
                "verification_scope": "targeted",
                "source": "immediate_auto_verification",
            }
            targeted_started_at = perf_counter()
            previous_test_command = self.tool_executor.test_command
            self.tool_executor.test_command = targeted_command
            try:
                targeted_result_for_model = self.tool_executor.execute("run_tests", targeted_input)
            finally:
                self.tool_executor.test_command = previous_test_command
            targeted_duration_sec = round(perf_counter() - targeted_started_at, 4)
            self._append_tool_trace_step(
                tool_name="run_tests",
                tool_input=targeted_input,
                tool_result=targeted_result_for_model,
                duration_sec=targeted_duration_sec,
                decision="Run targeted test after write.",
            )
            self.agent_state.verification_strength = strength_after_test(
                current=self.agent_state.verification_strength,
                exit_code=targeted_result_for_model.get("data", {}).get("exit_code"),
                workspace_generation=0,
                command_source=str(self.task.metadata.get("test_command_source", "")),
            )

        tool_input = {"timeout_sec": 120, "verification_scope": "full", "source": "immediate_auto_verification"}
        tool_started_at = perf_counter()
        tool_result = self.tool_executor.execute("run_tests", tool_input)
        tool_duration_sec = round(perf_counter() - tool_started_at, 4)
        self.last_test_exit_code = tool_result.get("data", {}).get("exit_code")
        self.last_test_summary = tool_result.get("summary", "")
        self.post_test_exit_code = self.last_test_exit_code
        self.post_test_summary = self.last_test_summary
        self.verified_generation = self.workspace_generation
        self.last_full_verified_generation = self.workspace_generation
        self.last_full_verified_exit_code = self.last_test_exit_code
        self.pending_auto_verification = False
        self.agent_state.has_reproduction_evidence = True
        if self.agent_state.reproduction_evidence_kind != "weak_static":
            self.agent_state.reproduction_evidence_kind = "test"
        self.record_phase_milestone(
            "reproduce",
            summary="Auto run_tests provided reproduction or verification evidence.",
            evidence={"exit_code": self.last_test_exit_code, "workspace_generation": self.workspace_generation},
        )
        self.agent_state.verification_strength = strength_after_test(
            current=self.agent_state.verification_strength,
            exit_code=self.last_test_exit_code,
            workspace_generation=self.workspace_generation,
            command_source=str(self.task.metadata.get("test_command_source", "")),
        )
        failure_summary = tool_result.get("data", {}).get("failure_summary")
        if failure_summary:
            if self.last_test_exit_code not in {0, None}:
                self.run_guided_failure_search(failure_summary, source="immediate_auto_verification")
            self.latest_failure_summary = failure_summary
            self.agent_state.failure_signature = FailureSignature.from_failure_summary(failure_summary)
            self.refresh_localization_candidates()
        if self.last_test_exit_code not in {0, None}:
            self._inject_context_diff_into_failure(
                tool_result=tool_result,
                diff_result=diff_result_for_model,
                max_chars=self.llm_config.max_tool_chars,
            )
        if self.last_test_exit_code == 0 and self.workspace_generation > 0:
            self.record_phase_milestone(
                "verify",
                summary="Auto full run_tests passed, verification evidence recorded.",
                evidence={"exit_code": self.last_test_exit_code, "workspace_generation": self.workspace_generation},
            )
        self._append_tool_trace_step(
            tool_name="run_tests",
            tool_input=tool_input,
            tool_result=tool_result,
            duration_sec=tool_duration_sec,
            decision="Auto run_tests after write; results fed back to model.",
        )

        auto_reflection_message = ""
        if self.last_test_exit_code not in {0, None}:
            changed_files = diff_result_for_model.get("data", {}).get("changed_files", [])
            reflection_decision = reflect_after_failed_verification(
                state=self.agent_state,
                previous_failure_signature=self.last_failure_signature_before_patch,
                current_failure_signature=self.agent_state.failure_signature,
                changed_files=changed_files,
                max_patch_files=self.policy_config.max_patch_files,
            )
            self.agent_state.phase = reflection_decision.next_phase
            auto_reflection_message = build_reflection_message(reflection_decision)
            if reflection_decision.should_undo:
                undo_result = self.auto_undo_after_reflection(reflection_decision.likely_cause)
                auto_reflection_message += (
                    "\n\nAUTO_UNDO_RESULT:\n"
                    f"{ToolExecutor.summarize_for_model(undo_result, max_chars=self.llm_config.max_tool_chars)}"
                )

        auto_verification_parts = [
            "IMMEDIATE_AUTO_VERIFICATION: show_diff and run_tests executed automatically after write.",
            "show_diff:\n"
            f"{ToolExecutor.summarize_for_model(diff_result_for_model, max_chars=self.llm_config.max_tool_chars)}",
        ]
        if targeted_result_for_model:
            auto_verification_parts.append(
                "targeted_run_tests:\n"
                f"{ToolExecutor.summarize_for_model(targeted_result_for_model, max_chars=self.llm_config.max_tool_chars)}"
            )
        auto_verification_parts.append(
            "run_tests:\n"
            f"{ToolExecutor.summarize_for_model(tool_result, max_chars=self.llm_config.max_tool_chars)}"
        )
        if auto_reflection_message:
            auto_verification_parts.append(auto_reflection_message)
        return "\n\n" + "\n\n".join(auto_verification_parts)

    @staticmethod
    def _inject_context_diff_into_failure(
        *,
        tool_result: dict[str, Any],
        diff_result: dict[str, Any],
        max_chars: int,
    ) -> None:
        failure_summary = tool_result.get("data", {}).get("failure_summary")
        if not failure_summary or tool_result.get("ok", False):
            return
        diff_text = diff_result.get("data", {}).get("diff_text", "")
        if not diff_text:
            return
        if len(diff_text) > max_chars:
            diff_text = f"{diff_text[:max_chars]}\n...<truncated>"
        failure_summary["context_diff"] = diff_text
        failure_summary["context_diff_changed_files"] = diff_result.get("data", {}).get("changed_files", [])

    def run_guided_failure_search(self, failure_summary: dict[str, Any] | None, *, source: str) -> None:
        if not self._should_run_guided_failure_search(failure_summary):
            return
        from time import perf_counter

        assert failure_summary is not None
        guided_results: list[dict[str, Any]] = []
        symbols = [str(item).strip() for item in failure_summary.get("possible_symbols", [])][:3]
        skipped_symbols: list[dict[str, str]] = []
        for symbol in symbols:
            if not symbol:
                continue
            normalized_symbol = symbol.casefold()
            already_covered = any(
                normalized_symbol in query or query in normalized_symbol
                for query in self.searched_queries
            )
            if already_covered:
                skipped_symbols.append({"query": symbol, "reason": "already_searched"})
                continue
            tool_input = {"query": symbol, "source": source, "automatic": True}
            self.searched_queries.add(normalized_symbol)
            started_at = perf_counter()
            search_result = self.tool_executor.execute("search_code", tool_input)
            duration_sec = round(perf_counter() - started_at, 4)
            match_files = [
                str(path).replace("\\", "/")
                for path in search_result.get("data", {}).get("match_files", [])[:5]
            ]
            guided_results.append({
                "query": symbol,
                "match_count": search_result.get("data", {}).get("match_count", 0),
                "match_files": match_files,
                "matches": search_result.get("data", {}).get("matches", [])[:5],
            })
            for relative_path in match_files:
                if relative_path and relative_path not in self.search_match_files:
                    self.search_match_files.append(relative_path)
                if relative_path:
                    self.agent_state.remember_candidate(
                        relative_path,
                        reason="guided_failure_search",
                        evidence=f"run_tests exception symbol `{symbol}` matched this file.",
                        confidence=0.6,
                    )
            self._append_tool_trace_step(
                tool_name="search_code",
                tool_input=tool_input,
                tool_result=search_result,
                duration_sec=duration_sec,
                decision="Auto search for possible symbols after test failure.",
            )
        if guided_results:
            failure_summary["guided_search"] = guided_results
            self.refresh_localization_candidates()
        if skipped_symbols:
            failure_summary["guided_search_skipped"] = skipped_symbols

    @staticmethod
    def _should_run_guided_failure_search(failure_summary: dict[str, Any] | None) -> bool:
        if not failure_summary:
            return False
        if failure_summary.get("locations"):
            return False
        if failure_summary.get("guided_search"):
            return False
        return bool(failure_summary.get("possible_symbols"))

    def auto_undo_after_reflection(self, reason: str) -> dict[str, Any]:
        from time import perf_counter

        undo_started_at = perf_counter()
        undo_result = self.tool_executor.execute("undo", {})
        undo_duration_sec = round(perf_counter() - undo_started_at, 4)
        if undo_result.get("ok"):
            self.workspace_generation += 1
            self.agent_state.remember_workspace_write()
            self.pending_auto_verification = False
            self.agent_state.modified_files = []
        self._append_tool_trace_step(
            tool_name="undo",
            tool_input={"reason": reason, "automatic": True},
            tool_result=undo_result,
            duration_sec=undo_duration_sec,
            decision="Reflection decided to undo recent patch; executing automatically.",
        )
        return undo_result

    def _append_tool_trace_step(
        self,
        *,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any],
        duration_sec: float,
        decision: str,
    ) -> None:
        from app.schemas.trace_schema import TraceStep

        self.trace.steps.append(
            TraceStep(
                step_index=len(self.trace.steps) + 1,
                action_type="tool_call",
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output_summary=tool_result.get("summary", ""),
                observation=str(tool_result),
                decision=decision,
                phase=self.agent_state.phase,
                state_snapshot=self.agent_state.snapshot(),
                verification_strength=self.agent_state.verification_strength,
                duration_sec=duration_sec,
            )
        )


        tool_name = block["name"]
        tool_input = block.get("input", {})
        if (
            tool_name == "run_tests"
            and str(tool_input.get("verification_scope", "full")) != "targeted"
            and self.already_full_verified_current_generation()
        ):
            return {
                "block": block,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "tool_result": self.skipped_duplicate_full_verification_result(tool_input),
                "tool_duration_sec": 0.0,
            }
        return self._execute_tool_block(
            tool_executor=self.tool_executor,
            tool_policy=self.tool_policy,
            state=self.agent_state,
            block=block,
        )

    def _execute_tool_block(
        self,
        *,
        tool_executor,
        tool_policy,
        state: AgentState,
        block: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single tool block with policy check."""
        from time import perf_counter

        tool_name = block["name"]
        tool_input = block.get("input", {})
        tool_started_at = perf_counter()
        policy_result = tool_policy.validate(
            state=state,
            tool_name=tool_name,
            tool_input=tool_input,
        )
        tool_result = policy_result or tool_executor.execute(tool_name, tool_input)
        tool_duration_sec = round(perf_counter() - tool_started_at, 4)
        return {
            "block": block,
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_result": tool_result,
            "tool_duration_sec": tool_duration_sec,
        }

    def skipped_duplicate_full_verification_result(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "tool_name": "run_tests",
            "summary": "Skipping duplicate full run_tests: current generation already verified.",
            "data": {
                "exit_code": 0,
                "duration_sec": 0.0,
                "verification_scope": "full",
                "workspace_generation": self.workspace_generation,
                "verified_generation": self.verified_generation,
                "deduped": True,
                "tool_input": tool_input,
            },
            "error": None,
        }


        from app.schemas.trace_schema import TraceStep

        self.trace.steps.append(
            TraceStep(
                step_index=len(self.trace.steps) + 1,
                action_type="auto_finalize",
                tool_name=None,
                tool_input={
                    "source": source,
                    "workspace_generation": self.workspace_generation,
                    "verified_generation": self.verified_generation,
                    "diff_observed_generation": self.agent_state.diff_observed_generation,
                },
                tool_output_summary="Current patch generation has diff evidence and full verification.",
                observation="AUTO_FINALIZE: diff observed and full verification passed.",
                decision="Early exit LLM loop, proceed to final results.",
                timestamp=self.agent_state.issue_summary[:30],
                duration_sec=None,
                phase=self.agent_state.phase,
                state_snapshot=self.agent_state.snapshot(),
                evidence_ids=[
                    f"workspace_generation:{self.workspace_generation}",
                    "diff:observed",
                    "verification:full",
                ],
                verification_strength=self.agent_state.verification_strength,
                tool_metrics={
                    "auto_finalize_reason": "full_verified_current_generation",
                    "last_full_verified_exit_code": self.last_full_verified_exit_code,
                },
            )
        )


        self.messages = ctx._microcompact_messages(
            self.messages, max_chars=self.llm_config.max_tool_chars
        )
        self.messages, compressed, before_chars, after_chars = ctx._compress_messages_if_needed(
            self.messages,
            max_context_chars=self.llm_config.max_context_chars,
        )
        if not compressed:
            return
        self.trace.steps.append(
            {
                "step_index": len(self.trace.steps) + 1,
                "action_type": "context_compression",
                "tool_name": None,
                "tool_input": {"reason": reason},
                "tool_output_summary": f"Context compressed from {before_chars} to {after_chars} chars.",
                "observation": "Old messages summarized, keeping initial input and recent conversation.",
                "decision": "Continue LLM loop, avoid exceeding context threshold.",
                "phase": self.agent_state.phase,
                "state_snapshot": self.agent_state.snapshot(),
                "verification_strength": self.agent_state.verification_strength,
                "tool_metrics": {
                    "before_chars": before_chars,
                    "after_chars": after_chars,
                    "max_context_chars": self.llm_config.max_context_chars,
                },
            }
        )
