from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import benchmark_run_tests_modes


def test_build_run_tests_mode_benchmark_returns_three_modes() -> None:
    summary = benchmark_run_tests_modes.build_run_tests_mode_benchmark(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
    )

    assert summary["task_id"] == "task_001"
    assert summary["repetitions"] == 1
    assert set(summary["mode_summaries"]) == {
        "source_repo",
        "persistent_workspace",
        "fresh_workspace",
    }
    for mode_summary in summary["mode_summaries"].values():
        assert mode_summary["run_count"] == 1
        assert isinstance(mode_summary["average_run_tests_duration_sec"], float)
        assert isinstance(mode_summary["average_command_execution_duration_sec"], float)
        assert isinstance(mode_summary["average_combined_duration_sec"], float)


def test_benchmark_run_tests_modes_writes_output_files(tmp_path: Path) -> None:
    output = benchmark_run_tests_modes.benchmark_run_tests_modes(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
        output_dir=tmp_path / "logs" / "summaries",
        benchmark_label="task001",
    )

    assert output["benchmark_id"] == "run_tests_modes_task001_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
