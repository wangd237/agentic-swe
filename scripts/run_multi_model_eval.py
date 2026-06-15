"""Run one manifest across multiple OpenAI-compatible LLM policies."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.executor import run_agent
from app.agent.llm_config import LLMConfig
from app.agent.policy import load_policy_config
from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task


AgentRunner = Callable[..., dict[str, Any]]


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_matrix_run_id(output_dir: Path, run_label: str | None = None) -> str:
    prefix = f"multi_model_eval_{run_label}_" if run_label else "multi_model_eval_"
    existing_numbers: list[int] = []
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    return f"{prefix}{max(existing_numbers, default=0) + 1:03d}"


def load_manifest_task_paths(repo_root: str | Path, manifest_path: str | Path) -> list[Path]:
    repository_root = Path(repo_root).resolve()
    manifest = _load_json(manifest_path)
    return [(repository_root / relative_path).resolve() for relative_path in manifest["tasks"]]


def load_policy_specs(policy_paths: list[str | Path]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for policy_path in policy_paths:
        resolved_path = Path(policy_path).resolve()
        policy = load_policy_config(resolved_path)
        specs.append(
            {
                "policy_id": policy.policy_id,
                "policy_path": str(resolved_path),
                "llm_provider": policy.llm_provider,
                "llm_model": policy.llm_model,
                "llm_api_key_env": policy.llm_api_key_env,
                "llm_base_url_env": policy.llm_base_url_env,
                "llm_model_env": policy.llm_model_env,
                "llm_base_url": policy.llm_base_url,
            }
        )
    return specs


def preflight_policy_env(policy_specs: list[dict[str, Any]]) -> dict[str, Any]:
    missing_by_policy: dict[str, list[str]] = {}
    ready_policies: list[str] = []
    for policy_spec in policy_specs:
        missing: list[str] = []
        api_key_env = policy_spec.get("llm_api_key_env")
        if api_key_env and not os.environ.get(str(api_key_env), "").strip():
            missing.append(str(api_key_env))

        base_url_env = policy_spec.get("llm_base_url_env")
        has_base_url_env = bool(base_url_env and os.environ.get(str(base_url_env), "").strip())
        has_default_base_url = bool(policy_spec.get("llm_base_url"))
        if base_url_env and not has_base_url_env and not has_default_base_url:
            missing.append(str(base_url_env))

        if missing:
            missing_by_policy[policy_spec["policy_id"]] = missing
        else:
            ready_policies.append(policy_spec["policy_id"])
    return {
        "ready": not missing_by_policy,
        "ready_policies": ready_policies,
        "missing_by_policy": missing_by_policy,
    }


def _record_key(record: dict[str, Any]) -> tuple[str, str]:
    return str(record["policy_id"]), str(record["task_id"])


def _completed_record_keys(records: list[dict[str, Any]]) -> set[tuple[str, str]]:
    completed: set[tuple[str, str]] = set()
    for record in records:
        if record.get("record_status") in {"completed", "skipped"}:
            completed.add(_record_key(record))
    return completed


def _build_pending_pairs(
    *,
    policy_specs: list[dict[str, Any]],
    task_paths: list[Path],
    existing_records: list[dict[str, Any]],
    limit: int | None,
) -> list[tuple[dict[str, Any], Path]]:
    completed = _completed_record_keys(existing_records)
    pairs: list[tuple[dict[str, Any], Path]] = []
    for policy_spec in policy_specs:
        for task_path in task_paths:
            task_id = load_task(task_path).task_id
            key = (policy_spec["policy_id"], task_id)
            if key in completed:
                continue
            pairs.append((policy_spec, task_path))
            if limit is not None and len(pairs) >= limit:
                return pairs
    return pairs


def _result_record_from_output(
    *,
    policy_spec: dict[str, Any],
    task_path: Path,
    run_output: dict[str, Any],
) -> dict[str, Any]:
    task = load_task(task_path)
    result = run_output["result"]
    tool_stats = result.get("tool_stats", {})
    return {
        "record_status": "completed",
        "task_id": task.task_id,
        "task_path": str(task_path.resolve()),
        "policy_id": policy_spec["policy_id"],
        "policy_path": policy_spec["policy_path"],
        "llm_provider": policy_spec.get("llm_provider"),
        "llm_model": tool_stats.get("llm_model") or policy_spec.get("llm_model"),
        "run_id": result.get("run_id"),
        "final_status": result.get("final_status"),
        "incomplete_reason": result.get("incomplete_reason", ""),
        "patch_applied": result.get("patch_applied", False),
        "modified_files": result.get("modified_files", []),
        "post_test_exit_code": result.get("post_test_exit_code"),
        "post_test_summary": result.get("post_test_summary", ""),
        "total_tool_calls": tool_stats.get("total_tool_calls", 0),
        "duration_sec": result.get("duration_sec"),
        "context_compression_count": tool_stats.get("context_compression_count", 0),
        "result_path": run_output["run_paths"]["result_json_path"],
        "trace_path": run_output["run_paths"]["trace_json_path"],
        "summary_path": run_output["run_paths"]["summary_md_path"],
    }


def _error_record(
    *,
    policy_spec: dict[str, Any],
    task_path: Path,
    error: Exception,
    attempt: int,
) -> dict[str, Any]:
    task = load_task(task_path)
    return {
        "record_status": "error",
        "task_id": task.task_id,
        "task_path": str(task_path.resolve()),
        "policy_id": policy_spec["policy_id"],
        "policy_path": policy_spec["policy_path"],
        "llm_provider": policy_spec.get("llm_provider"),
        "llm_model": policy_spec.get("llm_model"),
        "final_status": "error",
        "incomplete_reason": "runner_error",
        "attempt": attempt,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
    }


def _run_pair_with_retries(
    *,
    repo_root: Path,
    policy_spec: dict[str, Any],
    task_path: Path,
    retries: int,
    retry_delay_sec: float,
    agent_runner: AgentRunner,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 2):
        try:
            run_output = agent_runner(
                task_path=task_path,
                repo_root=repo_root,
                policy_path=Path(policy_spec["policy_path"]),
            )
            return _result_record_from_output(
                policy_spec=policy_spec,
                task_path=task_path,
                run_output=run_output,
            )
        except Exception as error:  # pragma: no cover - exercised through tests with fake runner.
            last_error = error
            if attempt <= retries:
                sleep(retry_delay_sec)
    assert last_error is not None
    return _error_record(
        policy_spec=policy_spec,
        task_path=task_path,
        error=last_error,
        attempt=retries + 1,
    )


def build_summary_markdown(summary: dict[str, Any]) -> str:
    policy_lines = "\n".join(
        f"- `{item['policy_id']}`: completed `{item['completed_count']}`, "
        f"success `{item['success_count']}`, success_rate `{item['success_rate']}`"
        for item in summary["policy_summaries"]
    ) or "- no policies"

    record_lines = "\n".join(
        f"- `{record['policy_id']}` / `{record['task_id']}` -> "
        f"`{record.get('final_status')}` (run: `{record.get('run_id', '')}`)"
        for record in summary["records"]
        if record.get("record_status") == "completed"
    ) or "- no completed records"

    return f"""# Multi-Model Eval Summary

## Run

- matrix_run_id: `{summary["matrix_run_id"]}`
- manifest_id: `{summary["manifest_id"]}`
- task_count: `{summary["task_count"]}`
- policy_count: `{summary["policy_count"]}`
- expected_pair_count: `{summary["expected_pair_count"]}`
- completed_count: `{summary["completed_count"]}`
- success_count: `{summary["success_count"]}`
- error_count: `{summary["error_count"]}`

## Per Policy

{policy_lines}

## Completed Records

{record_lines}
"""


def _build_policy_summaries(records: list[dict[str, Any]], policy_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for policy_spec in policy_specs:
        policy_records = [
            record
            for record in records
            if record.get("policy_id") == policy_spec["policy_id"]
            and record.get("record_status") == "completed"
        ]
        success_count = sum(1 for record in policy_records if record.get("final_status") == "success")
        completed_count = len(policy_records)
        summaries.append(
            {
                "policy_id": policy_spec["policy_id"],
                "llm_provider": policy_spec.get("llm_provider"),
                "llm_model": policy_spec.get("llm_model"),
                "completed_count": completed_count,
                "success_count": success_count,
                "success_rate": round(success_count / completed_count, 4) if completed_count else 0.0,
            }
        )
    return summaries


def _write_summary(summary_path: Path, markdown_path: Path, summary: dict[str, Any]) -> None:
    write_json(summary_path, summary)
    write_text(markdown_path, build_summary_markdown(summary))


def run_multi_model_eval(
    *,
    repo_root: str | Path,
    manifest_path: str | Path,
    policy_paths: list[str | Path],
    output_dir: str | Path,
    run_label: str | None = None,
    max_workers: int = 1,
    retries: int = 0,
    retry_delay_sec: float = 1.0,
    resume_from: str | Path | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    preflight: bool = True,
    agent_runner: AgentRunner = run_agent,
) -> dict[str, Any]:
    repository_root = Path(repo_root).resolve()
    LLMConfig.load_env_file(repository_root)
    resolved_manifest_path = Path(manifest_path).resolve()
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    manifest = _load_json(resolved_manifest_path)
    manifest_id = manifest.get("manifest_id", resolved_manifest_path.stem)
    task_paths = load_manifest_task_paths(repository_root, resolved_manifest_path)
    policy_specs = load_policy_specs(policy_paths)
    preflight_result = preflight_policy_env(policy_specs)
    if preflight and not dry_run and not preflight_result["ready"]:
        missing_text = "; ".join(
            f"{policy_id}: {', '.join(names)}"
            for policy_id, names in preflight_result["missing_by_policy"].items()
        )
        raise RuntimeError(
            "LLM policy preflight failed, missing environment variables: "
            f"{missing_text}"
        )

    if resume_from is not None:
        resume_payload = _load_json(resume_from)
        matrix_run_id = resume_payload["matrix_run_id"]
        records = list(resume_payload.get("records", []))
        summary_path = Path(resume_from).resolve()
        markdown_path = summary_path.with_suffix(".md")
        started_at = resume_payload.get("started_at", _utc_timestamp())
    else:
        matrix_run_id = _next_matrix_run_id(output_directory, run_label=run_label)
        records = []
        summary_path = output_directory / f"{matrix_run_id}.json"
        markdown_path = output_directory / f"{matrix_run_id}.md"
        started_at = _utc_timestamp()

    pending_pairs = _build_pending_pairs(
        policy_specs=policy_specs,
        task_paths=task_paths,
        existing_records=records,
        limit=limit,
    )

    if dry_run:
        for policy_spec, task_path in pending_pairs:
            task = load_task(task_path)
            records.append(
                {
                    "record_status": "skipped",
                    "skip_reason": "dry_run",
                    "task_id": task.task_id,
                    "task_path": str(task_path.resolve()),
                    "policy_id": policy_spec["policy_id"],
                    "policy_path": policy_spec["policy_path"],
                    "llm_provider": policy_spec.get("llm_provider"),
                    "llm_model": policy_spec.get("llm_model"),
                    "final_status": "skipped",
                    "incomplete_reason": "dry_run",
                }
            )
    else:
        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            futures = [
                executor.submit(
                    _run_pair_with_retries,
                    repo_root=repository_root,
                    policy_spec=policy_spec,
                    task_path=task_path,
                    retries=retries,
                    retry_delay_sec=retry_delay_sec,
                    agent_runner=agent_runner,
                )
                for policy_spec, task_path in pending_pairs
            ]
            for future in as_completed(futures):
                records.append(future.result())
                partial_summary = _build_summary(
                    matrix_run_id=matrix_run_id,
                    manifest_id=manifest_id,
                    manifest_path=resolved_manifest_path,
                    started_at=started_at,
                    policy_specs=policy_specs,
                    task_paths=task_paths,
                    records=records,
                    preflight_result=preflight_result,
                )
                _write_summary(summary_path, markdown_path, partial_summary)

    summary = _build_summary(
        matrix_run_id=matrix_run_id,
        manifest_id=manifest_id,
        manifest_path=resolved_manifest_path,
        started_at=started_at,
        policy_specs=policy_specs,
        task_paths=task_paths,
        records=records,
        preflight_result=preflight_result,
    )
    _write_summary(summary_path, markdown_path, summary)
    return {
        "matrix_run_id": matrix_run_id,
        "summary_json_path": str(summary_path),
        "summary_md_path": str(markdown_path),
        "summary": summary,
    }


def _build_summary(
    *,
    matrix_run_id: str,
    manifest_id: str,
    manifest_path: Path,
    started_at: str,
    policy_specs: list[dict[str, Any]],
    task_paths: list[Path],
    records: list[dict[str, Any]],
    preflight_result: dict[str, Any],
) -> dict[str, Any]:
    completed_records = [
        record
        for record in records
        if record.get("record_status") == "completed"
    ]
    error_records = [
        record
        for record in records
        if record.get("record_status") == "error"
    ]
    success_count = sum(1 for record in completed_records if record.get("final_status") == "success")
    expected_pair_count = len(policy_specs) * len(task_paths)
    return {
        "matrix_run_id": matrix_run_id,
        "manifest_id": manifest_id,
        "manifest_path": str(manifest_path),
        "started_at": started_at,
        "finished_at": _utc_timestamp(),
        "policy_count": len(policy_specs),
        "task_count": len(task_paths),
        "expected_pair_count": expected_pair_count,
        "record_count": len(records),
        "completed_count": len(completed_records),
        "success_count": success_count,
        "error_count": len(error_records),
        "success_rate": round(success_count / len(completed_records), 4) if completed_records else 0.0,
        "policies": policy_specs,
        "preflight": preflight_result,
        "policy_summaries": _build_policy_summaries(records, policy_specs),
        "records": sorted(records, key=lambda item: (str(item.get("policy_id")), str(item.get("task_id")))),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one task manifest across multiple LLM policies.")
    parser.add_argument("--manifest", required=True, help="Manifest JSON path.")
    parser.add_argument(
        "--policy",
        dest="policies",
        action="append",
        required=True,
        help="Policy JSON path. Pass multiple times for multiple models.",
    )
    parser.add_argument("--output-dir", default="logs/summaries", help="Summary output directory.")
    parser.add_argument("--run-label", default=None, help="Optional run label.")
    parser.add_argument("--max-workers", type=int, default=1, help="Concurrent (task, policy) workers.")
    parser.add_argument("--retries", type=int, default=0, help="Retries per failed pair.")
    parser.add_argument("--retry-delay-sec", type=float, default=1.0, help="Delay between retries.")
    parser.add_argument("--resume-from", default=None, help="Existing summary JSON to resume.")
    parser.add_argument("--limit", type=int, default=None, help="Limit pending pairs for smoke runs.")
    parser.add_argument("--dry-run", action="store_true", help="Write skipped records without calling APIs.")
    parser.add_argument(
        "--no-preflight",
        action="store_true",
        help="Skip API key/base URL environment checks before real runs.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_multi_model_eval(
        repo_root=REPO_ROOT,
        manifest_path=args.manifest,
        policy_paths=args.policies,
        output_dir=args.output_dir,
        run_label=args.run_label,
        max_workers=args.max_workers,
        retries=args.retries,
        retry_delay_sec=args.retry_delay_sec,
        resume_from=args.resume_from,
        limit=args.limit,
        dry_run=args.dry_run,
        preflight=not args.no_preflight,
    )
    summary = output["summary"]
    print("=== Multi-Model Eval Summary ===")
    print(f"matrix_run_id: {output['matrix_run_id']}")
    print(f"expected_pair_count: {summary['expected_pair_count']}")
    print(f"completed_count: {summary['completed_count']}")
    print(f"success_rate: {summary['success_rate']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
