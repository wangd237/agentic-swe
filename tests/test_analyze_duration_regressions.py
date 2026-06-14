from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import analyze_duration_regressions


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_batch_summary(base_dir: Path, name: str, task_specs: list[dict]) -> Path:
    tasks: list[dict] = []
    for spec in task_specs:
        result_path = base_dir / "logs" / "trajectories" / spec["task_id"] / name / "result.json"
        write_json(
            result_path,
            {
                "task_id": spec["task_id"],
                "final_status": spec.get("final_status", "success"),
                "duration_sec": spec["duration_sec"],
                "tool_stats": {"total_tool_calls": spec.get("tool_calls", 8)},
            },
        )
        tasks.append(
            {
                "task_id": spec["task_id"],
                "task_path": str(base_dir / "benchmarks" / "tasks" / f"{spec['task_id']}.json"),
                "run_id": f"{name}_{spec['task_id']}",
                "final_status": spec.get("final_status", "success"),
                "result_path": str(result_path),
            }
        )

    summary_path = base_dir / "logs" / "summaries" / f"{name}.json"
    write_json(
        summary_path,
        {
            "batch_run_id": name,
            "tasks": tasks,
        },
    )
    return summary_path


def test_resolve_batch_summary_path_supports_eval_file(tmp_path: Path) -> None:
    summary_path = tmp_path / "logs" / "summaries" / "batch_run_demo_001.json"
    write_json(summary_path, {"batch_run_id": "batch_run_demo_001", "tasks": []})
    eval_path = tmp_path / "logs" / "summaries" / "batch_eval_demo_001.json"
    write_json(eval_path, {"source_batch_run_id": "batch_run_demo_001"})

    resolved = analyze_duration_regressions.resolve_batch_summary_path(eval_path=eval_path)

    assert resolved == summary_path.resolve()


def test_analyze_duration_regressions_builds_overlap_and_task_deltas(tmp_path: Path) -> None:
    baseline_summary = make_batch_summary(
        tmp_path,
        "batch_run_realissuev31_001",
        [
            {"task_id": "task_001", "duration_sec": 0.4, "tool_calls": 7},
            {"task_id": "task_002", "duration_sec": 0.6, "tool_calls": 9},
        ],
    )
    improved_summary = make_batch_summary(
        tmp_path,
        "batch_run_realissuev32_001",
        [
            {"task_id": "task_001", "duration_sec": 0.55, "tool_calls": 7},
            {"task_id": "task_002", "duration_sec": 0.5, "tool_calls": 8},
            {"task_id": "task_003", "duration_sec": 0.7, "tool_calls": 10},
        ],
    )

    output = analyze_duration_regressions.analyze_duration_regressions(
        baseline_batch_summary_path=baseline_summary,
        improved_batch_summary_path=improved_summary,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="realissuev32",
        top_n=5,
    )

    summary = output["summary"]
    assert summary["task_set"]["common_task_count"] == 2
    assert summary["task_set"]["added_task_ids"] == ["task_003"]
    assert summary["aggregate"]["baseline_average_duration_sec_common"] == 0.5
    assert summary["aggregate"]["improved_average_duration_sec_common"] == 0.525
    assert summary["aggregate"]["common_average_delta_sec"] == 0.025
    assert summary["top_regressions"][0]["task_id"] == "task_001"
    assert summary["top_regressions"][0]["delta_duration_sec"] == 0.15
    assert summary["top_improvements"][0]["task_id"] == "task_002"
    assert summary["top_improvements"][0]["delta_duration_sec"] == -0.1
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()


def test_analyze_duration_regressions_applies_environment_baseline_adjustment(tmp_path: Path) -> None:
    baseline_summary = make_batch_summary(
        tmp_path,
        "batch_run_realissuev40_001",
        [
            {"task_id": "task_001", "duration_sec": 0.4},
        ],
    )
    improved_summary = make_batch_summary(
        tmp_path,
        "batch_run_realissuev41_001",
        [
            {"task_id": "task_001", "duration_sec": 0.46},
        ],
    )
    env_baseline_path = tmp_path / "logs" / "env_baselines" / "env_baseline_demo.json"
    write_json(
        env_baseline_path,
        {
            "snapshot_id": "env_baseline_demo",
            "comparison": {
                "reference_snapshot_id": "env_baseline_old",
                "reference_snapshot_path": "logs/env_baselines/env_baseline_old.json",
                "comparable_command_count": 2,
                "mean_delta_sec": 0.02,
                "max_delta_sec": 0.03,
                "mean_ratio": 1.1,
            },
        },
    )

    output = analyze_duration_regressions.analyze_duration_regressions(
        baseline_batch_summary_path=baseline_summary,
        improved_batch_summary_path=improved_summary,
        env_baseline_path=env_baseline_path,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="realissuev41",
    )

    summary = output["summary"]
    assert summary["aggregate"]["common_average_delta_sec"] == 0.06
    assert summary["aggregate"]["env_adjusted_common_average_delta_sec"] == 0.04
    assert summary["environment_baseline"]["adjustment_available"] is True
