from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import benchmark_search_code_cold_warm


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_queries_from_trace_extracts_search_order(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.json"
    write_json(
        trace_path,
        {
            "steps": [
                {"tool_name": "search_code", "tool_input": {"query": "alpha"}},
                {"tool_name": "read_file", "tool_input": {"relative_path": "foo.py"}},
                {"tool_name": "search_code", "tool_input": {"query": "beta"}},
            ]
        },
    )

    queries = benchmark_search_code_cold_warm.load_queries_from_trace(trace_path)

    assert queries == ["alpha", "beta"]


def test_build_search_code_cold_warm_benchmark_aggregates_rounds(tmp_path: Path, monkeypatch) -> None:
    task_path = tmp_path / "benchmarks" / "tasks" / "task_demo.json"
    repo_dir = tmp_path / "benchmarks" / "repos" / "demo_repo"
    repo_dir.mkdir(parents=True)
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(
        json.dumps(
            {
                "task_id": "task_demo",
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
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    call_durations = iter([0.02, 0.01, 0.01, 0.005, 0.01, 0.005])

    class FakePerfCounter:
        def __init__(self) -> None:
            self.current = 0.0
            self.pending_end: float | None = None

        def __call__(self) -> float:
            if self.pending_end is None:
                delta = next(call_durations)
                start = self.current
                self.current += delta
                self.pending_end = self.current
                return start
            end = self.pending_end
            self.pending_end = None
            return end

    fake_counter = FakePerfCounter()

    def fake_search_code(repo_path: str, query: str) -> dict:
        return {
            "ok": True,
            "tool_name": "search_code",
            "summary": "ok",
            "data": {
                "match_count": 1 if query == "alpha" else 2,
                "match_files": ["foo.py"] if query == "alpha" else ["foo.py", "bar.py"],
            },
            "error": None,
        }

    monkeypatch.setattr(benchmark_search_code_cold_warm, "perf_counter", fake_counter)
    monkeypatch.setattr(benchmark_search_code_cold_warm, "search_code", fake_search_code)

    summary = benchmark_search_code_cold_warm.build_search_code_cold_warm_benchmark(
        task_path=task_path,
        repo_root=tmp_path,
        rounds=3,
        queries=["alpha", "beta"],
    )

    assert summary["aggregate"]["cold_total_duration_sec"] == 0.03
    assert summary["aggregate"]["warm_mean_total_duration_sec"] == 0.015
    assert summary["aggregate"]["warm_minus_cold_total_delta_sec"] == -0.015
    assert summary["aggregate"]["cold_first_query_duration_sec"] == 0.02
    assert summary["aggregate"]["warm_mean_first_query_duration_sec"] == 0.01
    assert summary["aggregate"]["warm_minus_cold_first_query_delta_sec"] == -0.01
    assert summary["query_profiles"][0]["query"] == "alpha"
    assert summary["query_profiles"][0]["warm_match_count_consistent"] is True


def test_benchmark_search_code_cold_warm_writes_output_files(tmp_path: Path, monkeypatch) -> None:
    task_path = REPO_ROOT / "benchmarks" / "tasks" / "task_001.json"

    def fake_build(**_: object) -> dict:
        return {
            "created_at": "2026-06-13T10:00:00+00:00",
            "task_id": "task_001",
            "task_path": str(task_path),
            "source_repo_path": str(REPO_ROOT / "benchmarks" / "repos" / "requests_repo"),
            "trace_path": None,
            "rounds": 2,
            "queries": ["alpha"],
            "round_records": [],
            "aggregate": {
                "cold_total_duration_sec": 0.02,
                "warm_mean_total_duration_sec": 0.01,
                "warm_minus_cold_total_delta_sec": -0.01,
                "cold_first_query_duration_sec": 0.02,
                "warm_mean_first_query_duration_sec": 0.01,
                "warm_minus_cold_first_query_delta_sec": -0.01,
                "query_count": 1,
            },
            "query_profiles": [],
        }

    monkeypatch.setattr(
        benchmark_search_code_cold_warm,
        "build_search_code_cold_warm_benchmark",
        fake_build,
    )

    output = benchmark_search_code_cold_warm.benchmark_search_code_cold_warm(
        task_path=task_path,
        repo_root=REPO_ROOT,
        rounds=2,
        queries=["alpha"],
        output_dir=tmp_path / "logs" / "summaries",
        benchmark_label="task001",
    )

    assert output["benchmark_id"] == "search_code_cold_warm_task001_001"
    assert Path(output["summary_json_path"]).exists()
    assert Path(output["summary_md_path"]).exists()
