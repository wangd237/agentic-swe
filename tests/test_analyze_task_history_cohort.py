from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_task_history_cohort


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_run(
    task_dir: Path,
    *,
    task_id: str,
    run_id: str,
    policy_id: str,
    duration_sec: float,
    run_tests_total_duration_sec: float,
    subprocess_duration_sec: float | None = None,
) -> None:
    steps: list[dict] = [
        {
            "step_index": 1,
            "action_type": "tool_call",
            "tool_name": "run_tests",
            "timestamp": "2026-06-11T05:00:00+00:00",
            "duration_sec": run_tests_total_duration_sec,
            "tool_metrics": {},
        }
    ]
    if subprocess_duration_sec is not None:
        steps[0]["tool_metrics"]["subprocess_duration_sec"] = subprocess_duration_sec
        steps[0]["tool_metrics"]["summary_extraction_duration_sec"] = 0.0

    write_json(
        task_dir / run_id / "result.json",
        {
            "task_id": task_id,
            "run_id": run_id,
            "final_status": "success",
            "duration_sec": duration_sec,
            "tool_stats": {
                "policy_id": policy_id,
            },
        },
    )
    write_json(
        task_dir / run_id / "trace.json",
        {
            "task_id": task_id,
            "run_id": run_id,
            "steps": steps,
            "final_status": "success",
            "total_tool_calls": 1,
            "read_files": [],
        },
    )


def test_build_task_history_cohort_summary_aggregates_multiple_tasks(tmp_path: Path) -> None:
    trajectories_root = tmp_path / "logs" / "trajectories"

    make_run(
        trajectories_root / "task_101",
        task_id="task_101",
        run_id="run_20260611T050000000000Z_0001",
        policy_id="improved_v31",
        duration_sec=0.60,
        run_tests_total_duration_sec=0.52,
    )
    make_run(
        trajectories_root / "task_101",
        task_id="task_101",
        run_id="run_20260611T050100000000Z_0002",
        policy_id="improved_v32",
        duration_sec=0.90,
        run_tests_total_duration_sec=0.81,
        subprocess_duration_sec=0.80,
    )
    make_run(
        trajectories_root / "task_102",
        task_id="task_102",
        run_id="run_20260611T050000000000Z_0003",
        policy_id="improved_v31",
        duration_sec=0.55,
        run_tests_total_duration_sec=0.45,
    )
    make_run(
        trajectories_root / "task_102",
        task_id="task_102",
        run_id="run_20260611T050100000000Z_0004",
        policy_id="improved_v32",
        duration_sec=0.70,
        run_tests_total_duration_sec=0.62,
        subprocess_duration_sec=0.60,
    )

    summary = analyze_task_history_cohort.build_task_history_cohort_summary(
        task_ids=["task_101", "task_102"],
        trajectories_root=trajectories_root,
        cohort_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["comparable_task_count"] == 2
    assert summary["aggregate"]["average_duration_delta_sec"] == 0.225
    assert summary["aggregate"]["average_run_tests_delta_sec"] == 0.23
    assert summary["aggregate"]["positive_duration_delta_count"] == 2
    assert summary["aggregate"]["latest_run_tests_subprocess_observed_task_count"] == 2
    assert summary["aggregate"]["latest_run_tests_subprocess_average_sec"] == 0.7
    assert summary["top_regressions"][0]["task_id"] == "task_101"


def test_analyze_task_history_cohort_writes_output_files(tmp_path: Path) -> None:
    trajectories_root = tmp_path / "logs" / "trajectories"
    make_run(
        trajectories_root / "task_101",
        task_id="task_101",
        run_id="run_20260611T050000000000Z_0001",
        policy_id="improved_v31",
        duration_sec=0.60,
        run_tests_total_duration_sec=0.52,
    )
    make_run(
        trajectories_root / "task_101",
        task_id="task_101",
        run_id="run_20260611T050100000000Z_0002",
        policy_id="improved_v32",
        duration_sec=0.90,
        run_tests_total_duration_sec=0.81,
        subprocess_duration_sec=0.80,
    )

    output = analyze_task_history_cohort.analyze_task_history_cohort(
        task_ids=["task_101"],
        trajectories_root=trajectories_root,
        output_dir=tmp_path / "logs" / "summaries",
        cohort_label="hotspots",
    )

    assert output["analysis_id"] == "task_history_cohort_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
