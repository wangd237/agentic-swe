"""最小 LLM coding agent。"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from app.agent.base import BaseAgent
from app.agent.code_intelligence import build_code_intelligence_backend
from app.agent.code_locator import rank_candidates
from app.agent.llm_client import OpenAICompatibleChatClient
from app.agent.llm_config import DEFAULT_LLM_CONFIG, LLMConfig
from app.agent.llm_context import AgentContextMixin
from app.agent.llm_finalization import AgentFinalizationMixin
from app.agent.llm_prompts import build_system_prompt, build_user_prompt
from app.agent.llm_tool_helpers import AgentToolMixin
from app.agent.llm_verification import execute_auto_verification
from app.agent.memory import AgentState, FailureSignature
from app.agent.policy import load_policy_config
from app.agent.reflector import build_reflection_message, reflect_after_failed_verification
from app.agent.strategy_memory import format_strategy_memory_hints, retrieve_strategy_memories
from app.agent.tool_definitions import read_only_tool_names
from app.agent.tool_executor import ToolExecutor
from app.agent.tool_policy import ToolPolicy, next_phase_after_tool
from app.agent.tool_router import SCHEMA_STRATEGY_PHASE_STATE_FILTERED, build_tools_for_state, tool_names
from app.agent.verification import initial_verification_strength, strength_after_test
from app.runtime.harness import COPY_IGNORE_DIR_NAMES, build_run_paths, copy_repo_to_workspace, next_run_id
from app.runtime.logger import write_json
from app.schemas.task_schema import load_task
from app.schemas.trace_schema import Trace, TraceStep

READ_ONLY_TOOL_NAMES = read_only_tool_names()


def _resolve_test_patch_path(
    *,
    source_repo_path: str | Path,
    source_type: str = "",
) -> Path | None:
    """Return the test.patch path for a SWE-bench Lite task, or None."""
    if source_type != "swe_bench_lite":
        return None
    repo = Path(source_repo_path).resolve()
    slug = repo.name
    artifacts_dir = repo.parent.parent / slug
    candidate = artifacts_dir / "test.patch"
    return candidate if candidate.exists() else None


ANTI_LOOP_MESSAGE = (
    "你似乎在同一个修复方向上循环：最近连续多次修改同一个文件，"
    "且编辑模式高度相似。请退一步重新读取相关代码或测试，验证你的核心假设；"
    "如果涉及第三方库行为，优先用 python_repl 查询实际行为，然后再修改。"
)
EDIT_RECOVERY_MESSAGE = (
    "EDIT_RECOVERY_NOTICE: edit_file 没有找到 old_string。请优先使用工具结果里的 "
    "similar_contexts[].suggested_old_string 作为下一次 edit_file 的 old_string；"
    "如果仍不确定，请 read_file 读取该建议行号附近的最新内容后再编辑。"
)


class LLMCodeAgent(AgentContextMixin, AgentToolMixin, AgentFinalizationMixin, BaseAgent):
    """基于工具调用循环的最小 coding agent。"""

    def __init__(
        self,
        *,
        llm_config: LLMConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.llm_config = llm_config or DEFAULT_LLM_CONFIG
        self.client = client

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_assistant_blocks(response: dict[str, Any]) -> list[dict[str, Any]]:
        content = response.get("content", [])
        normalized: list[dict[str, Any]] = []
        for block in content:
            block_type = block.get("type")
            if block_type == "text":
                normalized.append({"type": "text", "text": block.get("text", "")})
            elif block_type == "tool_use":
                normalized.append(
                    {
                        "type": "tool_use",
                        "id": block.get("id", ""),
                        "name": block.get("name", ""),
                        "input": block.get("input", {}),
                    }
                )
        return normalized

    @staticmethod
    def _response_total_tokens(response: dict[str, Any]) -> int | None:
        usage = response.get("usage")
        if not isinstance(usage, dict):
            return None
        value = usage.get("total_tokens")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _response_prompt_tokens(response: dict[str, Any]) -> int | None:
        """API 返回的 prompt_tokens，作为上下文 token 估算的实测锚点。"""
        usage = response.get("usage")
        if not isinstance(usage, dict):
            return None
        value = usage.get("prompt_tokens")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _extract_text(content_blocks: list[dict[str, Any]]) -> str:
        texts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
        return "\n".join(part for part in texts if part).strip()

    @staticmethod
    def _model_reported_incomplete(text: str) -> bool:
        normalized_text = text.lower()
        incomplete_markers = [
            "未完成",
            "无法完成",
            "不能完成",
            "还需要继续",
            "需要继续",
            "没有全部完成",
            "not complete",
            "incomplete",
            "cannot complete",
            "unable to complete",
        ]
        return any(marker in normalized_text for marker in incomplete_markers)

    @staticmethod
    def _classify_final_state(
        *,
        patch_applied: bool,
        last_test_exit_code: int | None,
        verified_generation: int | None,
        workspace_generation: int,
        ever_used_tool: bool,
        max_iterations_reached: bool,
        model_reported_incomplete: bool,
        reproduction_evidence_kind: str = "none",
        verification_strength: str = "none",
    ) -> tuple[str, str]:
        if model_reported_incomplete and not max_iterations_reached:
            return "incomplete", "task_incomplete"
        if (
            patch_applied
            and last_test_exit_code == 0
            and verified_generation == workspace_generation
        ):
            return "success", ""
        if (
            patch_applied
            and reproduction_evidence_kind == "weak_static"
            and verification_strength == "weak"
            and verified_generation == workspace_generation
        ):
            return "success", ""
        if not ever_used_tool:
            return "stopped_without_verification", "no_tool_calls"
        if max_iterations_reached:
            return "incomplete", "max_iterations"
        if not patch_applied:
            return "incomplete", "no_patch"
        if last_test_exit_code is not None and last_test_exit_code != 0:
            return "incomplete", "failed_tests"
        if last_test_exit_code is None:
            return "incomplete", "no_tests_run"
        if verified_generation != workspace_generation:
            return "incomplete", "unverified_patch"
        return "incomplete", "unknown"

    def run(
        self,
        *,
        task_path: str | Path,
        repo_root: str | Path,
        policy_path: str | Path | None = None,
    ) -> dict:
        started_at = perf_counter()
        repository_root = Path(repo_root).resolve()
        task = load_task(task_path)
        policy_config = load_policy_config(policy_path)
        LLMConfig.load_env_file(repository_root)
        if self.llm_config == DEFAULT_LLM_CONFIG:
            self.llm_config = LLMConfig.from_policy(policy_config)
        if self.client is None:
            self.client = OpenAICompatibleChatClient(self.llm_config)
        source_repo_path = (repository_root / task.repo_path).resolve()

        if not source_repo_path.exists():
            raise FileNotFoundError(f"任务 repo 不存在: {source_repo_path}")

        task_runs_dir = repository_root / "logs" / "trajectories" / task.task_id
        run_id = next_run_id(task_runs_dir)
        run_paths = build_run_paths(repository_root / "logs" / "trajectories", task.task_id, run_id)
        run_paths.run_dir.mkdir(parents=True, exist_ok=True)
        run_paths.tool_outputs_dir.mkdir(parents=True, exist_ok=True)

        workspace_copy_started_at = perf_counter()
        _test_patch_path = _resolve_test_patch_path(
            source_repo_path=source_repo_path,
            source_type=task.source_type,
        )
        copy_repo_to_workspace(
            source_repo_path,
            run_paths.workspace_dir,
            test_patch_path=_test_patch_path,
        )
        workspace_copy_duration_sec = round(perf_counter() - workspace_copy_started_at, 4)

        trace = Trace(task_id=task.task_id, run_id=run_id, started_at=self._utc_timestamp())
        agent_state = AgentState(
            phase="understand",
            issue_summary=f"{task.issue_title}\n{task.issue_text}".strip(),
            verification_strength=initial_verification_strength(task.metadata),
        )
        metadata_verification_strength = str(task.metadata.get("verification_strength", "")).strip().lower()
        metadata_test_source = str(task.metadata.get("test_command_source", "")).strip().lower()
        if metadata_verification_strength in {"weak", "none"} or metadata_test_source == "pytest_fallback":
            agent_state.has_reproduction_evidence = True
            agent_state.reproduction_evidence_kind = "weak_static"
        latest_failure_summary: dict[str, Any] | None = None
        search_match_files: list[str] = []
        searched_queries: set[str] = set()
        code_intelligence_backend = build_code_intelligence_backend(policy_config)
        code_intelligence_result = code_intelligence_backend.collect_localization_hints(
            repo_path=run_paths.workspace_dir,
            issue_text=agent_state.issue_summary,
            max_results=policy_config.code_intelligence_max_results,
        )
        agent_state.set_localization_candidates(
            rank_candidates(
                repo_path=run_paths.workspace_dir,
                issue_text=agent_state.issue_summary,
                target_files_hint=task.target_files_hint,
                existing_candidates=code_intelligence_result.candidates,
            )
        )
        trace.steps.append(
            TraceStep(
                step_index=1,
                action_type="workspace_prep",
                tool_name="copy_workspace",
                tool_input={
                    "source_repo_path": str(source_repo_path),
                    "workspace_path": str(run_paths.workspace_dir),
                },
                tool_output_summary="已完成 benchmark repo 到工作副本的复制。",
                observation="LLM agent 将在隔离 workspace 中运行。",
                decision="继续进入工具观察与修复阶段。",
                timestamp=self._utc_timestamp(),
                duration_sec=workspace_copy_duration_sec,
                phase=agent_state.phase,
                state_snapshot=agent_state.snapshot(),
                evidence_ids=["workspace:copy"],
                verification_strength=agent_state.verification_strength,
                tool_metrics={
                    "ignored_dir_count": len(COPY_IGNORE_DIR_NAMES),
                    "code_intelligence": {
                        "backend": code_intelligence_result.backend,
                        "enabled": code_intelligence_result.enabled,
                        "available": code_intelligence_result.available,
                        "fallback_reason": code_intelligence_result.fallback_reason,
                    },
                },
            )
        )
        if code_intelligence_result.enabled:
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="code_intelligence",
                    tool_name=code_intelligence_result.backend,
                    tool_input={
                        "backend": code_intelligence_result.backend,
                        "max_results": policy_config.code_intelligence_max_results,
                    },
                    tool_output_summary=(
                        f"code intelligence backend returned "
                        f"{len(code_intelligence_result.candidates)} candidates"
                    ),
                    observation=code_intelligence_result.compact_hints
                    or code_intelligence_result.fallback_reason
                    or "no graph hints",
                    decision="将 graph-assisted localization hints 作为弱定位先验合并进候选列表。",
                    timestamp=self._utc_timestamp(),
                    phase=agent_state.phase,
                    state_snapshot=agent_state.snapshot(),
                    evidence_ids=[
                        f"code_intelligence:{code_intelligence_result.backend}",
                        f"fallback:{code_intelligence_result.fallback_reason or 'none'}",
                    ],
                    verification_strength=agent_state.verification_strength,
                    tool_metrics=code_intelligence_result.to_dict(),
                )
            )
        write_json(run_paths.task_json_path, task)

        tool_executor = ToolExecutor(
            repo_path=run_paths.workspace_dir,
            original_repo_path=source_repo_path,
            policy_config=policy_config,
            test_command=task.test_command,
            code_intelligence_backend=code_intelligence_backend,
        )
        tool_policy = ToolPolicy()
        system_prompt = build_system_prompt()
        strategy_memory_path = repository_root / "logs" / "agent_memory" / "strategy_memory.jsonl"
        retrieved_memories = retrieve_strategy_memories(
            memory_path=strategy_memory_path,
            issue_text=agent_state.issue_summary,
            target_files_hint=task.target_files_hint,
        )
        memory_hints = format_strategy_memory_hints(retrieved_memories)
        user_prompt = build_user_prompt(task)
        if memory_hints:
            user_prompt = f"{user_prompt}\n\n{memory_hints}"
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="memory_retrieval",
                    tool_name=None,
                    tool_input={
                        "memory_path": str(strategy_memory_path),
                        "issue_text": agent_state.issue_summary,
                        "target_files_hint": task.target_files_hint,
                    },
                    tool_output_summary=f"检索到 {len(retrieved_memories)} 条 strategy memory。",
                    observation=memory_hints,
                    decision="将相关历史修复经验作为弱先验加入初始上下文。",
                    timestamp=self._utc_timestamp(),
                    phase=agent_state.phase,
                    state_snapshot=agent_state.snapshot(),
                    evidence_ids=[
                        f"memory:{entry.task_id}:{entry.run_id}"
                        for entry in retrieved_memories
                    ],
                    verification_strength=agent_state.verification_strength,
                    tool_metrics={
                        "retrieved_memory_count": len(retrieved_memories),
                        "memory_task_ids": [entry.task_id for entry in retrieved_memories],
                    },
                )
            )
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": user_prompt,
            }
        ]

        final_summary = ""
        last_test_exit_code: int | None = None
        last_test_summary = ""
        pre_test_exit_code: int | None = None
        pre_test_summary = ""
        post_test_exit_code: int | None = None
        post_test_summary = ""
        workspace_generation = 0
        verified_generation: int | None = None
        last_full_verified_generation: int | None = None
        last_full_verified_exit_code: int | None = None
        ever_used_tool = False
        pending_auto_verification = False
        max_iterations_reached = True
        write_history: list[dict[str, str]] = []
        anti_loop_injected = False
        successful_write_before_repro_count = 0
        last_failure_signature_before_patch: FailureSignature | None = None
        recorded_phase_milestones = {"understand"}
        llm_call_count = 0
        empty_response_retries = 0
        llm_total_tokens = 0
        llm_prompt_tokens = 0
        llm_missing_usage_count = 0
        llm_missing_prompt_usage_count = 0
        last_measured_prompt_tokens: int | None = None
        total_tool_schema_sent = 0
        tools_by_phase: dict[str, list[str]] = {}

        def record_phase_milestone(phase: str, *, summary: str, evidence: dict[str, Any] | None = None) -> None:
            if phase in recorded_phase_milestones:
                return
            recorded_phase_milestones.add(phase)
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="phase_milestone",
                    tool_name=None,
                    tool_input=evidence or {},
                    tool_output_summary=summary,
                    observation=summary,
                    decision=f"阶段证据已满足，记录 {phase.upper()} 里程碑。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=None,
                    phase=phase,
                    state_snapshot=agent_state.snapshot(),
                    evidence_ids=[f"phase:{phase}"],
                    verification_strength=agent_state.verification_strength,
                    tool_metrics={"phase": phase},
                )
            )

        def refresh_localization_candidates() -> None:
            agent_state.set_localization_candidates(
                rank_candidates(
                    repo_path=run_paths.workspace_dir,
                    issue_text=agent_state.issue_summary,
                    target_files_hint=task.target_files_hint,
                    failure_summary=latest_failure_summary,
                    search_match_files=search_match_files,
                    existing_candidates=agent_state.localization_candidates,
                )
            )

        def run_guided_failure_search(failure_summary: dict[str, Any] | None, *, source: str) -> None:
            if not self._should_run_guided_failure_search(failure_summary):
                return
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
                    for query in searched_queries
                )
                if already_covered:
                    skipped_symbols.append({"query": symbol, "reason": "already_searched"})
                    continue
                tool_input = {
                    "query": symbol,
                    "source": source,
                    "automatic": True,
                }
                searched_queries.add(normalized_symbol)
                started_at = perf_counter()
                search_result = tool_executor.execute("search_code", tool_input)
                duration_sec = round(perf_counter() - started_at, 4)
                matches = search_result.get("data", {}).get("matches", [])[:10]
                match_files = [
                    str(path).replace("\\", "/")
                    for path in search_result.get("data", {}).get("match_files", [])[:5]
                ]
                guided_results.append(
                    {
                        "query": symbol,
                        "match_count": search_result.get("data", {}).get("match_count", 0),
                        "match_files": match_files,
                        "matches": matches[:5],
                    }
                )
                for relative_path in match_files:
                    if relative_path and relative_path not in search_match_files:
                        search_match_files.append(relative_path)
                    if relative_path:
                        agent_state.remember_candidate(
                            relative_path,
                            reason="guided_failure_search",
                            evidence=f"run_tests exception symbol `{symbol}` matched this file.",
                            confidence=0.6,
                        )
                self._append_tool_trace_step(
                    trace=trace,
                    state=agent_state,
                    tool_name="search_code",
                    tool_input=tool_input,
                    tool_result=search_result,
                    duration_sec=duration_sec,
                    decision="run_tests 失败后根据 possible_symbols 自动执行只读搜索，补充定位信号。",
                )
            if guided_results:
                failure_summary["guided_search"] = guided_results
                refresh_localization_candidates()
            if skipped_symbols:
                failure_summary["guided_search_skipped"] = skipped_symbols

        if agent_state.localization_candidates:
            record_phase_milestone(
                "localize",
                summary="初始任务提示和代码索引已生成候选定位文件。",
                evidence={
                    "candidate_files": [
                        candidate.relative_path
                        for candidate in agent_state.localization_candidates[:3]
                    ],
                    "source": "initial_candidate_ranking",
                },
            )
            if agent_state.reproduction_evidence_kind == "weak_static":
                agent_state.phase = "patch"
                record_phase_milestone(
                    "patch",
                    summary="任务显式标记为弱/静态验证，允许在定位候选范围内进入 PATCH。",
                    evidence={
                        "reproduction_evidence_kind": agent_state.reproduction_evidence_kind,
                        "verification_strength": agent_state.verification_strength,
                        "source": "task_metadata",
                    },
                )

        def auto_undo_after_reflection(reason: str) -> dict[str, Any]:
            nonlocal workspace_generation, pending_auto_verification
            undo_started_at = perf_counter()
            undo_result = tool_executor.execute("undo", {})
            undo_duration_sec = round(perf_counter() - undo_started_at, 4)
            if undo_result.get("ok"):
                workspace_generation += 1
                agent_state.remember_workspace_write()
                pending_auto_verification = False
                agent_state.modified_files = []
            self._append_tool_trace_step(
                trace=trace,
                state=agent_state,
                tool_name="undo",
                tool_input={"reason": reason, "automatic": True},
                tool_result=undo_result,
                duration_sec=undo_duration_sec,
                decision="反思判定最近补丁应回滚，自动执行 undo。",
            )
            return undo_result

        def compress_context_if_needed(reason: str) -> None:
            nonlocal messages
            messages = self._microcompact_messages(messages, max_chars=self.llm_config.max_tool_chars)
            messages, compressed, before_chars, after_chars = self._compress_messages_if_needed(
                messages,
                max_context_chars=self.llm_config.max_context_chars,
                context_window_tokens=self.llm_config.context_window_tokens,
                reserve_tokens=self.llm_config.reserve_tokens,
                measured_prompt_tokens=last_measured_prompt_tokens,
            )
            if not compressed:
                return
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="context_compression",
                    tool_name=None,
                    tool_input={"reason": reason},
                    tool_output_summary=f"上下文从 {before_chars} 字符压缩到 {after_chars} 字符。",
                    observation="旧消息已压缩为摘要，保留初始任务输入和最近对话。",
                    decision="继续 LLM 循环，避免上下文超过安全阈值。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=None,
                    phase=agent_state.phase,
                    state_snapshot=agent_state.snapshot(),
                    verification_strength=agent_state.verification_strength,
                    tool_metrics={
                        "before_chars": before_chars,
                        "after_chars": after_chars,
                        "max_context_chars": self.llm_config.max_context_chars,
                        # ADR-0002 Step 2：token 判定依据。
                        "context_window_tokens": self.llm_config.context_window_tokens,
                        "reserve_tokens": self.llm_config.reserve_tokens,
                        "estimated_tokens_at_compression": self._estimate_context_tokens(
                            messages,
                            measured_prompt_tokens=last_measured_prompt_tokens,
                        ),
                        "last_measured_prompt_tokens": last_measured_prompt_tokens,
                    },
                )
            )

        SPILL_TO_DISK_THRESHOLD_CHARS = 12000

        def _spill_large_tool_result(
            tool_result: dict[str, Any],
            tool_name: str,
            step_index: int,
        ) -> str | None:
            """工具结果超过阈值时落盘，返回落盘路径；否则返回 None。"""
            # run_tests 的完整 stdout/stderr 就在 data 里，且 LLM agent 路径
            # 没有其他落盘渠道（task_runner 的 pre/post_test_stdout 只在
            # rule-based 路径写入）——因此 run_tests 恰恰最需要 spill。
            result_text = json.dumps(tool_result, ensure_ascii=False)
            if len(result_text) <= SPILL_TO_DISK_THRESHOLD_CHARS:
                return None
            file_name = f"step_{step_index:03d}_{tool_name}.json"
            spill_path = run_paths.tool_outputs_dir / file_name
            spill_path.write_text(result_text, encoding="utf-8")
            return str(spill_path.relative_to(run_paths.run_dir))

        def already_full_verified_current_generation() -> bool:
            return (
                workspace_generation > 0
                and verified_generation == workspace_generation
                and last_full_verified_generation == workspace_generation
                and last_full_verified_exit_code == 0
            )

        def can_auto_finalize_current_generation() -> bool:
            return (
                already_full_verified_current_generation()
                and agent_state.workspace_generation == workspace_generation
                and agent_state.diff_observed_generation == workspace_generation
                and not pending_auto_verification
            )

        def append_auto_finalize_trace(source: str) -> None:
            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="auto_finalize",
                    tool_name=None,
                    tool_input={
                        "source": source,
                        "workspace_generation": workspace_generation,
                        "verified_generation": verified_generation,
                        "diff_observed_generation": agent_state.diff_observed_generation,
                    },
                    tool_output_summary="当前补丁 generation 已查看 diff 且 full run_tests 通过。",
                    observation=(
                        "AUTO_FINALIZE: 当前改动已经具备 diff 证据和 full verification，"
                        "无需再让模型发起额外的 show_diff/read_file/run_tests 探索。"
                    ),
                    decision="提前收束 LLM 循环，进入最终结果汇总。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=None,
                    phase=agent_state.phase,
                    state_snapshot=agent_state.snapshot(),
                    evidence_ids=[
                        f"workspace_generation:{workspace_generation}",
                        "diff:observed",
                        "verification:full",
                    ],
                    verification_strength=agent_state.verification_strength,
                    tool_metrics={
                        "auto_finalize_reason": "full_verified_current_generation",
                        "last_full_verified_exit_code": last_full_verified_exit_code,
                    },
                )
            )

        def skipped_duplicate_full_verification_result(tool_input: dict[str, Any]) -> dict[str, Any]:
            return {
                "ok": True,
                "tool_name": "run_tests",
                "summary": "跳过重复 full run_tests：当前 workspace generation 已经通过 full verification。",
                "data": {
                    "exit_code": 0,
                    "duration_sec": 0.0,
                    "verification_scope": "full",
                    "workspace_generation": workspace_generation,
                    "verified_generation": verified_generation,
                    "deduped": True,
                    "tool_input": tool_input,
                },
                "error": None,
            }

        def execute_tool_block_or_skip(block: dict[str, Any]) -> dict[str, Any]:
            tool_name = block["name"]
            tool_input = block.get("input", {})
            if (
                tool_name == "run_tests"
                and str(tool_input.get("verification_scope", "full")) != "targeted"
                and already_full_verified_current_generation()
            ):
                return {
                    "block": block,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_result": skipped_duplicate_full_verification_result(tool_input),
                    "tool_duration_sec": 0.0,
                }
            return self._execute_tool_block(
                tool_executor=tool_executor,
                tool_policy=tool_policy,
                state=agent_state,
                block=block,
            )

        def apply_auto_verification(source: str) -> str:
            nonlocal latest_failure_summary
            nonlocal last_test_exit_code, last_test_summary
            nonlocal post_test_exit_code, post_test_summary
            nonlocal verified_generation, pending_auto_verification
            nonlocal last_full_verified_generation, last_full_verified_exit_code

            outcome = execute_auto_verification(
                agent=self,
                source=source,
                tool_executor=tool_executor,
                task=task,
                trace=trace,
                agent_state=agent_state,
                policy_config=policy_config,
                workspace_generation=workspace_generation,
                latest_failure_summary=latest_failure_summary,
                last_failure_signature_before_patch=last_failure_signature_before_patch,
                record_phase_milestone=record_phase_milestone,
                refresh_localization_candidates=refresh_localization_candidates,
                run_guided_failure_search=run_guided_failure_search,
                auto_undo_after_reflection=auto_undo_after_reflection,
            )
            latest_failure_summary = outcome.latest_failure_summary
            last_test_exit_code = outcome.test_exit_code
            last_test_summary = outcome.test_summary
            post_test_exit_code = outcome.test_exit_code
            post_test_summary = outcome.test_summary
            verified_generation = outcome.verified_generation
            pending_auto_verification = False
            if source == "immediate_auto_verification":
                last_full_verified_generation = outcome.verified_generation
                last_full_verified_exit_code = outcome.test_exit_code
            return outcome.message

        def run_immediate_auto_verification() -> str:
            return apply_auto_verification("immediate_auto_verification")

        # 预算升级干预：轮次达 75% 且 0 写入时，注入强制总结+写 patch 指令。
        # 背景（failure_analysis.md）：click#3449 和 jsonschema#1328 两次 run 中，
        # 模型在前 25% 预算内就理解了根因，但剩余 75% 烧在重叠读/重复搜索/
        # 环境探测上，探索到死。写入侧有反循环检测，探索侧此前无任何干预。
        budget_escalation_injected = False

        def budget_escalation_needed() -> bool:
            if budget_escalation_injected:
                return False
            if workspace_generation > 0:
                return False
            threshold = max(1, int(self.llm_config.max_iterations * 0.75))
            return iteration_index + 1 >= threshold

        for iteration_index in range(self.llm_config.max_iterations):
            if can_auto_finalize_current_generation():
                append_auto_finalize_trace("loop_start")
                final_summary = "自动验证已通过，当前任务完成。"
                max_iterations_reached = False
                break

            if budget_escalation_needed():
                budget_escalation_injected = True
                escalation_message = (
                    "\n\n【系统提示·预算告警】你已用掉 75% 的迭代预算，但尚未写入任何补丁。"
                    "请立即：1) 用一句话总结你已确认的根因；"
                    "2) 直接用 edit_file 写出最小补丁（基于你已读过的代码）；"
                    "3) 不要再读新文件或搜索——系统会在写入后自动验证。"
                    "如果确实无法定位，写出你当前最佳假设的补丁并说明不确定性。"
                )
                # 拼进最后一条 user 消息尾部，不新增独立消息——
                # 避免改变消息序列结构（user->user 连续消息部分 API 不容忍），
                # 也避免隔断 assistant(tool_calls) 与 tool_result 的配对。
                if messages and messages[-1].get("role") == "user":
                    last_content = messages[-1].get("content")
                    if isinstance(last_content, str):
                        messages[-1] = {
                            "role": "user",
                            "content": last_content + escalation_message,
                        }
                    elif isinstance(last_content, list):
                        # tool_result 列表：追加一个文本块，不影响 tool_use_id 配对
                        messages[-1] = {
                            "role": "user",
                            "content": [
                                *last_content,
                                {"type": "text", "text": escalation_message.strip()},
                            ],
                        }
                else:
                    messages.append(
                        {
                            "role": "user",
                            "content": escalation_message.strip(),
                        }
                    )
                trace.steps.append(
                    TraceStep(
                        step_index=len(trace.steps) + 1,
                        action_type="budget_escalation",
                        tool_name=None,
                        tool_input={
                            "iteration_index": iteration_index + 1,
                            "max_iterations": self.llm_config.max_iterations,
                            "workspace_generation": workspace_generation,
                        },
                        tool_output_summary="轮次达 75% 且 0 写入，注入预算升级干预。",
                        observation=escalation_message,
                        decision="强制模型从探索切换到写入，避免探索到死。",
                        timestamp=self._utc_timestamp(),
                        duration_sec=None,
                        phase=agent_state.phase,
                        state_snapshot=agent_state.snapshot(),
                        verification_strength=agent_state.verification_strength,
                        tool_metrics={
                            "iteration_index": iteration_index + 1,
                            "threshold": max(1, int(self.llm_config.max_iterations * 0.75)),
                        },
                    )
                )

            tools = build_tools_for_state(
                agent_state,
                code_intelligence_backend=code_intelligence_backend,
            )
            current_tool_names = tool_names(tools)
            total_tool_schema_sent += len(tools)
            tools_by_phase.setdefault(agent_state.phase, current_tool_names)
            response_started_at = perf_counter()
            response = self.client.create_message(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
            )
            response_duration_sec = round(perf_counter() - response_started_at, 4)
            llm_call_count += 1
            response_total_tokens = self._response_total_tokens(response)
            if response_total_tokens is None:
                llm_missing_usage_count += 1
            else:
                llm_total_tokens += response_total_tokens
            response_prompt_tokens = self._response_prompt_tokens(response)
            if response_prompt_tokens is None:
                llm_missing_prompt_usage_count += 1
            else:
                llm_prompt_tokens += response_prompt_tokens
                last_measured_prompt_tokens = response_prompt_tokens
            assistant_blocks = self._normalize_assistant_blocks(response)
            assistant_text = self._extract_text(assistant_blocks)
            tool_blocks = self._tool_use_blocks(assistant_blocks)
            recovered_text_tool_blocks: list[dict[str, Any]] = []
            if assistant_text and not tool_blocks:
                recovered_text_tool_blocks = self._recover_text_tool_blocks(
                    text=assistant_text,
                    allowed_tool_names=current_tool_names,
                )
                if recovered_text_tool_blocks:
                    assistant_blocks = [*assistant_blocks, *recovered_text_tool_blocks]
                    tool_blocks = recovered_text_tool_blocks
            llm_response_metrics: dict[str, Any] = {
                "content_block_count": len(assistant_blocks),
                "tool_schema_strategy": SCHEMA_STRATEGY_PHASE_STATE_FILTERED,
                "tool_schema_count": len(tools),
                "tool_schema_names": current_tool_names,
            }
            if response_total_tokens is not None:
                llm_response_metrics["llm_total_tokens"] = response_total_tokens
            if response_prompt_tokens is not None:
                llm_response_metrics["llm_prompt_tokens"] = response_prompt_tokens
                # ADR-0002 Step 1：字符估算 vs 实测 prompt_tokens 对照，量化压缩触发时机的偏差。
                llm_response_metrics["context_char_estimate"] = self._message_char_estimate(messages)
                llm_response_metrics["char_to_prompt_token_ratio"] = round(
                    self._message_char_estimate(messages) / response_prompt_tokens,
                    3,
                )
            if recovered_text_tool_blocks:
                llm_response_metrics["recovered_text_tool_call_count"] = len(recovered_text_tool_blocks)
                llm_response_metrics["recovered_text_tool_names"] = [
                    str(block.get("name", "")) for block in recovered_text_tool_blocks
                ]

            trace.steps.append(
                TraceStep(
                    step_index=len(trace.steps) + 1,
                    action_type="llm_response",
                    tool_name=None,
                    tool_input={"iteration_index": iteration_index + 1},
                    tool_output_summary=assistant_text[:400] or "模型返回了工具调用。",
                    observation=f"模型在第 {iteration_index + 1} 轮给出响应。",
                    decision="解析工具调用并继续执行。",
                    timestamp=self._utc_timestamp(),
                    duration_sec=response_duration_sec,
                    phase=agent_state.phase,
                    state_snapshot=agent_state.snapshot(),
                    verification_strength=agent_state.verification_strength,
                    tool_metrics=llm_response_metrics,
                )
            )
            if assistant_text and tool_blocks:
                agent_state.remember_hypothesis(assistant_text)
                trace.steps.append(
                    TraceStep(
                        step_index=len(trace.steps) + 1,
                        action_type="planning",
                        tool_name=None,
                        tool_input={"iteration_index": iteration_index + 1},
                        tool_output_summary=assistant_text[:400],
                        observation=assistant_text,
                        decision="模型在调用工具前给出计划，随后执行同轮工具调用。",
                        timestamp=self._utc_timestamp(),
                        duration_sec=None,
                        phase=agent_state.phase,
                        state_snapshot=agent_state.snapshot(),
                        verification_strength=agent_state.verification_strength,
                        tool_metrics={"planned_tool_count": len(tool_blocks)},
                    )
                )

            if assistant_blocks:
                # 空 assistant 消息（reasoning 模型偶发 content/tool_calls 双空）
                # 不能进 messages：转换成 OpenAI 协议后是 content=None 且无
                # tool_calls，严格校验的 API（DeepSeek 官方）会直接 400。
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_blocks,
                    }
                )
            compress_context_if_needed("assistant_response")

            tool_results_for_model: list[dict[str, Any]] = []
            if tool_blocks:
                ever_used_tool = True
            parallel_group_counter = 0
            auto_finalize_after_tool = False
            for batch in self._partition_tool_batches(tool_blocks):
                parallel_group_id: str | None = None
                if len(batch) > 1 and all(block.get("name") in READ_ONLY_TOOL_NAMES for block in batch):
                    parallel_group_counter += 1
                    parallel_group_id = f"iter_{iteration_index + 1}_parallel_{parallel_group_counter}"
                    batch_results: list[dict[str, Any] | None] = [None] * len(batch)
                    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                        future_to_index = {
                            executor.submit(
                                self._execute_tool_block,
                                tool_executor=tool_executor,
                                tool_policy=tool_policy,
                                state=agent_state.model_copy(deep=True),
                                block=block,
                            ): index
                            for index, block in enumerate(batch)
                        }
                        for future in as_completed(future_to_index):
                            batch_results[future_to_index[future]] = future.result()
                    executed_results = [result for result in batch_results if result is not None]
                else:
                    executed_results = [
                        execute_tool_block_or_skip(block)
                        for block in batch
                    ]

                for executed in executed_results:
                    block = executed["block"]
                    tool_name = executed["tool_name"]
                    tool_input = executed["tool_input"]
                    tool_result = executed["tool_result"]
                    tool_duration_sec = executed["tool_duration_sec"]

                    spill_path = _spill_large_tool_result(
                        tool_result,
                        tool_name,
                        len(trace.steps) + 1,
                    )

                    if tool_name == "read_file" and tool_result.get("ok"):
                        relative_path = tool_result["data"].get("relative_path", "")
                        if relative_path and relative_path not in trace.read_files:
                            trace.read_files.append(relative_path)
                        if relative_path:
                            record_phase_milestone(
                                "localize",
                                summary=f"已读取候选文件 {relative_path}，具备定位证据。",
                                evidence={"relative_path": relative_path, "source_tool": "read_file"},
                            )
                            agent_state.remember_read_file(relative_path)
                            agent_state.remember_candidate(
                                relative_path,
                                reason="file_read",
                                evidence="Agent read this file while localizing the issue.",
                                confidence=0.5,
                            )
                            refresh_localization_candidates()
                    if tool_name in {"search_code", "grep", "search_graph"} and tool_result.get("ok"):
                        query_text = str(
                            tool_result.get("data", {}).get("query")
                            or tool_result.get("data", {}).get("pattern")
                            or tool_input.get("query")
                            or tool_input.get("pattern")
                            or ""
                        ).strip()
                        if query_text:
                            searched_queries.add(query_text.casefold())
                        for relative_path in tool_result.get("data", {}).get("match_files", [])[:5]:
                            normalized_path = str(relative_path).replace("\\", "/")
                            if normalized_path and normalized_path not in search_match_files:
                                search_match_files.append(normalized_path)
                            if normalized_path:
                                record_phase_milestone(
                                    "localize",
                                    summary=f"{tool_name} 命中候选文件 {normalized_path}，具备定位证据。",
                                    evidence={"relative_path": normalized_path, "source_tool": tool_name},
                                )
                            agent_state.remember_candidate(
                                normalized_path,
                                reason=f"{tool_name}_hit",
                                evidence=f"{tool_name} matched this file.",
                                confidence=0.45,
                            )
                        refresh_localization_candidates()
                    if tool_name == "run_tests":
                        last_test_exit_code = tool_result.get("data", {}).get("exit_code")
                        last_test_summary = tool_result.get("summary", "")
                        policy_blocked = bool(tool_result.get("data", {}).get("policy_blocked"))
                        verification_scope = str(tool_input.get("verification_scope", "full"))
                        if not policy_blocked:
                            if workspace_generation == 0 and pre_test_exit_code is None:
                                pre_test_exit_code = last_test_exit_code
                                pre_test_summary = last_test_summary
                            if workspace_generation > 0 and verification_scope != "targeted":
                                post_test_exit_code = last_test_exit_code
                                post_test_summary = last_test_summary
                                last_full_verified_generation = workspace_generation
                                last_full_verified_exit_code = last_test_exit_code
                            verified_generation = workspace_generation
                            agent_state.has_reproduction_evidence = True
                            if agent_state.reproduction_evidence_kind != "weak_static":
                                agent_state.reproduction_evidence_kind = "test"
                            record_phase_milestone(
                                "reproduce",
                                summary="run_tests 已提供复现或验证证据。",
                                evidence={
                                    "exit_code": last_test_exit_code,
                                    "workspace_generation": workspace_generation,
                                },
                            )
                        diff_result_for_failure: dict[str, Any] | None = None
                        failure_summary = tool_result.get("data", {}).get("failure_summary")
                        if failure_summary:
                            if last_test_exit_code not in {0, None}:
                                run_guided_failure_search(failure_summary, source="agent_run_tests")
                            latest_failure_summary = failure_summary
                            agent_state.failure_signature = FailureSignature.from_failure_summary(failure_summary)
                            for location in failure_summary.get("locations", []):
                                relative_path = str(location.get("path", ""))
                                if relative_path:
                                    agent_state.remember_candidate(
                                        relative_path,
                                        reason="test_failure_location",
                                        evidence=f"run_tests reported failure location {relative_path}:{location.get('line')}",
                                        confidence=0.75,
                                    )
                            refresh_localization_candidates()
                        agent_state.verification_strength = strength_after_test(
                            current=agent_state.verification_strength,
                            exit_code=last_test_exit_code,
                            workspace_generation=workspace_generation,
                            command_source=str(task.metadata.get("test_command_source", "")),
                        )
                        if (
                            last_test_exit_code not in {0, None}
                            and workspace_generation > 0
                        ):
                            diff_result_for_failure = tool_executor.execute("show_diff", {})
                            self._inject_context_diff_into_failure(
                                tool_result=tool_result,
                                diff_result=diff_result_for_failure,
                                max_chars=self.llm_config.max_tool_chars,
                            )
                    if tool_name in {"write_file", "edit_file", "undo"} and tool_result.get("ok"):
                        if tool_name in {"write_file", "edit_file"} and not agent_state.has_reproduction_evidence:
                            successful_write_before_repro_count += 1
                        if tool_name in {"write_file", "edit_file"}:
                            last_failure_signature_before_patch = agent_state.failure_signature
                            record_phase_milestone(
                                "patch",
                                summary=f"{tool_name} 已成功修改文件。",
                                evidence={
                                    "relative_path": tool_input.get("relative_path", ""),
                                    "tool_name": tool_name,
                                },
                            )
                        workspace_generation += 1
                        agent_state.remember_workspace_write()
                        pending_auto_verification = True
                        relative_path = str(tool_input.get("relative_path", "")).replace("\\", "/")
                        agent_state.remember_modified_file(relative_path)
                        override_reason = str(tool_input.get("localization_override_reason", "")).strip()
                        if tool_name in {"write_file", "edit_file"} and relative_path and override_reason:
                            agent_state.remember_candidate(
                                relative_path,
                                reason="localization_override",
                                evidence=override_reason,
                                confidence=0.4,
                            )
                    if tool_name == "show_diff" and tool_result.get("ok"):
                        agent_state.remember_diff_observed()
                    write_signature = self._write_signature(tool_name, tool_input)
                    if write_signature and tool_result.get("ok"):
                        write_history.append(write_signature)
                    old_phase = agent_state.phase
                    agent_state.phase = next_phase_after_tool(
                        state=agent_state,
                        tool_name=tool_name,
                        tool_result=tool_result,
                    )
                    phase_hint_for_model = ""
                    if agent_state.phase == "patch" and agent_state.phase != old_phase:
                        # Inject phase transition hint when entering PATCH.
                        # 注意：不能作为独立 user 消息插入——那会隔断 assistant(tool_calls)
                        # 与 tool_result 的配对，违反 OpenAI 协议（DeepSeek 官方 API 严格校验）。
                        # 改为拼进本轮 tool_result 内容。
                        phase_hint_for_model = (
                            "\n\n【系统提示】当前阶段已切换到 PATCH。"
                            "你已经定位到目标文件和修复方向。"
                            "请根据已读代码内容，使用 edit_file 或 write_file 生成最小补丁。"
                            "如果对 old_string 不确定，先 read_file 确认原文后再 edit_file。"
                        )
                    if (
                        tool_name == "run_tests"
                        and tool_result.get("ok")
                        and workspace_generation > 0
                    ):
                        record_phase_milestone(
                            "verify",
                            summary="补丁后的 run_tests 已通过，具备验证证据。",
                            evidence={
                                "exit_code": last_test_exit_code,
                                "workspace_generation": workspace_generation,
                            },
                        )

                    self._append_tool_trace_step(
                        trace=trace,
                        state=agent_state,
                        tool_name=tool_name,
                        tool_input=tool_input,
                        tool_result=tool_result,
                        duration_sec=tool_duration_sec,
                        decision="将工具结果回喂给模型继续决策。",
                        parallel_group_id=parallel_group_id,
                    )
                    if spill_path:
                        trace.steps[-1].evidence_ids.append(f"spill:{spill_path}")

                    reflection_message_for_model = ""
                    if (
                        tool_name == "run_tests"
                        and last_test_exit_code not in {0, None}
                        and workspace_generation > 0
                    ):
                        changed_files = []
                        if diff_result_for_failure:
                            changed_files = diff_result_for_failure.get("data", {}).get("changed_files", [])
                        reflection_decision = reflect_after_failed_verification(
                            state=agent_state,
                            previous_failure_signature=last_failure_signature_before_patch,
                            current_failure_signature=agent_state.failure_signature,
                            changed_files=changed_files,
                            max_patch_files=policy_config.max_patch_files,
                        )
                        agent_state.phase = reflection_decision.next_phase
                        trace.steps.append(
                            TraceStep(
                                step_index=len(trace.steps) + 1,
                                action_type="reflection",
                                tool_name=None,
                                tool_input={"changed_files": changed_files},
                                tool_output_summary=reflection_decision.likely_cause,
                                observation=build_reflection_message(reflection_decision),
                                decision=f"反思后转入 {reflection_decision.next_phase} 阶段。",
                                timestamp=self._utc_timestamp(),
                                duration_sec=None,
                                phase=agent_state.phase,
                                state_snapshot=agent_state.snapshot(),
                                evidence_ids=[
                                    f"reflection:{reflection_decision.likely_cause}",
                                    *(f"diff:{path}" for path in changed_files[:5]),
                                ],
                                reflection_type=reflection_decision.likely_cause,
                                verification_strength=agent_state.verification_strength,
                                tool_metrics=reflection_decision.model_dump(mode="json"),
                            )
                        )
                        reflection_message_for_model = "\n\n" + build_reflection_message(reflection_decision)
                        if reflection_decision.should_undo:
                            undo_result = auto_undo_after_reflection(reflection_decision.likely_cause)
                            reflection_message_for_model += (
                                "\n\nAUTO_UNDO_RESULT:\n"
                                f"{ToolExecutor.summarize_for_model(undo_result, max_chars=self.llm_config.max_tool_chars)}"
                            )

                    anti_loop_message_for_model = ""
                    if (
                        write_signature
                        and tool_result.get("ok")
                        and not anti_loop_injected
                        and self._detect_repeated_write_loop(write_history)
                    ):
                        anti_loop_injected = True
                        trace.steps.append(
                            TraceStep(
                                step_index=len(trace.steps) + 1,
                                action_type="anti_loop",
                                tool_name=None,
                                tool_input={"recent_writes": write_history[-3:]},
                                tool_output_summary="检测到连续相似写操作，已注入反循环提醒。",
                                observation=ANTI_LOOP_MESSAGE,
                                decision="提醒模型重新验证假设，而不是继续相同修改方向。",
                                timestamp=self._utc_timestamp(),
                                duration_sec=None,
                                phase=agent_state.phase,
                                state_snapshot=agent_state.snapshot(),
                                evidence_ids=[
                                    f"anti_loop:{write_history[-1]['relative_path']}",
                                ],
                                reflection_type="anti_loop",
                                verification_strength=agent_state.verification_strength,
                                tool_metrics={
                                    "recent_write_count": 3,
                                    "relative_path": write_history[-1]["relative_path"],
                                },
                            )
                        )
                        anti_loop_message_for_model = f"\n\nANTI_LOOP_NOTICE: {ANTI_LOOP_MESSAGE}"

                    edit_recovery_message_for_model = ""
                    if (
                        tool_name == "edit_file"
                        and (tool_result.get("error") or {}).get("type") == "old_string_not_found"
                    ):
                        edit_recovery_message_for_model = f"\n\n{EDIT_RECOVERY_MESSAGE}"

                    immediate_auto_verification_message = ""
                    if (
                        tool_name in {"write_file", "edit_file"}
                        and tool_result.get("ok")
                        and pending_auto_verification
                        and verified_generation != workspace_generation
                    ):
                        immediate_auto_verification_message = run_immediate_auto_verification()

                    spill_hint_for_model = ""
                    if spill_path:
                        result_chars = len(json.dumps(tool_result, ensure_ascii=False))
                        spill_hint_for_model = (
                            f"\n\n[完整输出({result_chars}字符)已落盘至 {spill_path}。"
                            "以上为摘要预览。如需查看更多匹配行，请用 grep 重新搜索并缩小范围。]"
                        )
                    tool_results_for_model.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.get("id", ""),
                            "content": ToolExecutor.summarize_for_model(
                                tool_result,
                                max_chars=self.llm_config.max_tool_chars,
                            )
                            + phase_hint_for_model
                            + immediate_auto_verification_message
                            + reflection_message_for_model
                            + anti_loop_message_for_model
                            + edit_recovery_message_for_model
                            + spill_hint_for_model,
                        }
                    )

                    if immediate_auto_verification_message and can_auto_finalize_current_generation():
                        # 先把本轮 tool_result 补进 messages，再 break。
                        # 否则 assistant 的 tool_use 没有对应 tool_result，
                        # 严格校验的 API（如 DeepSeek 官方）会在下一轮报 400。
                        messages.append(
                            {
                                "role": "user",
                                "content": tool_results_for_model,
                            }
                        )
                        append_auto_finalize_trace("immediate_auto_verification")
                        final_summary = "自动验证已通过，当前任务完成。"
                        max_iterations_reached = False
                        auto_finalize_after_tool = True
                        break

                if auto_finalize_after_tool:
                    break

            if auto_finalize_after_tool:
                break

            if tool_results_for_model:
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results_for_model,
                    }
                )
                compress_context_if_needed("tool_results")
                continue

            if pending_auto_verification and verified_generation != workspace_generation:
                verification_message = apply_auto_verification("auto_verification")
                if can_auto_finalize_current_generation():
                    append_auto_finalize_trace("auto_verification_after_model_stop")
                    final_summary = "自动验证已通过，当前任务完成。"
                    max_iterations_reached = False
                    break
                messages.append({"role": "user", "content": verification_message})
                compress_context_if_needed("auto_verification")
                continue

            if not tool_blocks and not assistant_text:
                # 模型返回空响应（reasoning 模型思考耗尽后可能发生）。
                # 注入提醒并重试，而不是直接放弃任务。
                empty_response_retries += 1
                if empty_response_retries > self.llm_config.max_empty_response_retries:
                    final_summary = "模型连续返回空响应，任务终止。"
                    break
                trace.steps.append(
                    TraceStep(
                        step_index=len(trace.steps) + 1,
                        action_type="empty_response_retry",
                        tool_name=None,
                        tool_input={"retry_count": empty_response_retries},
                        tool_output_summary="模型返回空响应，注入提醒后重试。",
                        observation=(
                            "EMPTY_RESPONSE_NOTICE: 上一轮响应为空。"
                            "请继续任务：调用工具或给出文本结论。"
                        ),
                        decision="空响应重试，避免 reasoning 模型思考耗尽导致任务提前终止。",
                        timestamp=self._utc_timestamp(),
                        duration_sec=None,
                        phase=agent_state.phase,
                        state_snapshot=agent_state.snapshot(),
                        verification_strength=agent_state.verification_strength,
                        tool_metrics={"retry_count": empty_response_retries},
                    )
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "【系统提醒】你上一轮没有返回任何内容或工具调用。"
                            "任务尚未完成，请继续：调用工具推进修复，或给出明确结论。"
                        ),
                    }
                )
                continue

            final_summary = assistant_text or "模型结束了当前任务。"
            max_iterations_reached = False
            break

        if pending_auto_verification and verified_generation != workspace_generation:
            apply_auto_verification("final_pending_verification")

        return self._finalize_run(
            tool_executor=tool_executor,
            run_paths=run_paths,
            agent_state=agent_state,
            task=task,
            trace=trace,
            policy_config=policy_config,
            started_at=started_at,
            last_test_exit_code=last_test_exit_code,
            pre_test_exit_code=pre_test_exit_code,
            post_test_exit_code=post_test_exit_code,
            pre_test_summary=pre_test_summary,
            post_test_summary=post_test_summary,
            last_test_summary=last_test_summary,
            verified_generation=verified_generation,
            workspace_generation=workspace_generation,
            ever_used_tool=ever_used_tool,
            max_iterations_reached=max_iterations_reached,
            final_summary=final_summary,
            latest_failure_summary=latest_failure_summary,
            successful_write_before_repro_count=successful_write_before_repro_count,
            code_intelligence_result=code_intelligence_result,
            code_intelligence_backend=code_intelligence_backend,
            llm_call_count=llm_call_count,
            llm_total_tokens=llm_total_tokens,
            llm_prompt_tokens=llm_prompt_tokens,
            llm_missing_usage_count=llm_missing_usage_count,
            llm_missing_prompt_usage_count=llm_missing_prompt_usage_count,
            total_tool_schema_sent=total_tool_schema_sent,
            tools_by_phase=tools_by_phase,
            strategy_memory_path=strategy_memory_path,
            run_id=run_id,
        )
