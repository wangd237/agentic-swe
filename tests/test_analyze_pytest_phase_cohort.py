from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_pytest_phase_cohort


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_benchmark_summary(
    base_dir: Path,
    *,
    task_id: str,
    python_noop: float,
    pytest_version: float,
    pytest_collect_only: float,
    pytest_full_run: float,
    collect_first_minus_repeated: float | None,
    full_first_minus_repeated: float | None,
) -> Path:
    summary_path = base_dir / f"{task_id}.json"
    write_json(
        summary_path,
        {
            "task_id": task_id,
            "test_command": "python -m pytest tests/test_demo.py -q",
            "repetitions": 3,
            "phase_summaries": {
                "python_noop": {
                    "average_command_execution_duration_sec": python_noop,
                },
                "pytest_version": {
                    "average_command_execution_duration_sec": pytest_version,
                },
                "pytest_collect_only": {
                    "average_command_execution_duration_sec": pytest_collect_only,
                },
                "pytest_full_run": {
                    "average_command_execution_duration_sec": pytest_full_run,
                },
            },
            "derived_metrics": {
                "average_pytest_startup_over_python_sec": round(pytest_version - python_noop, 4),
                "average_collect_over_pytest_startup_sec": round(pytest_collect_only - pytest_version, 4),
                "average_full_over_collect_sec": round(pytest_full_run - pytest_collect_only, 4),
                "collect_first_minus_repeated_sec": collect_first_minus_repeated,
                "full_first_minus_repeated_sec": full_first_minus_repeated,
            },
        },
    )
    return summary_path


def test_build_pytest_phase_cohort_summary_aggregates_tasks(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        python_noop=0.02,
        pytest_version=0.11,
        pytest_collect_only=0.19,
        pytest_full_run=0.27,
        collect_first_minus_repeated=0.01,
        full_first_minus_repeated=0.012,
    )
    second = make_benchmark_summary(
        tmp_path,
        task_id="task_102",
        python_noop=0.021,
        pytest_version=0.109,
        pytest_collect_only=0.181,
        pytest_full_run=0.245,
        collect_first_minus_repeated=0.008,
        full_first_minus_repeated=0.009,
    )

    summary = analyze_pytest_phase_cohort.build_pytest_phase_cohort_summary(
        benchmark_summary_paths=[first, second],
        cohort_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["aggregate"]["average_pytest_startup_over_python_sec"] == 0.089
    assert summary["aggregate"]["average_collect_over_pytest_startup_sec"] == 0.076
    assert summary["aggregate"]["average_full_over_collect_sec"] == 0.072
    assert summary["aggregate"]["average_collect_first_minus_repeated_sec"] == 0.009
    assert summary["aggregate"]["average_full_first_minus_repeated_sec"] == 0.0105
    assert summary["aggregate"]["full_slower_than_collect_task_count"] == 2
    assert summary["top_full_over_collect_deltas"][0]["task_id"] == "task_101"


def test_analyze_pytest_phase_cohort_writes_output_files(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        python_noop=0.02,
        pytest_version=0.11,
        pytest_collect_only=0.19,
        pytest_full_run=0.27,
        collect_first_minus_repeated=0.01,
        full_first_minus_repeated=0.012,
    )

    output = analyze_pytest_phase_cohort.analyze_pytest_phase_cohort(
        benchmark_summary_paths=[first],
        cohort_label="hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_phases_cohort_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
