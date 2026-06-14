"""分析两次 batch run 之间 search_code 步骤的回升模式。"""

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
from scripts.analyze_trace_hotspots import infer_step_duration_sec


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _round_float(value: float) -> float:
    return round(value, 4)


def _next_analysis_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"search_code_regressions_{run_label}_" if run_label else "search_code_regressions_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def extract_search_steps(trace_path: str | Path, run_id: str) -> list[dict]:
    trace = _load_json(trace_path)
    search_steps: list[dict] = []
    previous_step: dict | None = None
    for step in trace.get("steps", []):
        duration_sec = infer_step_duration_sec(
            step=step,
            previous_step=previous_step,
            run_id=run_id,
        )
        if step.get("tool_name") == "search_code":
            tool_input = step.get("tool_input", {})
            tool_metrics = step.get("tool_metrics", {})
            search_steps.append(
                {
                    "step_index": step.get("step_index"),
                    "query": str(tool_input.get("query", "")),
                    "duration_sec": _round_float(float(duration_sec or 0.0)),
                    "match_count": int(tool_metrics.get("match_count", 0)),
                    "match_file_count": int(tool_metrics.get("match_file_count", 0)),
                }
            )
        previous_step = step
    return search_steps


def load_search_profiles(batch_summary_path: str | Path) -> dict[str, dict]:
    batch_summary = _load_json(batch_summary_path)
    profiles: dict[str, dict] = {}
    for task_entry in batch_summary.get("tasks", []):
        search_steps = extract_search_steps(
            task_entry["trace_path"],
            task_entry["run_id"],
        )
        profiles[task_entry["task_id"]] = {
            "task_id": task_entry["task_id"],
            "run_id": task_entry["run_id"],
            "trace_path": task_entry["trace_path"],
            "search_steps": search_steps,
            "search_step_count": len(search_steps),
            "total_search_duration_sec": _round_float(
                sum(step["duration_sec"] for step in search_steps)
            ),
        }
    return profiles


def build_query_signature(search_steps: list[dict]) -> list[dict]:
    return [
        {
            "query": step["query"],
            "match_count": step["match_count"],
            "match_file_count": step["match_file_count"],
        }
        for step in search_steps
    ]


def build_search_code_regression_summary(
    *,
    baseline_batch_summary_path: str | Path,
    improved_batch_summary_path: str | Path,
    top_n: int = 10,
) -> dict:
    baseline_profiles = load_search_profiles(baseline_batch_summary_path)
    improved_profiles = load_search_profiles(improved_batch_summary_path)

    common_task_ids = sorted(set(baseline_profiles) & set(improved_profiles))
    baseline_total_search_duration_sec = 0.0
    improved_total_search_duration_sec = 0.0
    first_search_total_delta_sec = 0.0
    identical_signature_task_count = 0
    identical_signature_regression_task_count = 0
    first_search_dominant_regression_task_count = 0
    task_regressions: list[dict] = []
    query_aggregate: dict[str, dict[str, float | int | str]] = {}

    for task_id in common_task_ids:
        baseline_profile = baseline_profiles[task_id]
        improved_profile = improved_profiles[task_id]
        baseline_steps = baseline_profile["search_steps"]
        improved_steps = improved_profile["search_steps"]
        baseline_total_search_duration_sec += baseline_profile["total_search_duration_sec"]
        improved_total_search_duration_sec += improved_profile["total_search_duration_sec"]

        baseline_signature = build_query_signature(baseline_steps)
        improved_signature = build_query_signature(improved_steps)
        identical_signature = baseline_signature == improved_signature
        if identical_signature:
            identical_signature_task_count += 1

        total_delta = _round_float(
            improved_profile["total_search_duration_sec"]
            - baseline_profile["total_search_duration_sec"]
        )
        first_search_delta = 0.0
        if baseline_steps and improved_steps:
            first_search_delta = _round_float(
                improved_steps[0]["duration_sec"] - baseline_steps[0]["duration_sec"]
            )
            first_search_total_delta_sec += first_search_delta

        if identical_signature and total_delta > 0:
            identical_signature_regression_task_count += 1
        if total_delta > 0 and first_search_delta > 0 and first_search_delta >= total_delta / 2:
            first_search_dominant_regression_task_count += 1

        paired_queries: list[dict] = []
        if identical_signature:
            for baseline_step, improved_step in zip(baseline_steps, improved_steps, strict=False):
                query_delta = _round_float(
                    improved_step["duration_sec"] - baseline_step["duration_sec"]
                )
                paired_queries.append(
                    {
                        "query": baseline_step["query"],
                        "baseline_duration_sec": baseline_step["duration_sec"],
                        "improved_duration_sec": improved_step["duration_sec"],
                        "delta_duration_sec": query_delta,
                        "match_count": baseline_step["match_count"],
                        "match_file_count": baseline_step["match_file_count"],
                    }
                )
                aggregate = query_aggregate.setdefault(
                    baseline_step["query"],
                    {
                        "query": baseline_step["query"],
                        "task_count": 0,
                        "baseline_total_duration_sec": 0.0,
                        "improved_total_duration_sec": 0.0,
                        "total_delta_sec": 0.0,
                    },
                )
                aggregate["task_count"] = int(aggregate["task_count"]) + 1
                aggregate["baseline_total_duration_sec"] = _round_float(
                    float(aggregate["baseline_total_duration_sec"]) + baseline_step["duration_sec"]
                )
                aggregate["improved_total_duration_sec"] = _round_float(
                    float(aggregate["improved_total_duration_sec"]) + improved_step["duration_sec"]
                )
                aggregate["total_delta_sec"] = _round_float(
                    float(aggregate["total_delta_sec"]) + query_delta
                )

        task_regressions.append(
            {
                "task_id": task_id,
                "baseline_total_search_duration_sec": baseline_profile["total_search_duration_sec"],
                "improved_total_search_duration_sec": improved_profile["total_search_duration_sec"],
                "delta_total_search_duration_sec": total_delta,
                "baseline_search_step_count": baseline_profile["search_step_count"],
                "improved_search_step_count": improved_profile["search_step_count"],
                "identical_query_signature": identical_signature,
                "first_search_delta_sec": first_search_delta,
                "paired_queries": paired_queries,
            }
        )

    top_task_regressions = sorted(
        task_regressions,
        key=lambda item: item["delta_total_search_duration_sec"],
        reverse=True,
    )[:top_n]
    top_query_regressions = sorted(
        query_aggregate.values(),
        key=lambda item: float(item["total_delta_sec"]),
        reverse=True,
    )[:top_n]

    baseline_batch_summary = _load_json(baseline_batch_summary_path)
    improved_batch_summary = _load_json(improved_batch_summary_path)
    common_task_count = len(common_task_ids)

    return {
        "created_at": _utc_timestamp(),
        "baseline_batch_run_id": baseline_batch_summary.get("batch_run_id"),
        "improved_batch_run_id": improved_batch_summary.get("batch_run_id"),
        "baseline_batch_summary_path": str(Path(baseline_batch_summary_path).resolve()),
        "improved_batch_summary_path": str(Path(improved_batch_summary_path).resolve()),
        "aggregate": {
            "common_task_count": common_task_count,
            "baseline_total_search_duration_sec": _round_float(baseline_total_search_duration_sec),
            "improved_total_search_duration_sec": _round_float(improved_total_search_duration_sec),
            "total_search_duration_delta_sec": _round_float(
                improved_total_search_duration_sec - baseline_total_search_duration_sec
            ),
            "baseline_average_search_duration_sec": _round_float(
                baseline_total_search_duration_sec / common_task_count if common_task_count else 0.0
            ),
            "improved_average_search_duration_sec": _round_float(
                improved_total_search_duration_sec / common_task_count if common_task_count else 0.0
            ),
            "average_search_duration_delta_sec": _round_float(
                (improved_total_search_duration_sec - baseline_total_search_duration_sec)
                / common_task_count
                if common_task_count
                else 0.0
            ),
            "identical_query_signature_task_count": identical_signature_task_count,
            "identical_query_signature_regression_task_count": identical_signature_regression_task_count,
            "first_search_total_delta_sec": _round_float(first_search_total_delta_sec),
            "first_search_dominant_regression_task_count": first_search_dominant_regression_task_count,
        },
        "top_task_regressions": top_task_regressions,
        "top_query_regressions": top_query_regressions,
        "per_task_regressions": task_regressions,
    }


def build_search_code_regression_markdown(summary: dict) -> str:
    task_lines = "\n".join(
        [
            (
                f"- `{item['task_id']}`: search_code "
                f"{item['baseline_total_search_duration_sec']} -> {item['improved_total_search_duration_sec']} "
                f"(delta {item['delta_total_search_duration_sec']}); "
                f"identical_signature={item['identical_query_signature']}; "
                f"first_search_delta={item['first_search_delta_sec']}"
            )
            for item in summary["top_task_regressions"]
        ]
    ) or "- 无"
    query_lines = "\n".join(
        [
            (
                f"- `{item['query']}`: total "
                f"{item['baseline_total_duration_sec']} -> {item['improved_total_duration_sec']} "
                f"(delta {item['total_delta_sec']}) across {item['task_count']} tasks"
            )
            for item in summary["top_query_regressions"]
        ]
    ) or "- 无"
    aggregate = summary["aggregate"]
    return f"""# Search Code Regression Summary

- baseline_batch_run_id: `{summary["baseline_batch_run_id"]}`
- improved_batch_run_id: `{summary["improved_batch_run_id"]}`
- common_task_count: `{aggregate["common_task_count"]}`
- baseline_total_search_duration_sec: `{aggregate["baseline_total_search_duration_sec"]}`
- improved_total_search_duration_sec: `{aggregate["improved_total_search_duration_sec"]}`
- total_search_duration_delta_sec: `{aggregate["total_search_duration_delta_sec"]}`
- identical_query_signature_task_count: `{aggregate["identical_query_signature_task_count"]}`
- identical_query_signature_regression_task_count: `{aggregate["identical_query_signature_regression_task_count"]}`
- first_search_total_delta_sec: `{aggregate["first_search_total_delta_sec"]}`
- first_search_dominant_regression_task_count: `{aggregate["first_search_dominant_regression_task_count"]}`

## Top Task Regressions

{task_lines}

## Top Query Regressions

{query_lines}
"""


def analyze_search_code_regressions(
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
    summary = build_search_code_regression_summary(
        baseline_batch_summary_path=baseline_summary_path,
        improved_batch_summary_path=improved_summary_path,
        top_n=top_n,
    )

    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_id = _next_analysis_id(output_directory, run_label=run_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_search_code_regression_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="分析两次 batch run 的 search_code 回升模式。")
    parser.add_argument("--baseline-batch-summary", default=None, help="baseline batch summary JSON 路径")
    parser.add_argument("--improved-batch-summary", default=None, help="improved batch summary JSON 路径")
    parser.add_argument("--baseline-eval", default=None, help="可选：baseline eval JSON 路径")
    parser.add_argument("--improved-eval", default=None, help="可选：improved eval JSON 路径")
    parser.add_argument("--output-dir", default="logs/summaries", help="分析结果输出目录")
    parser.add_argument("--run-label", default=None, help="可选标签，例如 realissuev69r1")
    parser.add_argument("--top-n", type=int, default=10, help="输出前 N 个热点任务和查询")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_search_code_regressions(
        baseline_batch_summary_path=args.baseline_batch_summary,
        improved_batch_summary_path=args.improved_batch_summary,
        baseline_eval_path=args.baseline_eval,
        improved_eval_path=args.improved_eval,
        output_dir=args.output_dir,
        run_label=args.run_label,
        top_n=args.top_n,
    )
    aggregate = output["summary"]["aggregate"]
    print("=== Search Code Regression Analysis Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"baseline_batch_run_id: {output['summary']['baseline_batch_run_id']}")
    print(f"improved_batch_run_id: {output['summary']['improved_batch_run_id']}")
    print(f"common_task_count: {aggregate['common_task_count']}")
    print(f"total_search_duration_delta_sec: {aggregate['total_search_duration_delta_sec']}")
    print(f"identical_query_signature_regression_task_count: {aggregate['identical_query_signature_regression_task_count']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
