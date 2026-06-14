from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import run_pytest_policy_pair_matrix


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_task_file(base_dir: Path, task_id: str) -> Path:
    task_path = base_dir / f"{task_id}.json"
    write_json(
        task_path,
        {
            "task_id": task_id,
        },
    )
    return task_path


def test_build_pytest_policy_pair_matrix_summary_aggregates_task_records(tmp_path: Path, monkeypatch) -> None:
    task_1 = make_task_file(tmp_path, "task_101")
    task_2 = make_task_file(tmp_path, "task_102")
    call_log: list[tuple[str, str]] = []

    def fake_benchmark_pytest_phases(**kwargs: object) -> dict:
        task_path = Path(str(kwargs["task_path"]))
        policy_path = Path(str(kwargs["policy_path"]))
        task_id = task_path.stem
        policy_label = policy_path.stem
        call_log.append(("phase", f"{task_id}:{policy_label}"))
        summary_path = tmp_path / f"{task_id}_{policy_label}_phase.json"
        write_json(summary_path, {"task_id": task_id, "policy_id": policy_label})
        return {
            "summary_json_path": str(summary_path),
            "summary": {"task_id": task_id, "policy_id": policy_label},
        }

    def fake_benchmark_pytest_importtime(**kwargs: object) -> dict:
        task_path = Path(str(kwargs["task_path"]))
        policy_path = Path(str(kwargs["policy_path"]))
        task_id = task_path.stem
        policy_label = policy_path.stem
        call_log.append(("importtime", f"{task_id}:{policy_label}"))
        summary_path = tmp_path / f"{task_id}_{policy_label}_importtime.json"
        write_json(summary_path, {"task_id": task_id, "policy_id": policy_label})
        return {
            "summary_json_path": str(summary_path),
            "summary": {"task_id": task_id, "policy_id": policy_label},
        }

    def fake_compare_pytest_policy_pair(**kwargs: object) -> dict:
        baseline_path = Path(str(kwargs["baseline_summary_path"]))
        compare_label = str(kwargs["compare_label"])
        task_id = baseline_path.stem.split("_")[0]
        if "phase" in compare_label:
            summary = {
                "kind": "pytest_phases",
                "task_id": task_id,
                "baseline_policy_id": "improved_v68",
                "improved_policy_id": "improved_v69",
                "runtime_equivalent": True,
                "deltas": {
                    "pytest_startup_over_python_delta_sec": -0.01,
                    "collect_over_pytest_startup_delta_sec": 0.02,
                    "full_over_collect_delta_sec": 0.01,
                    "collect_first_minus_repeated_delta_sec": 0.0,
                    "full_first_minus_repeated_delta_sec": 0.01,
                },
            }
        else:
            summary = {
                "kind": "pytest_importtime",
                "task_id": task_id,
                "baseline_policy_id": "improved_v68",
                "improved_policy_id": "improved_v69",
                "runtime_equivalent": True,
                "deltas": {
                    "collect_wall_delta_sec": 0.003,
                    "collect_import_self_delta_us": 1000,
                    "collect_unique_module_delta": 0,
                    "collect_wall_first_minus_repeated_delta_sec": -0.01,
                    "collect_import_self_first_minus_repeated_delta_us": -2000,
                },
            }
        summary_path = tmp_path / f"{compare_label}.json"
        write_json(summary_path, summary)
        return {
            "summary_json_path": str(summary_path),
            "summary": summary,
        }

    def fake_analyze_pytest_policy_pair_cohort(**kwargs: object) -> dict:
        compare_paths = [Path(str(item)).name for item in kwargs["compare_summary_paths"]]
        cohort_label = str(kwargs["cohort_label"])
        if cohort_label.endswith("_phase"):
            summary = {
                "kind": "pytest_phases",
                "cohort_label": cohort_label,
                "aggregate": {
                    "average_pytest_startup_over_python_delta_sec": -0.01,
                    "average_collect_over_pytest_startup_delta_sec": 0.02,
                    "average_full_over_collect_delta_sec": 0.01,
                    "collect_slower_task_count": 2,
                    "full_slower_task_count": 2,
                },
            }
        else:
            summary = {
                "kind": "pytest_importtime",
                "cohort_label": cohort_label,
                "aggregate": {
                    "average_collect_wall_delta_sec": 0.003,
                    "average_collect_import_self_delta_us": 1000,
                    "collect_wall_slower_task_count": 2,
                    "collect_import_self_higher_task_count": 2,
                },
            }
        summary_path = tmp_path / f"{cohort_label}.json"
        write_json(summary_path, summary)
        return {
            "summary_json_path": str(summary_path),
            "summary": summary | {"compare_paths": compare_paths},
        }

    monkeypatch.setattr(run_pytest_policy_pair_matrix, "benchmark_pytest_phases", fake_benchmark_pytest_phases)
    monkeypatch.setattr(run_pytest_policy_pair_matrix, "benchmark_pytest_importtime", fake_benchmark_pytest_importtime)
    monkeypatch.setattr(run_pytest_policy_pair_matrix, "compare_pytest_policy_pair", fake_compare_pytest_policy_pair)
    monkeypatch.setattr(
        run_pytest_policy_pair_matrix,
        "analyze_pytest_policy_pair_cohort",
        fake_analyze_pytest_policy_pair_cohort,
    )

    summary = run_pytest_policy_pair_matrix.build_pytest_policy_pair_matrix_summary(
        task_paths=[task_1, task_2],
        repo_root=tmp_path,
        baseline_policy_path=tmp_path / "improved_v68.json",
        improved_policy_path=tmp_path / "improved_v69.json",
        repetitions=3,
        output_dir=tmp_path,
        matrix_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["matrix_label"] == "hotspots"
    assert summary["runtime_equivalent_task_count"] == 2
    assert summary["phase_cohort_summary"]["aggregate"]["average_collect_over_pytest_startup_delta_sec"] == 0.02
    assert summary["importtime_cohort_summary"]["aggregate"]["average_collect_wall_delta_sec"] == 0.003
    assert len(summary["task_records"]) == 2
    assert call_log.count(("phase", "task_101:improved_v68")) == 1
    assert call_log.count(("phase", "task_101:improved_v69")) == 1
    assert call_log.count(("importtime", "task_102:improved_v68")) == 1
    assert call_log.count(("importtime", "task_102:improved_v69")) == 1


def test_run_pytest_policy_pair_matrix_writes_output_files(tmp_path: Path, monkeypatch) -> None:
    def fake_build(**_: object) -> dict:
        return {
            "created_at": "2026-06-13T10:00:00+00:00",
            "matrix_label": "hotspots",
            "task_count": 2,
            "repetitions": 3,
            "repo_root": str(tmp_path),
            "baseline_policy_path": str(tmp_path / "improved_v68.json"),
            "improved_policy_path": str(tmp_path / "improved_v69.json"),
            "runtime_equivalent_task_count": 2,
            "task_records": [],
            "phase_cohort_summary_path": str(tmp_path / "phase.json"),
            "importtime_cohort_summary_path": str(tmp_path / "importtime.json"),
            "phase_cohort_summary": {
                "aggregate": {
                    "average_pytest_startup_over_python_delta_sec": -0.01,
                    "average_collect_over_pytest_startup_delta_sec": 0.02,
                    "average_full_over_collect_delta_sec": 0.01,
                    "collect_slower_task_count": 1,
                    "full_slower_task_count": 1,
                }
            },
            "importtime_cohort_summary": {
                "aggregate": {
                    "average_collect_wall_delta_sec": 0.003,
                    "average_collect_import_self_delta_us": 1000,
                    "collect_wall_slower_task_count": 1,
                    "collect_import_self_higher_task_count": 1,
                }
            },
        }

    monkeypatch.setattr(run_pytest_policy_pair_matrix, "build_pytest_policy_pair_matrix_summary", fake_build)

    output = run_pytest_policy_pair_matrix.run_pytest_policy_pair_matrix(
        task_paths=[tmp_path / "task_101.json"],
        repo_root=tmp_path,
        baseline_policy_path=tmp_path / "improved_v68.json",
        improved_policy_path=tmp_path / "improved_v69.json",
        repetitions=3,
        output_dir=tmp_path / "logs" / "summaries",
        matrix_label="hotspots",
    )

    assert output["analysis_id"] == "pytest_policy_pair_matrix_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
