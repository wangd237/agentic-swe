from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import recheck_policy_pair_tasks


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def make_task_file(base_dir: Path, task_id: str) -> Path:
    task_path = base_dir / "benchmarks" / "tasks" / f"{task_id}.json"
    write_json(
        task_path,
        {
            "task_id": task_id,
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo",
            "issue_text": "demo",
            "test_command": "python -m pytest -q",
            "success_criteria": "demo",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": [],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    return task_path


def make_trace(path: Path, *, search_duration: float, run_tests_durations: list[float]) -> None:
    steps = [
        {
            "step_index": 1,
            "action_type": "tool_call",
            "tool_name": "search_code",
            "timestamp": "2026-06-13T10:00:00.100000+00:00",
            "duration_sec": search_duration,
        }
    ]
    for index, duration_sec in enumerate(run_tests_durations, start=2):
        steps.append(
            {
                "step_index": index,
                "action_type": "tool_call",
                "tool_name": "run_tests",
                "timestamp": f"2026-06-13T10:00:00.{index}00000+00:00",
                "duration_sec": duration_sec,
            }
        )
    write_json(
        path,
        {
            "task_id": "task_001",
            "run_id": "run_20260613T100000000000Z_0001",
            "steps": steps,
        },
    )


def test_build_policy_pair_recheck_summary_aggregates_tasks(tmp_path: Path, monkeypatch) -> None:
    task_1 = make_task_file(tmp_path, "task_001")
    task_2 = make_task_file(tmp_path, "task_002")
    trace_dir = tmp_path / "logs" / "trajectories"
    call_index = {"value": 0}

    run_specs = [
        ("task_001", "baseline_v68", 0.50, 0.05, [0.18, 0.12]),
        ("task_001", "improved_v69", 0.58, 0.08, [0.22, 0.14]),
        ("task_001", "baseline_v68", 0.51, 0.05, [0.19, 0.12]),
        ("task_001", "improved_v69", 0.57, 0.08, [0.21, 0.14]),
        ("task_002", "baseline_v68", 0.42, 0.02, [0.11, 0.10]),
        ("task_002", "improved_v69", 0.41, 0.01, [0.10, 0.10]),
        ("task_002", "baseline_v68", 0.43, 0.02, [0.12, 0.10]),
        ("task_002", "improved_v69", 0.42, 0.01, [0.11, 0.10]),
    ]

    def fake_run_agent(*, task_path: str | Path, repo_root: str | Path, policy_path: str | Path | None = None) -> dict:
        _ = repo_root
        spec = run_specs[call_index["value"]]
        call_index["value"] += 1
        task_id, policy_id, duration_sec, search_duration, run_tests_durations = spec
        trace_path = trace_dir / task_id / f"run_{call_index['value']:03d}" / "trace.json"
        result_path = trace_dir / task_id / f"run_{call_index['value']:03d}" / "result.json"
        make_trace(trace_path, search_duration=search_duration, run_tests_durations=run_tests_durations)
        write_json(
            result_path,
            {
                "task_id": task_id,
                "run_id": f"run_{call_index['value']:03d}",
                "final_status": "success",
                "duration_sec": duration_sec,
                "tool_stats": {
                    "policy_id": policy_id,
                    "total_tool_calls": 2,
                },
            },
        )
        return {
            "result": {
                "run_id": f"run_{call_index['value']:03d}",
                "final_status": "success",
                "duration_sec": duration_sec,
                "tool_stats": {
                    "policy_id": policy_id,
                    "total_tool_calls": 2,
                },
            },
            "run_paths": {
                "trace_json_path": str(trace_path),
                "result_json_path": str(result_path),
            },
        }

    monkeypatch.setattr(recheck_policy_pair_tasks, "run_agent", fake_run_agent)

    summary = recheck_policy_pair_tasks.build_policy_pair_recheck_summary(
        task_paths=[task_1, task_2],
        baseline_policy_path=tmp_path / "baseline_v68.json",
        improved_policy_path=tmp_path / "improved_v69.json",
        repo_root=tmp_path,
        repetitions=2,
    )

    assert summary["task_count"] == 2
    assert summary["aggregate"]["average_duration_delta_sec"] == 0.03
    assert summary["aggregate"]["average_search_code_delta_sec"] == 0.01
    assert summary["aggregate"]["average_run_tests_delta_sec"] == 0.02
    assert summary["aggregate"]["average_run_tests_first_delta_sec"] == 0.01
    assert summary["aggregate"]["average_run_tests_second_delta_sec"] == 0.01
    assert summary["aggregate"]["reproduced_duration_task_count"] == 1
    assert summary["aggregate"]["reproduced_search_code_task_count"] == 1
    assert summary["aggregate"]["reproduced_run_tests_task_count"] == 1
    assert summary["aggregate"]["reproduced_run_tests_first_task_count"] == 1
    assert summary["aggregate"]["reproduced_run_tests_second_task_count"] == 1
    assert summary["task_summaries"][0]["comparison"]["dominant_delta_tool"] == "overall_duration"


def test_recheck_policy_pair_tasks_writes_output_files(tmp_path: Path, monkeypatch) -> None:
    def fake_build(**_: object) -> dict:
        return {
            "created_at": "2026-06-13T10:00:00+00:00",
            "task_count": 1,
            "repetitions": 2,
            "baseline_policy_path": str(tmp_path / "baseline.json"),
            "improved_policy_path": str(tmp_path / "improved.json"),
            "task_summaries": [],
            "aggregate": {
                "average_duration_delta_sec": 0.01,
                "average_search_code_delta_sec": 0.005,
                "average_run_tests_delta_sec": 0.012,
                "average_run_tests_first_delta_sec": 0.009,
                "average_run_tests_second_delta_sec": 0.003,
                "reproduced_duration_task_count": 1,
                "reproduced_search_code_task_count": 1,
                "reproduced_run_tests_task_count": 1,
                "reproduced_run_tests_first_task_count": 1,
                "reproduced_run_tests_second_task_count": 1,
                "positive_duration_ratio": 1.0,
                "positive_search_code_ratio": 1.0,
                "positive_run_tests_ratio": 1.0,
                "positive_run_tests_first_ratio": 1.0,
                "positive_run_tests_second_ratio": 1.0,
            },
        }

    monkeypatch.setattr(recheck_policy_pair_tasks, "build_policy_pair_recheck_summary", fake_build)

    output = recheck_policy_pair_tasks.recheck_policy_pair_tasks(
        task_paths=[tmp_path / "benchmarks" / "tasks" / "task_001.json"],
        baseline_policy_path=tmp_path / "baseline.json",
        improved_policy_path=tmp_path / "improved.json",
        repo_root=tmp_path,
        repetitions=2,
        output_dir=tmp_path / "logs" / "summaries",
        run_label="hotspots",
    )

    assert output["analysis_id"] == "policy_pair_recheck_hotspots_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
