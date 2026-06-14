from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_pytest_policy_pair_cohort


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_phase_compare_summary(
    path: Path,
    *,
    task_id: str,
    startup_delta: float,
    collect_delta: float,
    full_delta: float,
    runtime_equivalent: bool = True,
) -> None:
    write_json(
        path,
        {
            "kind": "pytest_phases",
            "task_id": task_id,
            "baseline_policy_id": "improved_v68",
            "improved_policy_id": "improved_v69",
            "runtime_equivalent": runtime_equivalent,
            "deltas": {
                "pytest_startup_over_python_delta_sec": startup_delta,
                "collect_over_pytest_startup_delta_sec": collect_delta,
                "full_over_collect_delta_sec": full_delta,
                "collect_first_minus_repeated_delta_sec": 0.01,
                "full_first_minus_repeated_delta_sec": -0.02,
            },
        },
    )


def make_importtime_compare_summary(
    path: Path,
    *,
    task_id: str,
    wall_delta: float,
    import_delta: int,
    module_delta: int,
    runtime_equivalent: bool = True,
) -> None:
    write_json(
        path,
        {
            "kind": "pytest_importtime",
            "task_id": task_id,
            "baseline_policy_id": "improved_v68",
            "improved_policy_id": "improved_v69",
            "runtime_equivalent": runtime_equivalent,
            "deltas": {
                "collect_wall_delta_sec": wall_delta,
                "collect_import_self_delta_us": import_delta,
                "collect_unique_module_delta": module_delta,
                "collect_wall_first_minus_repeated_delta_sec": -0.01,
                "collect_import_self_first_minus_repeated_delta_us": 1000,
            },
        },
    )


def test_build_pytest_policy_pair_cohort_summary_for_phase_compares(tmp_path: Path) -> None:
    first_path = tmp_path / "task_101_phase.json"
    second_path = tmp_path / "task_102_phase.json"
    make_phase_compare_summary(first_path, task_id="task_101", startup_delta=0.01, collect_delta=0.02, full_delta=0.03)
    make_phase_compare_summary(second_path, task_id="task_102", startup_delta=-0.02, collect_delta=0.01, full_delta=-0.01)

    summary = analyze_pytest_policy_pair_cohort.build_pytest_policy_pair_cohort_summary(
        compare_summary_paths=[first_path, second_path],
        cohort_label="hotspots",
    )

    assert summary["kind"] == "pytest_phases"
    assert summary["task_count"] == 2
    assert summary["runtime_equivalent_task_count"] == 2
    assert summary["aggregate"]["average_pytest_startup_over_python_delta_sec"] == -0.005
    assert summary["aggregate"]["average_collect_over_pytest_startup_delta_sec"] == 0.015
    assert summary["aggregate"]["average_full_over_collect_delta_sec"] == 0.01
    assert summary["aggregate"]["collect_slower_task_count"] == 2
    assert summary["top_collect_over_pytest_startup_deltas"][0]["task_id"] == "task_101"


def test_build_pytest_policy_pair_cohort_summary_for_importtime_compares(tmp_path: Path) -> None:
    first_path = tmp_path / "task_101_importtime.json"
    second_path = tmp_path / "task_102_importtime.json"
    make_importtime_compare_summary(first_path, task_id="task_101", wall_delta=0.03, import_delta=12000, module_delta=0)
    make_importtime_compare_summary(second_path, task_id="task_102", wall_delta=-0.01, import_delta=-4000, module_delta=1)

    summary = analyze_pytest_policy_pair_cohort.build_pytest_policy_pair_cohort_summary(
        compare_summary_paths=[first_path, second_path],
        cohort_label="hotspots",
    )

    assert summary["kind"] == "pytest_importtime"
    assert summary["task_count"] == 2
    assert summary["runtime_equivalent_task_count"] == 2
    assert summary["aggregate"]["average_collect_wall_delta_sec"] == 0.01
    assert summary["aggregate"]["average_collect_import_self_delta_us"] == 4000
    assert summary["aggregate"]["average_collect_unique_module_delta"] == 0
    assert summary["aggregate"]["collect_wall_slower_task_count"] == 1
    assert summary["aggregate"]["collect_import_self_higher_task_count"] == 1
    assert summary["top_collect_wall_deltas"][0]["task_id"] == "task_101"


def test_analyze_pytest_policy_pair_cohort_writes_output_files(tmp_path: Path) -> None:
    first_path = tmp_path / "task_101_phase.json"
    make_phase_compare_summary(first_path, task_id="task_101", startup_delta=0.01, collect_delta=0.02, full_delta=0.03)

    output = analyze_pytest_policy_pair_cohort.analyze_pytest_policy_pair_cohort(
        compare_summary_paths=[first_path],
        cohort_label="hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_policy_pair_phases_cohort_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
