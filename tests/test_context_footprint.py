"""Tests for read-only context footprint analysis, including incomplete old traces."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.analyze_context_footprint import _percentile, analyze, write_report


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_context_audit_preserves_unknown_sizes_and_prompt_gaps(tmp_path: Path) -> None:
    run = tmp_path / "logs" / "trajectories" / "demo" / "run_1"
    _write_json(run / "tool_outputs" / "step_003_run_tests.json", {
        "data": {"truncated": True, "stdout": "SENSITIVE-DONT-COPY"}, "summary": "failed",
    })
    _write_json(run / "result.json", {
        "final_status": "success", "tool_stats": {"llm_model": "example-model"},
    })
    _write_json(run / "trace.json", {
        "task_id": "demo", "run_id": "run_1",
        "steps": [
            {"step_index": 1, "action_type": "llm_response", "tool_metrics": {
                "llm_prompt_tokens": 1000, "tool_schema_count": 4,
            }},
            {"step_index": 2, "action_type": "tool_call", "tool_name": "grep",
             "observation": "tiny preview", "tool_metrics": {
                 "raw_result_chars": 2000, "model_visible_chars": 400,
                 "tool_payload_truncated": True, "model_summary_truncated": False,
             }},
            {"step_index": 3, "action_type": "tool_call", "tool_name": "run_tests",
             "observation": "not the full reply",
             "evidence_ids": ["spill:tool_outputs/step_003_run_tests.json"]},
            {"step_index": 4, "action_type": "context_compression"},
            {"step_index": 5, "action_type": "llm_response",
             "tool_metrics": {"llm_prompt_tokens": 1200, "tool_schema_count": 5}},
        ],
    })
    data = analyze([tmp_path / "logs" / "trajectories"], context_window_tokens=1400)
    summary = data["summary"]
    assert (summary["runs"], summary["tool_calls"], summary["prompt_samples"]) == (1, 2, 2)
    assert summary["raw_size_coverage"] == 2
    assert summary["model_visible_coverage"] == 1
    assert summary["prompt_samples_above_threshold"] == 1  # >= 1120 tokens
    assert data["tool_calls"][0]["model_visible_chars"] == 400
    assert data["tool_calls"][1]["model_visible_chars"] is None
    assert data["tool_calls"][1]["raw_size_source"] == "spill"
    assert data["tool_calls"][1]["source_truncated"] is True
    assert data["prompt_deltas"][1]["prompt_delta"] == 200
    assert data["prompt_deltas"][1]["tool_calls_since_previous"] == 2
    assert data["prompt_deltas"][1]["model_visible_chars_since_previous"] is None
    assert data["prompt_deltas"][1]["compressions_since_previous"] == 1
    out = tmp_path / "reports"
    write_report(data, out)
    assert "SENSITIVE-DONT-COPY" not in (out / "report.md").read_text(encoding="utf-8")
    assert "SENSITIVE-DONT-COPY" not in (out / "tool_calls.csv").read_text(encoding="utf-8")
    assert (out / "prompt_deltas.csv").is_file()


def test_context_audit_does_not_confuse_trace_observation_with_model_reply(tmp_path: Path) -> None:
    run = tmp_path / "evidence" / "old_case"
    _write_json(run / "trace.json", {
        "task_id": "old", "final_status": "incomplete",
        "steps": [
            {"step_index": 1, "action_type": "tool_call", "tool_name": "read_file",
             "observation": "A" * 600, "tool_metrics": {}},
            {"step_index": 2, "action_type": "llm_response", "tool_metrics": {
                "llm_total_tokens": 500,
            }},
        ],
    })
    data = analyze([tmp_path / "evidence"])
    assert data["summary"]["runs"] == 1
    assert data["summary"]["model_visible_coverage"] == 0
    assert data["summary"]["raw_size_coverage"] == 0
    assert data["prompt_deltas"][0]["prompt_tokens"] is None
    assert data["tool_calls"][0]["trace_preview_chars"] == 600
    assert data["tool_calls"][0]["model_visible_chars"] is None
    assert data["status_groups"][0]["group"] == "other"


def test_context_audit_rejects_spill_traversal_and_deduplicates_roots(tmp_path: Path) -> None:
    run = tmp_path / "logs" / "trajectories" / "x" / "run_1"
    _write_json(run / "private.json", {"secret": "SENSITIVE"})
    _write_json(run / "trace.json", {
        "task_id": "x", "steps": [
            {"step_index": 1, "action_type": "tool_call", "tool_name": "grep",
             "evidence_ids": ["spill:../private.json", "spill:private.json"]},
        ],
    })
    data = analyze([run / "trace.json", tmp_path / "logs"])
    assert data["summary"]["runs"] == 1
    assert data["tool_calls"][0]["raw_result_chars"] is None


def test_context_audit_skips_malformed_traces(tmp_path: Path) -> None:
    bad = tmp_path / "evidence" / "bad" / "trace.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("{", encoding="utf-8")
    data = analyze([tmp_path / "evidence"])
    assert data["summary"]["runs"] == 0
    assert len(data["summary"]["warnings"]) == 1


def test_context_audit_percentile_uses_nearest_rank() -> None:
    assert _percentile([], 0.95) is None
    assert _percentile([100, 20, 300, 40, 50], 0.5) == 50
    assert _percentile([100, 20, 300, 40, 50], 0.95) == 300


def test_context_audit_parses_committed_evidence_end_to_end(tmp_path: Path) -> None:
    """Use actual checked-in traces, not just synthetic fixtures."""
    repo = Path(__file__).resolve().parents[1]
    data = analyze([repo / "evidence"])
    assert data["summary"]["runs"] >= 15
    assert data["summary"]["tool_calls"] > 0
    assert data["summary"]["prompt_samples"] > 0
    write_report(data, tmp_path / "audit")
    assert (tmp_path / "audit" / "report.md").is_file()
    assert (tmp_path / "audit" / "tool_summary.csv").is_file()
