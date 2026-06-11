from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_run_tests_mode_cohort


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_benchmark_summary(
    base_dir: Path,
    *,
    task_id: str,
    source_run_tests: float,
    persistent_run_tests: float,
    fresh_run_tests: float,
    fresh_copy: float,
) -> Path:
    summary_path = base_dir / f"{task_id}.json"
    write_json(
        summary_path,
        {
            "task_id": task_id,
            "test_command": "python -m pytest tests/test_demo.py -q",
            "repetitions": 3,
            "mode_summaries": {
                "source_repo": {
                    "average_run_tests_duration_sec": source_run_tests,
                    "average_command_execution_duration_sec": source_run_tests - 0.0002,
                    "average_combined_duration_sec": source_run_tests,
                },
                "persistent_workspace": {
                    "average_copy_duration_sec": 0.001,
                    "average_run_tests_duration_sec": persistent_run_tests,
                    "average_command_execution_duration_sec": persistent_run_tests - 0.0002,
                    "average_combined_duration_sec": persistent_run_tests + 0.001,
                },
                "fresh_workspace": {
                    "average_copy_duration_sec": fresh_copy,
                    "average_run_tests_duration_sec": fresh_run_tests,
                    "average_command_execution_duration_sec": fresh_run_tests - 0.0002,
                    "average_combined_duration_sec": fresh_run_tests + fresh_copy,
                },
            },
        },
    )
    return summary_path


def test_build_run_tests_mode_cohort_summary_aggregates_tasks(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        source_run_tests=0.25,
        persistent_run_tests=0.26,
        fresh_run_tests=0.27,
        fresh_copy=0.002,
    )
    second = make_benchmark_summary(
        tmp_path,
        task_id="task_102",
        source_run_tests=0.24,
        persistent_run_tests=0.245,
        fresh_run_tests=0.248,
        fresh_copy=0.003,
    )

    summary = analyze_run_tests_mode_cohort.build_run_tests_mode_cohort_summary(
        benchmark_summary_paths=[first, second],
        cohort_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["aggregate"]["average_persistent_run_tests_delta_sec"] == 0.0075
    assert summary["aggregate"]["average_fresh_run_tests_delta_sec"] == 0.014
    assert summary["aggregate"]["average_fresh_copy_duration_sec"] == 0.0025
    assert summary["aggregate"]["average_fresh_combined_delta_sec"] == 0.0165
    assert summary["aggregate"]["fresh_slower_than_source_task_count"] == 2
    assert summary["top_fresh_combined_deltas"][0]["task_id"] == "task_101"


def test_analyze_run_tests_mode_cohort_writes_output_files(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        source_run_tests=0.25,
        persistent_run_tests=0.26,
        fresh_run_tests=0.27,
        fresh_copy=0.002,
    )

    output = analyze_run_tests_mode_cohort.analyze_run_tests_mode_cohort(
        benchmark_summary_paths=[first],
        cohort_label="hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "run_tests_modes_cohort_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
