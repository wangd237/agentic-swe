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
