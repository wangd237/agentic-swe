"""审计真实 issue 候选到 semi-real 正式接入的推进状态。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_summary_id(summary_dir: Path, run_label: str | None = None) -> str:
    prefix = f"semi_real_pipeline_audit_{run_label}_" if run_label else "semi_real_pipeline_audit_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _task_number(task_id: str) -> int:
    suffix = str(task_id).removeprefix("task_")
    return int(suffix) if suffix.isdigit() else -1


def _summarize_status_counts(candidates: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for candidate in candidates:
        status = str(candidate.get("status", "unknown")).strip() or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _load_manifest_candidate_ids(*, repo_root: Path, manifest_path: Path | None) -> set[str]:
    if manifest_path is None or not manifest_path.exists():
        return set()
    manifest_payload = _load_json(manifest_path)
    candidate_ids: set[str] = set()
    for relative_task_path in manifest_payload.get("tasks", []):
        task_path = (repo_root / relative_task_path).resolve()
        if not task_path.exists():
            continue
        task_payload = _load_json(task_path)
        candidate_id = str(task_payload.get("metadata", {}).get("candidate_id", "")).strip()
        if candidate_id:
            candidate_ids.add(candidate_id)
    return candidate_ids


def _load_latest_candidate_tasks(tasks_dir: Path) -> dict[str, dict]:
    latest_tasks: dict[str, dict] = {}
    for task_path in sorted(tasks_dir.glob("task_*.json")):
        task_payload = _load_json(task_path)
        candidate_id = str(task_payload.get("metadata", {}).get("candidate_id", "")).strip()
        if not candidate_id:
            continue
        current = latest_tasks.get(candidate_id)
        next_task_number = _task_number(str(task_payload.get("task_id", "")))
        if current is None or next_task_number > current["task_number"]:
            latest_tasks[candidate_id] = {
                "task_number": next_task_number,
                "task_id": task_payload.get("task_id"),
                "task_path": str(task_path),
                "source_type": task_payload.get("source_type"),
                "repo_scaffold_status": task_payload.get("metadata", {}).get("repo_scaffold_status"),
                "ready_note": task_payload.get("metadata", {}).get("ready_note"),
                "repo_path": task_payload.get("repo_path"),
                "issue_title": task_payload.get("issue_title"),
            }
    return latest_tasks


def _build_candidate_stage_record(
    candidate: dict,
    latest_task: dict | None,
    formal_candidate_ids: set[str],
    challenge_candidate_ids: set[str],
) -> dict:
    candidate_id = str(candidate.get("candidate_id", "")).strip()
    status = str(candidate.get("status", "unknown")).strip() or "unknown"
    in_formal_manifest = candidate_id in formal_candidate_ids
    in_challenge_manifest = candidate_id in challenge_candidate_ids
    repo_scaffold_status = None if latest_task is None else latest_task.get("repo_scaffold_status")
    has_task = latest_task is not None
    is_ready = repo_scaffold_status == "ready"

    if status == "accepted" and in_formal_manifest:
        stage = "accepted_in_formal_manifest"
    elif status == "accepted" and in_challenge_manifest:
        stage = "accepted_in_challenge_manifest"
    elif status == "accepted" and is_ready:
        stage = "accepted_ready_not_in_any_manifest"
    elif status == "accepted" and has_task:
        stage = "accepted_draft_task_not_in_formal_manifest"
    elif status == "accepted":
        stage = "accepted_without_task"
    elif status == "screened" and has_task:
        stage = "screened_with_task"
    elif status == "screened":
        stage = "screened_without_task"
    elif status == "imported":
        stage = "imported"
    elif status == "blocked":
        stage = "blocked"
    elif status == "completed":
        stage = "completed"
    else:
        stage = "other"

    return {
        "candidate_id": candidate_id,
        "repo_full_name": candidate.get("repo_full_name"),
        "issue_number": candidate.get("issue_number"),
        "issue_title": candidate.get("issue_title"),
        "status": status,
        "stage": stage,
        "in_formal_manifest": in_formal_manifest,
        "in_challenge_manifest": in_challenge_manifest,
        "has_task": has_task,
        "task_id": None if latest_task is None else latest_task.get("task_id"),
        "task_path": None if latest_task is None else latest_task.get("task_path"),
        "repo_scaffold_status": repo_scaffold_status,
        "ready_note": None if latest_task is None else latest_task.get("ready_note"),
    }


def _summarize_stage_counts(records: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        stage = str(record.get("stage", "other"))
        counts[stage] = counts.get(stage, 0) + 1
    return dict(sorted(counts.items()))


def build_semi_real_pipeline_audit(
    *,
    repo_root: Path,
    candidate_file: Path,
    tasks_dir: Path,
    formal_manifest_path: Path,
    challenge_manifest_path: Path | None = None,
) -> dict:
    candidate_payload = _load_json(candidate_file)
    candidates = list(candidate_payload.get("candidates", []))
    formal_candidate_ids = _load_manifest_candidate_ids(repo_root=repo_root, manifest_path=formal_manifest_path)
    challenge_candidate_ids = _load_manifest_candidate_ids(repo_root=repo_root, manifest_path=challenge_manifest_path)
    latest_tasks = _load_latest_candidate_tasks(tasks_dir)

    records = [
        _build_candidate_stage_record(
            candidate,
            latest_tasks.get(str(candidate.get("candidate_id", "")).strip()),
            formal_candidate_ids,
            challenge_candidate_ids,
        )
        for candidate in candidates
    ]

    accepted_in_challenge_manifest = [
        record
        for record in records
        if record["stage"] == "accepted_in_challenge_manifest"
    ]
    accepted_ready_not_in_any_manifest = [
        record
        for record in records
        if record["stage"] == "accepted_ready_not_in_any_manifest"
    ]
    screened_candidates = [record for record in records if record["status"] == "screened"]

    return {
        "created_at": _utc_timestamp(),
        "candidate_file": str(candidate_file),
        "tasks_dir": str(tasks_dir),
        "formal_manifest_path": str(formal_manifest_path),
        "challenge_manifest_path": None if challenge_manifest_path is None else str(challenge_manifest_path),
        "candidate_count": len(candidates),
        "formal_candidate_count": len(formal_candidate_ids),
        "challenge_candidate_count": len(challenge_candidate_ids),
        "candidate_status_counts": _summarize_status_counts(candidates),
        "stage_counts": _summarize_stage_counts(records),
        "accepted_in_challenge_manifest": accepted_in_challenge_manifest,
        "accepted_ready_not_in_any_manifest": accepted_ready_not_in_any_manifest,
        "screened_candidates": screened_candidates,
        "records": records,
    }


def build_semi_real_pipeline_audit_markdown(summary: dict) -> str:
    status_lines = "\n".join(
        f"- `{status}`: `{count}`"
        for status, count in summary["candidate_status_counts"].items()
    ) or "- 当前没有候选"
    stage_lines = "\n".join(
        f"- `{stage}`: `{count}`"
        for stage, count in summary["stage_counts"].items()
    ) or "- 当前没有阶段数据"
    accepted_in_challenge_lines = "\n".join(
        (
            f"- `{record['candidate_id']}`: "
            f"`{record['task_id']}` / `{record['repo_scaffold_status']}` / in_formal_manifest=`{record['in_formal_manifest']}`"
        )
        for record in summary["accepted_in_challenge_manifest"]
    ) or "- 当前没有 accepted 且已纳入 challenge manifest 的候选"
    accepted_ready_lines = "\n".join(
        (
            f"- `{record['candidate_id']}`: "
            f"`{record['task_id']}` / `{record['repo_scaffold_status']}` / in_formal_manifest=`{record['in_formal_manifest']}` / in_challenge_manifest=`{record['in_challenge_manifest']}`"
        )
        for record in summary["accepted_ready_not_in_any_manifest"]
    ) or "- 当前没有 accepted + ready 但未进入任何 manifest 的候选"

    return f"""# Semi-Real Pipeline Audit

## Scope

- candidate_count: `{summary["candidate_count"]}`
- formal_candidate_count: `{summary["formal_candidate_count"]}`
- challenge_candidate_count: `{summary["challenge_candidate_count"]}`
- candidate_file: `{summary["candidate_file"]}`
- formal_manifest_path: `{summary["formal_manifest_path"]}`
- challenge_manifest_path: `{summary["challenge_manifest_path"]}`

## Candidate Status Counts

{status_lines}

## Stage Counts

{stage_lines}

## Accepted In Challenge Manifest

{accepted_in_challenge_lines}

## Accepted Ready Not In Any Manifest

{accepted_ready_lines}
"""


def audit_semi_real_pipeline(
    *,
    candidate_file: str | Path = "benchmarks/real_world_candidates.json",
    tasks_dir: str | Path = "benchmarks/tasks",
    formal_manifest: str | Path = "benchmarks/manifests/real_issue_tasks.json",
    challenge_manifest: str | Path = "benchmarks/manifests/real_issue_tasks_challenge_v1.json",
    output_dir: str | Path = "logs/summaries",
    run_label: str | None = None,
) -> dict:
    output_directory = Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    summary = build_semi_real_pipeline_audit(
        repo_root=REPO_ROOT,
        candidate_file=(REPO_ROOT / candidate_file).resolve() if not Path(candidate_file).is_absolute() else Path(candidate_file).resolve(),
        tasks_dir=(REPO_ROOT / tasks_dir).resolve() if not Path(tasks_dir).is_absolute() else Path(tasks_dir).resolve(),
        formal_manifest_path=(REPO_ROOT / formal_manifest).resolve()
        if not Path(formal_manifest).is_absolute()
        else Path(formal_manifest).resolve(),
        challenge_manifest_path=(REPO_ROOT / challenge_manifest).resolve()
        if not Path(challenge_manifest).is_absolute()
        else Path(challenge_manifest).resolve(),
    )
    analysis_id = _next_summary_id(output_directory, run_label=run_label)
    summary["analysis_id"] = analysis_id

    summary_json_path = output_directory / f"{analysis_id}.json"
    summary_md_path = output_directory / f"{analysis_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_semi_real_pipeline_audit_markdown(summary))

    return {
        "analysis_id": analysis_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计真实 issue 到 semi-real 正式接入的推进状态。")
    parser.add_argument("--candidate-file", default="benchmarks/real_world_candidates.json", help="候选文件路径")
    parser.add_argument("--tasks-dir", default="benchmarks/tasks", help="任务目录")
    parser.add_argument("--formal-manifest", default="benchmarks/manifests/real_issue_tasks.json", help="正式任务 manifest")
    parser.add_argument("--challenge-manifest", default="benchmarks/manifests/real_issue_tasks_challenge_v1.json", help="challenge 任务 manifest")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--run-label", default=None, help="输出标签")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = audit_semi_real_pipeline(
        candidate_file=args.candidate_file,
        tasks_dir=args.tasks_dir,
        formal_manifest=args.formal_manifest,
        challenge_manifest=args.challenge_manifest,
        output_dir=args.output_dir,
        run_label=args.run_label,
    )
    summary = output["summary"]
    print("=== Semi-Real Pipeline Audit Summary ===")
    print(f"analysis_id: {output['analysis_id']}")
    print(f"candidate_count: {summary['candidate_count']}")
    print(f"formal_candidate_count: {summary['formal_candidate_count']}")
    print(f"challenge_candidate_count: {summary['challenge_candidate_count']}")
    for stage, count in summary["stage_counts"].items():
        print(f"{stage}: {count}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
