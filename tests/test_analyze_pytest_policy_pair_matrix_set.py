from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_pytest_policy_pair_matrix_set


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_matrix_summary(
    path: Path,
    *,
    matrix_label: str,
    startup_delta: float,
    collect_delta: float,
    full_delta: float,
    collect_wall_delta: float,
    collect_import_delta: int,
) -> None:
    write_json(
        path,
        {
            "matrix_label": matrix_label,
            "task_count": 4,
            "runtime_equivalent_task_count": 4,
            "task_records": [
                {"task_id": "task_001"},
                {"task_id": "task_002"},
            ],
            "phase_cohort_summary": {
                "aggregate": {
                    "average_pytest_startup_over_python_delta_sec": startup_delta,
                    "average_collect_over_pytest_startup_delta_sec": collect_delta,
                    "average_full_over_collect_delta_sec": full_delta,
                    "startup_slower_task_count": 2,
                    "collect_slower_task_count": 1,
                    "full_slower_task_count": 3,
                }
            },
            "importtime_cohort_summary": {
                "aggregate": {
                    "average_collect_wall_delta_sec": collect_wall_delta,
                    "average_collect_import_self_delta_us": collect_import_delta,
                    "collect_wall_slower_task_count": 2,
                    "collect_import_self_higher_task_count": 3,
                }
            },
        },
    )


def test_build_pytest_policy_pair_matrix_set_summary_aggregates_matrices(tmp_path: Path) -> None:
    first_path = tmp_path / "matrix_a.json"
    second_path = tmp_path / "matrix_b.json"
    make_matrix_summary(
        first_path,
        matrix_label="group_a",
        startup_delta=0.01,
        collect_delta=-0.02,
        full_delta=0.03,
        collect_wall_delta=-0.01,
        collect_import_delta=1000,
    )
    make_matrix_summary(
        second_path,
        matrix_label="group_b",
        startup_delta=-0.02,
        collect_delta=0.01,
        full_delta=-0.01,
        collect_wall_delta=0.02,
        collect_import_delta=7000,
    )

    summary = analyze_pytest_policy_pair_matrix_set.build_pytest_policy_pair_matrix_set_summary(
        matrix_summary_paths=[first_path, second_path],
        set_label="v68_v69",
    )

    assert summary["matrix_count"] == 2
    assert summary["aggregate"]["average_startup_delta_sec"] == -0.005
    assert summary["aggregate"]["average_collect_delta_sec"] == -0.005
    assert summary["aggregate"]["average_full_delta_sec"] == 0.01
    assert summary["aggregate"]["average_collect_wall_delta_sec"] == 0.005
    assert summary["aggregate"]["average_collect_import_self_delta_us"] == 4000.0
    assert summary["aggregate"]["runtime_equivalent_matrix_count"] == 2
    assert summary["aggregate"]["startup_positive_matrix_count"] == 1
    assert summary["aggregate"]["collect_import_positive_matrix_count"] == 2
    assert summary["top_collect_import_matrices"][0]["matrix_label"] == "group_b"


def test_analyze_pytest_policy_pair_matrix_set_writes_output_files(tmp_path: Path) -> None:
    first_path = tmp_path / "matrix_a.json"
    make_matrix_summary(
        first_path,
        matrix_label="group_a",
        startup_delta=0.01,
        collect_delta=-0.02,
        full_delta=0.03,
        collect_wall_delta=-0.01,
        collect_import_delta=1000,
    )

    output = analyze_pytest_policy_pair_matrix_set.analyze_pytest_policy_pair_matrix_set(
        matrix_summary_paths=[first_path],
        set_label="v68_v69",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_policy_pair_matrix_set_v68_v69_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
