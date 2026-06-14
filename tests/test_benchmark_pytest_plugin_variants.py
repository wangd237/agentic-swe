from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import benchmark_pytest_plugin_variants


def test_build_collect_importtime_command_includes_plugin_flags() -> None:
    command = benchmark_pytest_plugin_variants._build_collect_importtime_command(
        "python -m pytest tests/test_demo.py -q",
        ["-p no:junitxml", "-p no:pastebin"],
    )

    assert command == "python -X importtime -m pytest tests/test_demo.py -q --collect-only -p no:junitxml -p no:pastebin"


def test_build_variant_delta_computes_removed_modules() -> None:
    baseline_summary = {
        "variant_name": "default_plugins",
        "average_command_execution_duration_sec": 0.25,
        "average_total_import_self_us": 100000,
        "average_unique_module_count": 290,
        "latest_module_names": ["pytest", "junitxml", "pastebin", "colorama"],
    }
    candidate_summary = {
        "variant_name": "light_terminal_plugins",
        "plugin_flags": ["-p no:junitxml"],
        "average_command_execution_duration_sec": 0.2,
        "average_total_import_self_us": 90000,
        "average_unique_module_count": 280,
        "latest_module_names": ["pytest", "colorama"],
    }

    delta = benchmark_pytest_plugin_variants._build_variant_delta(candidate_summary, baseline_summary)

    assert delta["wall_delta_sec"] == -0.05
    assert delta["import_self_delta_us"] == -10000
    assert delta["unique_module_delta"] == -10
    assert delta["removed_modules"] == ["junitxml", "pastebin"]


def test_build_pytest_plugin_variant_benchmark_returns_variants() -> None:
    summary = benchmark_pytest_plugin_variants.build_pytest_plugin_variant_benchmark(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
    )

    assert summary["task_id"] == "task_001"
    assert summary["repetitions"] == 1
    assert set(summary["variant_summaries"]) == {
        "default_plugins",
        "light_terminal_plugins",
        "debugging_only",
        "unraisableexception_only",
        "threadexception_only",
        "debug_exception_plugins",
        "minimal_safe_plugins",
    }
    assert isinstance(summary["derived_metrics"]["ranked_by_wall_reduction"], list)


def test_build_pytest_plugin_variant_benchmark_passes_policy_flags(tmp_path: Path, monkeypatch) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(
        '{"policy_id":"plugin_policy","description":"demo","pytest_additional_flags":["-p no:unraisableexception","-p no:threadexception"]}',
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
            },
        }

    monkeypatch.setattr(benchmark_pytest_plugin_variants, "run_tests", fake_run_tests)

    summary = benchmark_pytest_plugin_variants.build_pytest_plugin_variant_benchmark(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
        policy_path=policy_path,
    )

    assert summary["policy_id"] == "plugin_policy"
    assert summary["pytest_additional_flags"] == ["-p no:unraisableexception", "-p no:threadexception"]
    assert len(observed_flags) == len(benchmark_pytest_plugin_variants.PLUGIN_VARIANTS)
    assert all(flags == ["-p no:unraisableexception", "-p no:threadexception"] for flags in observed_flags)


def test_benchmark_pytest_plugin_variants_writes_output_files(tmp_path: Path) -> None:
    output = benchmark_pytest_plugin_variants.benchmark_pytest_plugin_variants(
        task_path=REPO_ROOT / "benchmarks" / "tasks" / "task_001.json",
        repo_root=REPO_ROOT,
        repetitions=1,
        output_dir=tmp_path / "logs" / "summaries",
        benchmark_label="task001",
    )

    assert output["benchmark_id"] == "pytest_plugin_variants_task001_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
