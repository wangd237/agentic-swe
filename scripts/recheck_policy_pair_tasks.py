"""对一组热点任务重复复跑两个策略版本，复核性能差异是否稳定复现。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.executor import run_agent
from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task
from scripts.analyze_trace_hotspots import infer_step_duration_sec


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _round_float(value: float) -> float:
    return round(value, 4)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _stddev(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    average = sum(values) / len(values)
    variance = sum((value - average) ** 2 for value in values) / len(values)
    return _round_float(variance**0.5)


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_analysis_id(summary_dir: Path, run_label: str | None = None) -> str:
    prefix = f"policy_pair_recheck_{run_label}_" if run_label else "policy_pair_recheck_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def summarize_trace_metrics(trace_path: str | Path) -> dict:
    trace = _load_json(trace_path)
    previous_step: dict | None = None
    search_code_total_duration_sec = 0.0
    run_tests_total_duration_sec = 0.0
    run_tests_durations: list[float] = []
    search_code_call_count = 0
    run_tests_call_count = 0

    for step in trace.get("steps", []):
        duration_sec = infer_step_duration_sec(
            step=step,
            previous_step=previous_step,
            run_id=trace.get("run_id", ""),
        )
        tool_name = step.get("tool_name")
        if tool_name == "search_code":
            search_code_call_count += 1
            if duration_sec is not None:
                search_code_total_duration_sec += float(duration_sec)
        elif tool_name == "run_tests":
            run_tests_call_count += 1
            if duration_sec is not None:
                run_tests_total_duration_sec += float(duration_sec)
                run_tests_durations.append(float(duration_sec))
        previous_step = step

    return {
        "search_code_total_duration_sec": _round_float(search_code_total_duration_sec),
        "run_tests_total_duration_sec": _round_float(run_tests_total_duration_sec),
        "run_tests_first_duration_sec": _round_float(run_tests_durations[0]) if run_tests_durations else 0.0,
        "run_tests_second_duration_sec": _round_float(run_tests_durations[1]) if len(run_tests_durations) >= 2 else 0.0,
        "search_code_call_count": search_code_call_count,
        "run_tests_call_count": run_tests_call_count,
    }


def build_run_record(task_path: str | Path, policy_path: str | Path, repo_root: str | Path) -> dict:
    run_output = run_agent(task_path=task_path, repo_root=repo_root, policy_path=policy_path)
    task = load_task(task_path)
    result = run_output["result"]
    run_paths = run_output["run_paths"]
    trace_metrics = summarize_trace_metrics(run_paths["trace_json_path"])
    return {
        "task_id": task.task_id,
        "policy_id": result["tool_stats"]["policy_id"],
        "run_id": result["run_id"],
        "final_status": result["final_status"],
        "duration_sec": float(result.get("duration_sec") or 0.0),
        "search_code_total_duration_sec": trace_metrics["search_code_total_duration_sec"],
        "run_tests_total_duration_sec": trace_metrics["run_tests_total_duration_sec"],
        "run_tests_first_duration_sec": trace_metrics["run_tests_first_duration_sec"],
        "run_tests_second_duration_sec": trace_metrics["run_tests_second_duration_sec"],
        "search_code_call_count": trace_metrics["search_code_call_count"],
        "run_tests_call_count": trace_metrics["run_tests_call_count"],
        "trace_path": run_paths["trace_json_path"],
        "result_path": run_paths["result_json_path"],
    }


def build_metric_summary(records: list[dict], key: str) -> dict:
    values = [float(record[key]) for record in records]
    return {
        "count": len(values),
        "average": _average(values),
        "min": _round_float(min(values)) if values else 0.0,
        "max": _round_float(max(values)) if values else 0.0,
        "stddev": _stddev(values),
    }


def build_policy_summary(policy_label: str, records: list[dict]) -> dict:
    latest_record = records[-1]
    success_count = sum(1 for record in records if record["final_status"] == "success")
    return {
        "policy_label": policy_label,
        "policy_id": latest_record["policy_id"],
        "run_count": len(records),
        "success_count": success_count,
        "success_rate": _round_float(success_count / len(records)) if records else 0.0,
        "duration_sec": build_metric_summary(records, "duration_sec"),
        "search_code_total_duration_sec": build_metric_summary(records, "search_code_total_duration_sec"),
        "run_tests_total_duration_sec": build_metric_summary(records, "run_tests_total_duration_sec"),
        "run_tests_first_duration_sec": build_metric_summary(records, "run_tests_first_duration_sec"),
        "run_tests_second_duration_sec": build_metric_summary(records, "run_tests_second_duration_sec"),
        "search_code_call_count": build_metric_summary(records, "search_code_call_count"),
        "run_tests_call_count": build_metric_summary(records, "run_tests_call_count"),
        "records": records,
    }


def build_task_comparison(
    task_path: str | Path,
    baseline_policy_path: str | Path,
    improved_policy_path: str | Path,
    repo_root: str | Path,
    repetitions: int,
) -> dict:
    baseline_records: list[dict] = []
    improved_records: list[dict] = []
    for _ in range(repetitions):
        baseline_records.append(build_run_record(task_path, baseline_policy_path, repo_root))
        improved_records.append(build_run_record(task_path, improved_policy_path, repo_root))

    baseline_summary = build_policy_summary("baseline", baseline_records)
    improved_summary = build_policy_summary("improved", improved_records)
    duration_delta = _round_float(
        improved_summary["duration_sec"]["average"] - baseline_summary["duration_sec"]["average"]
    )
    search_code_delta = _round_float(
        improved_summary["search_code_total_duration_sec"]["average"]
        - baseline_summary["search_code_total_duration_sec"]["average"]
    )
    run_tests_delta = _round_float(
        improved_summary["run_tests_total_duration_sec"]["average"]
        - baseline_summary["run_tests_total_duration_sec"]["average"]
    )
    run_tests_first_delta = _round_float(
        improved_summary["run_tests_first_duration_sec"]["average"]
        - baseline_summary["run_tests_first_duration_sec"]["average"]
    )
    run_tests_second_delta = _round_float(
        improved_summary["run_tests_second_duration_sec"]["average"]
        - baseline_summary["run_tests_second_duration_sec"]["average"]
    )
    dominant_delta_tool = "overall_duration"
    dominant_delta_value = duration_delta
    if run_tests_delta >= search_code_delta and run_tests_delta >= duration_delta:
        dominant_delta_tool = "run_tests"
        dominant_delta_value = run_tests_delta
    elif search_code_delta >= duration_delta:
        dominant_delta_tool = "search_code"
        dominant_delta_value = search_code_delta

    task = load_task(task_path)
    return {
        "task_id": task.task_id,
        "task_path": str(Path(task_path).resolve()),
        "baseline": baseline_summary,
        "improved": improved_summary,
        "comparison": {
            "duration_average_delta_sec": duration_delta,
            "search_code_average_delta_sec": search_code_delta,
            "run_tests_average_delta_sec": run_tests_delta,
            "run_tests_first_average_delta_sec": run_tests_first_delta,
            "run_tests_second_average_delta_sec": run_tests_second_delta,
            "dominant_delta_tool": dominant_delta_tool,
            "dominant_delta_sec": dominant_delta_value,
        },
    }


def build_policy_pair_recheck_summary(
    *,
    task_paths: list[str | Path],
    baseline_policy_path: str | Path,
    improved_policy_path: str | Path,
    repo_root: str | Path,
    repetitions: int,
) -> dict:
    task_summaries = [
        build_task_comparison(
            task_path=task_path,
            baseline_policy_path=baseline_policy_path,
            improved_policy_path=improved_policy_path,
            repo_root=repo_root,
            repetitions=repetitions,
        )
        for task_path in task_paths
    ]

    duration_deltas = [item["comparison"]["duration_average_delta_sec"] for item in task_summaries]
    search_code_deltas = [item["comparison"]["search_code_average_delta_sec"] for item in task_summaries]
    run_tests_deltas = [item["comparison"]["run_tests_average_delta_sec"] for item in task_summaries]
    run_tests_first_deltas = [item["comparison"]["run_tests_first_average_delta_sec"] for item in task_summaries]
    run_tests_second_deltas = [item["comparison"]["run_tests_second_average_delta_sec"] for item in task_summaries]
    reproduced_search_code_task_count = sum(1 for value in search_code_deltas if value > 0)
    reproduced_run_tests_task_count = sum(1 for value in run_tests_deltas if value > 0)
    reproduced_run_tests_first_task_count = sum(1 for value in run_tests_first_deltas if value > 0)
    reproduced_run_tests_second_task_count = sum(1 for value in run_tests_second_deltas if value > 0)
    reproduced_duration_task_count = sum(1 for value in duration_deltas if value > 0)

    return {
        "created_at": _utc_timestamp(),
        "task_count": len(task_summaries),
        "repetitions": repetitions,
        "baseline_policy_path": str(Path(baseline_policy_path).resolve()),
        "improved_policy_path": str(Path(improved_policy_path).resolve()),
        "task_summaries": task_summaries,
        "aggregate": {
            "average_duration_delta_sec": _average(duration_deltas),
            "average_search_code_delta_sec": _average(search_code_deltas),
            "average_run_tests_delta_sec": _average(run_tests_deltas),
            "average_run_tests_first_delta_sec": _average(run_tests_first_deltas),
            "average_run_tests_second_delta_sec": _average(run_tests_second_deltas),
            "reproduced_duration_task_count": reproduced_duration_task_count,
            "reproduced_search_code_task_count": reproduced_search_code_task_count,
            "reproduced_run_tests_task_count": reproduced_run_tests_task_count,
            "reproduced_run_tests_first_task_count": reproduced_run_tests_first_task_count,
            "reproduced_run_tests_second_task_count": reproduced_run_tests_second_task_count,
            "positive_duration_ratio": _round_float(reproduced_duration_task_count / len(task_summaries))
            if task_summaries
            else 0.0,
            "positive_search_code_ratio": _round_float(reproduced_search_code_task_count / len(task_summaries))
            if task_summaries
            else 0.0,
            "positive_run_tests_ratio": _round_float(reproduced_run_tests_task_count / len(task_summaries))
            if task_summaries
            else 0.0,
            "positive_run_tests_first_ratio": _round_float(reproduced_run_tests_first_task_count / len(task_summaries))
            if task_summaries
            else 0.0,
            "positive_run_tests_second_ratio": _round_float(reproduced_run_tests_second_task_count / len(task_summaries))
            if task_summaries
            else 0.0,
        },
    }


def build_policy_pair_recheck_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    task_lines = "\n".join(
        (
            f"- `{item['task_id']}`: duration delta=`{item['comparison']['duration_average_delta_sec']}`, "
            f"search_code delta=`{item['comparison']['search_code_average_delta_sec']}`, "
            f"run_tests delta=`{item['comparison']['run_tests_average_delta_sec']}`, "
            f"run_tests_first delta=`{item['comparison']['run_tests_first_average_delta_sec']}`, "
            f"run_tests_second delta=`{item['comparison']['run_tests_second_average_delta_sec']}`, "
            f"dominant=`{item['comparison']['dominant_delta_tool']}`"
        )
        for item in summary["task_summaries"]
    )
    return f"""# Policy Pair Recheck

## Scope

- task_count: `{summary["task_count"]}`
- repetitions: `{summary["repetitions"]}`

## Aggregate

- average_duration_delta_sec: `{aggregate["average_duration_delta_sec"]}`
- average_search_code_delta_sec: `{aggregate["average_search_code_delta_sec"]}`
- average_run_tests_delta_sec: `{aggregate["average_run_tests_delta_sec"]}`
- average_run_tests_first_delta_sec: `{aggregate["average_run_tests_first_delta_sec"]}`
- average_run_tests_second_delta_sec: `{aggregate["average_run_tests_second_delta_sec"]}`
- reproduced_duration_task_count: `{aggregate["reproduced_duration_task_count"]}`
- reproduced_search_code_task_count: `{aggregate["reproduced_search_code_task_count"]}`
- reproduced_run_tests_task_count: `{aggregate["reproduced_run_tests_task_count"]}`
- reproduced_run_tests_first_task_count: `{aggregate["reproduced_run_tests_first_task_count"]}`
- reproduced_run_tests_second_task_count: `{aggregate["reproduced_run_tests_second_task_count"]}`
- positive_duration_ratio: `{aggregate["positive_duration_ratio"]}`
- positive_search_code_ratio: `{aggregate["positive_search_code_ratio"]}`
- positive_run_tests_ratio: `{aggregate["positive_run_tests_ratio"]}`
- positive_run_tests_first_ratio: `{aggregate["positive_run_tests_first_ratio"]}`
- positive_run_tests_second_ratio: `{aggregate["positive_run_tests_second_ratio"]}`

## Tasks

{task_lines}
"""


def recheck_policy_pair_tasks(
    *,
    task_paths: list[str | Path],
    baseline_policy_path: str | Path,
    improved_policy_path: str | Path,
    repo_root: str | Path,
    repetitions: int = 3,
    output_dir: str | Path = "logs/summaries",
    run_label: str | None = None,
) -> dict:
    summary = build_policy_pair_recheck_summary(
        task_paths=task_paths,
        baseline_policy_path=baseline_policy_path,
        improved_policy_path=improved_policy_path,
        repo_root=repo_root,
        repetitions=repetitions,
    )
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_analysis_id(output_directory, run_label=run_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_policy_pair_recheck_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="复跑一组任务，检查两个策略的性能差异是否稳定复现。")
    parser.add_argument("--task", action="append", required=True, help="可重复传入的任务 JSON 路径")
    parser.add_argument("--baseline-policy", required=True, help="baseline 策略 JSON 路径")
    parser.add_argument("--improved-policy", required=True, help="improved 策略 JSON 路径")
    parser.add_argument("--repo-root", default=".", help="仓库根目录")
    parser.add_argument("--repetitions", type=int, default=3, help="每个任务每个策略重复运行次数")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--run-label", default=None, help="可选输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = recheck_policy_pair_tasks(
        task_paths=args.task,
        baseline_policy_path=args.baseline_policy,
        improved_policy_path=args.improved_policy,
        repo_root=args.repo_root,
        repetitions=args.repetitions,
        output_dir=args.output_dir,
        run_label=args.run_label,
    )
    aggregate = output["summary"]["aggregate"]
    print("=== Policy Pair Recheck Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"task_count: {output['summary']['task_count']}")
    print(f"repetitions: {output['summary']['repetitions']}")
    print(f"average_duration_delta_sec: {aggregate['average_duration_delta_sec']}")
    print(f"average_search_code_delta_sec: {aggregate['average_search_code_delta_sec']}")
    print(f"average_run_tests_delta_sec: {aggregate['average_run_tests_delta_sec']}")
    print(f"average_run_tests_first_delta_sec: {aggregate['average_run_tests_first_delta_sec']}")
    print(f"average_run_tests_second_delta_sec: {aggregate['average_run_tests_second_delta_sec']}")
    print(f"reproduced_search_code_task_count: {aggregate['reproduced_search_code_task_count']}")
    print(f"reproduced_run_tests_task_count: {aggregate['reproduced_run_tests_task_count']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
