"""Run or plan a code intelligence A/B evaluation cohort."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.llm_config import LLMConfig
from app.runtime.batch_runner import load_task_paths, run_batch
from app.runtime.logger import write_json, write_text
from app.schemas.task_schema import load_task
from scripts.summarize_code_intelligence_runs import summarize_code_intelligence_runs


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_eval_id(output_dir: Path, cohort_label: str) -> str:
    prefix = f"code_intelligence_ab_{cohort_label}_"
    existing_numbers: list[int] = []
    for path in output_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _write_policy(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, payload)


def build_graph_policy(
    *,
    baseline_policy: dict[str, Any],
    graph_policy_id: str,
    codebase_memory_binary: str,
    timeout_sec: float,
    max_results: int,
    index_mode: str,
) -> dict[str, Any]:
    graph_policy = dict(baseline_policy)
    graph_policy["policy_id"] = graph_policy_id
    graph_policy["description"] = (
        f"{baseline_policy.get('description', '')} + codebase-memory graph-assisted localization"
    ).strip()
    graph_policy["code_intelligence_backend"] = "codebase_memory_cli"
    graph_policy["codebase_memory_binary"] = codebase_memory_binary
    graph_policy["codebase_memory_index_mode"] = index_mode
    graph_policy["codebase_memory_always_shadow_copy"] = True
    graph_policy["code_intelligence_timeout_sec"] = timeout_sec
    graph_policy["code_intelligence_max_results"] = max_results
    return graph_policy


def _result_paths_from_batch(batch_output: dict[str, Any]) -> list[str]:
    return [
        item["result_path"]
        for item in batch_output["batch_summary"]["tasks"]
        if item.get("result_path")
    ]


def collect_target_files_by_task(task_paths: list[str | Path]) -> dict[str, list[str]]:
    targets: dict[str, list[str]] = {}
    for task_path in task_paths:
        task = load_task(task_path)
        if task.target_files_hint:
            targets[task.task_id] = [str(path) for path in task.target_files_hint]
    return targets


def build_external_data_preview(
    *,
    baseline_policy: dict[str, Any],
    graph_policy: dict[str, Any],
    task_paths: list[str | Path],
    target_files_by_task: dict[str, list[str]],
) -> dict[str, Any]:
    task_items: list[dict[str, Any]] = []
    total_issue_text_chars = 0
    total_target_file_hints = 0
    repo_names: set[str] = set()
    for task_path in task_paths:
        task = load_task(task_path)
        target_files = target_files_by_task.get(task.task_id, [])
        total_issue_text_chars += len(task.issue_text)
        total_target_file_hints += len(target_files)
        repo_names.add(task.repo_name)
        task_items.append(
            {
                "task_id": task.task_id,
                "repo_name": task.repo_name,
                "repo_path": task.repo_path,
                "difficulty": task.difficulty,
                "tags": task.tags,
                "issue_title": task.issue_title,
                "issue_text_char_count": len(task.issue_text),
                "test_command": task.test_command,
                "success_criteria_char_count": len(task.success_criteria),
                "target_files_hint": target_files,
                "target_files_hint_count": len(target_files),
                "metadata_keys": sorted(task.metadata.keys()),
            }
        )

    return {
        "purpose": "Preview metadata for real A/B data that may be sent to the external LLM provider.",
        "contains_full_issue_text": False,
        "contains_code_snippets": False,
        "contains_tool_outputs": False,
        "contains_diffs": False,
        "real_ab_may_send": [
            "task issue title and issue text",
            "repository code snippets read by the agent",
            "tool outputs from tests, search, graph, and file reads",
            "patch diffs generated during repair",
            "agent traces needed for reasoning and summaries",
        ],
        "llm_provider": baseline_policy.get("llm_provider", ""),
        "llm_model": baseline_policy.get("llm_model", ""),
        "graph_backend": graph_policy.get("code_intelligence_backend", ""),
        "codebase_memory_index_mode": graph_policy.get("codebase_memory_index_mode", ""),
        "task_count": len(task_items),
        "repo_count": len(repo_names),
        "repo_names": sorted(repo_names),
        "total_issue_text_chars": total_issue_text_chars,
        "total_target_file_hints": total_target_file_hints,
        "tasks": task_items,
    }


def build_preflight_report(
    *,
    baseline_policy: dict[str, Any],
    graph_policy: dict[str, Any],
    codebase_memory_binary: str,
    task_paths: list[str | Path],
    target_files_by_task: dict[str, list[str]],
    external_llm_data_consent: bool = False,
    minimum_task_count: int = 8,
) -> dict[str, Any]:
    api_key_env = str(baseline_policy.get("llm_api_key_env") or "LLM_API_KEY")
    base_url_env = str(baseline_policy.get("llm_base_url_env") or "LLM_BASE_URL")
    model_env = str(baseline_policy.get("llm_model_env") or "LLM_MODEL")
    default_base_url = str(baseline_policy.get("llm_base_url") or "")
    binary_path = shutil.which(codebase_memory_binary) or (
        str(Path(codebase_memory_binary).resolve()) if Path(codebase_memory_binary).exists() else ""
    )
    version = ""
    binary_available = bool(binary_path)
    if binary_available:
        try:
            completed = subprocess.run(
                [binary_path, "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
            version_lines = (completed.stdout or completed.stderr or "").strip().splitlines()
            version = version_lines[0] if version_lines else ""
            binary_available = completed.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            binary_available = False

    task_ids_missing_targets: list[str] = []
    task_summaries: list[dict[str, Any]] = []
    for task_path in task_paths:
        task = load_task(task_path)
        targets = target_files_by_task.get(task.task_id, [])
        if not targets:
            task_ids_missing_targets.append(task.task_id)
        task_summaries.append(
            {
                "task_id": task.task_id,
                "repo_name": task.repo_name,
                "difficulty": task.difficulty,
                "target_files_hint_count": len(targets),
                "target_files_hint": targets,
            }
        )

    blockers: list[str] = []
    warnings: list[str] = []
    if not os.environ.get(api_key_env, "").strip():
        blockers.append(f"missing_llm_api_key:{api_key_env}")
    if not (os.environ.get(base_url_env, "").strip() or default_base_url):
        blockers.append(f"missing_llm_base_url:{base_url_env}")
    if not external_llm_data_consent:
        blockers.append("missing_external_llm_data_consent")
    if not binary_available:
        blockers.append("codebase_memory_binary_unavailable")
    if len(task_paths) < minimum_task_count:
        warnings.append(f"sample_size_below_recommended:{len(task_paths)}<{minimum_task_count}")
    if task_ids_missing_targets:
        warnings.append(f"tasks_missing_target_files:{','.join(task_ids_missing_targets)}")

    return {
        "ready_for_real_ab": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "llm": {
            "provider": baseline_policy.get("llm_provider", ""),
            "model": os.environ.get(model_env, "").strip() or baseline_policy.get("llm_model", ""),
            "api_key_env": api_key_env,
            "api_key_present": bool(os.environ.get(api_key_env, "").strip()),
            "base_url_env": base_url_env,
            "base_url_present": bool(os.environ.get(base_url_env, "").strip() or default_base_url),
            "model_env": model_env,
            "external_data_consent": external_llm_data_consent,
            "external_data_notice": (
                "Real A/B sends task issue text, code snippets, tool outputs, diffs, and traces "
                "needed by the agent to the configured OpenAI-compatible LLM provider."
            ),
        },
        "codebase_memory": {
            "binary_config": codebase_memory_binary,
            "binary_path": binary_path,
            "binary_available": binary_available,
            "version": version,
            "index_mode": graph_policy.get("codebase_memory_index_mode", ""),
            "always_shadow_copy": graph_policy.get("codebase_memory_always_shadow_copy", False),
        },
        "tasks": {
            "count": len(task_paths),
            "minimum_recommended_count": minimum_task_count,
            "with_target_files": len(target_files_by_task),
            "missing_target_task_ids": task_ids_missing_targets,
            "items": task_summaries,
        },
    }


def build_markdown(summary: dict[str, Any]) -> str:
    task_lines = "\n".join(f"- `{path}`" for path in summary["task_paths"]) or "- N/A"
    outputs = summary.get("outputs", {})
    preflight = summary.get("preflight", {})
    v16_acceptance = summary.get("v16_acceptance", {})
    preflight_section = ""
    if preflight:
        preflight_section = f"""
## Preflight

- ready_for_real_ab: `{preflight.get("ready_for_real_ab", False)}`
- blockers: `{preflight.get("blockers", [])}`
- warnings: `{preflight.get("warnings", [])}`
- llm_api_key_env: `{preflight.get("llm", {}).get("api_key_env", "")}`
- llm_api_key_present: `{preflight.get("llm", {}).get("api_key_present", False)}`
- external_llm_data_consent: `{preflight.get("llm", {}).get("external_data_consent", False)}`
- codebase_memory_binary_available: `{preflight.get("codebase_memory", {}).get("binary_available", False)}`
- task_count: `{preflight.get("tasks", {}).get("count", 0)}`
- tasks_with_target_files: `{preflight.get("tasks", {}).get("with_target_files", 0)}`
"""
    acceptance_section = ""
    if v16_acceptance:
        acceptance_section = f"""
## v16 Acceptance

- require_v16_acceptance: `{summary.get("require_v16_acceptance", False)}`
- ready_to_judge: `{v16_acceptance.get("ready_to_judge", False)}`
- accepted: `{v16_acceptance.get("accepted", False)}`
- failed_check_ids: `{v16_acceptance.get("failed_check_ids", [])}`
"""
    return f"""# Code Intelligence A/B Evaluation

## Plan

- eval_id: `{summary["eval_id"]}`
- cohort_label: `{summary["cohort_label"]}`
- dry_run: `{summary["dry_run"]}`
- preflight_only: `{summary.get("preflight_only", False)}`
- external_data_preview_only: `{summary.get("external_data_preview_only", False)}`
- aborted_by_preflight: `{summary.get("aborted_by_preflight", False)}`
- task_count: `{summary["task_count"]}`
- baseline_policy_path: `{summary["baseline_policy_path"]}`
- graph_policy_path: `{summary["graph_policy_path"]}`
- targets_json_path: `{summary.get("targets_json_path", "N/A")}`
- external_data_preview_path: `{summary.get("external_data_preview_path", "N/A")}`

## Tasks

{task_lines}
{preflight_section}

## Outputs

- baseline_batch_summary: `{outputs.get("baseline_batch_summary", "N/A")}`
- graph_batch_summary: `{outputs.get("graph_batch_summary", "N/A")}`
- ab_summary_json: `{outputs.get("ab_summary_json", "N/A")}`
- ab_summary_md: `{outputs.get("ab_summary_md", "N/A")}`
{acceptance_section}
"""


def run_code_intelligence_ab(
    *,
    manifest: str | Path,
    tasks_dir: str | Path,
    baseline_policy_path: str | Path,
    cohort_label: str,
    codebase_memory_binary: str = "codebase-memory-mcp",
    timeout_sec: float = 30.0,
    max_results: int = 5,
    index_mode: str = "fast",
    limit: int | None = None,
    dry_run: bool = False,
    preflight_only: bool = False,
    external_data_preview_only: bool = False,
    ignore_preflight_blockers: bool = False,
    confirm_external_llm_data: bool = False,
    require_v16_acceptance: bool = False,
    output_dir: str | Path = "logs/summaries",
) -> dict[str, Any]:
    LLMConfig.load_env_file(REPO_ROOT)
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    eval_id = _next_eval_id(output_directory, cohort_label)
    baseline_policy_file = Path(baseline_policy_path).resolve()
    baseline_policy = _load_json(baseline_policy_file)
    graph_policy_id = f"{baseline_policy.get('policy_id', baseline_policy_file.stem)}_code_intelligence"
    graph_policy = build_graph_policy(
        baseline_policy=baseline_policy,
        graph_policy_id=graph_policy_id,
        codebase_memory_binary=codebase_memory_binary,
        timeout_sec=timeout_sec,
        max_results=max_results,
        index_mode=index_mode,
    )
    graph_policy_path = output_directory / f"{eval_id}_graph_policy.json"
    _write_policy(graph_policy_path, graph_policy)

    manifest_path = Path(manifest).resolve()
    task_paths = load_task_paths(
        tasks_dir=tasks_dir,
        manifest_path=manifest_path if manifest_path.exists() else None,
    )
    if limit is not None:
        task_paths = task_paths[:limit]
    target_files_by_task = collect_target_files_by_task(task_paths)
    targets_json_path = output_directory / f"{eval_id}_targets.json"
    write_json(targets_json_path, target_files_by_task)

    summary: dict[str, Any] = {
        "created_at": _utc_timestamp(),
        "eval_id": eval_id,
        "cohort_label": cohort_label,
        "dry_run": dry_run,
        "preflight_only": preflight_only,
        "external_data_preview_only": external_data_preview_only,
        "ignore_preflight_blockers": ignore_preflight_blockers,
        "confirm_external_llm_data": confirm_external_llm_data,
        "require_v16_acceptance": require_v16_acceptance,
        "aborted_by_preflight": False,
        "task_count": len(task_paths),
        "task_paths": [str(path) for path in task_paths],
        "baseline_policy_path": str(baseline_policy_file),
        "graph_policy_path": str(graph_policy_path),
        "graph_policy": graph_policy,
        "target_files_by_task": target_files_by_task,
        "targets_json_path": str(targets_json_path),
        "external_data_preview_path": "",
        "external_data_preview": {},
        "ab_aggregate": {},
        "v16_acceptance": {},
        "outputs": {},
    }
    external_data_preview = build_external_data_preview(
        baseline_policy=baseline_policy,
        graph_policy=graph_policy,
        task_paths=task_paths,
        target_files_by_task=target_files_by_task,
    )
    external_data_preview_path = output_directory / f"{eval_id}_external_data_preview.json"
    write_json(external_data_preview_path, external_data_preview)
    summary["external_data_preview_path"] = str(external_data_preview_path)
    summary["external_data_preview"] = {
        "task_count": external_data_preview["task_count"],
        "repo_count": external_data_preview["repo_count"],
        "repo_names": external_data_preview["repo_names"],
        "total_issue_text_chars": external_data_preview["total_issue_text_chars"],
        "total_target_file_hints": external_data_preview["total_target_file_hints"],
        "contains_full_issue_text": external_data_preview["contains_full_issue_text"],
        "contains_code_snippets": external_data_preview["contains_code_snippets"],
        "real_ab_may_send": external_data_preview["real_ab_may_send"],
    }
    summary["preflight"] = build_preflight_report(
        baseline_policy=baseline_policy,
        graph_policy=graph_policy,
        codebase_memory_binary=codebase_memory_binary,
        task_paths=task_paths,
        target_files_by_task=target_files_by_task,
        external_llm_data_consent=confirm_external_llm_data,
    )

    preflight_blockers = summary["preflight"]["blockers"]
    missing_external_llm_data_consent = "missing_external_llm_data_consent" in preflight_blockers
    if (
        not dry_run
        and not preflight_only
        and not external_data_preview_only
        and preflight_blockers
        and (missing_external_llm_data_consent or not ignore_preflight_blockers)
    ):
        summary["aborted_by_preflight"] = True
        summary["outputs"] = {
            "aborted_reason": "preflight_blockers",
            "blockers": preflight_blockers,
        }

    if (
        not dry_run
        and not preflight_only
        and not external_data_preview_only
        and not summary["aborted_by_preflight"]
    ):
        baseline_batch = run_batch(
            repo_root=REPO_ROOT,
            task_paths=task_paths,
            policy_path=baseline_policy_file,
            run_label=f"{cohort_label}_baseline",
        )
        graph_batch = run_batch(
            repo_root=REPO_ROOT,
            task_paths=task_paths,
            policy_path=graph_policy_path,
            run_label=f"{cohort_label}_graph",
        )
        result_paths = [
            *_result_paths_from_batch(baseline_batch),
            *_result_paths_from_batch(graph_batch),
        ]
        ab_summary = summarize_code_intelligence_runs(
            result_paths=result_paths,
            cohort_label=f"{cohort_label}_ab",
            output_dir=output_directory,
            target_files_by_task=target_files_by_task,
            include_ab_pairs=True,
            baseline_backend="none",
            candidate_backend="codebase_memory_cli",
        )
        ab_summary_payload = ab_summary.get("summary", {})
        summary["ab_aggregate"] = ab_summary_payload.get("ab_aggregate", {})
        summary["v16_acceptance"] = ab_summary_payload.get("v16_acceptance", {})
        summary["outputs"] = {
            "baseline_batch_summary": baseline_batch["summary_json_path"],
            "graph_batch_summary": graph_batch["summary_json_path"],
            "ab_summary_json": ab_summary["summary_json_path"],
            "ab_summary_md": ab_summary["summary_md_path"],
        }

    summary_json_path = output_directory / f"{eval_id}.json"
    summary_md_path = output_directory / f"{eval_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_markdown(summary))
    return {
        "eval_id": eval_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or plan a code intelligence A/B evaluation.")
    parser.add_argument("--manifest", default="benchmarks/manifests/dev_tasks.json")
    parser.add_argument("--tasks-dir", default="benchmarks/tasks")
    parser.add_argument("--baseline-policy", required=True)
    parser.add_argument("--cohort-label", default="v16_ab")
    parser.add_argument("--codebase-memory-binary", default="codebase-memory-mcp")
    parser.add_argument("--timeout-sec", type=float, default=30.0)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--index-mode", default="fast")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--external-data-preview-only",
        action="store_true",
        help=(
            "Write a metadata-only preview of data categories and tasks that real A/B may send "
            "to the external LLM provider, without running batches."
        ),
    )
    parser.add_argument(
        "--ignore-preflight-blockers",
        action="store_true",
        help=(
            "Run real A/B even when technical preflight blockers are reported. "
            "This cannot override missing external LLM data consent."
        ),
    )
    parser.add_argument(
        "--confirm-external-llm-data",
        action="store_true",
        help=(
            "Confirm that real A/B may send task issue text, repository code snippets, "
            "tool outputs, diffs, and traces to the configured external LLM provider."
        ),
    )
    parser.add_argument(
        "--require-v16-acceptance",
        action="store_true",
        help="Return exit code 3 unless the completed real A/B v16 acceptance checklist passes.",
    )
    parser.add_argument("--output-dir", default="logs/summaries")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = run_code_intelligence_ab(
        manifest=REPO_ROOT / args.manifest,
        tasks_dir=REPO_ROOT / args.tasks_dir,
        baseline_policy_path=REPO_ROOT / args.baseline_policy,
        cohort_label=args.cohort_label,
        codebase_memory_binary=args.codebase_memory_binary,
        timeout_sec=args.timeout_sec,
        max_results=args.max_results,
        index_mode=args.index_mode,
        limit=args.limit,
        dry_run=args.dry_run,
        preflight_only=args.preflight_only,
        external_data_preview_only=args.external_data_preview_only,
        ignore_preflight_blockers=args.ignore_preflight_blockers,
        confirm_external_llm_data=args.confirm_external_llm_data,
        require_v16_acceptance=args.require_v16_acceptance,
        output_dir=REPO_ROOT / args.output_dir,
    )
    summary = output["summary"]
    print("=== Code Intelligence A/B Evaluation ===")
    print(f"eval_id: {output['eval_id']}")
    print(f"dry_run: {summary['dry_run']}")
    print(f"preflight_only: {summary['preflight_only']}")
    print(f"external_data_preview_only: {summary['external_data_preview_only']}")
    print(f"aborted_by_preflight: {summary['aborted_by_preflight']}")
    print(f"task_count: {summary['task_count']}")
    preflight = summary.get("preflight", {})
    if preflight:
        print(f"ready_for_real_ab: {preflight.get('ready_for_real_ab')}")
        print(f"blockers: {preflight.get('blockers')}")
        print(f"warnings: {preflight.get('warnings')}")
    print(f"graph_policy_path: {summary['graph_policy_path']}")
    print(f"targets_json_path: {summary['targets_json_path']}")
    print(f"external_data_preview_path: {summary['external_data_preview_path']}")
    v16_acceptance = summary.get("v16_acceptance", {})
    if v16_acceptance:
        print(f"v16_acceptance_ready_to_judge: {v16_acceptance.get('ready_to_judge', False)}")
        print(f"v16_acceptance_accepted: {v16_acceptance.get('accepted', False)}")
        print(f"v16_acceptance_failed_checks: {v16_acceptance.get('failed_check_ids', [])}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    if summary.get("aborted_by_preflight"):
        return 2
    if summary.get("require_v16_acceptance") and v16_acceptance and not v16_acceptance.get("accepted", False):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
