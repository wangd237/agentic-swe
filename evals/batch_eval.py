"""最小可用的 batch eval 入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.error_taxonomy import summarize_taxonomy
from evals.metrics import calculate_metrics


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_eval_id(summary_dir: Path, run_label: str | None = None) -> str:
    # 评测报告单独编号，和 batch run 结果区分开。
    existing_numbers: list[int] = []
    prefix = f"batch_eval_{run_label}_" if run_label else "batch_eval_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    if run_label:
        return f"{prefix}{max(existing_numbers, default=0) + 1:03d}"
    return f"batch_eval_{max(existing_numbers, default=0) + 1:03d}"


def _load_run_records(batch_summary: dict) -> list[dict]:
    # 评测统一从 batch summary 指向的 result/trace/task 文件读取。
    records: list[dict] = []
    for task_entry in batch_summary["tasks"]:
        task = _load_json(task_entry["task_path"])
        result = _load_json(task_entry["result_path"])
        trace = _load_json(task_entry["trace_path"])
        patch_path = Path(task_entry["result_path"]).with_name("patch.diff")
        patch_text = patch_path.read_text(encoding="utf-8") if patch_path.exists() else ""
        records.append(
            {
                "task": task,
                "result": result,
                "trace": trace,
                "patch_diff": patch_text,
            }
        )
    return records


def build_report_markdown(eval_summary: dict) -> str:
    # 第一版报告先突出指标和 taxonomy，方便 README 与结果文档引用。
    metrics = eval_summary["metrics"]
    taxonomy = eval_summary["taxonomy"]

    label_lines = "\n".join(
        f"- `{label}`: `{count}`"
        for label, count in taxonomy["label_counts"].items()
    ) or "- 当前没有命中任何错误标签"

    task_lines = "\n".join(
        f"- `{task_id}`: {', '.join(labels) if labels else '无错误标签'}"
        for task_id, labels in taxonomy["task_labels"].items()
    ) or "- 无任务记录"

    return f"""# Batch Eval Report

## Metrics

- task_count: `{metrics["task_count"]}`
- success_rate: `{metrics["success_rate"]}`
- test_pass_rate: `{metrics["test_pass_rate"]}`
- partial_fix_rate: `{metrics["partial_fix_rate"]}`
- average_steps: `{metrics["average_steps"]}`
- average_tool_calls: `{metrics["average_tool_calls"]}`
- average_duration_sec: `{metrics["average_duration_sec"]}`
- average_modified_files: `{metrics["average_modified_files"]}`
- key_file_read_rate: `{metrics["key_file_read_rate"]}`
- test_execution_rate: `{metrics["test_execution_rate"]}`
- repeated_search_rate: `{metrics["repeated_search_rate"]}`
- reasonable_finish_rate: `{metrics["reasonable_finish_rate"]}`

## Error Taxonomy Counts

{label_lines}

## Per-Task Labels

{task_lines}
"""


def run_batch_eval(batch_summary_path: str | Path, output_dir: str | Path, run_label: str | None = None) -> dict:
    # 读取 batch run 产物，计算指标、分类错误并输出报告。
    batch_summary = _load_json(batch_summary_path)
    run_records = _load_run_records(batch_summary)
    metrics = calculate_metrics(run_records)
    taxonomy = summarize_taxonomy(run_records)

    eval_summary = {
        "source_batch_run_id": batch_summary["batch_run_id"],
        "policy_id": batch_summary.get("policy_id"),
        "metrics": metrics,
        "taxonomy": taxonomy,
    }

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    eval_id = _next_eval_id(output_directory, run_label=run_label)

    summary_json_path = output_directory / f"{eval_id}.json"
    summary_md_path = output_directory / f"{eval_id}.md"
    summary_json_path.write_text(
        json.dumps(eval_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary_md_path.write_text(build_report_markdown(eval_summary), encoding="utf-8")

    return {
        "eval_id": eval_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "eval_summary": eval_summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="对 batch run 结果执行最小 baseline 评测。")
    parser.add_argument(
        "--batch-summary",
        default="logs/summaries/batch_run_001.json",
        help="批量运行汇总 JSON 路径",
    )
    parser.add_argument(
        "--output-dir",
        default="logs/summaries",
        help="评测结果输出目录",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="可选的评测标签，例如 baseline 或 improved",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_batch_eval(args.batch_summary, args.output_dir, run_label=args.run_label)
    print("=== Batch Eval Summary ===")
    print(f"eval_id: {output['eval_id']}")
    print(f"source_batch_run_id: {output['eval_summary']['source_batch_run_id']}")
    print(f"success_rate: {output['eval_summary']['metrics']['success_rate']}")
    print(f"test_pass_rate: {output['eval_summary']['metrics']['test_pass_rate']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    print("phase_status: Phase 5 eval complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
