"""Phase 6 的 baseline vs improved 自动对比报告。"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from app.runtime.logger import write_json, write_text


HIGHER_IS_BETTER_METRICS = {
    "success_count",
    "success_rate",
    "test_pass_count",
    "test_pass_rate",
    "key_file_read_rate",
    "test_execution_rate",
    "reasonable_finish_rate",
}

LOWER_IS_BETTER_METRICS = {
    "partial_fix_count",
    "partial_fix_rate",
    "average_steps",
    "average_tool_calls",
    "average_duration_sec",
    "average_modified_files",
    "repeated_search_rate",
}


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _next_compare_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"batch_compare_{run_label}_" if run_label else "batch_compare_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"batch_compare_{next_number:03d}"


def _format_delta(before: float, after: float) -> float:
    return round(after - before, 4)


def _metric_outcome(metric_name: str, delta: float) -> str:
    if metric_name in HIGHER_IS_BETTER_METRICS:
        if delta > 0:
            return "improved"
        if delta < 0:
            return "regressed"
        return "unchanged"

    if metric_name in LOWER_IS_BETTER_METRICS:
        if delta < 0:
            return "improved"
        if delta > 0:
            return "regressed"
        return "unchanged"

    return "neutral"


def _build_metric_deltas(baseline_metrics: dict, improved_metrics: dict) -> dict:
    metric_names = sorted(set(baseline_metrics) | set(improved_metrics))
    metric_deltas: dict[str, dict] = {}
    for metric_name in metric_names:
        before = baseline_metrics.get(metric_name, 0.0)
        after = improved_metrics.get(metric_name, 0.0)
        delta = _format_delta(float(before), float(after))
        metric_deltas[metric_name] = {
            "baseline": before,
            "improved": after,
            "delta": delta,
            "outcome": _metric_outcome(metric_name, delta),
        }
    return metric_deltas


def _build_taxonomy_delta(baseline_taxonomy: dict, improved_taxonomy: dict) -> dict:
    baseline_counts = baseline_taxonomy.get("label_counts", {})
    improved_counts = improved_taxonomy.get("label_counts", {})
    all_labels = sorted(set(baseline_counts) | set(improved_counts))

    label_deltas: dict[str, dict] = {}
    for label in all_labels:
        before = int(baseline_counts.get(label, 0))
        after = int(improved_counts.get(label, 0))
        label_deltas[label] = {
            "baseline": before,
            "improved": after,
            "delta": after - before,
        }

    task_label_changes: dict[str, dict] = {}
    baseline_task_labels = baseline_taxonomy.get("task_labels", {})
    improved_task_labels = improved_taxonomy.get("task_labels", {})
    all_task_ids = sorted(set(baseline_task_labels) | set(improved_task_labels))
    for task_id in all_task_ids:
        before_labels = baseline_task_labels.get(task_id, [])
        after_labels = improved_task_labels.get(task_id, [])
        task_label_changes[task_id] = {
            "baseline": before_labels,
            "improved": after_labels,
            "changed": before_labels != after_labels,
        }

    return {
        "label_deltas": label_deltas,
        "task_label_changes": task_label_changes,
    }


def _build_headline(metric_deltas: dict) -> list[str]:
    headline_metrics = [
        "success_rate",
        "test_pass_rate",
        "partial_fix_rate",
        "average_duration_sec",
    ]
    lines: list[str] = []
    for metric_name in headline_metrics:
        metric = metric_deltas.get(metric_name)
        if metric is None:
            continue
        lines.append(
            f"- `{metric_name}`: `{metric['baseline']}` -> `{metric['improved']}` "
            f"(delta: `{metric['delta']}`, outcome: `{metric['outcome']}`)"
        )
    return lines


def build_compare_markdown(compare_summary: dict) -> str:
    metric_lines = "\n".join(
        f"- `{metric_name}`: baseline `{metric['baseline']}` -> improved `{metric['improved']}` "
        f"(delta: `{metric['delta']}`, outcome: `{metric['outcome']}`)"
        for metric_name, metric in compare_summary["metric_deltas"].items()
    ) or "- 无指标差异"

    taxonomy_lines = "\n".join(
        f"- `{label}`: baseline `{delta['baseline']}` -> improved `{delta['improved']}` "
        f"(delta: `{delta['delta']}`)"
        for label, delta in compare_summary["taxonomy_deltas"]["label_deltas"].items()
    ) or "- 当前没有 taxonomy 差异"

    task_lines = "\n".join(
        f"- `{task_id}`: baseline `{', '.join(change['baseline']) if change['baseline'] else '无错误标签'}` -> "
        f"improved `{', '.join(change['improved']) if change['improved'] else '无错误标签'}` "
        f"(changed: `{change['changed']}`)"
        for task_id, change in compare_summary["taxonomy_deltas"]["task_label_changes"].items()
    ) or "- 无任务标签记录"

    headline_lines = "\n".join(compare_summary["headline"]) or "- 无核心结论"

    return f"""# Batch Eval Compare Report

## Compare

- compare_id: `{compare_summary["compare_id"]}`
- baseline_eval_id: `{compare_summary["baseline_eval_id"]}`
- improved_eval_id: `{compare_summary["improved_eval_id"]}`
- baseline_policy_id: `{compare_summary["baseline_policy_id"]}`
- improved_policy_id: `{compare_summary["improved_policy_id"]}`
- created_at: `{compare_summary["created_at"]}`

## Headline

{headline_lines}

## Metric Deltas

{metric_lines}

## Taxonomy Deltas

{taxonomy_lines}

## Per-Task Label Changes

{task_lines}
"""


def compare_eval_summaries(
    baseline_eval_path: str | Path,
    improved_eval_path: str | Path,
    output_dir: str | Path,
    run_label: str | None = None,
) -> dict:
    baseline_eval = _load_json(baseline_eval_path)
    improved_eval = _load_json(improved_eval_path)

    metric_deltas = _build_metric_deltas(
        baseline_eval.get("metrics", {}),
        improved_eval.get("metrics", {}),
    )
    taxonomy_deltas = _build_taxonomy_delta(
        baseline_eval.get("taxonomy", {}),
        improved_eval.get("taxonomy", {}),
    )

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    compare_id = _next_compare_id(output_directory, run_label=run_label)

    compare_summary = {
        "compare_id": compare_id,
        "created_at": _utc_timestamp(),
        "baseline_eval_id": Path(baseline_eval_path).stem,
        "improved_eval_id": Path(improved_eval_path).stem,
        "baseline_policy_id": baseline_eval.get("policy_id"),
        "improved_policy_id": improved_eval.get("policy_id"),
        "baseline_source_batch_run_id": baseline_eval.get("source_batch_run_id"),
        "improved_source_batch_run_id": improved_eval.get("source_batch_run_id"),
        "metric_deltas": metric_deltas,
        "taxonomy_deltas": taxonomy_deltas,
        "headline": _build_headline(metric_deltas),
    }

    summary_json_path = output_directory / f"{compare_id}.json"
    summary_md_path = output_directory / f"{compare_id}.md"
    write_json(summary_json_path, compare_summary)
    write_text(summary_md_path, build_compare_markdown(compare_summary))

    return {
        "compare_id": compare_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "compare_summary": compare_summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="比较 baseline 与 improved 的 batch eval 结果。")
    parser.add_argument(
        "--baseline-eval",
        required=True,
        help="baseline 评测 JSON 路径",
    )
    parser.add_argument(
        "--improved-eval",
        required=True,
        help="improved 评测 JSON 路径",
    )
    parser.add_argument(
        "--output-dir",
        default="logs/summaries",
        help="对比报告输出目录",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="可选的对比标签，例如 phase6 或 policy",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = compare_eval_summaries(
        baseline_eval_path=args.baseline_eval,
        improved_eval_path=args.improved_eval,
        output_dir=args.output_dir,
        run_label=args.run_label,
    )
    compare_summary = output["compare_summary"]
    print("=== Batch Eval Compare Summary ===")
    print(f"compare_id: {output['compare_id']}")
    print(f"baseline_eval_id: {compare_summary['baseline_eval_id']}")
    print(f"improved_eval_id: {compare_summary['improved_eval_id']}")
    print(
        "success_rate_delta: "
        f"{compare_summary['metric_deltas']['success_rate']['delta']}"
    )
    print(
        "test_pass_rate_delta: "
        f"{compare_summary['metric_deltas']['test_pass_rate']['delta']}"
    )
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    print("phase_status: Phase 6 compare complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
