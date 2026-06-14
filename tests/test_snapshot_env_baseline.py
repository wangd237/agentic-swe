from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import snapshot_env_baseline


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_compare_snapshots_builds_drift_summary() -> None:
    reference = {
        "snapshot_id": "env_baseline_old",
        "commands": [
            {"command_id": "python_noop", "mean_sec": 0.1},
            {"command_id": "pytest_version", "mean_sec": 0.2},
        ],
    }
    current = {
        "snapshot_id": "env_baseline_new",
        "commands": [
            {"command_id": "python_noop", "mean_sec": 0.12},
            {"command_id": "pytest_version", "mean_sec": 0.25},
        ],
    }

    comparison = snapshot_env_baseline.compare_snapshots(
        reference_snapshot=reference,
        current_snapshot=current,
        reference_snapshot_path="logs/env_baselines/env_baseline_old.json",
    )

    assert comparison["comparable_command_count"] == 2
    assert comparison["mean_delta_sec"] == 0.035
    assert comparison["max_delta_sec"] == 0.05
    assert comparison["per_command"][0]["command_id"] == "pytest_version"


def test_snapshot_env_baseline_uses_benchmarks_and_writes_files(
    monkeypatch,
    tmp_path: Path,
) -> None:
    measured_specs: list[str] = []

    def fake_run_command_benchmark(*, command_spec: dict, repetitions: int, cwd: Path) -> dict:
        measured_specs.append(command_spec["command_id"])
        return snapshot_env_baseline.summarize_samples(
            command_id=command_spec["command_id"],
            description=command_spec["description"],
            argv=list(command_spec["argv"]),
            samples_sec=[0.1, 0.12, 0.11],
            stdout_preview="ok",
        )

    monkeypatch.setattr(snapshot_env_baseline, "run_command_benchmark", fake_run_command_benchmark)

    output = snapshot_env_baseline.snapshot_env_baseline(
        output_dir=tmp_path / "logs" / "env_baselines",
        repetitions=3,
        command_specs=[
            {
                "command_id": "python_noop",
                "description": "demo",
                "argv": [sys.executable, "-c", "pass"],
            }
        ],
        cwd=tmp_path,
    )

    assert measured_specs == ["python_noop"]
    assert output["summary"]["aggregate"]["mean_of_means_sec"] == 0.11
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()


def test_snapshot_env_baseline_builds_comparison_when_reference_is_given(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reference_path = tmp_path / "logs" / "env_baselines" / "env_baseline_old.json"
    write_json(
        reference_path,
        {
            "snapshot_id": "env_baseline_old",
            "commands": [
                {"command_id": "python_noop", "mean_sec": 0.1},
            ],
        },
    )

    def fake_run_command_benchmark(*, command_spec: dict, repetitions: int, cwd: Path) -> dict:
        return snapshot_env_baseline.summarize_samples(
            command_id=command_spec["command_id"],
            description=command_spec["description"],
            argv=list(command_spec["argv"]),
            samples_sec=[0.13, 0.12],
        )

    monkeypatch.setattr(snapshot_env_baseline, "run_command_benchmark", fake_run_command_benchmark)

    output = snapshot_env_baseline.snapshot_env_baseline(
        output_dir=tmp_path / "logs" / "env_baselines",
        repetitions=2,
        compare_against=reference_path,
        command_specs=[
            {
                "command_id": "python_noop",
                "description": "demo",
                "argv": [sys.executable, "-c", "pass"],
            }
        ],
        cwd=tmp_path,
    )

    comparison = output["summary"]["comparison"]
    assert comparison is not None
    assert comparison["reference_snapshot_id"] == "env_baseline_old"
    assert comparison["mean_delta_sec"] == 0.025
