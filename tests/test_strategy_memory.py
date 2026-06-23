from __future__ import annotations

import json
from pathlib import Path

from app.agent.memory import AgentState, FailureSignature, LocalizationCandidate
from app.agent.strategy_memory import (
    StrategyMemoryEntry,
    append_strategy_memory,
    distill_strategy_memory_entry,
    format_strategy_memory_hints,
    retrieve_strategy_memories,
)
from app.schemas.result_schema import Result
from app.schemas.trace_schema import Trace, TraceStep


def test_distill_strategy_memory_entry_captures_repair_facts(tmp_path: Path) -> None:
    state = AgentState(
        failure_signature=FailureSignature(
            failed_tests=["tests/test_app.py::test_value - assert 0 == 1"],
            assertion_lines=["assert value() == 1"],
            locations=[{"path": "tests/test_app.py", "line": 4, "error": "AssertionError"}],
            output_hash="abc123",
        ),
        localization_candidates=[
            LocalizationCandidate(
                relative_path="demo_pkg/app.py",
                reason="test_failure_location",
                evidence=["run_tests reported failure location tests/test_app.py:4"],
                confidence=0.9,
            )
        ],
        verification_strength="full",
    )
    trace = Trace(
        task_id="task_demo",
        run_id="run_001",
        steps=[
            TraceStep(
                step_index=1,
                action_type="tool_call",
                tool_name="edit_file",
                tool_metrics={"ok": True},
            )
        ],
        final_status="success",
    )
    result = Result(
        task_id="task_demo",
        run_id="run_001",
        final_status="success",
        summary="fixed",
        patch_applied=True,
        modified_files=["demo_pkg/app.py"],
        tool_stats={
            "verification_strength": "full",
            "agent_core_metrics": {"pre_repro_rate": 1.0},
        },
    )

    entry = distill_strategy_memory_entry(
        state=state,
        trace=trace,
        result=result,
        trace_path=tmp_path / "trace.json",
        result_path=tmp_path / "result.json",
    )

    assert entry.task_id == "task_demo"
    assert entry.failure_mode == "abc123"
    assert entry.likely_cause == "fixed"
    assert entry.successful is True
    assert entry.patch_style == "single_edit"
    assert entry.verification_strength == "full"
    assert entry.metrics == {"pre_repro_rate": 1.0}
    assert entry.top_localization_evidence[0]["relative_path"] == "demo_pkg/app.py"


def test_append_strategy_memory_writes_jsonl(tmp_path: Path) -> None:
    result = Result(
        task_id="task_demo",
        run_id="run_001",
        final_status="incomplete",
        incomplete_reason="failed_tests",
        summary="not fixed",
    )
    entry = distill_strategy_memory_entry(
        state=AgentState(),
        trace=Trace(task_id="task_demo", run_id="run_001"),
        result=result,
    )
    memory_path = tmp_path / "logs" / "agent_memory" / "strategy_memory.jsonl"

    append_strategy_memory(memory_path, entry)

    lines = memory_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["task_id"] == "task_demo"
    assert payload["likely_cause"] == "failed_tests"


def test_retrieve_strategy_memories_ranks_relevant_successful_entries(tmp_path: Path) -> None:
    memory_path = tmp_path / "strategy_memory.jsonl"
    relevant = StrategyMemoryEntry(
        task_id="task_relevant",
        run_id="run_001",
        created_at="2026-06-22T00:00:00+00:00",
        final_status="success",
        likely_cause="fixed",
        successful=True,
        modified_files=["demo_pkg/parser.py"],
        top_localization_evidence=[
            {
                "relative_path": "demo_pkg/parser.py",
                "reason": "grep_hit",
                "evidence": ["parse_items matched this file"],
                "confidence": 0.9,
            }
        ],
        patch_style="single_edit",
        verification_strength="full",
    )
    irrelevant = StrategyMemoryEntry(
        task_id="task_irrelevant",
        run_id="run_002",
        created_at="2026-06-22T00:01:00+00:00",
        final_status="success",
        likely_cause="fixed",
        successful=True,
        modified_files=["other/module.py"],
        patch_style="single_edit",
        verification_strength="full",
    )
    append_strategy_memory(memory_path, irrelevant)
    append_strategy_memory(memory_path, relevant)

    retrieved = retrieve_strategy_memories(
        memory_path=memory_path,
        issue_text="parse_items fails for empty input",
        target_files_hint=["demo_pkg/parser.py"],
    )

    assert [entry.task_id for entry in retrieved] == ["task_relevant"]


def test_format_strategy_memory_hints_is_prompt_ready() -> None:
    hints = format_strategy_memory_hints(
        [
            StrategyMemoryEntry(
                task_id="task_demo",
                run_id="run_001",
                created_at="2026-06-22T00:00:00+00:00",
                final_status="success",
                likely_cause="fixed",
                successful=True,
                modified_files=["demo_pkg/app.py"],
                top_localization_evidence=[
                    {"relative_path": "demo_pkg/app.py", "reason": "file_read", "evidence": []}
                ],
                patch_style="single_edit",
                verification_strength="full",
            )
        ]
    )

    assert hints.startswith("STRATEGY_MEMORY_HINTS:")
    assert "demo_pkg/app.py" in hints
    assert "weak priors" in hints
