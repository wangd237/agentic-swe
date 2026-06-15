"""生成 roadmap 当前状态快照，收口关键治理与推进信号。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text
from scripts.analyze_benchmark_maturity import build_benchmark_maturity_summary
from scripts.audit_semi_real_pipeline import build_semi_real_pipeline_audit
from scripts.validate_challenge_shortlist import summarize_challenge_shortlist


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_snapshot_id(summary_dir: Path, run_label: str | None = None) -> str:
    prefix = f"roadmap_status_{run_label}_" if run_label else "roadmap_status_"
    existing_numbers: list[int] = []
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    return f"{prefix}{next_number:03d}"


def _build_next_challenge_action(*, challenge_task_count: int, shortlist_summary: dict) -> str:
    if shortlist_summary["next_candidate"] is not None:
        return f"优先评估 challenge 候选 {shortlist_summary['next_candidate']['issue_ref']}"
    return f"重新 sourcing 第 {challenge_task_count + 1} 条 challenge 候选"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _count_shortlist_candidates_in_stage(shortlist_summary: dict, pipeline_summary: dict, *, stage: str) -> int:
    shortlist_issue_refs = {
        (repo_full_name, issue_number)
        for repo_full_name, issue_number in shortlist_summary.get("candidate_issue_refs", [])
    }
    if not shortlist_issue_refs:
        return 0

    matched_count = 0
    for record in pipeline_summary.get("records", []):
        issue_ref = (record.get("repo_full_name"), record.get("issue_number"))
        if issue_ref not in shortlist_issue_refs:
            continue
        if record.get("stage") != stage:
            continue
        matched_count += 1
    return matched_count


def _load_latest_summary(directory: Path, pattern: str) -> tuple[dict | None, Path | None]:
    if not directory.exists():
        return None, None

    latest_payload: dict | None = None
    latest_path: Path | None = None
    latest_created_at = ""
    for path in sorted(directory.glob(pattern)):
        payload = _load_json(path)
        created_at = str(payload.get("created_at", ""))
        if latest_payload is None or (created_at, path.name) > (latest_created_at, latest_path.name if latest_path is not None else ""):
            latest_payload = payload
            latest_path = path
            latest_created_at = created_at
    return latest_payload, latest_path


def _looks_like_github_token(token: str) -> bool:
    normalized = token.strip()
    return normalized.startswith(("ghp_", "gho_", "ghu_", "ghs_", "github_pat_"))


def _run_command(command: list[str], *, extra_env: dict[str, str] | None = None) -> tuple[int | None, str, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=extra_env,
        )
    except FileNotFoundError:
        return None, "", ""
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def _build_challenge_local_auth_readiness() -> dict:
    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    gh_token = os.environ.get("GH_TOKEN", "").strip()
    env_token = github_token or gh_token
    env_token_source = None
    if github_token:
        env_token_source = "GITHUB_TOKEN"
    elif gh_token:
        env_token_source = "GH_TOKEN"

    readiness = {
        "env_token_present": bool(env_token),
        "env_token_source": env_token_source,
        "env_token_looks_valid": bool(env_token and _looks_like_github_token(env_token)),
        "gh_cli_available": False,
        "gh_auth_logged_in": False,
        "gh_auth_active_account": None,
        "gh_auth_token_exportable": False,
        "preferred_search_mode": "unavailable",
    }

    status_rc, status_stdout, status_stderr = _run_command(["gh", "auth", "status"])
    if status_rc is not None:
        readiness["gh_cli_available"] = True
    if status_rc == 0:
        readiness["gh_auth_logged_in"] = True
        combined_status = "\n".join(part for part in [status_stdout, status_stderr] if part)
        for line in combined_status.splitlines():
            stripped = line.strip()
            if stripped.startswith("✓ Logged in to github.com account "):
                readiness["gh_auth_active_account"] = stripped.removeprefix("✓ Logged in to github.com account ").split(" ", 1)[0]
                break

    auth_env = os.environ.copy()
    auth_env.pop("GITHUB_TOKEN", None)
    auth_env.pop("GH_TOKEN", None)
    token_rc, token_stdout, _ = _run_command(["gh", "auth", "token"], extra_env=auth_env)
    if token_rc == 0 and token_stdout:
        readiness["gh_auth_token_exportable"] = True

    if readiness["env_token_looks_valid"]:
        readiness["preferred_search_mode"] = "env_token"
    elif readiness["gh_auth_token_exportable"]:
        readiness["preferred_search_mode"] = "gh_auth_token"
    elif readiness["gh_auth_logged_in"]:
        readiness["preferred_search_mode"] = "gh_session_fallback"

    return readiness


def _build_performance_status(*, summary_dir: Path, env_baseline_dir: Path) -> dict:
    latest_duration_compare, latest_duration_compare_path = _load_latest_summary(summary_dir, "duration_compare_*.json")
    latest_env_baseline, latest_env_baseline_path = _load_latest_summary(env_baseline_dir, "env_baseline_*.json")

    aggregate = latest_duration_compare.get("aggregate", {}) if latest_duration_compare else {}
    env_baseline_comparison = latest_duration_compare.get("environment_baseline", {}) if latest_duration_compare else {}
    env_aggregate = latest_env_baseline.get("aggregate", {}) if latest_env_baseline else {}

    return {
        "latest_env_baseline_snapshot_id": None if latest_env_baseline is None else latest_env_baseline.get("snapshot_id"),
        "latest_env_baseline_summary_json_path": None if latest_env_baseline_path is None else str(latest_env_baseline_path),
        "latest_env_baseline_mean_of_means_sec": env_aggregate.get("mean_of_means_sec"),
        "latest_duration_compare_id": None if latest_duration_compare_path is None else latest_duration_compare_path.stem,
        "latest_duration_compare_summary_json_path": None if latest_duration_compare_path is None else str(latest_duration_compare_path),
        "latest_duration_compare_common_average_delta_sec": aggregate.get("common_average_delta_sec"),
        "latest_duration_compare_env_adjusted_common_average_delta_sec": aggregate.get("env_adjusted_common_average_delta_sec"),
        "latest_duration_compare_baseline_batch_run_id": None if latest_duration_compare is None else latest_duration_compare.get("baseline_batch_run_id"),
        "latest_duration_compare_improved_batch_run_id": None if latest_duration_compare is None else latest_duration_compare.get("improved_batch_run_id"),
        "latest_duration_compare_env_baseline_snapshot_id": env_baseline_comparison.get("snapshot_id"),
    }


def build_roadmap_status_summary(
    *,
    repo_root: Path,
    formal_manifest_path: Path,
    challenge_manifest_path: Path,
    challenge_shortlist_path: Path,
    candidate_file: Path,
    frozen_manifest_glob: str,
    summary_dir: Path,
    env_baseline_dir: Path,
    tasks_dir: Path,
) -> dict:
    maturity_summary = build_benchmark_maturity_summary(
        repo_root=repo_root,
        formal_manifest_path=formal_manifest_path,
        challenge_manifest_path=challenge_manifest_path,
        candidate_file=candidate_file,
        summary_dir=summary_dir,
        frozen_manifest_glob=frozen_manifest_glob,
    )
    pipeline_summary = build_semi_real_pipeline_audit(
        repo_root=repo_root,
        candidate_file=candidate_file,
        tasks_dir=tasks_dir,
        formal_manifest_path=formal_manifest_path,
        challenge_manifest_path=challenge_manifest_path,
    )

    goal_gaps = maturity_summary["goal_gaps"]
    formal_manifest = maturity_summary["formal_manifest"]
    challenge_manifest = maturity_summary["challenge_manifest"]
    frozen_40_streak = maturity_summary["frozen_40_streak"]
    stage_counts = pipeline_summary["stage_counts"]
    shortlist_summary = summarize_challenge_shortlist(
        challenge_shortlist_path,
        repo_root=repo_root,
        challenge_manifest_path=challenge_manifest_path,
    ) if challenge_shortlist_path.exists() else {
        "candidate_issue_refs": [],
        "candidate_count": 0,
        "is_empty": True,
        "next_candidate": None,
        "filtered_existing_challenge_issue_refs": [],
    }

    next_challenge_action = _build_next_challenge_action(
        challenge_task_count=challenge_manifest["task_count"],
        shortlist_summary=shortlist_summary,
    )
    shortlist_screened_with_task_count = _count_shortlist_candidates_in_stage(
        shortlist_summary,
        pipeline_summary,
        stage="screened_with_task",
    )

    current_state = {
        "formal_task_count": formal_manifest["task_count"],
        "challenge_task_count": challenge_manifest["task_count"],
        "ecosystem_count": formal_manifest["ecosystem_count"],
        "candidate_count": pipeline_summary["candidate_count"],
        "accepted_candidate_count": pipeline_summary["candidate_status_counts"].get("accepted", 0),
        "screened_candidate_count": pipeline_summary["candidate_status_counts"].get("screened", 0),
        "screened_with_task_count": stage_counts.get("screened_with_task", 0),
        "imported_candidate_count": pipeline_summary["candidate_status_counts"].get("imported", 0),
        "blocked_candidate_count": pipeline_summary["candidate_status_counts"].get("blocked", 0),
        "formal_candidate_count": pipeline_summary["formal_candidate_count"],
        "challenge_candidate_count": pipeline_summary["challenge_candidate_count"],
        "latest_frozen_task_count": maturity_summary["frozen_manifests"]["latest_frozen_task_count"],
        "frozen_40_streak": frozen_40_streak["longest_streak_length"],
        "current_formal_policy_anchor": "improved_v69",
        "historical_stable_policy_anchor": "improved_v50",
    }
    performance_status = _build_performance_status(
        summary_dir=summary_dir,
        env_baseline_dir=env_baseline_dir,
    )
    challenge_local_auth_readiness = _build_challenge_local_auth_readiness()

    roadmap_focus = {
        "performance_track": {
            "status": "ongoing",
            "summary": "继续把 v68 -> v69 的性能回升与环境噪声区分开，当前 pytest compare 口径应视为 runtime-equivalent noise probe。",
        },
        "formal_expansion_track": {
            "status": "ongoing",
            "summary": "继续按并发与协程、文件路径与 IO、新生态控制流问题扩正式主集。",
        },
        "challenge_track": {
            "status": "started",
            "summary": (
                f"challenge manifest 已建立，当前已有 {challenge_manifest['task_count']} 条 challenge 题；"
                f"当前 shortlist 候选数为 {shortlist_summary['candidate_count']}，"
                f"下一步为：{next_challenge_action}。"
            ),
        },
    }

    return {
        "created_at": _utc_timestamp(),
        "objective": "将这个roadmap作为goal，持续追踪",
        "current_state": current_state,
        "goal_progress": {
            "formal_task_goal": goal_gaps["formal_task_goal"],
            "ecosystem_goal": goal_gaps["ecosystem_goal"],
            "frozen_goal": goal_gaps["frozen_goal"],
            "frozen_40_streak_goal": goal_gaps["frozen_40_streak_goal"],
        },
        "challenge_status": {
            "accepted_in_challenge_manifest_count": stage_counts.get("accepted_in_challenge_manifest", 0),
            "accepted_ready_not_in_any_manifest_count": stage_counts.get("accepted_ready_not_in_any_manifest", 0),
            "shortlist_candidate_count": shortlist_summary["candidate_count"],
            "shortlist_screened_with_task_count": shortlist_screened_with_task_count,
            "shortlist_is_empty": shortlist_summary["is_empty"],
            "next_candidate_issue_ref": None if shortlist_summary["next_candidate"] is None else shortlist_summary["next_candidate"]["issue_ref"],
            "next_action": next_challenge_action,
            "current_challenge_task_ids": [item["task_id"] for item in challenge_manifest["tasks"]],
            "local_auth_readiness": challenge_local_auth_readiness,
        },
        "performance_status": performance_status,
        "roadmap_focus": roadmap_focus,
        "maturity_summary": maturity_summary,
        "pipeline_summary": pipeline_summary,
    }


def build_roadmap_status_markdown(summary: dict) -> str:
    current_state = summary["current_state"]
    goal_progress = summary["goal_progress"]
    challenge_status = summary["challenge_status"]
    performance_status = summary.get("performance_status", {})
    roadmap_focus = summary["roadmap_focus"]

    return f"""# Roadmap Status Snapshot

## Current State

- formal_task_count: `{current_state["formal_task_count"]}`
- challenge_task_count: `{current_state["challenge_task_count"]}`
- ecosystem_count: `{current_state["ecosystem_count"]}`
- candidate_count: `{current_state["candidate_count"]}`
- accepted_candidate_count: `{current_state["accepted_candidate_count"]}`
- screened_candidate_count: `{current_state["screened_candidate_count"]}`
- screened_with_task_count: `{current_state["screened_with_task_count"]}`
- imported_candidate_count: `{current_state["imported_candidate_count"]}`
- blocked_candidate_count: `{current_state["blocked_candidate_count"]}`
- formal_candidate_count: `{current_state["formal_candidate_count"]}`
- challenge_candidate_count: `{current_state["challenge_candidate_count"]}`
- latest_frozen_task_count: `{current_state["latest_frozen_task_count"]}`
- frozen_40_streak: `{current_state["frozen_40_streak"]}`
- current_formal_policy_anchor: `{current_state["current_formal_policy_anchor"]}`
- historical_stable_policy_anchor: `{current_state["historical_stable_policy_anchor"]}`

## Goal Progress

- formal_task_goal: `{goal_progress["formal_task_goal"]["actual"]}` / `{goal_progress["formal_task_goal"]["target"]}` (met=`{goal_progress["formal_task_goal"]["met"]}`)
- ecosystem_goal: `{goal_progress["ecosystem_goal"]["actual"]}` / `{goal_progress["ecosystem_goal"]["target"]}` (met=`{goal_progress["ecosystem_goal"]["met"]}`)
- frozen_goal: `{goal_progress["frozen_goal"]["actual"]}` / `{goal_progress["frozen_goal"]["target"]}` (met=`{goal_progress["frozen_goal"]["met"]}`)
- frozen_40_streak_goal: `{goal_progress["frozen_40_streak_goal"]["actual"]}` / `{goal_progress["frozen_40_streak_goal"]["target"]}` (met=`{goal_progress["frozen_40_streak_goal"]["met"]}`)

## Challenge Status

- accepted_in_challenge_manifest_count: `{challenge_status["accepted_in_challenge_manifest_count"]}`
- accepted_ready_not_in_any_manifest_count: `{challenge_status["accepted_ready_not_in_any_manifest_count"]}`
- shortlist_candidate_count: `{challenge_status["shortlist_candidate_count"]}`
- shortlist_screened_with_task_count: `{challenge_status["shortlist_screened_with_task_count"]}`
- shortlist_is_empty: `{challenge_status["shortlist_is_empty"]}`
- next_candidate_issue_ref: `{challenge_status["next_candidate_issue_ref"]}`
- current_challenge_task_ids: `{challenge_status["current_challenge_task_ids"]}`
- next_action: `{challenge_status["next_action"]}`
- challenge_auth_env_token_present: `{challenge_status["local_auth_readiness"]["env_token_present"]}`
- challenge_auth_env_token_looks_valid: `{challenge_status["local_auth_readiness"]["env_token_looks_valid"]}`
- challenge_auth_gh_cli_available: `{challenge_status["local_auth_readiness"]["gh_cli_available"]}`
- challenge_auth_logged_in: `{challenge_status["local_auth_readiness"]["gh_auth_logged_in"]}`
- challenge_auth_active_account: `{challenge_status["local_auth_readiness"]["gh_auth_active_account"]}`
- challenge_auth_token_exportable: `{challenge_status["local_auth_readiness"]["gh_auth_token_exportable"]}`
- challenge_auth_preferred_search_mode: `{challenge_status["local_auth_readiness"]["preferred_search_mode"]}`

## Performance Status

- latest_env_baseline_snapshot_id: `{performance_status.get("latest_env_baseline_snapshot_id")}`
- latest_env_baseline_mean_of_means_sec: `{performance_status.get("latest_env_baseline_mean_of_means_sec")}`
- latest_duration_compare_id: `{performance_status.get("latest_duration_compare_id")}`
- latest_duration_compare_common_average_delta_sec: `{performance_status.get("latest_duration_compare_common_average_delta_sec")}`
- latest_duration_compare_env_adjusted_common_average_delta_sec: `{performance_status.get("latest_duration_compare_env_adjusted_common_average_delta_sec")}`

## Roadmap Focus

- performance_track: `{roadmap_focus["performance_track"]["status"]}` / {roadmap_focus["performance_track"]["summary"]}
- formal_expansion_track: `{roadmap_focus["formal_expansion_track"]["status"]}` / {roadmap_focus["formal_expansion_track"]["summary"]}
- challenge_track: `{roadmap_focus["challenge_track"]["status"]}` / {roadmap_focus["challenge_track"]["summary"]}
"""


def snapshot_roadmap_status(
    *,
    repo_root: Path = REPO_ROOT,
    formal_manifest: str | Path = "benchmarks/manifests/real_issue_tasks.json",
    challenge_manifest: str | Path = "benchmarks/manifests/real_issue_tasks_challenge_v1.json",
    challenge_shortlist: str | Path = "docs/challenge_shortlist.md",
    candidate_file: str | Path = "benchmarks/real_world_candidates.json",
    frozen_manifest_glob: str = "real_issue_tasks_frozen_*_v1.json",
    tasks_dir: str | Path = "benchmarks/tasks",
    output_dir: str | Path = "logs/summaries",
    env_baseline_dir: str | Path = "logs/env_baselines",
    run_label: str | None = None,
) -> dict:
    output_directory = (repo_root / output_dir).resolve() if not Path(output_dir).is_absolute() else Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    summary = build_roadmap_status_summary(
        repo_root=repo_root,
        formal_manifest_path=(repo_root / formal_manifest).resolve() if not Path(formal_manifest).is_absolute() else Path(formal_manifest).resolve(),
        challenge_manifest_path=(repo_root / challenge_manifest).resolve() if not Path(challenge_manifest).is_absolute() else Path(challenge_manifest).resolve(),
        challenge_shortlist_path=(repo_root / challenge_shortlist).resolve() if not Path(challenge_shortlist).is_absolute() else Path(challenge_shortlist).resolve(),
        candidate_file=(repo_root / candidate_file).resolve() if not Path(candidate_file).is_absolute() else Path(candidate_file).resolve(),
        frozen_manifest_glob=frozen_manifest_glob,
        summary_dir=output_directory,
        env_baseline_dir=(repo_root / env_baseline_dir).resolve() if not Path(env_baseline_dir).is_absolute() else Path(env_baseline_dir).resolve(),
        tasks_dir=(repo_root / tasks_dir).resolve() if not Path(tasks_dir).is_absolute() else Path(tasks_dir).resolve(),
    )

    snapshot_id = _next_snapshot_id(output_directory, run_label=run_label)
    summary["snapshot_id"] = snapshot_id
    summary_json_path = output_directory / f"{snapshot_id}.json"
    summary_md_path = output_directory / f"{snapshot_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_roadmap_status_markdown(summary))

    return {
        "snapshot_id": snapshot_id,
        "summary": summary,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成 roadmap 当前状态快照。")
    parser.add_argument("--formal-manifest", default="benchmarks/manifests/real_issue_tasks.json", help="正式主集 manifest 路径")
    parser.add_argument("--challenge-manifest", default="benchmarks/manifests/real_issue_tasks_challenge_v1.json", help="challenge manifest 路径")
    parser.add_argument("--challenge-shortlist", default="docs/challenge_shortlist.md", help="challenge shortlist 路径")
    parser.add_argument("--candidate-file", default="benchmarks/real_world_candidates.json", help="候选池文件路径")
    parser.add_argument("--frozen-manifest-glob", default="real_issue_tasks_frozen_*_v1.json", help="冻结 manifest 的 glob 模式")
    parser.add_argument("--tasks-dir", default="benchmarks/tasks", help="任务目录")
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--env-baseline-dir", default="logs/env_baselines", help="环境基线目录")
    parser.add_argument("--run-label", default=None, help="可选标签，例如 roadmap")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = snapshot_roadmap_status(
        repo_root=REPO_ROOT,
        formal_manifest=args.formal_manifest,
        challenge_manifest=args.challenge_manifest,
        challenge_shortlist=args.challenge_shortlist,
        candidate_file=args.candidate_file,
        frozen_manifest_glob=args.frozen_manifest_glob,
        tasks_dir=args.tasks_dir,
        output_dir=args.output_dir,
        env_baseline_dir=args.env_baseline_dir,
        run_label=args.run_label,
    )
    summary = output["summary"]
    print(f"snapshot_id: {output['snapshot_id']}")
    print(f"formal_task_count: {summary['current_state']['formal_task_count']}")
    print(f"challenge_task_count: {summary['current_state']['challenge_task_count']}")
    print(f"ecosystem_count: {summary['current_state']['ecosystem_count']}")
    print(f"frozen_40_streak: {summary['current_state']['frozen_40_streak']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
