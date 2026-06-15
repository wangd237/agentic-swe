from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import aggregate_model_comparison


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_aggregate_model_comparison_builds_intersection_report(tmp_path: Path) -> None:
    summary_path = tmp_path / "logs" / "summaries" / "multi_model_eval_demo_001.json"
    write_json(
        summary_path,
        {
            "matrix_run_id": "multi_model_eval_demo_001",
            "records": [
                {
                    "record_status": "completed",
                    "policy_id": "llm_a",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-a",
                    "task_id": "task_001",
                    "final_status": "success",
                    "incomplete_reason": "",
                    "total_tool_calls": 4,
                    "duration_sec": 1.0,
                    "trace_path": "logs/a/task_001/trace.json",
                    "result_path": "logs/a/task_001/result.json",
                },
                {
                    "record_status": "completed",
                    "policy_id": "llm_b",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-b",
                    "task_id": "task_001",
                    "final_status": "success",
                    "incomplete_reason": "",
                    "total_tool_calls": 6,
                    "duration_sec": 2.0,
                    "trace_path": "logs/b/task_001/trace.json",
                    "result_path": "logs/b/task_001/result.json",
                },
                {
                    "record_status": "completed",
                    "policy_id": "llm_a",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-a",
                    "task_id": "task_002",
                    "final_status": "success",
                    "incomplete_reason": "",
                    "total_tool_calls": 5,
                    "duration_sec": 1.5,
                    "trace_path": "logs/a/task_002/trace.json",
                    "result_path": "logs/a/task_002/result.json",
                },
                {
                    "record_status": "completed",
                    "policy_id": "llm_b",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-b",
                    "task_id": "task_002",
                    "final_status": "incomplete",
                    "incomplete_reason": "max_iterations",
                    "total_tool_calls": 12,
                    "duration_sec": 3.0,
                    "trace_path": "logs/b/task_002/trace.json",
                    "result_path": "logs/b/task_002/result.json",
                },
            ],
        },
    )
    docs_output = tmp_path / "docs" / "model_comparison.md"

    output = aggregate_model_comparison.aggregate_model_comparison(
        summary_paths=[summary_path],
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
        docs_output_path=docs_output,
    )

    comparison = output["comparison"]
    assert comparison["comparison_id"] == "model_comparison_demo_001"
    assert comparison["policy_count"] == 2
    assert comparison["observed_task_count"] == 2
    assert comparison["intersections"]["all_success"] == ["task_001"]
    assert comparison["intersections"]["inconsistent"] == ["task_002"]
    assert comparison["policy_summaries"][0]["success_rate"] == 1.0
    assert comparison["policy_summaries"][1]["success_rate"] == 0.5
    assert comparison["policy_summaries"][1]["incomplete_reason_counts"] == {"max_iterations": 1}
    assert Path(output["summary_json_path"]).exists()
    assert docs_output.exists()
    docs_text = docs_output.read_text(encoding="utf-8")
    assert "## Intersection Analysis" in docs_text
    assert "## Inconsistent Tasks" in docs_text
    assert "`task_002`" in docs_text
    assert "[link](logs/b/task_002/result.json)" in docs_text
    assert "[link](logs/b/task_002/trace.json)" in docs_text


def test_aggregate_model_comparison_lists_all_failed_task_artifacts(tmp_path: Path) -> None:
    summary_path = tmp_path / "logs" / "summaries" / "multi_model_eval_demo_001.json"
    write_json(
        summary_path,
        {
            "matrix_run_id": "multi_model_eval_demo_001",
            "records": [
                {
                    "record_status": "completed",
                    "policy_id": "llm_a",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-a",
                    "task_id": "task_003",
                    "final_status": "incomplete",
                    "incomplete_reason": "failed_tests",
                    "total_tool_calls": 8,
                    "duration_sec": 2.5,
                    "trace_path": "logs/a/task_003/trace.json",
                    "result_path": "logs/a/task_003/result.json",
                },
                {
                    "record_status": "completed",
                    "policy_id": "llm_b",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-b",
                    "task_id": "task_003",
                    "final_status": "incomplete",
                    "incomplete_reason": "max_iterations",
                    "total_tool_calls": 12,
                    "duration_sec": 3.5,
                    "trace_path": "logs/b/task_003/trace.json",
                    "result_path": "logs/b/task_003/result.json",
                },
            ],
        },
    )
    docs_output = tmp_path / "docs" / "model_comparison.md"

    output = aggregate_model_comparison.aggregate_model_comparison(
        summary_paths=[summary_path],
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
        docs_output_path=docs_output,
    )

    comparison = output["comparison"]
    docs_text = docs_output.read_text(encoding="utf-8")
    assert comparison["intersections"]["all_failed"] == ["task_003"]
    assert "## All-Failed Tasks" in docs_text
    assert "`task_003`" in docs_text
    assert "reason: `failed_tests`" in docs_text
    assert "reason: `max_iterations`" in docs_text
    assert "[link](logs/a/task_003/result.json)" in docs_text
    assert "[link](logs/b/task_003/trace.json)" in docs_text


def test_aggregate_model_comparison_normalizes_artifact_links_and_inserts_note(tmp_path: Path) -> None:
    summary_path = tmp_path / "logs" / "summaries" / "multi_model_eval_demo_001.json"
    write_json(
        summary_path,
        {
            "matrix_run_id": "multi_model_eval_demo_001",
            "records": [
                {
                    "record_status": "completed",
                    "policy_id": "llm_a",
                    "llm_provider": "openai_compatible",
                    "llm_model": "model-a",
                    "task_id": "task_004",
                    "final_status": "incomplete",
                    "incomplete_reason": "max_iterations",
                    "total_tool_calls": 12,
                    "duration_sec": 3.5,
                    "trace_path": r"E:\repo\logs\task_004\trace.json",
                    "result_path": r"E:\repo\logs\task_004\result.json",
                },
            ],
        },
    )
    docs_output = tmp_path / "docs" / "model_comparison.md"

    aggregate_model_comparison.aggregate_model_comparison(
        summary_paths=[summary_path],
        output_dir=tmp_path / "logs" / "summaries",
        run_label="demo",
        docs_output_path=docs_output,
        interim_note="状态：interim report。",
    )

    docs_text = docs_output.read_text(encoding="utf-8")
    assert "状态：interim report。" in docs_text
    assert "[link](E:/repo/logs/task_004/result.json)" in docs_text
    assert "[link](E:/repo/logs/task_004/trace.json)" in docs_text
