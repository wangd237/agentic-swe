"""分析单个任务在历史运行中的时延变化。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from scripts.analyze_trace_hotspots import infer_step_duration_sec


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _round_float(value: float) -> float:
    return round(value, 4)


def _display_optional_number(value: float | None) -> str:
    if value is None:
        return "未观测"
    return str(value)


def _extract_policy_sort_key(policy_id: str) -> tuple[int, str]:
    if "_v" in policy_id:
        suffix = policy_id.rsplit("_v", maxsplit=1)[-1]
        if suffix.isdigit():
            return (int(suffix), policy_id)
    return (10**9, policy_id)


def _build_history_analysis_id(summary_dir: Path, task_id: str) -> str:
    prefix = f"task_history_{task_id}_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def summarize_numeric_series(values: list[float]) -> dict:
    if not values:
        return {
            "count": 0,
            "average": 0.0,
            "min": 0.0,
            "max": 0.0,
            "stddev": 0.0,
            "range": 0.0,
        }

    average = mean(values)
    minimum = min(values)
    maximum = max(values)
    stddev = pstdev(values) if len(values) > 1 else 0.0
    return {
        "count": len(values),
        "average": _round_float(average),
        "min": _round_float(minimum),
        "max": _round_float(maximum),
        "stddev": _round_float(stddev),
        "range": _round_float(maximum - minimum),
    }


def summarize_optional_numeric_series(values: list[float | None]) -> dict:
    observed_values = [value for value in values if value is not None]
    if not observed_values:
        return {
            "count": 0,
            "average": None,
            "min": None,
            "max": None,
            "stddev": None,
            "range": None,
            "observed_count": 0,
            "missing_count": len(values),
        }

    summary = summarize_numeric_series(observed_values)
    summary["observed_count"] = summary["count"]
    summary["missing_count"] = len(values) - len(observed_values)
    return summary


def load_task_run_record(run_dir: str | Path) -> dict:
    resolved_run_dir = Path(run_dir).resolve()
    result_path = resolved_run_dir / "result.json"
    trace_path = resolved_run_dir / "trace.json"

    result = _load_json(result_path)
    trace = _load_json(trace_path)
    steps = trace.get("steps", [])
    previous_step: dict | None = None
    run_tests_total_duration = 0.0
    run_tests_subprocess_durations: list[float] = []
    run_tests_summary_durations: list[float] = []
    run_tests_call_count = 0

    for step in steps:
        if step.get("tool_name") != "run_tests":
            previous_step = step
            continue

        duration_sec = infer_step_duration_sec(
            step=step,
            previous_step=previous_step,
            run_id=trace.get("run_id", ""),
        )
        if duration_sec is not None:
            run_tests_total_duration += float(duration_sec)

        tool_metrics = step.get("tool_metrics", {})
        if "subprocess_duration_sec" in tool_metrics:
            run_tests_subprocess_durations.append(float(tool_metrics["subprocess_duration_sec"]))
        if "summary_extraction_duration_sec" in tool_metrics:
            run_tests_summary_durations.append(float(tool_metrics["summary_extraction_duration_sec"]))
        run_tests_call_count += 1
        previous_step = step

    return {
        "task_id": result.get("task_id"),
        "run_id": result.get("run_id"),
        "run_dir": str(resolved_run_dir),
        "result_path": str(result_path),
        "trace_path": str(trace_path),
        "policy_id": result.get("tool_stats", {}).get("policy_id", "unknown"),
        "final_status": result.get("final_status"),
        "duration_sec": float(result.get("duration_sec") or 0.0),
        "step_count": len(steps),
        "tool_call_count": int(trace.get("total_tool_calls", 0)),
        "run_tests_call_count": run_tests_call_count,
        "run_tests_total_duration_sec": _round_float(run_tests_total_duration),
        "run_tests_subprocess_duration_sec": _round_float(sum(run_tests_subprocess_durations))
        if run_tests_subprocess_durations
        else None,
        "run_tests_summary_duration_sec": _round_float(sum(run_tests_summary_durations))
        if run_tests_summary_durations
        else None,
    }


def load_task_history_records(task_dir: str | Path) -> list[dict]:
    resolved_task_dir = Path(task_dir).resolve()
    records: list[dict] = []

    for run_dir in sorted(resolved_task_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        if not run_dir.name.startswith("run_"):
            continue
        result_path = run_dir / "result.json"
        trace_path = run_dir / "trace.json"
        if not result_path.exists() or not trace_path.exists():
            continue
        records.append(load_task_run_record(run_dir))

    return records


def build_policy_summary(policy_id: str, records: list[dict]) -> dict:
    durations = [record["duration_sec"] for record in records]
    run_tests_totals = [record["run_tests_total_duration_sec"] for record in records]
    subprocess_totals = [record["run_tests_subprocess_duration_sec"] for record in records]
    summary_totals = [record["run_tests_summary_duration_sec"] for record in records]
    step_counts = [float(record["step_count"]) for record in records]
    tool_call_counts = [float(record["tool_call_count"]) for record in records]

    latest_record = sorted(records, key=lambda item: item["run_id"])[-1]
    return {
        "policy_id": policy_id,
        "run_count": len(records),
        "latest_run_id": latest_record["run_id"],
        "duration_sec": summarize_numeric_series(durations),
        "run_tests_total_duration_sec": summarize_numeric_series(run_tests_totals),
        "run_tests_subprocess_duration_sec": summarize_optional_numeric_series(subprocess_totals),
        "run_tests_summary_duration_sec": summarize_optional_numeric_series(summary_totals),
        "step_count": summarize_numeric_series(step_counts),
        "tool_call_count": summarize_numeric_series(tool_call_counts),
        "runs": sorted(records, key=lambda item: item["run_id"]),
    }


def build_task_history_summary(task_dir: str | Path) -> dict:
    records = load_task_history_records(task_dir)
    if not records:
        raise ValueError(f"任务目录中没有可分析的运行结果: {task_dir}")

    task_id = records[0]["task_id"]
    records_by_policy: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        records_by_policy[record["policy_id"]].append(record)

    policy_summaries = [
        build_policy_summary(policy_id, policy_records)
        for policy_id, policy_records in sorted(records_by_policy.items(), key=lambda item: _extract_policy_sort_key(item[0]))
    ]

    latest_policy = policy_summaries[-1]
    previous_policy = policy_summaries[-2] if len(policy_summaries) >= 2 else None
    comparison = None
    if previous_policy is not None:
        improved_subprocess_average = latest_policy["run_tests_subprocess_duration_sec"]["average"]
        baseline_subprocess_average = previous_policy["run_tests_subprocess_duration_sec"]["average"]
        improved_summary_average = latest_policy["run_tests_summary_duration_sec"]["average"]
        baseline_summary_average = previous_policy["run_tests_summary_duration_sec"]["average"]
        comparison = {
            "baseline_policy_id": previous_policy["policy_id"],
            "improved_policy_id": latest_policy["policy_id"],
            "duration_average_delta_sec": _round_float(
                latest_policy["duration_sec"]["average"] - previous_policy["duration_sec"]["average"]
            ),
            "run_tests_average_delta_sec": _round_float(
                latest_policy["run_tests_total_duration_sec"]["average"]
                - previous_policy["run_tests_total_duration_sec"]["average"]
            ),
            "run_tests_subprocess_average_delta_sec": _round_float(
                improved_subprocess_average - baseline_subprocess_average
            )
            if improved_subprocess_average is not None and baseline_subprocess_average is not None
            else None,
            "run_tests_summary_average_delta_sec": _round_float(
                improved_summary_average - baseline_summary_average
            )
            if improved_summary_average is not None and baseline_summary_average is not None
            else None,
        }

    slowest_runs = sorted(records, key=lambda item: item["duration_sec"], reverse=True)[:5]
    return {
        "created_at": _utc_timestamp(),
        "task_id": task_id,
        "task_dir": str(Path(task_dir).resolve()),
        "run_count": len(records),
        "policy_count": len(policy_summaries),
        "policy_summaries": policy_summaries,
        "latest_policy_summary": latest_policy,
        "previous_policy_summary": previous_policy,
        "latest_policy_comparison": comparison,
        "slowest_runs": slowest_runs,
    }


def build_task_history_markdown(summary: dict) -> str:
    comparison = summary.get("latest_policy_comparison")
    comparison_block = "\n".join(
        [
            f"- baseline_policy_id: `{comparison['baseline_policy_id']}`",
            f"- improved_policy_id: `{comparison['improved_policy_id']}`",
            f"- duration_average_delta_sec: `{comparison['duration_average_delta_sec']}`",
            f"- run_tests_average_delta_sec: `{comparison['run_tests_average_delta_sec']}`",
            f"- run_tests_subprocess_average_delta_sec: `{_display_optional_number(comparison['run_tests_subprocess_average_delta_sec'])}`",
            f"- run_tests_summary_average_delta_sec: `{_display_optional_number(comparison['run_tests_summary_average_delta_sec'])}`",
        ]
    ) if comparison else "- 当前只有一个策略版本，暂无最近两版对比"

    policy_lines = "\n".join(
        (
            f"- `{item['policy_id']}`: runs=`{item['run_count']}`, "
            f"duration avg=`{item['duration_sec']['average']}` "
            f"(range=`{item['duration_sec']['min']}`~`{item['duration_sec']['max']}`, std=`{item['duration_sec']['stddev']}`), "
            f"run_tests avg=`{item['run_tests_total_duration_sec']['average']}`, "
            f"subprocess avg=`{_display_optional_number(item['run_tests_subprocess_duration_sec']['average'])}` "
            f"(observed_runs=`{item['run_tests_subprocess_duration_sec']['observed_count']}`), "
            f"summary avg=`{_display_optional_number(item['run_tests_summary_duration_sec']['average'])}` "
            f"(observed_runs=`{item['run_tests_summary_duration_sec']['observed_count']}`)"
        )
        for item in summary["policy_summaries"]
    )

    slowest_run_lines = "\n".join(
        (
            f"- `{item['run_id']}` / `{item['policy_id']}`: duration=`{item['duration_sec']}`, "
            f"run_tests_total=`{item['run_tests_total_duration_sec']}`, "
            f"run_tests_subprocess=`{_display_optional_number(item['run_tests_subprocess_duration_sec'])}`"
        )
        for item in summary["slowest_runs"]
    )

    return f"""# Task History Analysis

## Task

- task_id: `{summary["task_id"]}`
- run_count: `{summary["run_count"]}`
- policy_count: `{summary["policy_count"]}`
- task_dir: `{summary["task_dir"]}`

## Latest Policy Comparison

{comparison_block}

## Policy Summaries

{policy_lines}

## Slowest Runs

{slowest_run_lines}
"""


def analyze_task_history(
    *,
    task_dir: str | Path,
    output_dir: str | Path = "logs/summaries",
) -> dict:
    summary = build_task_history_summary(task_dir)
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _build_history_analysis_id(output_directory, summary["task_id"])
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_task_history_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="分析单个任务的历史时延变化。")
    parser.add_argument("--task-dir", required=True, help="任务轨迹目录，例如 logs/trajectories/task_040")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析结果输出目录")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_task_history(task_dir=args.task_dir, output_dir=args.output_dir)
    summary = output["summary"]
    print("=== Task History Analysis Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"task_id: {summary['task_id']}")
    print(f"run_count: {summary['run_count']}")
    print(f"policy_count: {summary['policy_count']}")
    if summary.get("latest_policy_comparison"):
        print(
            "latest_duration_average_delta_sec: "
            f"{summary['latest_policy_comparison']['duration_average_delta_sec']}"
        )
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
