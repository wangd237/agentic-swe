from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import benchmark_pytest_importtime


def test_parse_importtime_entries_extracts_modules() -> None:
    sample = (
        "import time: self [us] | cumulative | imported package\n"
        "import time:       120 |        300 | pytest\n"
        "import time:        45 |         80 |   pluggy\n"
    )

    entries = benchmark_pytest_importtime.parse_importtime_entries(sample)

    assert len(entries) == 2
    assert entries[0]["module"] == "pytest"
    assert entries[1]["module"] == "pluggy"
    assert entries[1]["self_us"] == 45


def test_build_importtime_command_injects_flag() -> None:
    command = benchmark_pytest_importtime._build_importtime_command("python -m pytest --version")

    assert command == "python -X importtime -m pytest --version"


def test_build_collect_extra_modules_filters_zero_placeholder_modules() -> None:
    version_summary = {
        "latest_module_names": ["pytest", "pluggy"],
    }
    collect_summary = {
        "records": [
            {
                "module_names": ["pytest", "pluggy", "_ctypes", "colorama"],
                "import_entries": [
                    {"module": "pytest", "self_us": 500, "cumulative_us": 1000},
                    {"module": "_ctypes", "self_us": 2500, "cumulative_us": 2500},
                    {"module": "colorama", "self_us": 800, "cumulative_us": 1200},
                ],
            }
        ]
    }

    extra_modules = benchmark_pytest_importtime._build_collect_extra_modules(version_summary, collect_summary)

    assert [entry["module"] for entry in extra_modules] == ["_ctypes", "colorama"]
    assert extra_modules[0]["self_us"] == 2500


def test_build_pytest_importtime_benchmark_returns_expected_phases() -> None:
    summary = benchmark_pytest_importtime.build_pytest_importtime_benchmark(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
    )

    assert summary["task_id"] == "task_001"
    assert summary["repetitions"] == 1
    assert set(summary["phase_summaries"]) == {
        "pytest_version_importtime",
        "pytest_collect_importtime",
    }
    assert isinstance(summary["derived_metrics"]["average_collect_wall_delta_sec"], float)
    assert isinstance(summary["derived_metrics"]["average_collect_import_self_delta_us"], int)
    assert isinstance(summary["derived_metrics"]["average_collect_unique_module_delta"], int)


def test_build_pytest_importtime_benchmark_passes_policy_flags(tmp_path: Path, monkeypatch) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        '{"policy_id":"import_policy","description":"demo","pytest_additional_flags":["-p no:threadexception"]}',
        encoding="utf-8",
    )
    observed_flags: list[list[str]] = []

    def fake_run_tests(repo_path: str, command: str, timeout_sec: int = 30, additional_pytest_flags: list[str] | None = None) -> dict:
        _ = repo_path, command, timeout_sec
        observed_flags.append(additional_pytest_flags or [])
        return {
            "ok": True,
            "summary": "ok",
            "data": {
                "exit_code": 0,
                "stderr": "",
                "command_execution_duration_sec": 0.01,
                "summary_extraction_duration_sec": 0.0,
            },
        }

    monkeypatch.setattr(benchmark_pytest_importtime, "run_tests", fake_run_tests)

    summary = benchmark_pytest_importtime.build_pytest_importtime_benchmark(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
        policy_path=policy_path,
    )

    assert summary["policy_id"] == "import_policy"
    assert summary["pytest_additional_flags"] == ["-p no:threadexception"]
    assert observed_flags == [["-p no:threadexception"]] * 2


def test_benchmark_pytest_importtime_writes_output_files(tmp_path: Path) -> None:
    output = benchmark_pytest_importtime.benchmark_pytest_importtime(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
        output_dir=tmp_path / "logs" / "summaries",
        benchmark_label="task001",
    )

    assert output["benchmark_id"] == "pytest_importtime_task001_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
