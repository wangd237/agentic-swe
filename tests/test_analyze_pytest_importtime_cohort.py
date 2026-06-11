from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_pytest_importtime_cohort


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_benchmark_summary(
    base_dir: Path,
    *,
    task_id: str,
    version_wall: float,
    collect_wall: float,
    version_import_self: int,
    collect_import_self: int,
    version_module_count: int,
    collect_module_count: int,
    collect_wall_first_minus_repeated: float | None,
    collect_import_first_minus_repeated: int | None,
    extra_modules: list[dict],
) -> Path:
    summary_path = base_dir / f"{task_id}.json"
    write_json(
        summary_path,
        {
            "task_id": task_id,
            "test_command": "python -m pytest tests/test_demo.py -q",
            "repetitions": 3,
            "phase_summaries": {
                "pytest_version_importtime": {
                    "average_command_execution_duration_sec": version_wall,
                    "average_total_import_self_us": version_import_self,
                    "average_unique_module_count": version_module_count,
                },
                "pytest_collect_importtime": {
                    "average_command_execution_duration_sec": collect_wall,
                    "average_total_import_self_us": collect_import_self,
                    "average_unique_module_count": collect_module_count,
                },
            },
            "derived_metrics": {
                "average_collect_wall_delta_sec": round(collect_wall - version_wall, 4),
                "average_collect_import_self_delta_us": collect_import_self - version_import_self,
                "average_collect_unique_module_delta": collect_module_count - version_module_count,
                "collect_wall_first_minus_repeated_sec": collect_wall_first_minus_repeated,
                "collect_import_self_first_minus_repeated_us": collect_import_first_minus_repeated,
                "latest_collect_extra_modules_top_self": extra_modules,
            },
        },
    )
    return summary_path


def test_build_pytest_importtime_cohort_summary_aggregates_tasks(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        version_wall=0.18,
        collect_wall=0.26,
        version_import_self=60000,
        collect_import_self=82000,
        version_module_count=420,
        collect_module_count=510,
        collect_wall_first_minus_repeated=0.01,
        collect_import_first_minus_repeated=3500,
        extra_modules=[{"module": "tests.test_demo", "self_us": 1200, "cumulative_us": 3000}],
    )
    second = make_benchmark_summary(
        tmp_path,
        task_id="task_102",
        version_wall=0.17,
        collect_wall=0.245,
        version_import_self=59000,
        collect_import_self=80000,
        version_module_count=418,
        collect_module_count=500,
        collect_wall_first_minus_repeated=0.008,
        collect_import_first_minus_repeated=2800,
        extra_modules=[{"module": "tests.test_demo", "self_us": 900, "cumulative_us": 2600}],
    )

    summary = analyze_pytest_importtime_cohort.build_pytest_importtime_cohort_summary(
        benchmark_summary_paths=[first, second],
        cohort_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["aggregate"]["average_collect_wall_delta_sec"] == 0.0775
    assert summary["aggregate"]["average_collect_import_self_delta_us"] == 21500
    assert summary["aggregate"]["average_collect_unique_module_delta"] == 86
    assert summary["aggregate"]["average_collect_wall_first_minus_repeated_sec"] == 0.009
    assert summary["aggregate"]["average_collect_import_self_first_minus_repeated_us"] == 3150.0
    assert summary["aggregate"]["collect_slower_than_version_task_count"] == 2
    assert summary["top_extra_modules"][0]["module"] == "tests.test_demo"
    assert summary["top_collect_import_deltas"][0]["task_id"] == "task_101"


def test_analyze_pytest_importtime_cohort_writes_output_files(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        version_wall=0.18,
        collect_wall=0.26,
        version_import_self=60000,
        collect_import_self=82000,
        version_module_count=420,
        collect_module_count=510,
        collect_wall_first_minus_repeated=0.01,
        collect_import_first_minus_repeated=3500,
        extra_modules=[{"module": "tests.test_demo", "self_us": 1200, "cumulative_us": 3000}],
    )

    output = analyze_pytest_importtime_cohort.analyze_pytest_importtime_cohort(
        benchmark_summary_paths=[first],
        cohort_label="hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_importtime_cohort_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
