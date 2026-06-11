from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import benchmark_pytest_phases


def test_build_collect_only_command_appends_flag() -> None:
    command = benchmark_pytest_phases._build_collect_only_command("python -m pytest tests/test_demo.py -q")

    assert command == "python -m pytest tests/test_demo.py -q --collect-only"


def test_build_pytest_phase_benchmark_returns_expected_phases() -> None:
    summary = benchmark_pytest_phases.build_pytest_phase_benchmark(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
    )

    assert summary["task_id"] == "task_001"
    assert summary["repetitions"] == 1
    assert set(summary["phase_summaries"]) == {
        "python_noop",
        "pytest_version",
        "pytest_collect_only",
        "pytest_full_run",
    }
    assert isinstance(summary["derived_metrics"]["average_pytest_startup_over_python_sec"], float)
    assert isinstance(summary["derived_metrics"]["average_collect_over_pytest_startup_sec"], float)
    assert isinstance(summary["derived_metrics"]["average_full_over_collect_sec"], float)


def test_benchmark_pytest_phases_writes_output_files(tmp_path: Path) -> None:
    output = benchmark_pytest_phases.benchmark_pytest_phases(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
        output_dir=tmp_path / "logs" / "summaries",
        benchmark_label="task001",
    )

    assert output["benchmark_id"] == "pytest_phases_task001_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
