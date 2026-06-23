"""Lightweight long-term strategy memory for repair runs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agent.memory import AgentState
from app.schemas.result_schema import Result
from app.schemas.trace_schema import Trace


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


class StrategyMemoryEntry(BaseModel):
    """A compact, auditable memory distilled from one repair run."""

    model_config = ConfigDict(extra="forbid")

    task_id: str
    run_id: str
    created_at: str
    final_status: str
    failure_mode: str = ""
    likely_cause: str = ""
    successful: bool = False
    modified_files: list[str] = Field(default_factory=list)
    top_localization_evidence: list[dict[str, Any]] = Field(default_factory=list)
    patch_style: str = ""
    verification_strength: str = "none"
    metrics: dict[str, Any] = Field(default_factory=dict)
    trace_path: str = ""
    result_path: str = ""


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _latest_reflection_type(trace: Trace) -> str:
    for step in reversed(trace.steps):
        if step.action_type == "reflection" and step.reflection_type:
            return step.reflection_type
    return ""


def _classify_patch_style(result: Result, trace: Trace) -> str:
    changed_file_count = len(result.modified_files)
    write_tools = [
        step.tool_name
        for step in trace.steps
        if step.tool_name in {"edit_file", "write_file"} and step.tool_metrics.get("ok") is True
    ]
    if not result.patch_applied:
        return "no_patch"
    if changed_file_count > 1:
        return "multi_file_patch"
    if write_tools == ["edit_file"]:
        return "single_edit"
    if write_tools == ["write_file"]:
        return "single_file_rewrite"
    if "edit_file" in write_tools:
        return "edit_sequence"
    if "write_file" in write_tools:
        return "rewrite_sequence"
    return "patch_unknown"


def distill_strategy_memory_entry(
    *,
    state: AgentState,
    trace: Trace,
    result: Result,
    trace_path: str | Path = "",
    result_path: str | Path = "",
) -> StrategyMemoryEntry:
    """Distill the most useful reusable repair facts from a completed run."""

    failure_signature = state.failure_signature
    top_candidates = sorted(
        state.localization_candidates,
        key=lambda candidate: candidate.confidence,
        reverse=True,
    )[:3]
    metrics = dict(result.tool_stats.get("agent_core_metrics", {}))
    likely_cause = _latest_reflection_type(trace)
    if not likely_cause and result.final_status.startswith("success"):
        likely_cause = "fixed"
    if not likely_cause:
        likely_cause = result.incomplete_reason or "unknown"

    return StrategyMemoryEntry(
        task_id=result.task_id,
        run_id=result.run_id,
        created_at=_utc_timestamp(),
        final_status=result.final_status,
        failure_mode=(
            failure_signature.output_hash
            if failure_signature
            else result.incomplete_reason or result.final_status
        ),
        likely_cause=likely_cause,
        successful=result.final_status == "success",
        modified_files=result.modified_files,
        top_localization_evidence=[
            {
                "relative_path": candidate.relative_path,
                "confidence": candidate.confidence,
                "reason": candidate.reason,
                "evidence": candidate.evidence[:3],
            }
            for candidate in top_candidates
        ],
        patch_style=_classify_patch_style(result, trace),
        verification_strength=str(result.tool_stats.get("verification_strength", "none")),
        metrics=metrics,
        trace_path=str(trace_path),
        result_path=str(result_path),
    )


def append_strategy_memory(memory_path: str | Path, entry: StrategyMemoryEntry) -> None:
    """Append one JSONL strategy memory record."""

    destination = Path(memory_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def load_strategy_memory(memory_path: str | Path, *, limit: int = 200) -> list[StrategyMemoryEntry]:
    """Load recent strategy memories from JSONL, skipping malformed lines."""

    source = Path(memory_path)
    if not source.exists():
        return []

    entries: list[StrategyMemoryEntry] = []
    for line in source.read_text(encoding="utf-8").splitlines()[-limit:]:
        if not line.strip():
            continue
        try:
            entries.append(StrategyMemoryEntry.model_validate(json.loads(line)))
        except (json.JSONDecodeError, ValueError):
            continue
    return entries


def _tokens_from_text(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(text)
        if len(token) >= 3
    }


def _entry_tokens(entry: StrategyMemoryEntry) -> set[str]:
    tokens = set(entry.modified_files)
    tokens.update(entry.failure_mode.split())
    tokens.update(entry.likely_cause.split())
    tokens.update(entry.patch_style.split("_"))
    for evidence in entry.top_localization_evidence:
        tokens.add(str(evidence.get("relative_path", "")))
        tokens.add(str(evidence.get("reason", "")))
        tokens.update(str(item) for item in evidence.get("evidence", []) or [])
    return _tokens_from_text(" ".join(tokens))


def retrieve_strategy_memories(
    *,
    memory_path: str | Path,
    issue_text: str,
    target_files_hint: list[str] | None = None,
    limit: int = 3,
) -> list[StrategyMemoryEntry]:
    """Retrieve a few relevant strategy memories for a new repair task."""

    query_text = issue_text + " " + " ".join(target_files_hint or [])
    query_tokens = _tokens_from_text(query_text)
    if not query_tokens:
        return []

    scored_entries: list[tuple[float, StrategyMemoryEntry]] = []
    for entry in load_strategy_memory(memory_path):
        overlap = len(query_tokens & _entry_tokens(entry))
        if overlap == 0:
            continue
        score = float(overlap)
        if entry.successful:
            score += 2.0
        if entry.verification_strength == "full":
            score += 1.0
        if entry.patch_style != "no_patch":
            score += 0.5
        scored_entries.append((score, entry))

    scored_entries.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    return [entry for _, entry in scored_entries[:limit]]


def format_strategy_memory_hints(entries: list[StrategyMemoryEntry]) -> str:
    """Format retrieved memories for the agent prompt."""

    if not entries:
        return ""

    lines = ["STRATEGY_MEMORY_HINTS:"]
    for index, entry in enumerate(entries, start=1):
        candidate_paths = [
            str(candidate.get("relative_path", ""))
            for candidate in entry.top_localization_evidence
            if candidate.get("relative_path")
        ]
        lines.append(
            (
                f"{index}. status={entry.final_status}; cause={entry.likely_cause}; "
                f"patch_style={entry.patch_style}; verification={entry.verification_strength}; "
                f"modified_files={', '.join(entry.modified_files) or '(none)'}; "
                f"candidate_files={', '.join(candidate_paths) or '(none)'}"
            )
        )
    lines.append("Use these as weak priors only; still reproduce, localize, patch, and verify from current evidence.")
    return "\n".join(lines)
