"""Aggregate multi-model eval summaries into a model comparison report."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_comparison_id(output_dir: Path, run_label: str | None = None) -> str:
    prefix = f"model_comparison_{run_label}_" if run_label else "model_comparison_"
    existing_numbers: list[int] = []
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    return f"{prefix}{max(existing_numbers, default=0) + 1:03d}"


def _load_records(summary_paths: list[str | Path]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    source_ids: list[str] = []
    for summary_path in summary_paths:
        payload = _load_json(summary_path)
        source_ids.append(payload.get("matrix_run_id", Path(summary_path).stem))
        records.extend(
            record
            for record in payload.get("records", [])
            if record.get("record_status") == "completed"
        )
    return records, source_ids


def _average(values: list[float]) -> float:
    return round(mean(values), 4) if values else 0.0


def _summarize_policy(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_policy[str(record.get("policy_id"))].append(record)

    summaries: list[dict[str, Any]] = []
    for policy_id, policy_records in sorted(by_policy.items()):
        success_count = sum(1 for record in policy_records if record.get("final_status") == "success")
        incomplete_reasons = Counter(
            str(record.get("incomplete_reason") or "none")
            for record in policy_records
            if record.get("final_status") != "success"
        )
        tool_calls = [
            float(record.get("total_tool_calls") or 0)
            for record in policy_records
            if record.get("total_tool_calls") is not None
        ]
        durations = [
            float(record.get("duration_sec") or 0)
            for record in policy_records
            if record.get("duration_sec") is not None
        ]
        summaries.append(
            {
                "policy_id": policy_id,
                "llm_provider": policy_records[0].get("llm_provider"),
                "llm_model": policy_records[0].get("llm_model"),
                "task_count": len(policy_records),
                "success_count": success_count,
                "success_rate": round(success_count / len(policy_records), 4) if policy_records else 0.0,
                "average_tool_calls": _average(tool_calls),
                "average_duration_sec": _average(durations),
                "incomplete_reason_counts": dict(sorted(incomplete_reasons.items())),
            }
        )
    return summaries


def _build_task_matrix(records: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    matrix: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        task_id = str(record.get("task_id"))
        policy_id = str(record.get("policy_id"))
        matrix[task_id][policy_id] = {
            "final_status": record.get("final_status"),
            "incomplete_reason": record.get("incomplete_reason", ""),
            "total_tool_calls": record.get("total_tool_calls"),
            "duration_sec": record.get("duration_sec"),
            "result_path": record.get("result_path"),
            "trace_path": record.get("trace_path"),
        }
    return dict(sorted(matrix.items()))


def _classify_task_intersections(
    task_matrix: dict[str, dict[str, dict[str, Any]]],
    policy_ids: list[str],
) -> dict[str, list[str]]:
    all_success: list[str] = []
    all_failed: list[str] = []
    inconsistent: list[str] = []
    incomplete_coverage: list[str] = []

    for task_id, policy_results in task_matrix.items():
        if any(policy_id not in policy_results for policy_id in policy_ids):
            incomplete_coverage.append(task_id)
            continue
        statuses = {
            policy_results[policy_id].get("final_status")
            for policy_id in policy_ids
        }
        if statuses == {"success"}:
            all_success.append(task_id)
        elif "success" not in statuses:
            all_failed.append(task_id)
        else:
            inconsistent.append(task_id)

    return {
        "all_success": all_success,
        "all_failed": all_failed,
        "inconsistent": inconsistent,
        "incomplete_coverage": incomplete_coverage,
    }


def _format_artifact_link(path: str | None) -> str:
    if not path:
        return "-"
    normalized_path = str(path).replace("\\", "/")
    return f"[link]({normalized_path})"


def _format_task_policy_result(result: dict[str, Any]) -> str:
    status = result.get("final_status") or "unknown"
    reason = result.get("incomplete_reason") or "none"
    return (
        f"{status}"
        f" (reason: `{reason}`, "
        f"result: {_format_artifact_link(result.get('result_path'))}, "
        f"trace: {_format_artifact_link(result.get('trace_path'))})"
    )


def _format_task_detail_lines(
    *,
    task_ids: list[str],
    comparison: dict[str, Any],
    empty_message: str,
    limit: int = 30,
) -> str:
    if not task_ids:
        return f"- {empty_message}"

    lines: list[str] = []
    for task_id in task_ids[:limit]:
        policy_results = comparison["task_matrix"][task_id]
        details = ", ".join(
            f"`{policy_id}`={_format_task_policy_result(policy_results[policy_id])}"
            for policy_id in comparison["policy_ids"]
            if policy_id in policy_results
        )
        lines.append(f"- `{task_id}`: {details}")

    remaining_count = len(task_ids) - limit
    if remaining_count > 0:
        lines.append(f"- ... {remaining_count} more")
    return "\n".join(lines)


def build_model_comparison_markdown(comparison: dict[str, Any]) -> str:
    interim_note = str(comparison.get("interim_note") or "").strip()
    interim_section = f"\n{interim_note}\n" if interim_note else ""

    policy_lines = "\n".join(
        f"| `{item['policy_id']}` | `{item.get('llm_model')}` | {item['task_count']} | "
        f"{item['success_count']} | {item['success_rate']} | {item['average_tool_calls']} | "
        f"{item['average_duration_sec']} |"
        for item in comparison["policy_summaries"]
    ) or "| - | - | 0 | 0 | 0 | 0 | 0 |"

    reason_lines = "\n".join(
        f"- `{item['policy_id']}`: "
        + (
            ", ".join(
                f"`{reason}`={count}"
                for reason, count in item["incomplete_reason_counts"].items()
            )
            or "no failures"
        )
        for item in comparison["policy_summaries"]
    ) or "- no policies"

    intersections = comparison["intersections"]
    intersection_lines = "\n".join(
        [
            f"- all_success: `{len(intersections['all_success'])}`",
            f"- all_failed: `{len(intersections['all_failed'])}`",
            f"- inconsistent: `{len(intersections['inconsistent'])}`",
            f"- incomplete_coverage: `{len(intersections['incomplete_coverage'])}`",
        ]
    )

    all_failed_lines = _format_task_detail_lines(
        task_ids=intersections["all_failed"],
        comparison=comparison,
        empty_message="no all-failed tasks",
    )

    inconsistent_lines = _format_task_detail_lines(
        task_ids=intersections["inconsistent"],
        comparison=comparison,
        empty_message="no inconsistent tasks",
    )

    incomplete_coverage_lines = "\n".join(
        f"- `{task_id}`: covered by "
        + ", ".join(f"`{policy_id}`" for policy_id in comparison["task_matrix"][task_id])
        for task_id in intersections["incomplete_coverage"][:30]
    ) or "- no incomplete-coverage tasks"

    return f"""# Model Comparison
{interim_section}

## Run

- comparison_id: `{comparison["comparison_id"]}`
- created_at: `{comparison["created_at"]}`
- source_matrix_run_ids: `{", ".join(comparison["source_matrix_run_ids"])}`
- policy_count: `{comparison["policy_count"]}`
- observed_task_count: `{comparison["observed_task_count"]}`

## Per-Model Metrics

| Policy | Model | Tasks | Success | Success Rate | Avg Tool Calls | Avg Duration Sec |
|--------|-------|-------|---------|--------------|----------------|------------------|
{policy_lines}

## Incomplete Reasons

{reason_lines}

## Intersection Analysis

{intersection_lines}

## All-Failed Tasks

{all_failed_lines}

## Inconsistent Tasks

{inconsistent_lines}

## Incomplete Coverage Tasks

{incomplete_coverage_lines}
"""


def aggregate_model_comparison(
    *,
    summary_paths: list[str | Path],
    output_dir: str | Path,
    run_label: str | None = None,
    docs_output_path: str | Path | None = None,
    interim_note: str | None = None,
) -> dict[str, Any]:
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    records, source_ids = _load_records(summary_paths)
    policy_summaries = _summarize_policy(records)
    policy_ids = [item["policy_id"] for item in policy_summaries]
    task_matrix = _build_task_matrix(records)
    comparison_id = _next_comparison_id(output_directory, run_label=run_label)
    comparison = {
        "comparison_id": comparison_id,
        "created_at": _utc_timestamp(),
        "source_matrix_run_ids": source_ids,
        "policy_count": len(policy_ids),
        "policy_ids": policy_ids,
        "observed_task_count": len(task_matrix),
        "record_count": len(records),
        "policy_summaries": policy_summaries,
        "intersections": _classify_task_intersections(task_matrix, policy_ids),
        "task_matrix": task_matrix,
    }
    if interim_note:
        comparison["interim_note"] = interim_note

    summary_json_path = output_directory / f"{comparison_id}.json"
    summary_md_path = output_directory / f"{comparison_id}.md"
    markdown = build_model_comparison_markdown(comparison)
    write_json(summary_json_path, comparison)
    write_text(summary_md_path, markdown)
    if docs_output_path is not None:
        write_text(docs_output_path, markdown)
    return {
        "comparison_id": comparison_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "docs_output_path": str(docs_output_path) if docs_output_path is not None else None,
        "comparison": comparison,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aggregate multi-model eval summaries.")
    parser.add_argument("--summary", action="append", required=True, help="Multi-model summary JSON.")
    parser.add_argument("--output-dir", default="logs/summaries", help="Output directory.")
    parser.add_argument("--run-label", default=None, help="Optional run label.")
    parser.add_argument(
        "--docs-output",
        default=None,
        help="Optional docs markdown output, e.g. docs/model_comparison.md.",
    )
    parser.add_argument(
        "--interim-note",
        default=None,
        help="Optional markdown note inserted under the report title.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = aggregate_model_comparison(
        summary_paths=args.summary,
        output_dir=args.output_dir,
        run_label=args.run_label,
        docs_output_path=args.docs_output,
        interim_note=args.interim_note,
    )
    comparison = output["comparison"]
    print("=== Model Comparison Summary ===")
    print(f"comparison_id: {output['comparison_id']}")
    print(f"policy_count: {comparison['policy_count']}")
    print(f"observed_task_count: {comparison['observed_task_count']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    if output["docs_output_path"]:
        print(f"docs_output_path: {output['docs_output_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
