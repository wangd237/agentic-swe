from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_search_code_regressions


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_batch_with_search_trace(base_dir: Path, name: str, task_specs: list[dict]) -> Path:
    tasks: list[dict] = []
    for spec in task_specs:
        trace_path = base_dir / "logs" / "trajectories" / spec["task_id"] / name / "trace.json"
        result_path = base_dir / "logs" / "trajectories" / spec["task_id"] / name / "result.json"
        write_json(
            trace_path,
            {
                "task_id": spec["task_id"],
                "run_id": spec["run_id"],
                "steps": spec["steps"],
                "final_status": "success",
                "total_tool_calls": len(spec["steps"]),
                "read_files": [],
            },
        )
        write_json(
            result_path,
            {
                "task_id": spec["task_id"],
                "run_id": spec["run_id"],
                "final_status": "success",
                "duration_sec": spec.get("duration_sec", 0.5),
            },
        )
        tasks.append(
            {
                "task_id": spec["task_id"],
                "run_id": spec["run_id"],
                "task_path": str(base_dir / "benchmarks" / "tasks" / f"{spec['task_id']}.json"),
                "trace_path": str(trace_path),
                "result_path": str(result_path),
            }
        )

    summary_path = base_dir / "logs" / "summaries" / f"{name}.json"
    write_json(summary_path, {"batch_run_id": name, "tasks": tasks})
    return summary_path


def make_search_step(step_index: int, query: str, duration_sec: float, match_count: int, match_file_count: int) -> dict:
    return {
        "step_index": step_index,
        "action_type": "tool_call",
        "tool_name": "search_code",
        "timestamp": f"2026-06-13T09:00:0{step_index}+00:00",
        "duration_sec": duration_sec,
        "tool_input": {"query": query},
        "tool_metrics": {
            "match_count": match_count,
            "match_file_count": match_file_count,
        },
    }


def test_analyze_search_code_regressions_detects_identical_signature_slowdown(tmp_path: Path) -> None:
    baseline_summary = make_batch_with_search_trace(
        tmp_path,
        "batch_run_realissuev68r1_001",
        [
            {
                "task_id": "task_001",
                "run_id": "run_20260613T090000000000Z_0001",
                "steps": [
                    make_search_step(1, "_exceptions", 0.01, 7, 2),
                    make_search_step(2, "__aexit__", 0.002, 1, 1),
                ],
            },
            {
                "task_id": "task_002",
                "run_id": "run_20260613T090100000000Z_0002",
                "steps": [
                    make_search_step(1, "test_bool_entry_supports_comment_after_add", 0.003, 1, 1),
                ],
            },
        ],
    )
    improved_summary = make_batch_with_search_trace(
        tmp_path,
        "batch_run_realissuev69r1_001",
        [
            {
                "task_id": "task_001",
                "run_id": "run_20260613T090200000000Z_0003",
                "steps": [
                    make_search_step(1, "_exceptions", 0.07, 7, 2),
                    make_search_step(2, "__aexit__", 0.003, 1, 1),
                ],
            },
            {
                "task_id": "task_002",
                "run_id": "run_20260613T090300000000Z_0004",
                "steps": [
                    make_search_step(1, "test_bool_entry_supports_comment_after_add", 0.03, 1, 1),
                ],
            },
        ],
    )

    output = analyze_search_code_regressions.analyze_search_code_regressions(
        baseline_batch_summary_path=baseline_summary,
        improved_batch_summary_path=improved_summary,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="realissuev69r1",
        top_n=5,
    )

    summary = output["summary"]
    assert summary["aggregate"]["common_task_count"] == 2
    assert summary["aggregate"]["identical_query_signature_task_count"] == 2
    assert summary["aggregate"]["identical_query_signature_regression_task_count"] == 2
    assert summary["aggregate"]["total_search_duration_delta_sec"] == 0.088
    assert summary["aggregate"]["first_search_total_delta_sec"] == 0.087
    assert summary["top_task_regressions"][0]["task_id"] == "task_001"
    assert summary["top_task_regressions"][0]["identical_query_signature"] is True
    assert summary["top_query_regressions"][0]["query"] == "_exceptions"
    assert summary["top_query_regressions"][0]["total_delta_sec"] == 0.06
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()


def test_extract_search_steps_uses_trace_metrics(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.json"
    write_json(
        trace_path,
        {
            "task_id": "task_demo",
            "run_id": "run_20260613T090000000000Z_0001",
            "steps": [
                make_search_step(1, "alpha", 0.0123, 2, 1),
                {
                    "step_index": 2,
                    "action_type": "tool_call",
                    "tool_name": "read_file",
                    "timestamp": "2026-06-13T09:00:02+00:00",
                    "duration_sec": 0.001,
                },
            ],
        },
    )

    steps = analyze_search_code_regressions.extract_search_steps(
        trace_path,
        "run_20260613T090000000000Z_0001",
    )

    assert steps == [
        {
            "step_index": 1,
            "query": "alpha",
            "duration_sec": 0.0123,
            "match_count": 2,
            "match_file_count": 1,
        }
    ]
