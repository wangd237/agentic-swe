"""Tool execution, recovery, and trace helpers for the coding agent."""

from __future__ import annotations

import json
from difflib import SequenceMatcher
from time import perf_counter
from typing import Any

from app.agent.memory import AgentState
from app.agent.tool_definitions import read_only_tool_names
from app.agent.tool_executor import ToolExecutor
from app.agent.tool_policy import ToolPolicy
from app.schemas.trace_schema import Trace, TraceStep

READ_ONLY_TOOL_NAMES = read_only_tool_names()
WRITE_TOOL_NAMES = {"write_file", "edit_file"}


class AgentToolMixin:
    """Tool-related helpers; the Agent loop retains execution ownership."""

    def _append_tool_trace_step(
        self,
        *,
        trace: Trace,
        state: AgentState,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any],
        duration_sec: float,
        decision: str,
        parallel_group_id: str | None = None,
    ) -> None:
        tool_metrics = {
            "ok": tool_result.get("ok", False),
        }
        error = tool_result.get("error")
        if isinstance(error, dict):
            tool_metrics["error_type"] = error.get("type", "")
        data = tool_result.get("data")
        if isinstance(data, dict) and data.get("policy_blocked"):
            tool_metrics["policy_blocked"] = True
        if isinstance(data, dict) and data.get("deduped"):
            tool_metrics["deduped"] = True
        if parallel_group_id:
            tool_metrics["parallel_group_id"] = parallel_group_id
        trace.steps.append(
            TraceStep(
                step_index=len(trace.steps) + 1,
                action_type="tool_call",
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output_summary=tool_result.get("summary", ""),
                observation=ToolExecutor.summarize_for_model(
                    tool_result,
                    max_chars=min(600, self.llm_config.max_tool_chars),
                ),
                decision=decision,
                timestamp=self._utc_timestamp(),
                duration_sec=duration_sec,
                phase=state.phase,
                state_snapshot=state.snapshot(),
                evidence_ids=self._evidence_ids_for_tool(tool_name, tool_input, tool_result),
                verification_strength=state.verification_strength,
                tool_metrics=tool_metrics,
            )
        )
        trace.total_tool_calls += 1

    @staticmethod
    def _tool_use_blocks(assistant_blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [block for block in assistant_blocks if block.get("type") == "tool_use"]

    @staticmethod
    def _json_objects_from_text(text: str) -> list[dict[str, Any]]:
        decoder = json.JSONDecoder()
        objects: list[dict[str, Any]] = []
        start = 0
        while True:
            brace_index = text.find("{", start)
            if brace_index < 0:
                return objects
            try:
                value, end_index = decoder.raw_decode(text[brace_index:])
            except json.JSONDecodeError:
                start = brace_index + 1
                continue
            if isinstance(value, dict):
                objects.append(value)
            start = brace_index + max(end_index, 1)

    @classmethod
    def _recover_text_tool_blocks(
        cls,
        *,
        text: str,
        allowed_tool_names: list[str],
        max_blocks: int = 1,
    ) -> list[dict[str, Any]]:
        allowed = set(allowed_tool_names)
        recovered: list[dict[str, Any]] = []
        for payload in cls._json_objects_from_text(text):
            tool_name = payload.get("name")
            if not isinstance(tool_name, str) or tool_name not in allowed:
                continue
            tool_input = payload.get("arguments", payload.get("input", {}))
            if tool_input is None:
                tool_input = {}
            if not isinstance(tool_input, dict):
                continue
            recovered.append(
                {
                    "type": "tool_use",
                    "id": f"text_tool_{len(recovered) + 1}",
                    "name": tool_name,
                    "input": tool_input,
                }
            )
            if len(recovered) >= max_blocks:
                break
        return recovered

    @staticmethod
    def _partition_tool_batches(tool_blocks: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        batches: list[list[dict[str, Any]]] = []
        current_read_only_batch: list[dict[str, Any]] = []
        for block in tool_blocks:
            if block.get("name") in READ_ONLY_TOOL_NAMES:
                current_read_only_batch.append(block)
                continue
            if current_read_only_batch:
                batches.append(current_read_only_batch)
                current_read_only_batch = []
            batches.append([block])
        if current_read_only_batch:
            batches.append(current_read_only_batch)
        return batches

    @staticmethod
    def _execute_tool_block(
        *,
        tool_executor: ToolExecutor,
        tool_policy: ToolPolicy,
        state: AgentState,
        block: dict[str, Any],
    ) -> dict[str, Any]:
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

    @staticmethod
    def _write_signature(tool_name: str, tool_input: dict[str, Any]) -> dict[str, str] | None:
        if tool_name not in WRITE_TOOL_NAMES:
            return None
        relative_path = str(tool_input.get("relative_path", "")).replace("\\", "/")
        if not relative_path:
            return None
        return {
            "tool_name": tool_name,
            "relative_path": relative_path,
            "old_string": str(tool_input.get("old_string", "")),
            "new_string": str(tool_input.get("new_string", "")),
            "content": str(tool_input.get("content", "")),
        }

    @staticmethod
    def _is_similar_text(left: str, right: str, *, threshold: float = 0.8) -> bool:
        if not left or not right:
            return left == right
        return SequenceMatcher(None, left, right).ratio() >= threshold

    @classmethod
    def _detect_repeated_write_loop(cls, write_history: list[dict[str, str]]) -> bool:
        if len(write_history) < 3:
            return False
        recent_writes = write_history[-3:]
        relative_paths = {entry["relative_path"] for entry in recent_writes}
        if len(relative_paths) != 1:
            return False

        old_strings = [entry.get("old_string", "") for entry in recent_writes]
        if all(old_strings) and len(set(old_strings)) == 1:
            return True

        new_texts = [
            entry.get("new_string") or entry.get("content") or ""
            for entry in recent_writes
        ]
        first_text = new_texts[0]
        return all(
            cls._is_similar_text(first_text, text)
            for text in new_texts[1:]
        )

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

    @staticmethod
    def _should_run_guided_failure_search(failure_summary: dict[str, Any] | None) -> bool:
        if not failure_summary:
            return False
        if failure_summary.get("locations"):
            return False
        if failure_summary.get("guided_search"):
            return False
        return bool(failure_summary.get("possible_symbols"))

    @staticmethod
    def _evidence_ids_for_tool(tool_name: str, tool_input: dict[str, Any], tool_result: dict[str, Any]) -> list[str]:
        data = tool_result.get("data", {})
        if not isinstance(data, dict):
            data = {}
        if tool_name == "run_tests":
            exit_code = data.get("exit_code")
            scope = str(tool_input.get("verification_scope", "reproduce"))
            return [f"run_tests:{scope}:exit_{exit_code}"]
        if tool_name == "read_file":
            relative_path = str(data.get("relative_path") or tool_input.get("relative_path", "")).replace("\\", "/")
            return [f"read_file:{relative_path}"] if relative_path else []
        if tool_name in {"search_code", "grep", "search_graph"}:
            match_files = [
                str(path).replace("\\", "/")
                for path in data.get("match_files", [])[:5]
            ]
            return [f"{tool_name}:{path}" for path in match_files]
        if tool_name == "show_diff":
            changed_files = [
                str(path).replace("\\", "/")
                for path in data.get("changed_files", [])[:5]
            ]
            return [f"diff:{path}" for path in changed_files] or ["diff:clean"]
        if tool_name in {"write_file", "edit_file"}:
            relative_path = str(tool_input.get("relative_path", "")).replace("\\", "/")
            return [f"patch:{relative_path}"] if relative_path else []
        if tool_name == "undo":
            return ["undo:latest_patch"]
        return []
