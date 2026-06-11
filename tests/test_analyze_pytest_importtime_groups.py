from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_pytest_importtime_groups


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_benchmark_summary(
    base_dir: Path,
    *,
    task_id: str,
    version_modules: list[str],
    collect_entries: list[dict],
    collect_import_self_delta_us: int,
    collect_wall_delta_sec: float = 0.07,
    collect_unique_module_delta: int = 5,
) -> Path:
    summary_path = base_dir / f"{task_id}.json"
    write_json(
        summary_path,
        {
            "task_id": task_id,
            "phase_summaries": {
                "pytest_version_importtime": {
                    "records": [
                        {
                            "module_names": version_modules,
                        }
                    ]
                },
                "pytest_collect_importtime": {
                    "records": [
                        {
                            "module_names": version_modules + [entry["module"] for entry in collect_entries],
                            "import_entries": collect_entries,
                        }
                    ]
                },
            },
            "derived_metrics": {
                "average_collect_wall_delta_sec": collect_wall_delta_sec,
                "average_collect_import_self_delta_us": collect_import_self_delta_us,
                "average_collect_unique_module_delta": collect_unique_module_delta,
            },
        },
    )
    return summary_path


def test_classify_module_group_recognizes_known_buckets() -> None:
    assert analyze_pytest_importtime_groups.classify_module_group("_ctypes") == "windows_ctypes"
    assert analyze_pytest_importtime_groups.classify_module_group("xml.etree.ElementTree") == "xml_stack"
    assert analyze_pytest_importtime_groups.classify_module_group("pdb") == "debugging_chain"
    assert analyze_pytest_importtime_groups.classify_module_group("_pytest.terminalprogress") == "terminal_chain"
    assert analyze_pytest_importtime_groups.classify_module_group("_pytest.junitxml") == "pytest_optional_plugins"
    assert analyze_pytest_importtime_groups.classify_module_group("_pytest.skipping") == "pytest_collection_core"
    assert analyze_pytest_importtime_groups.classify_module_group("readline") == "python_shell_chain"
    assert analyze_pytest_importtime_groups.classify_module_group("tests.test_demo") == "other"


def test_build_pytest_import_group_summary_aggregates_groups(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        version_modules=["pytest", "pluggy"],
        collect_entries=[
            {"module": "pytest", "self_us": 500, "cumulative_us": 2000},
            {"module": "_ctypes", "self_us": 7000, "cumulative_us": 7000},
            {"module": "ctypes.wintypes", "self_us": 3000, "cumulative_us": 3000},
            {"module": "xml.etree.ElementTree", "self_us": 2500, "cumulative_us": 2500},
            {"module": "_pytest.terminalprogress", "self_us": 1200, "cumulative_us": 1200},
            {"module": "tests.test_demo", "self_us": 600, "cumulative_us": 600},
        ],
        collect_import_self_delta_us=14300,
    )
    second = make_benchmark_summary(
        tmp_path,
        task_id="task_102",
        version_modules=["pytest", "pluggy"],
        collect_entries=[
            {"module": "pytest", "self_us": 450, "cumulative_us": 1800},
            {"module": "_ctypes", "self_us": 5000, "cumulative_us": 5000},
            {"module": "pdb", "self_us": 1800, "cumulative_us": 1800},
            {"module": "_pytest.skipping", "self_us": 1600, "cumulative_us": 1600},
        ],
        collect_import_self_delta_us=8400,
    )

    summary = analyze_pytest_importtime_groups.build_pytest_import_group_summary(
        benchmark_summary_paths=[first, second],
        cohort_label="hotspots",
    )

    assert summary["task_count"] == 2
    assert summary["ranked_groups"][0]["group_name"] == "windows_ctypes"
    assert summary["ranked_groups"][0]["average_self_us"] == 7500
    assert summary["ranked_groups"][0]["average_module_count"] == 2
    assert summary["dominant_tasks"][0]["task_id"] == "task_101"
    assert summary["dominant_tasks"][0]["dominant_group"] == "windows_ctypes"


def test_analyze_pytest_import_groups_writes_output_files(tmp_path: Path) -> None:
    first = make_benchmark_summary(
        tmp_path,
        task_id="task_101",
        version_modules=["pytest", "pluggy"],
        collect_entries=[
            {"module": "_ctypes", "self_us": 5000, "cumulative_us": 5000},
        ],
        collect_import_self_delta_us=5000,
    )

    output = analyze_pytest_importtime_groups.analyze_pytest_import_groups(
        benchmark_summary_paths=[first],
        cohort_label="hotspots",
        output_dir=tmp_path / "logs" / "summaries",
    )

    assert output["analysis_id"] == "pytest_import_groups_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
