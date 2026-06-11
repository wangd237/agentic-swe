from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_task_history


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_run(
    task_dir: Path,
    *,
    run_id: str,
    policy_id: str,
    duration_sec: float,
    run_tests_durations: list[tuple[float, float]],
) -> None:
    run_dir = task_dir / run_id
    steps: list[dict] = []
    for index, (subprocess_duration, summary_duration) in enumerate(run_tests_durations, start=1):
        steps.append(
            {
                "step_index": index,
                "action_type": "tool_call",
                "tool_name": "run_tests",
                "timestamp": f"2026-06-11T05:00:0{index}+00:00",
                "duration_sec": round(subprocess_duration + summary_duration, 4),
                "tool_metrics": {
                    "subprocess_duration_sec": subprocess_duration,
                    "summary_extraction_duration_sec": summary_duration,
                },
            }
        )

    write_json(
        run_dir / "result.json",
        {
            "task_id": "task_999",
            "run_id": run_id,
            "final_status": "success",
            "duration_sec": duration_sec,
            "tool_stats": {
                "policy_id": policy_id,
                "total_tool_calls": len(steps),
            },
        },
    )
    write_json(
        run_dir / "trace.json",
        {
            "task_id": "task_999",
            "run_id": run_id,
            "steps": steps,
            "final_status": "success",
            "total_tool_calls": len(steps),
            "read_files": [],
        },
    )


def test_build_task_history_summary_groups_by_policy(tmp_path: Path) -> None:
    task_dir = tmp_path / "logs" / "trajectories" / "task_999"
    make_run(
        task_dir,
        run_id="run_20260611T050000000000Z_0001",
        policy_id="improved_v31",
        duration_sec=0.62,
        run_tests_durations=[(0.26, 0.0), (0.27, 0.0)],
    )
    make_run(
        task_dir,
        run_id="run_20260611T050100000000Z_0002",
        policy_id="improved_v31",
        duration_sec=0.64,
        run_tests_durations=[(0.27, 0.0), (0.28, 0.0)],
    )
    make_run(
        task_dir,
        run_id="run_20260611T050200000000Z_0003",
        policy_id="improved_v32",
        duration_sec=0.91,
        run_tests_durations=[(0.41, 0.0), (0.42, 0.0)],
    )
    make_run(
        task_dir,
        run_id="run_20260611T050300000000Z_0004",
        policy_id="improved_v32",
        duration_sec=0.93,
        run_tests_durations=[(0.42, 0.0), (0.43, 0.0)],
    )

    summary = analyze_task_history.build_task_history_summary(task_dir)

    assert summary["task_id"] == "task_999"
    assert summary["run_count"] == 4
    assert summary["policy_count"] == 2
    assert summary["policy_summaries"][0]["policy_id"] == "improved_v31"
    assert summary["policy_summaries"][1]["policy_id"] == "improved_v32"
    assert summary["policy_summaries"][0]["duration_sec"]["average"] == 0.63
    assert summary["policy_summaries"][1]["duration_sec"]["average"] == 0.92
    assert summary["policy_summaries"][1]["run_tests_total_duration_sec"]["average"] == 0.84
    assert summary["latest_policy_comparison"]["duration_average_delta_sec"] == 0.29
    assert summary["latest_policy_comparison"]["run_tests_average_delta_sec"] == 0.3


def test_analyze_task_history_writes_output_files(tmp_path: Path) -> None:
    task_dir = tmp_path / "logs" / "trajectories" / "task_999"
    make_run(
        task_dir,
        run_id="run_20260611T050000000000Z_0001",
        policy_id="improved_v32",
        duration_sec=0.55,
        run_tests_durations=[(0.25, 0.0), (0.26, 0.0)],
    )

    output = analyze_task_history.analyze_task_history(
        task_dir=task_dir,
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "task_history_task_999_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
