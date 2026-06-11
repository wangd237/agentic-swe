"""分析两次 batch run 在 trace 级别的性能热点差异。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from scripts.analyze_duration_regressions import resolve_batch_summary_path


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _round_float(value: float) -> float:
    return round(value, 4)


def _next_trace_hotspot_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"trace_hotspots_{run_label}_" if run_label else "trace_hotspots_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"{prefix}{next_number:03d}"


def _parse_iso_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_run_id_timestamp(run_id: str) -> datetime | None:
    if not run_id.startswith("run_"):
        return None
    raw = run_id.removeprefix("run_").split("_", maxsplit=1)[0]
    try:
        parsed = datetime.strptime(raw, "%Y%m%dT%H%M%S%fZ")
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC)


def infer_step_duration_sec(
    *,
    step: dict,
    previous_step: dict | None,
    run_id: str,
) -> float | None:
    explicit_duration = step.get("duration_sec")
    if explicit_duration is not None:
        return float(explicit_duration)

    current_timestamp = _parse_iso_timestamp(step.get("timestamp", ""))
    if current_timestamp is None:
        return None

    previous_timestamp = None
    if previous_step is not None:
        previous_timestamp = _parse_iso_timestamp(previous_step.get("timestamp", ""))
    if previous_timestamp is None:
        previous_timestamp = _parse_run_id_timestamp(run_id)
    if previous_timestamp is None:
        return None

    delta = (current_timestamp - previous_timestamp).total_seconds()
    if delta < 0:
        return None
    return _round_float(delta)


def load_trace_profile(trace_path: str | Path, result_path: str | Path, run_id: str) -> dict:
    trace = _load_json(trace_path)
    result = _load_json(result_path)
    tool_totals: dict[str, float] = {}
    step_profiles: list[dict] = []
    previous_step: dict | None = None

    for step in trace.get("steps", []):
        tool_key = step.get("tool_name") or step.get("action_type") or "unknown"
        duration_sec = infer_step_duration_sec(
            step=step,
            previous_step=previous_step,
            run_id=run_id,
        )
        if duration_sec is not None:
            tool_totals[tool_key] = _round_float(tool_totals.get(tool_key, 0.0) + duration_sec)
        step_profiles.append(
            {
                "step_index": step.get("step_index"),
                "tool_name": tool_key,
                "action_type": step.get("action_type"),
                "duration_sec": duration_sec,
                "tool_output_summary": step.get("tool_output_summary", ""),
            }
        )
        previous_step = step

    measured_total = _round_float(sum(item["duration_sec"] or 0.0 for item in step_profiles))
    result_total = float(result.get("duration_sec") or 0.0)
    overhead_duration_sec = _round_float(max(result_total - measured_total, 0.0))
    if overhead_duration_sec > 0:
        tool_totals["unattributed_overhead"] = _round_float(
            tool_totals.get("unattributed_overhead", 0.0) + overhead_duration_sec
        )

    return {
        "task_id": trace.get("task_id"),
        "run_id": run_id,
        "final_status": result.get("final_status"),
        "result_duration_sec": result_total,
        "measured_step_duration_sec": measured_total,
        "overhead_duration_sec": overhead_duration_sec,
        "total_tool_calls": int(trace.get("total_tool_calls", 0)),
        "step_count": len(step_profiles),
        "tool_totals": dict(sorted(tool_totals.items())),
        "steps": step_profiles,
    }


def load_trace_profiles_from_batch(batch_summary_path: str | Path) -> dict[str, dict]:
    batch_summary = _load_json(batch_summary_path)
    profiles: dict[str, dict] = {}
    for task_entry in batch_summary.get("tasks", []):
        profiles[task_entry["task_id"]] = load_trace_profile(
            trace_path=task_entry["trace_path"],
            result_path=task_entry["result_path"],
            run_id=task_entry["run_id"],
        )
    return profiles


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return _round_float(sum(values) / len(values))


def _build_task_tool_delta(baseline_profile: dict, improved_profile: dict) -> dict[str, dict]:
    tool_names = sorted(set(baseline_profile["tool_totals"]) | set(improved_profile["tool_totals"]))
    deltas: dict[str, dict] = {}
    for tool_name in tool_names:
        baseline_value = float(baseline_profile["tool_totals"].get(tool_name, 0.0))
        improved_value = float(improved_profile["tool_totals"].get(tool_name, 0.0))
        deltas[tool_name] = {
            "baseline_duration_sec": baseline_value,
            "improved_duration_sec": improved_value,
            "delta_duration_sec": _round_float(improved_value - baseline_value),
        }
    return deltas


def build_trace_hotspot_summary(
    *,
    baseline_batch_summary_path: Path,
    improved_batch_summary_path: Path,
    top_n: int = 10,
) -> dict:
    baseline_profiles = load_trace_profiles_from_batch(baseline_batch_summary_path)
    improved_profiles = load_trace_profiles_from_batch(improved_batch_summary_path)

    baseline_task_ids = set(baseline_profiles)
    improved_task_ids = set(improved_profiles)
    common_task_ids = sorted(baseline_task_ids & improved_task_ids)

    per_task_profiles: list[dict] = []
    aggregate_tool_baseline: dict[str, float] = {}
    aggregate_tool_improved: dict[str, float] = {}

    for task_id in common_task_ids:
        baseline_profile = baseline_profiles[task_id]
        improved_profile = improved_profiles[task_id]
        duration_delta = _round_float(
            improved_profile["result_duration_sec"] - baseline_profile["result_duration_sec"]
        )
        tool_deltas = _build_task_tool_delta(baseline_profile, improved_profile)
        dominant_tool = None
        dominant_delta = 0.0
        for tool_name, delta in tool_deltas.items():
            if delta["delta_duration_sec"] > dominant_delta:
                dominant_delta = delta["delta_duration_sec"]
                dominant_tool = tool_name
            aggregate_tool_baseline[tool_name] = _round_float(
                aggregate_tool_baseline.get(tool_name, 0.0) + delta["baseline_duration_sec"]
            )
            aggregate_tool_improved[tool_name] = _round_float(
                aggregate_tool_improved.get(tool_name, 0.0) + delta["improved_duration_sec"]
            )

        per_task_profiles.append(
            {
                "task_id": task_id,
                "baseline_duration_sec": baseline_profile["result_duration_sec"],
                "improved_duration_sec": improved_profile["result_duration_sec"],
                "delta_duration_sec": duration_delta,
                "baseline_tool_calls": baseline_profile["total_tool_calls"],
                "improved_tool_calls": improved_profile["total_tool_calls"],
                "baseline_step_count": baseline_profile["step_count"],
                "improved_step_count": improved_profile["step_count"],
                "dominant_regression_tool": dominant_tool,
                "dominant_regression_delta_sec": _round_float(dominant_delta),
                "tool_deltas": tool_deltas,
            }
        )

    top_task_regressions = sorted(
        [item for item in per_task_profiles if item["delta_duration_sec"] > 0],
        key=lambda item: item["delta_duration_sec"],
        reverse=True,
    )[:top_n]

    aggregate_tool_deltas: list[dict] = []
    for tool_name in sorted(set(aggregate_tool_baseline) | set(aggregate_tool_improved)):
        baseline_value = aggregate_tool_baseline.get(tool_name, 0.0)
        improved_value = aggregate_tool_improved.get(tool_name, 0.0)
        aggregate_tool_deltas.append(
            {
                "tool_name": tool_name,
                "baseline_total_duration_sec": baseline_value,
                "improved_total_duration_sec": improved_value,
                "delta_total_duration_sec": _round_float(improved_value - baseline_value),
                "baseline_average_duration_sec": _round_float(baseline_value / len(common_task_ids))
                if common_task_ids
                else 0.0,
                "improved_average_duration_sec": _round_float(improved_value / len(common_task_ids))
                if common_task_ids
                else 0.0,
            }
        )

    top_tool_regressions = sorted(
        [item for item in aggregate_tool_deltas if item["delta_total_duration_sec"] > 0],
        key=lambda item: item["delta_total_duration_sec"],
        reverse=True,
    )[:top_n]

    return {
        "created_at": _utc_timestamp(),
        "baseline_batch_run_id": baseline_batch_summary_path.stem,
        "improved_batch_run_id": improved_batch_summary_path.stem,
        "common_task_count": len(common_task_ids),
        "baseline_average_duration_sec": _average(
            [baseline_profiles[task_id]["result_duration_sec"] for task_id in common_task_ids]
        ),
        "improved_average_duration_sec": _average(
            [improved_profiles[task_id]["result_duration_sec"] for task_id in common_task_ids]
        ),
        "average_duration_delta_sec": _round_float(
            _average([improved_profiles[task_id]["result_duration_sec"] for task_id in common_task_ids])
            - _average([baseline_profiles[task_id]["result_duration_sec"] for task_id in common_task_ids])
        ),
        "top_task_regressions": top_task_regressions,
        "top_tool_regressions": top_tool_regressions,
        "aggregate_tool_deltas": aggregate_tool_deltas,
        "per_task_profiles": per_task_profiles,
    }


def build_trace_hotspot_markdown(summary: dict) -> str:
    task_lines = "\n".join(
        f"- `{item['task_id']}`: `{item['baseline_duration_sec']}` -> `{item['improved_duration_sec']}` "
        f"(delta: `{item['delta_duration_sec']}`, dominant_tool: `{item['dominant_regression_tool'] or 'none'}`, "
        f"dominant_delta: `{item['dominant_regression_delta_sec']}`)"
        for item in summary["top_task_regressions"]
    ) or "- 当前没有检测到任务级时延回升"

    tool_lines = "\n".join(
        f"- `{item['tool_name']}`: baseline avg `{item['baseline_average_duration_sec']}` -> "
        f"improved avg `{item['improved_average_duration_sec']}` "
        f"(total delta: `{item['delta_total_duration_sec']}`)"
        for item in summary["top_tool_regressions"]
    ) or "- 当前没有检测到工具级时延回升"

    return f"""# Trace Hotspot Analysis

## Compare

- baseline_batch_run_id: `{summary["baseline_batch_run_id"]}`
- improved_batch_run_id: `{summary["improved_batch_run_id"]}`
- common_task_count: `{summary["common_task_count"]}`
- baseline_average_duration_sec: `{summary["baseline_average_duration_sec"]}`
- improved_average_duration_sec: `{summary["improved_average_duration_sec"]}`
- average_duration_delta_sec: `{summary["average_duration_delta_sec"]}`

## Top Task Regressions

{task_lines}

## Top Tool Regressions

{tool_lines}
"""


def analyze_trace_hotspots(
    *,
    baseline_batch_summary_path: str | Path | None = None,
    improved_batch_summary_path: str | Path | None = None,
    baseline_eval_path: str | Path | None = None,
    improved_eval_path: str | Path | None = None,
    output_dir: str | Path = "logs/summaries",
    run_label: str | None = None,
    top_n: int = 10,
) -> dict:
    baseline_summary_path = resolve_batch_summary_path(
        batch_summary_path=baseline_batch_summary_path,
        eval_path=baseline_eval_path,
    )
    improved_summary_path = resolve_batch_summary_path(
        batch_summary_path=improved_batch_summary_path,
        eval_path=improved_eval_path,
    )
    summary = build_trace_hotspot_summary(
        baseline_batch_summary_path=baseline_summary_path,
        improved_batch_summary_path=improved_summary_path,
        top_n=top_n,
    )

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_trace_hotspot_id(output_directory, run_label=run_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_trace_hotspot_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="分析两次 batch run 的 trace 级性能热点。")
    parser.add_argument("--baseline-batch-summary", default=None, help="baseline batch summary JSON 路径")
    parser.add_argument("--improved-batch-summary", default=None, help="improved batch summary JSON 路径")
    parser.add_argument("--baseline-eval", default=None, help="可选：baseline eval JSON 路径")
    parser.add_argument("--improved-eval", default=None, help="可选：improved eval JSON 路径")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析结果输出目录")
    parser.add_argument("--run-label", default=None, help="可选标签，例如 frozen20v32")
    parser.add_argument("--top-n", type=int, default=10, help="输出前 N 个热点任务和工具")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_trace_hotspots(
        baseline_batch_summary_path=args.baseline_batch_summary,
        improved_batch_summary_path=args.improved_batch_summary,
        baseline_eval_path=args.baseline_eval,
        improved_eval_path=args.improved_eval,
        output_dir=args.output_dir,
        run_label=args.run_label,
        top_n=args.top_n,
    )
    summary = output["summary"]
    print("=== Trace Hotspot Analysis Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"baseline_batch_run_id: {summary['baseline_batch_run_id']}")
    print(f"improved_batch_run_id: {summary['improved_batch_run_id']}")
    print(f"common_task_count: {summary['common_task_count']}")
    print(f"average_duration_delta_sec: {summary['average_duration_delta_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
