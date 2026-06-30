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

    def execute_tool_block_or_skip(self, block: dict[str, Any]) -> dict[str, Any]:
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
