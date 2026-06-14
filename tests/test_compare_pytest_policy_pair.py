from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import compare_pytest_policy_pair


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_phase_summary(
    path: Path,
    *,
    task_id: str,
    policy_id: str,
    startup: float,
    collect: float,
    full: float,
    pytest_additional_flags: list[str] | None = None,
) -> None:
    write_json(
        path,
        {
            "task_id": task_id,
            "policy_id": policy_id,
            "pytest_additional_flags": pytest_additional_flags or [],
            "phase_summaries": {
                "python_noop": {},
                "pytest_version": {},
                "pytest_collect_only": {},
                "pytest_full_run": {},
            },
            "derived_metrics": {
                "average_pytest_startup_over_python_sec": startup,
                "average_collect_over_pytest_startup_sec": collect,
                "average_full_over_collect_sec": full,
                "collect_first_minus_repeated_sec": -0.01,
                "full_first_minus_repeated_sec": 0.02,
            },
        },
    )


def make_importtime_summary(
    path: Path,
    *,
    task_id: str,
    policy_id: str,
    wall: float,
    import_us: int,
    modules: int,
    pytest_additional_flags: list[str] | None = None,
) -> None:
    write_json(
        path,
        {
            "task_id": task_id,
            "policy_id": policy_id,
            "pytest_additional_flags": pytest_additional_flags or [],
            "phase_summaries": {
                "pytest_version_importtime": {},
                "pytest_collect_importtime": {},
            },
            "derived_metrics": {
                "average_collect_wall_delta_sec": wall,
                "average_collect_import_self_delta_us": import_us,
                "average_collect_unique_module_delta": modules,
                "collect_wall_first_minus_repeated_sec": -0.02,
                "collect_import_self_first_minus_repeated_us": 1000,
            },
        },
    )


def test_build_pytest_policy_pair_comparison_for_phase_summary(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_phase.json"
    improved_path = tmp_path / "improved_phase.json"
    make_phase_summary(baseline_path, task_id="task_123", policy_id="improved_v68", startup=0.12, collect=0.11, full=0.02)
    make_phase_summary(improved_path, task_id="task_123", policy_id="improved_v69", startup=0.13, collect=0.10, full=0.03)

    summary = compare_pytest_policy_pair.build_pytest_policy_pair_comparison(
        baseline_summary_path=baseline_path,
        improved_summary_path=improved_path,
    )

    assert summary["kind"] == "pytest_phases"
    assert summary["runtime_equivalent"] is True
    assert summary["deltas"]["pytest_startup_over_python_delta_sec"] == 0.01
    assert summary["deltas"]["collect_over_pytest_startup_delta_sec"] == -0.01
    assert summary["deltas"]["full_over_collect_delta_sec"] == 0.01


def test_build_pytest_policy_pair_comparison_for_importtime_summary(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_importtime.json"
    improved_path = tmp_path / "improved_importtime.json"
    make_importtime_summary(baseline_path, task_id="task_119", policy_id="improved_v68", wall=0.05, import_us=12000, modules=35)
    make_importtime_summary(improved_path, task_id="task_119", policy_id="improved_v69", wall=0.04, import_us=9000, modules=35)

    summary = compare_pytest_policy_pair.build_pytest_policy_pair_comparison(
        baseline_summary_path=baseline_path,
        improved_summary_path=improved_path,
    )

    assert summary["kind"] == "pytest_importtime"
    assert summary["runtime_equivalent"] is True
    assert summary["deltas"]["collect_wall_delta_sec"] == -0.01
    assert summary["deltas"]["collect_import_self_delta_us"] == -3000
    assert summary["deltas"]["collect_unique_module_delta"] == 0


def test_compare_pytest_policy_pair_writes_output_files(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_phase.json"
    improved_path = tmp_path / "improved_phase.json"
    make_phase_summary(baseline_path, task_id="task_123", policy_id="improved_v68", startup=0.12, collect=0.11, full=0.02)
    make_phase_summary(improved_path, task_id="task_123", policy_id="improved_v69", startup=0.13, collect=0.10, full=0.03)

    output = compare_pytest_policy_pair.compare_pytest_policy_pair(
        baseline_summary_path=baseline_path,
        improved_summary_path=improved_path,
        output_dir=tmp_path / "logs" / "summaries",
        compare_label="task123_phase",
    )

    assert output["analysis_id"] == "pytest_policy_pair_task123_phase_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()


def test_build_pytest_policy_pair_comparison_marks_runtime_difference(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline_phase.json"
    improved_path = tmp_path / "improved_phase.json"
    make_phase_summary(
        baseline_path,
        task_id="task_123",
        policy_id="improved_v68",
        startup=0.12,
        collect=0.11,
        full=0.02,
        pytest_additional_flags=["-p no:unraisableexception"],
    )
    make_phase_summary(
        improved_path,
        task_id="task_123",
        policy_id="improved_v69",
        startup=0.13,
        collect=0.10,
        full=0.03,
        pytest_additional_flags=["-p no:threadexception"],
    )

    summary = compare_pytest_policy_pair.build_pytest_policy_pair_comparison(
        baseline_summary_path=baseline_path,
        improved_summary_path=improved_path,
    )

    assert summary["runtime_equivalent"] is False
