"""Read-only audit of context usage in Coding Agent traces.

Run on local logs/trajectories; --include-evidence also scans committed examples.
No tool inputs, raw outputs or message content are copied into the reports.
Older traces lack model_visible_chars: mark them unknown instead of guessing from
TraceStep.observation (which is only a short audit preview).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


TOOL_COLUMNS = [
    "run", "task_id", "final_status", "step_index", "phase", "tool",
    "raw_result_chars", "raw_size_source", "model_visible_chars",
    "trace_preview_chars", "source_truncated", "model_summary_truncated", "spilled",
]
PROMPT_COLUMNS = [
    "run", "task_id", "step_index", "prompt_tokens", "prompt_delta",
    "tool_calls_since_previous", "tool_names_since_previous",
    "model_visible_chars_since_previous", "compressions_since_previous",
    "tool_schema_count", "context_char_estimate",
]
RUN_COLUMNS = [
    "run", "task_id", "final_status", "llm_model", "tool_calls",
    "prompt_samples", "max_prompt_tokens", "max_prompt_utilization",
    "context_compressions", "spilled_outputs",
    "known_model_visible_calls", "known_raw_size_calls",
]


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value < 0 or not math.isfinite(value):
        return None
    return int(value)


def _json_dict(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def _percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def _spill_content(trace_path: Path, evidence_ids: list[Any]) -> str | None:
    """Only read referenced tool_outputs inside the corresponding run directory."""
    base = trace_path.parent.resolve()
    for evidence in evidence_ids:
        if not isinstance(evidence, str) or not evidence.startswith("spill:"):
            continue
        relative = evidence.removeprefix("spill:").replace("\\", "/")
        target = (base / relative).resolve()
        if not target.is_relative_to(base / "tool_outputs"):
            continue
        if target.is_file():
            try:
                return target.read_text(encoding="utf-8")
            except OSError:
                pass
    return None


def _tool_row(step: dict[str, Any], trace_path: Path, run: str, task_id: str, status: str) -> dict[str, Any]:
    metrics = step.get("tool_metrics") or {}
    if not isinstance(metrics, dict):
        metrics = {}
    raw = _positive_int(metrics.get("raw_result_chars"))
    visible = _positive_int(metrics.get("model_visible_chars"))
    raw_source = "trace_metrics" if raw is not None else "unavailable"
    source_truncated = metrics.get("tool_payload_truncated")
    if not isinstance(source_truncated, bool):
        source_truncated = None
    summary_truncated = metrics.get("model_summary_truncated")
    if not isinstance(summary_truncated, bool):
        summary_truncated = None
    ids = step.get("evidence_ids") or []
    spilled = any(isinstance(s, str) and s.startswith("spill:") for s in ids)
    if raw is None or source_truncated is None:
        content = _spill_content(trace_path, ids)
        if content is not None:
            if raw is None:
                raw = len(content)
                raw_source = "spill"
            if source_truncated is None:
                try:
                    data = json.loads(content).get("data", {})
                    source_truncated = data.get("truncated") if isinstance(data.get("truncated"), bool) else None
                except (ValueError, AttributeError):
                    pass
    return {
        "run": run, "task_id": task_id, "final_status": status,
        "step_index": step.get("step_index"), "phase": step.get("phase"),
        "tool": step.get("tool_name") or "unknown",
        "raw_result_chars": raw, "raw_size_source": raw_source,
        "model_visible_chars": visible,
        # This field is an audit preview, NOT the full text sent to the model.
        "trace_preview_chars": len(step.get("observation") or ""),
        "source_truncated": source_truncated,
        "model_summary_truncated": summary_truncated,
        "spilled": spilled,
    }


def _scan_roots(roots: list[Path]) -> list[Path]:
    paths: set[Path] = set()
    for root in roots:
        if root.is_file() and root.name == "trace.json":
            paths.add(root.resolve())
        elif root.is_dir():
            paths.update(p.resolve() for p in root.rglob("trace.json"))
    return sorted(paths)


def analyze(
    roots: list[Path],
    *,
    context_window_tokens: int | None = None,
    threshold_ratio: float = 0.8,
) -> dict[str, Any]:
    tool_rows: list[dict[str, Any]] = []
    prompt_rows: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    warnings: list[str] = []
    for trace_path in _scan_roots(roots):
        try:
            trace = _json_dict(trace_path)
            result_path = trace_path.with_name("result.json")
            result = _json_dict(result_path) if result_path.is_file() else {}
        except (OSError, ValueError) as exc:
            warnings.append(f"Skipped unreadable trace {trace_path}: {type(exc).__name__}")
            continue
        steps = trace.get("steps") or []
        if not isinstance(steps, list):
            warnings.append(f"Skipped invalid steps in {trace_path}")
            continue
        run = str(trace_path.parent)
        task_id = str(trace.get("task_id", result.get("task_id", "unknown")))
        status = str(result.get("final_status") or trace.get("final_status") or "unknown")
        stats = result.get("tool_stats") or {}
        if not isinstance(stats, dict):
            stats = {}
        local_tools: list[dict[str, Any]] = []
        local_prompts: list[dict[str, Any]] = []
        llm_model = str(stats.get("llm_model") or "unknown")
        previous_prompt: int | None = None
        previous_response_index = -1
        step_order = [s for s in steps if isinstance(s, dict)]
        for index, step in enumerate(step_order):
            if step.get("action_type") == "tool_call":
                row = _tool_row(step, trace_path, run, task_id, status)
                local_tools.append(row)
                tool_rows.append(row)
            if step.get("action_type") != "llm_response":
                continue
            metrics = step.get("tool_metrics") or {}
            if not isinstance(metrics, dict):
                metrics = {}
            prompt_tokens = _positive_int(metrics.get("llm_prompt_tokens"))
            gap = step_order[previous_response_index + 1:index] if previous_response_index >= 0 else []
            gap_tool_steps = [s for s in gap if s.get("action_type") == "tool_call"]
            # Using step index is safe even if non-tool trace entries were added.
            gap_tool_ids = {s.get("step_index") for s in gap_tool_steps}
            gap_tools = [t for t in local_tools if t["step_index"] in gap_tool_ids]
            visible_sum = (
                sum(t["model_visible_chars"] for t in gap_tools)
                if len(gap_tools) == len(gap_tool_steps)
                and all(t["model_visible_chars"] is not None for t in gap_tools)
                else None
            )
            row = {
                "run": run, "task_id": task_id,
                "step_index": step.get("step_index"), "prompt_tokens": prompt_tokens,
                "prompt_delta": (
                    prompt_tokens - previous_prompt
                    if prompt_tokens is not None and previous_prompt is not None
                    else None
                ),
                "tool_calls_since_previous": len(gap_tool_steps),
                "tool_names_since_previous": ",".join(str(s.get("tool_name") or "") for s in gap_tool_steps),
                "model_visible_chars_since_previous": visible_sum,
                "compressions_since_previous": sum(s.get("action_type") == "context_compression" for s in gap),
                "tool_schema_count": _positive_int(metrics.get("tool_schema_count")),
                "context_char_estimate": _positive_int(metrics.get("context_char_estimate")),
            }
            local_prompts.append(row)
            prompt_rows.append(row)
            previous_prompt = prompt_tokens
            previous_response_index = index
        valid_prompts = [p["prompt_tokens"] for p in local_prompts if p["prompt_tokens"] is not None]
        max_prompt = max(valid_prompts, default=None)
        runs.append({
            "run": run, "task_id": task_id, "final_status": status,
            "llm_model": llm_model, "tool_calls": len(local_tools),
            "prompt_samples": len(valid_prompts), "max_prompt_tokens": max_prompt,
            "max_prompt_utilization": (
                round(max_prompt / context_window_tokens, 4)
                if max_prompt is not None and context_window_tokens else None
            ),
            "context_compressions": sum(s.get("action_type") == "context_compression" for s in step_order),
            "spilled_outputs": sum(t["spilled"] for t in local_tools),
            "known_model_visible_calls": sum(t["model_visible_chars"] is not None for t in local_tools),
            "known_raw_size_calls": sum(t["raw_result_chars"] is not None for t in local_tools),
        })
    by_tool: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for tool in tool_rows:
        by_tool[str(tool["tool"])].append(tool)
    tool_summary: list[dict[str, Any]] = []
    for name, items in sorted(by_tool.items(), key=lambda x: (-len(x[1]), x[0])):
        raw = [x["raw_result_chars"] for x in items if x["raw_result_chars"] is not None]
        visible = [x["model_visible_chars"] for x in items if x["model_visible_chars"] is not None]
        tool_summary.append({
            "tool": name, "calls": len(items),
            "raw_coverage": len(raw), "raw_p50": _percentile(raw, 0.5),
            "raw_p95": _percentile(raw, 0.95), "raw_max": max(raw, default=None),
            "visible_coverage": len(visible), "visible_p50": _percentile(visible, 0.5),
            "visible_p95": _percentile(visible, 0.95), "visible_max": max(visible, default=None),
            "visible_sum_known": sum(visible) if visible else None,
            "spill_count": sum(x["spilled"] for x in items),
            "source_truncated_known": sum(x["source_truncated"] is not None for x in items),
            "source_truncated_true": sum(x["source_truncated"] is True for x in items),
            "summary_truncated_known": sum(x["model_summary_truncated"] is not None for x in items),
            "summary_truncated_true": sum(x["model_summary_truncated"] is True for x in items),
        })
    status_summary = []
    by_status: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in runs:
        by_status["success" if item["final_status"].startswith("success") else "other"].append(item)
    for name, items in sorted(by_status.items()):
        maxes = [x["max_prompt_tokens"] for x in items if x["max_prompt_tokens"] is not None]
        status_summary.append({
            "group": name, "runs": len(items),
            "mean_tool_calls": round(mean(x["tool_calls"] for x in items), 2),
            "max_prompt_coverage": len(maxes),
            "mean_max_prompt_tokens": round(mean(maxes), 1) if maxes else None,
        })
    valid_prompt_rows = [p for p in prompt_rows if p["prompt_tokens"] is not None]
    limit = round(context_window_tokens * threshold_ratio) if context_window_tokens else None
    return {
        "summary": {
            "roots": [str(root) for root in roots],
            "runs": len(runs), "tool_calls": len(tool_rows),
            "raw_size_coverage": sum(t["raw_result_chars"] is not None for t in tool_rows),
            "model_visible_coverage": sum(t["model_visible_chars"] is not None for t in tool_rows),
            "prompt_samples": len(valid_prompt_rows),
            "context_window_tokens": context_window_tokens,
            "threshold_ratio": threshold_ratio,
            "threshold_tokens": limit,
            "prompt_samples_above_threshold": (
                sum(p["prompt_tokens"] >= limit for p in valid_prompt_rows)
                if limit is not None else None
            ),
            "warnings": warnings,
        },
        "runs": runs, "tool_calls": tool_rows,
        "prompt_deltas": prompt_rows, "tools": tool_summary,
        "status_groups": status_summary,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _markdown(data: dict[str, Any]) -> str:
    summary = data["summary"]
    lines = [
        "# Agent context footprint audit",
        "",
        f"- Runs: {summary['runs']}; tool calls: {summary['tool_calls']}; prompt samples: {summary['prompt_samples']}",
        f"- Raw result size coverage: {summary['raw_size_coverage']}/{summary['tool_calls']}",
        f"- Model-visible size coverage: {summary['model_visible_coverage']}/{summary['tool_calls']}",
        f"- Context threshold: {summary['threshold_tokens'] if summary['threshold_tokens'] is not None else 'not configured'}",
        f"- Prompt samples at/above threshold: {summary['prompt_samples_above_threshold'] if summary['prompt_samples_above_threshold'] is not None else 'N/A'}",
        "",
        "## Tools (characters, available samples only)",
        "",
        "| Tool | Calls | Raw known | Raw P95 | Model-visible known | Model-visible P95 | Spills |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in data["tools"]:
        lines.append(
            f"| {row['tool']} | {row['calls']} | {row['raw_coverage']} | "
            f"{row['raw_p95'] if row['raw_p95'] is not None else 'N/A'} | "
            f"{row['visible_coverage']} | "
            f"{row['visible_p95'] if row['visible_p95'] is not None else 'N/A'} | {row['spill_count']} |"
        )
    lines.extend([
        "",
        "## Outcome groups (descriptive, not causal)",
        "",
        "| Final status group | Runs | Mean tool calls | Prompt coverage | Mean max prompt tokens |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in data["status_groups"]:
        lines.append(
            f"| {row['group']} | {row['runs']} | {row['mean_tool_calls']} | "
            f"{row['max_prompt_coverage']} | "
            f"{row['mean_max_prompt_tokens'] if row['mean_max_prompt_tokens'] is not None else 'N/A'} |"
        )
    lines.extend([
        "",
        "## Interpretation and limits",
        "",
        "- trace.observation is a SHORT audit preview, not the actual tool message sent to the LLM. It is never used as model-visible size.",
        "- Old traces usually lack full raw/model-visible sizes. Raw size may be recovered from referenced spill files; missing values remain null.",
        "- A prompt-token delta includes prior assistant messages, tool schemas, system text and other changes; it cannot be attributed solely to tools.",
        "- A provided context window applies to all runs in this report; do not compare window utilization across models with different limits.",
        "- Success/failure summaries are observational and do not demonstrate that truncation caused the outcome.",
        "- Reports contain only metadata and lengths; no raw tool output, prompts, or tool arguments.",
    ])
    if summary["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in summary["warnings"])
    return "\n".join(lines) + "\n"


def write_report(data: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "tool_calls.csv", data["tool_calls"], TOOL_COLUMNS)
    _write_csv(output_dir / "prompt_deltas.csv", data["prompt_deltas"], PROMPT_COLUMNS)
    _write_csv(output_dir / "runs.csv", data["runs"], RUN_COLUMNS)
    tool_columns = list(data["tools"][0]) if data["tools"] else ["tool", "calls"]
    _write_csv(output_dir / "tool_summary.csv", data["tools"], tool_columns)
    (output_dir / "summary.json").write_text(json.dumps(data["summary"] | {
        "tools": data["tools"], "status_groups": data["status_groups"],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "report.md").write_text(_markdown(data), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only footprint audit of Agent trace files")
    parser.add_argument("--root", action="append", type=Path, help="Directory of runs or a trace.json (repeatable)")
    parser.add_argument("--include-evidence", action="store_true", help="Also scan committed evidence/**/trace.json")
    parser.add_argument("--output-dir", type=Path, default=Path("logs/summaries/context_footprint"))
    parser.add_argument("--context-window-tokens", type=int, help="Actual model window; omit to avoid unsupported utilization claims")
    parser.add_argument("--threshold-ratio", type=float, default=0.8)
    args = parser.parse_args()
    if args.context_window_tokens is not None and args.context_window_tokens <= 0:
        parser.error("--context-window-tokens must be positive")
    if not 0 < args.threshold_ratio < 1:
        parser.error("--threshold-ratio must be between 0 and 1")
    roots = args.root if args.root else [Path("logs/trajectories")]
    if args.include_evidence:
        roots = [*roots, Path("evidence")]
    data = analyze(roots, context_window_tokens=args.context_window_tokens, threshold_ratio=args.threshold_ratio)
    write_report(data, args.output_dir)
    s = data["summary"]
    print(f"Audited {s['runs']} runs, {s['tool_calls']} tool calls, {s['prompt_samples']} prompt usage samples.")
    print(f"Raw coverage: {s['raw_size_coverage']}; model-visible coverage: {s['model_visible_coverage']}.")
    print(f"Report: {args.output_dir / 'report.md'}")
    if s["runs"] == 0:
        print("No traces found. Pass --include-evidence, --root DIR, or run Agent to create logs/trajectories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
