"""分析两次 batch run 之间的任务时延变化。"""

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


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_duration_compare_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"duration_compare_{run_label}_" if run_label else "duration_compare_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"duration_compare_{next_number:03d}"


def resolve_batch_summary_path(
    *,
    batch_summary_path: str | Path | None = None,
    eval_path: str | Path | None = None,
) -> Path:
    if batch_summary_path is not None:
        return Path(batch_summary_path).resolve()
    if eval_path is None:
        raise ValueError("必须至少提供 batch summary 路径或 eval 路径。")

    eval_payload = _load_json(eval_path)
    batch_run_id = eval_payload.get("source_batch_run_id")
    if not batch_run_id:
        raise ValueError("给定的 eval 文件缺少 source_batch_run_id。")
    inferred_path = Path(eval_path).resolve().with_name(f"{batch_run_id}.json")
    if not inferred_path.exists():
        raise FileNotFoundError(f"无法从 eval 文件推断 batch summary：{inferred_path}")
    return inferred_path


def load_duration_records(batch_summary_path: str | Path) -> dict[str, dict]:
    batch_summary = _load_json(batch_summary_path)
    records: dict[str, dict] = {}
    for task_entry in batch_summary.get("tasks", []):
        result = _load_json(task_entry["result_path"])
        records[task_entry["task_id"]] = {
            "task_id": task_entry["task_id"],
            "task_path": task_entry["task_path"],
            "run_id": task_entry["run_id"],
            "result_path": task_entry["result_path"],
            "final_status": result.get("final_status", task_entry.get("final_status")),
            "duration_sec": float(result.get("duration_sec", 0.0)),
            "tool_calls": int(result.get("tool_stats", {}).get("total_tool_calls", 0)),
        }
    return records


def _round_float(value: float) -> float:
    return round(value, 4)


def _average_duration(records: list[dict]) -> float:
    if not records:
        return 0.0
    return _round_float(sum(item["duration_sec"] for item in records) / len(records))


def build_duration_compare_summary(
    *,
    baseline_batch_summary_path: Path,
    improved_batch_summary_path: Path,
    top_n: int = 10,
) -> dict:
    baseline_records = load_duration_records(baseline_batch_summary_path)
    improved_records = load_duration_records(improved_batch_summary_path)

    baseline_task_ids = set(baseline_records)
    improved_task_ids = set(improved_records)
    common_task_ids = sorted(baseline_task_ids & improved_task_ids)
    added_task_ids = sorted(improved_task_ids - baseline_task_ids)
    removed_task_ids = sorted(baseline_task_ids - improved_task_ids)

    per_task_deltas: list[dict] = []
    for task_id in common_task_ids:
        baseline_item = baseline_records[task_id]
        improved_item = improved_records[task_id]
        delta = _round_float(improved_item["duration_sec"] - baseline_item["duration_sec"])
        per_task_deltas.append(
            {
                "task_id": task_id,
                "baseline_duration_sec": baseline_item["duration_sec"],
                "improved_duration_sec": improved_item["duration_sec"],
                "delta_duration_sec": delta,
                "baseline_status": baseline_item["final_status"],
                "improved_status": improved_item["final_status"],
                "baseline_tool_calls": baseline_item["tool_calls"],
                "improved_tool_calls": improved_item["tool_calls"],
            }
        )

    regressions = sorted(
        [item for item in per_task_deltas if item["delta_duration_sec"] > 0],
        key=lambda item: item["delta_duration_sec"],
        reverse=True,
    )[:top_n]
    improvements = sorted(
        [item for item in per_task_deltas if item["delta_duration_sec"] < 0],
        key=lambda item: item["delta_duration_sec"],
    )[:top_n]

    baseline_all_records = list(baseline_records.values())
    improved_all_records = list(improved_records.values())
    baseline_common_records = [baseline_records[task_id] for task_id in common_task_ids]
    improved_common_records = [improved_records[task_id] for task_id in common_task_ids]

    baseline_common_avg = _average_duration(baseline_common_records)
    improved_common_avg = _average_duration(improved_common_records)

    return {
        "created_at": _utc_timestamp(),
        "baseline_batch_run_id": baseline_batch_summary_path.stem,
        "improved_batch_run_id": improved_batch_summary_path.stem,
        "baseline_batch_summary_path": str(baseline_batch_summary_path),
        "improved_batch_summary_path": str(improved_batch_summary_path),
        "task_set": {
            "baseline_task_count": len(baseline_all_records),
            "improved_task_count": len(improved_all_records),
            "common_task_count": len(common_task_ids),
            "added_task_ids": added_task_ids,
            "removed_task_ids": removed_task_ids,
        },
        "aggregate": {
            "baseline_average_duration_sec_all": _average_duration(baseline_all_records),
            "improved_average_duration_sec_all": _average_duration(improved_all_records),
            "baseline_average_duration_sec_common": baseline_common_avg,
            "improved_average_duration_sec_common": improved_common_avg,
            "common_average_delta_sec": _round_float(improved_common_avg - baseline_common_avg),
            "baseline_total_duration_sec_common": _round_float(
                sum(item["duration_sec"] for item in baseline_common_records)
            ),
            "improved_total_duration_sec_common": _round_float(
                sum(item["duration_sec"] for item in improved_common_records)
            ),
        },
        "top_regressions": regressions,
        "top_improvements": improvements,
        "per_task_deltas": per_task_deltas,
    }


def build_duration_compare_markdown(summary: dict) -> str:
    aggregate = summary["aggregate"]
    task_set = summary["task_set"]

    regression_lines = "\n".join(
        f"- `{item['task_id']}`: `{item['baseline_duration_sec']}` -> `{item['improved_duration_sec']}` "
        f"(delta: `{item['delta_duration_sec']}`, tool_calls: `{item['baseline_tool_calls']}` -> `{item['improved_tool_calls']}`)"
        for item in summary["top_regressions"]
    ) or "- 当前没有检测到公共任务上的时延回升"

    improvement_lines = "\n".join(
        f"- `{item['task_id']}`: `{item['baseline_duration_sec']}` -> `{item['improved_duration_sec']}` "
        f"(delta: `{item['delta_duration_sec']}`, tool_calls: `{item['baseline_tool_calls']}` -> `{item['improved_tool_calls']}`)"
        for item in summary["top_improvements"]
    ) or "- 当前没有检测到公共任务上的时延改善"

    return f"""# Duration Regression Analysis

## Compare

- baseline_batch_run_id: `{summary["baseline_batch_run_id"]}`
- improved_batch_run_id: `{summary["improved_batch_run_id"]}`
- created_at: `{summary["created_at"]}`

## Task Set

- baseline_task_count: `{task_set["baseline_task_count"]}`
- improved_task_count: `{task_set["improved_task_count"]}`
- common_task_count: `{task_set["common_task_count"]}`
- added_task_ids: `{task_set["added_task_ids"]}`
- removed_task_ids: `{task_set["removed_task_ids"]}`

## Aggregate

- baseline_average_duration_sec_all: `{aggregate["baseline_average_duration_sec_all"]}`
- improved_average_duration_sec_all: `{aggregate["improved_average_duration_sec_all"]}`
- baseline_average_duration_sec_common: `{aggregate["baseline_average_duration_sec_common"]}`
- improved_average_duration_sec_common: `{aggregate["improved_average_duration_sec_common"]}`
- common_average_delta_sec: `{aggregate["common_average_delta_sec"]}`
- baseline_total_duration_sec_common: `{aggregate["baseline_total_duration_sec_common"]}`
- improved_total_duration_sec_common: `{aggregate["improved_total_duration_sec_common"]}`

## Top Regressions

{regression_lines}

## Top Improvements

{improvement_lines}
"""


def analyze_duration_regressions(
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
    summary = build_duration_compare_summary(
        baseline_batch_summary_path=baseline_summary_path,
        improved_batch_summary_path=improved_summary_path,
        top_n=top_n,
    )

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    compare_id = _next_duration_compare_id(output_directory, run_label=run_label)
    summary["compare_id"] = compare_id

    summary_json_path = output_directory / f"{compare_id}.json"
    summary_md_path = output_directory / f"{compare_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_duration_compare_markdown(summary))

    return {
        "compare_id": compare_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="分析两次 batch run 之间的任务时延变化。")
    parser.add_argument("--baseline-batch-summary", default=None, help="baseline batch summary JSON 路径")
    parser.add_argument("--improved-batch-summary", default=None, help="improved batch summary JSON 路径")
    parser.add_argument("--baseline-eval", default=None, help="可选：baseline eval JSON 路径")
    parser.add_argument("--improved-eval", default=None, help="可选：improved eval JSON 路径")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析结果输出目录")
    parser.add_argument("--run-label", default=None, help="可选标签，例如 realissuev32")
    parser.add_argument("--top-n", type=int, default=10, help="输出时延回升/改善前 N 条任务")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_duration_regressions(
        baseline_batch_summary_path=args.baseline_batch_summary,
        improved_batch_summary_path=args.improved_batch_summary,
        baseline_eval_path=args.baseline_eval,
        improved_eval_path=args.improved_eval,
        output_dir=args.output_dir,
        run_label=args.run_label,
        top_n=args.top_n,
    )
    summary = output["summary"]
    print("=== Duration Regression Analysis Summary ===")
    print(f"compare_id: {output['compare_id']}")
    print(f"baseline_batch_run_id: {summary['baseline_batch_run_id']}")
    print(f"improved_batch_run_id: {summary['improved_batch_run_id']}")
    print(f"common_task_count: {summary['task_set']['common_task_count']}")
    print(f"common_average_delta_sec: {summary['aggregate']['common_average_delta_sec']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
