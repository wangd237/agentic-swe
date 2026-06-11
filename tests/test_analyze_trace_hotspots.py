from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_trace_hotspots


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_batch_with_trace(base_dir: Path, name: str, task_specs: list[dict]) -> Path:
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
                "duration_sec": spec["duration_sec"],
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


def test_infer_step_duration_prefers_explicit_duration() -> None:
    duration = analyze_trace_hotspots.infer_step_duration_sec(
        step={"timestamp": "2026-06-11T05:00:01+00:00", "duration_sec": 0.1234},
        previous_step={"timestamp": "2026-06-11T05:00:00+00:00"},
        run_id="run_20260611T050000000000Z_0001",
    )

    assert duration == 0.1234


def test_infer_step_duration_falls_back_to_timestamp_delta() -> None:
    duration = analyze_trace_hotspots.infer_step_duration_sec(
        step={"timestamp": "2026-06-11T05:00:01+00:00"},
        previous_step={"timestamp": "2026-06-11T05:00:00.700000+00:00"},
        run_id="run_20260611T050000000000Z_0001",
    )

    assert duration == 0.3


def test_analyze_trace_hotspots_builds_task_and_tool_regressions(tmp_path: Path) -> None:
    baseline_summary = make_batch_with_trace(
        tmp_path,
        "batch_run_realissuev31_001",
        [
            {
                "task_id": "task_001",
                "run_id": "run_20260611T050000000000Z_0001",
                "duration_sec": 0.5,
                "steps": [
                    {
                        "step_index": 1,
                        "action_type": "tool_call",
                        "tool_name": "search_code",
                        "timestamp": "2026-06-11T05:00:00.100000+00:00",
                        "duration_sec": 0.1,
                    },
                    {
                        "step_index": 2,
                        "action_type": "tool_call",
                        "tool_name": "run_tests",
                        "timestamp": "2026-06-11T05:00:00.400000+00:00",
                        "duration_sec": 0.3,
                    },
                ],
            }
        ],
    )
    improved_summary = make_batch_with_trace(
        tmp_path,
        "batch_run_realissuev32_001",
        [
            {
                "task_id": "task_001",
                "run_id": "run_20260611T050100000000Z_0002",
                "duration_sec": 0.8,
                "steps": [
                    {
                        "step_index": 1,
                        "action_type": "tool_call",
                        "tool_name": "search_code",
                        "timestamp": "2026-06-11T05:01:00.150000+00:00",
                        "duration_sec": 0.15,
                    },
                    {
                        "step_index": 2,
                        "action_type": "tool_call",
                        "tool_name": "run_tests",
                        "timestamp": "2026-06-11T05:01:00.650000+00:00",
                        "duration_sec": 0.5,
                    },
                ],
            }
        ],
    )

    output = analyze_trace_hotspots.analyze_trace_hotspots(
        baseline_batch_summary_path=baseline_summary,
        improved_batch_summary_path=improved_summary,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="realissuev32",
        top_n=5,
    )

    summary = output["summary"]
    assert summary["common_task_count"] == 1
    assert summary["average_duration_delta_sec"] == 0.3
    assert summary["top_task_regressions"][0]["task_id"] == "task_001"
    assert summary["top_task_regressions"][0]["dominant_regression_tool"] == "run_tests"
    assert summary["top_tool_regressions"][0]["tool_name"] == "run_tests"
    assert summary["top_tool_regressions"][0]["delta_total_duration_sec"] == 0.2
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
