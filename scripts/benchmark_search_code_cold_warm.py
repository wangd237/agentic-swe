"""对比 search_code 在首轮与后续轮次中的冷启动 / 热启动开销。"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task
from app.tools.search_code import search_code


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _next_benchmark_id(summary_dir: Path, benchmark_label: str) -> str:
    prefix = f"search_code_cold_warm_{benchmark_label}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def load_queries_from_trace(trace_path: str | Path) -> list[str]:
    import json

    trace_payload = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    queries: list[str] = []
    for step in trace_payload.get("steps", []):
        if step.get("tool_name") != "search_code":
            continue
        query = str(step.get("tool_input", {}).get("query", "")).strip()
        if query:
            queries.append(query)
    return queries


def run_search_sequence(repo_path: str | Path, queries: list[str]) -> dict:
    query_records: list[dict] = []
    total_duration_sec = 0.0
    for query_index, query in enumerate(queries, start=1):
        started_at = perf_counter()
        result = search_code(str(repo_path), query)
        duration_sec = _round_float(perf_counter() - started_at)
        total_duration_sec += duration_sec
        data = result.get("data", {})
        query_records.append(
            {
                "query_index": query_index,
                "query": query,
                "duration_sec": duration_sec,
                "ok": bool(result.get("ok")),
                "match_count": int(data.get("match_count", 0)),
                "match_file_count": len(data.get("match_files", [])),
            }
        )

    return {
        "query_records": query_records,
        "total_duration_sec": _round_float(total_duration_sec),
        "first_query_duration_sec": query_records[0]["duration_sec"] if query_records else 0.0,
    }


def build_search_code_cold_warm_benchmark(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    rounds: int = 5,
    trace_path: str | Path | None = None,
    queries: list[str] | None = None,
) -> dict:
    repository_root = Path(repo_root).resolve()
    task = load_task(task_path)
    source_repo_path = (repository_root / task.repo_path).resolve()
    if not source_repo_path.exists():
        raise FileNotFoundError(f"任务 repo 不存在: {source_repo_path}")

    effective_queries = [query.strip() for query in (queries or []) if query.strip()]
    if trace_path is not None:
        effective_queries = load_queries_from_trace(trace_path)
    if not effective_queries:
        raise ValueError("必须提供 trace_path 或至少一条非空 query。")

    round_records: list[dict] = []
    for round_index in range(1, rounds + 1):
        sequence_result = run_search_sequence(source_repo_path, effective_queries)
        round_records.append(
            {
                "round_index": round_index,
                **sequence_result,
            }
        )

    cold_round = round_records[0]
    warm_rounds = round_records[1:]
    warm_total_durations = [record["total_duration_sec"] for record in warm_rounds]
    warm_first_query_durations = [record["first_query_duration_sec"] for record in warm_rounds]

    query_profiles: list[dict] = []
    for query_index, query in enumerate(effective_queries):
        cold_record = cold_round["query_records"][query_index]
        warm_records = [record["query_records"][query_index] for record in warm_rounds]
        warm_mean_duration = _average([record["duration_sec"] for record in warm_records])
        warm_match_count_values = [record["match_count"] for record in warm_records]
        warm_match_file_values = [record["match_file_count"] for record in warm_records]
        query_profiles.append(
            {
                "query_index": query_index + 1,
                "query": query,
                "cold_duration_sec": cold_record["duration_sec"],
                "warm_mean_duration_sec": warm_mean_duration,
                "delta_warm_minus_cold_sec": _round_float(warm_mean_duration - cold_record["duration_sec"]),
                "cold_match_count": cold_record["match_count"],
                "warm_match_count_consistent": (
                    all(value == cold_record["match_count"] for value in warm_match_count_values)
                    if warm_rounds
                    else True
                ),
                "cold_match_file_count": cold_record["match_file_count"],
                "warm_match_file_count_consistent": (
                    all(value == cold_record["match_file_count"] for value in warm_match_file_values)
                    if warm_rounds
                    else True
                ),
            }
        )

    return {
        "created_at": _utc_timestamp(),
        "task_id": task.task_id,
        "task_path": str(Path(task_path).resolve()),
        "source_repo_path": str(source_repo_path),
        "trace_path": str(Path(trace_path).resolve()) if trace_path is not None else None,
        "rounds": rounds,
        "queries": effective_queries,
        "round_records": round_records,
        "aggregate": {
            "cold_total_duration_sec": cold_round["total_duration_sec"],
            "warm_mean_total_duration_sec": _average(warm_total_durations),
            "warm_minus_cold_total_delta_sec": _round_float(
                _average(warm_total_durations) - cold_round["total_duration_sec"]
            ),
            "cold_first_query_duration_sec": cold_round["first_query_duration_sec"],
            "warm_mean_first_query_duration_sec": _average(warm_first_query_durations),
            "warm_minus_cold_first_query_delta_sec": _round_float(
                _average(warm_first_query_durations) - cold_round["first_query_duration_sec"]
            ),
            "query_count": len(effective_queries),
        },
        "query_profiles": query_profiles,
    }


def build_search_code_cold_warm_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    query_lines = "\n".join(
        (
            f"- `{profile['query']}`: cold=`{profile['cold_duration_sec']}`, "
            f"warm_mean=`{profile['warm_mean_duration_sec']}`, "
            f"delta=`{profile['delta_warm_minus_cold_sec']}`, "
            f"match_count_consistent=`{profile['warm_match_count_consistent']}`"
        )
        for profile in summary["query_profiles"]
    )

    return f"""# Search Code Cold Warm Benchmark

## Task

- task_id: `{summary["task_id"]}`
- rounds: `{summary["rounds"]}`
- query_count: `{aggregate["query_count"]}`

## Aggregate

- cold_total_duration_sec: `{aggregate["cold_total_duration_sec"]}`
- warm_mean_total_duration_sec: `{aggregate["warm_mean_total_duration_sec"]}`
- warm_minus_cold_total_delta_sec: `{aggregate["warm_minus_cold_total_delta_sec"]}`
- cold_first_query_duration_sec: `{aggregate["cold_first_query_duration_sec"]}`
- warm_mean_first_query_duration_sec: `{aggregate["warm_mean_first_query_duration_sec"]}`
- warm_minus_cold_first_query_delta_sec: `{aggregate["warm_minus_cold_first_query_delta_sec"]}`

## Query Profiles

{query_lines}
"""


def benchmark_search_code_cold_warm(
    *,
    task_path: str | Path,
    repo_root: str | Path,
    rounds: int = 5,
    trace_path: str | Path | None = None,
    queries: list[str] | None = None,
    output_dir: str | Path = "logs/summaries",
    benchmark_label: str | None = None,
) -> dict:
    summary = build_search_code_cold_warm_benchmark(
        task_path=task_path,
        repo_root=repo_root,
        rounds=rounds,
        trace_path=trace_path,
        queries=queries,
    )
    label = benchmark_label or summary["task_id"]
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    benchmark_id = _next_benchmark_id(output_directory, label)
    summary["benchmark_id"] = benchmark_id

    summary_json_path = output_directory / f"{benchmark_id}.json"
    summary_md_path = output_directory / f"{benchmark_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_search_code_cold_warm_markdown(summary))

    return {
        "benchmark_id": benchmark_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="基准对比 search_code 的冷启动 / 热启动开销。")
    parser.add_argument("--task", required=True, help="任务 JSON 路径")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--rounds", type=int, default=5, help="重复运行轮次")
    parser.add_argument("--trace-path", default=None, help="可选：从 trace 中提取搜索词序列")
    parser.add_argument("--query", action="append", default=None, help="可重复传入的搜索词")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--benchmark-label", default=None, help="输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = benchmark_search_code_cold_warm(
        task_path=args.task,
        repo_root=args.repo_root,
        rounds=args.rounds,
        trace_path=args.trace_path,
        queries=args.query,
        output_dir=args.output_dir,
        benchmark_label=args.benchmark_label,
    )
    aggregate = output["summary"]["aggregate"]
    print("=== Search Code Cold Warm Benchmark Summary ===")
    print(f"benchmark_id: {output['benchmark_id']}")
    print(f"task_id: {output['summary']['task_id']}")
    print(f"cold_total_duration_sec: {aggregate['cold_total_duration_sec']}")
    print(f"warm_mean_total_duration_sec: {aggregate['warm_mean_total_duration_sec']}")
    print(f"warm_minus_cold_total_delta_sec: {aggregate['warm_minus_cold_total_delta_sec']}")
    print(f"cold_first_query_duration_sec: {aggregate['cold_first_query_duration_sec']}")
    print(f"warm_mean_first_query_duration_sec: {aggregate['warm_mean_first_query_duration_sec']}")
    print(f"warm_minus_cold_first_query_delta_sec: {aggregate['warm_minus_cold_first_query_delta_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
