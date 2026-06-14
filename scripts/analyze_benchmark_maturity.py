"""审计 Benchmark Maturity v1 目标当前完成度。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.logger import write_json, write_text


TARGET_FORMAL_TASK_COUNT = 60
TARGET_ECOSYSTEM_COUNT = 6
TARGET_FROZEN_COUNT = 40
TARGET_STREAK = 5
MIN_SUCCESS_RATE = 0.95
MIN_TEST_PASS_RATE = 0.95
MAX_DURATION_GROWTH_RATIO = 0.03
BASELINE_POLICY_ID = "improved_v32"


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _next_summary_id(summary_dir: Path, run_label: str | None = None) -> str:
    existing_numbers: list[int] = []
    prefix = f"benchmark_maturity_{run_label}_" if run_label else "benchmark_maturity_"
    for path in summary_dir.glob(f"{prefix}*.json"):
        suffix = path.stem.removeprefix(prefix)
        if suffix.isdigit():
            existing_numbers.append(int(suffix))
    next_number = max(existing_numbers, default=0) + 1
    if run_label:
        return f"{prefix}{next_number:03d}"
    return f"benchmark_maturity_{next_number:03d}"


def _parse_policy_version(policy_id: str) -> int | None:
    match = re.fullmatch(r"improved_v(\d+)", policy_id.strip())
    if match is None:
        return None
    return int(match.group(1))


def _canonical_repo_name(task_payload: dict) -> str:
    metadata = task_payload.get("metadata", {})
    repo_full_name = metadata.get("repo_full_name")
    if isinstance(repo_full_name, str) and repo_full_name.strip():
        return repo_full_name.strip()
    repo_url = metadata.get("repo_url")
    if isinstance(repo_url, str) and "github.com/" in repo_url:
        return repo_url.rstrip("/").split("github.com/", 1)[1]
    return str(task_payload.get("repo_name", "unknown")).strip()


def load_manifest_task_paths(
    *,
    repo_root: Path,
    manifest_path: Path,
) -> list[Path]:
    if not manifest_path.exists():
        return []
    manifest_payload = _load_json(manifest_path)
    return [(repo_root / task_path).resolve() for task_path in manifest_payload.get("tasks", [])]


def summarize_task_manifest(task_paths: list[Path]) -> dict:
    source_type_counts: dict[str, int] = {}
    ecosystem_counts: dict[str, int] = {}
    task_details: list[dict] = []

    for task_path in task_paths:
        payload = _load_json(task_path)
        source_type = str(payload.get("source_type", "unknown"))
        source_type_counts[source_type] = source_type_counts.get(source_type, 0) + 1

        repo_name = _canonical_repo_name(payload)
        ecosystem_counts[repo_name] = ecosystem_counts.get(repo_name, 0) + 1
        task_details.append(
            {
                "task_id": payload.get("task_id"),
                "repo_full_name": repo_name,
                "source_type": source_type,
                "issue_title": payload.get("issue_title"),
            }
        )

    return {
        "task_count": len(task_paths),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "ecosystem_count": len(ecosystem_counts),
        "ecosystem_counts": dict(sorted(ecosystem_counts.items())),
        "tasks": task_details,
    }


def summarize_candidate_dataset(candidate_file: Path) -> dict:
    dataset = _load_json(candidate_file)
    status_counts: dict[str, int] = {}
    repo_counts: dict[str, int] = {}

    for candidate in dataset.get("candidates", []):
        status = str(candidate.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1

        repo_name = str(candidate.get("repo_full_name", "unknown")).strip()
        repo_counts[repo_name] = repo_counts.get(repo_name, 0) + 1

    return {
        "candidate_count": len(dataset.get("candidates", [])),
        "status_counts": dict(sorted(status_counts.items())),
        "repo_counts": dict(sorted(repo_counts.items())),
    }


def summarize_frozen_manifests(manifest_paths: list[Path]) -> dict:
    frozen_sets: list[dict] = []

    for manifest_path in sorted(manifest_paths):
        payload = _load_json(manifest_path)
        task_count = len(payload.get("tasks", []))
        frozen_sets.append(
            {
                "manifest_id": payload.get("manifest_id", manifest_path.stem),
                "path": str(manifest_path),
                "task_count": task_count,
            }
        )

    latest_frozen = max(frozen_sets, key=lambda item: item["task_count"], default=None)
    return {
        "frozen_sets": frozen_sets,
        "latest_frozen_task_count": latest_frozen["task_count"] if latest_frozen else 0,
        "latest_frozen_manifest": latest_frozen,
    }


def load_frozen_eval_records(summary_dir: Path) -> dict[int, dict[int, dict]]:
    records: dict[int, dict[int, dict]] = {}
    pattern = re.compile(r"batch_eval_frozen(?P<frozen_count>\d+)v(?P<policy_version>\d+)_(?P<run>\d+)\.json$")

    for path in summary_dir.glob("batch_eval_frozen*.json"):
        match = pattern.fullmatch(path.name)
        if match is None:
            continue

        payload = _load_json(path)
        metrics = payload.get("metrics", {})
        frozen_count = int(match.group("frozen_count"))
        policy_id = str(payload.get("policy_id", "")).strip() or f"improved_v{match.group('policy_version')}"
        policy_version = _parse_policy_version(policy_id)
        if policy_version is None:
            continue

        existing = records.setdefault(frozen_count, {}).get(policy_version)
        candidate_record = {
            "policy_id": policy_id,
            "policy_version": policy_version,
            "path": str(path),
            "success_rate": float(metrics.get("success_rate", 0.0)),
            "test_pass_rate": float(metrics.get("test_pass_rate", 0.0)),
            "average_duration_sec": float(metrics.get("average_duration_sec", 0.0)),
        }
        # 同版本若有多次运行，优先保留最新编号的文件。
        if existing is None or path.name > Path(existing["path"]).name:
            records[frozen_count][policy_version] = candidate_record

    return records


def evaluate_frozen_streak(
    *,
    eval_records: dict[int, dict[int, dict]],
    frozen_count: int,
    baseline_policy_id: str = BASELINE_POLICY_ID,
) -> dict:
    frozen_records = eval_records.get(frozen_count, {})
    baseline_version = _parse_policy_version(baseline_policy_id)
    if baseline_version is None:
        raise ValueError(f"无法解析 baseline policy：{baseline_policy_id}")

    if not frozen_records:
        return {
            "frozen_count": frozen_count,
            "baseline_policy_id": baseline_policy_id,
            "baseline_eval_present": False,
            "meets_target": False,
            "reason": f"当前没有 frozen_{frozen_count} 的评测结果。",
            "qualifying_versions": [],
            "longest_streak_versions": [],
            "longest_streak_length": 0,
        }

    baseline_record = frozen_records.get(baseline_version)
    if baseline_record is None:
        return {
            "frozen_count": frozen_count,
            "baseline_policy_id": baseline_policy_id,
            "baseline_eval_present": False,
            "meets_target": False,
            "reason": f"缺少 frozen_{frozen_count} 上的 {baseline_policy_id} 基线结果。",
            "qualifying_versions": [],
            "longest_streak_versions": [],
            "longest_streak_length": 0,
        }

    duration_threshold = baseline_record["average_duration_sec"] * (1 + MAX_DURATION_GROWTH_RATIO)
    qualifying_versions: list[int] = []
    for version in sorted(frozen_records):
        record = frozen_records[version]
        if (
            record["success_rate"] >= MIN_SUCCESS_RATE
            and record["test_pass_rate"] >= MIN_TEST_PASS_RATE
            and record["average_duration_sec"] <= duration_threshold
        ):
            qualifying_versions.append(version)

    longest_streak_versions: list[int] = []
    current_streak: list[int] = []
    for version in qualifying_versions:
        if not current_streak or version == current_streak[-1] + 1:
            current_streak.append(version)
        else:
            if len(current_streak) > len(longest_streak_versions):
                longest_streak_versions = current_streak[:]
            current_streak = [version]
    if len(current_streak) > len(longest_streak_versions):
        longest_streak_versions = current_streak[:]

    return {
        "frozen_count": frozen_count,
        "baseline_policy_id": baseline_policy_id,
        "baseline_eval_present": True,
        "baseline_average_duration_sec": baseline_record["average_duration_sec"],
        "duration_threshold_sec": round(duration_threshold, 4),
        "qualifying_versions": qualifying_versions,
        "longest_streak_versions": longest_streak_versions,
        "longest_streak_length": len(longest_streak_versions),
        "meets_target": len(longest_streak_versions) >= TARGET_STREAK,
        "reason": (
            "已满足连续版本要求。"
            if len(longest_streak_versions) >= TARGET_STREAK
            else f"当前最长连续版本仅有 {len(longest_streak_versions)} 个。"
        ),
    }


def build_gap_summary(
    *,
    formal_summary: dict,
    frozen_summary: dict,
    frozen_40_streak: dict,
) -> dict:
    formal_gap = max(TARGET_FORMAL_TASK_COUNT - formal_summary["task_count"], 0)
    ecosystem_gap = max(TARGET_ECOSYSTEM_COUNT - formal_summary["ecosystem_count"], 0)
    frozen_gap = max(TARGET_FROZEN_COUNT - frozen_summary["latest_frozen_task_count"], 0)
    streak_gap = max(TARGET_STREAK - frozen_40_streak["longest_streak_length"], 0)

    return {
        "formal_task_goal": {
            "target": TARGET_FORMAL_TASK_COUNT,
            "actual": formal_summary["task_count"],
            "gap": formal_gap,
            "met": formal_gap == 0,
        },
        "ecosystem_goal": {
            "target": TARGET_ECOSYSTEM_COUNT,
            "actual": formal_summary["ecosystem_count"],
            "gap": ecosystem_gap,
            "met": ecosystem_gap == 0,
        },
        "frozen_goal": {
            "target": TARGET_FROZEN_COUNT,
            "actual": frozen_summary["latest_frozen_task_count"],
            "gap": frozen_gap,
            "met": frozen_gap == 0,
        },
        "frozen_40_streak_goal": {
            "target": TARGET_STREAK,
            "actual": frozen_40_streak["longest_streak_length"],
            "gap": streak_gap,
            "met": streak_gap == 0,
        },
    }


def build_benchmark_maturity_summary(
    *,
    repo_root: Path,
    formal_manifest_path: Path,
    challenge_manifest_path: Path | None,
    candidate_file: Path,
    frozen_manifest_glob: str,
    summary_dir: Path,
) -> dict:
    formal_task_paths = load_manifest_task_paths(repo_root=repo_root, manifest_path=formal_manifest_path)
    formal_summary = summarize_task_manifest(formal_task_paths)
    challenge_task_paths = (
        []
        if challenge_manifest_path is None
        else load_manifest_task_paths(repo_root=repo_root, manifest_path=challenge_manifest_path)
    )
    challenge_summary = summarize_task_manifest(challenge_task_paths)
    candidate_summary = summarize_candidate_dataset(candidate_file)
    frozen_manifest_paths = sorted((repo_root / "benchmarks" / "manifests").glob(frozen_manifest_glob))
    frozen_summary = summarize_frozen_manifests(frozen_manifest_paths)
    frozen_eval_records = load_frozen_eval_records(summary_dir)
    frozen_40_streak = evaluate_frozen_streak(eval_records=frozen_eval_records, frozen_count=40)

    return {
        "created_at": _utc_timestamp(),
        "objective": {
            "formal_task_target": TARGET_FORMAL_TASK_COUNT,
            "ecosystem_target": TARGET_ECOSYSTEM_COUNT,
            "frozen_target": TARGET_FROZEN_COUNT,
            "frozen_streak_target": TARGET_STREAK,
            "minimum_success_rate": MIN_SUCCESS_RATE,
            "minimum_test_pass_rate": MIN_TEST_PASS_RATE,
            "max_duration_growth_ratio": MAX_DURATION_GROWTH_RATIO,
            "baseline_policy_id": BASELINE_POLICY_ID,
        },
        "formal_manifest": {
            "path": str(formal_manifest_path),
            **formal_summary,
        },
        "challenge_manifest": {
            "path": None if challenge_manifest_path is None else str(challenge_manifest_path),
            **challenge_summary,
        },
        "candidate_dataset": {
            "path": str(candidate_file),
            **candidate_summary,
        },
        "frozen_manifests": frozen_summary,
        "frozen_eval_records": {
            str(frozen_count): {
                str(policy_version): record
                for policy_version, record in sorted(policy_records.items())
            }
            for frozen_count, policy_records in sorted(frozen_eval_records.items())
        },
        "frozen_40_streak": frozen_40_streak,
        "goal_gaps": build_gap_summary(
            formal_summary=formal_summary,
            frozen_summary=frozen_summary,
            frozen_40_streak=frozen_40_streak,
        ),
    }


def build_benchmark_maturity_markdown(summary: dict) -> str:
    formal_manifest = summary["formal_manifest"]
    challenge_manifest = summary["challenge_manifest"]
    frozen_manifests = summary["frozen_manifests"]
    frozen_40_streak = summary["frozen_40_streak"]
    goal_gaps = summary["goal_gaps"]

    ecosystems = "\n".join(
        f"- `{repo_name}`: `{count}`"
        for repo_name, count in formal_manifest["ecosystem_counts"].items()
    ) or "- 当前没有正式任务"

    frozen_sets = "\n".join(
        f"- `{item['manifest_id']}`: `{item['task_count']}` 条"
        for item in frozen_manifests["frozen_sets"]
    ) or "- 当前没有 frozen manifest"
    challenge_tasks = "\n".join(
        f"- `{item['task_id']}`: `{item['repo_full_name']}` / `{item['issue_title']}`"
        for item in challenge_manifest["tasks"]
    ) or "- 当前没有 challenge 任务"

    return f"""# Benchmark Maturity Audit

## Snapshot

- created_at: `{summary["created_at"]}`
- formal_manifest: `{formal_manifest["path"]}`
- candidate_dataset: `{summary["candidate_dataset"]["path"]}`

## Goal Gaps

- formal_task_count: `{goal_gaps["formal_task_goal"]["actual"]}` / `{goal_gaps["formal_task_goal"]["target"]}` (gap: `{goal_gaps["formal_task_goal"]["gap"]}`)
- ecosystem_count: `{goal_gaps["ecosystem_goal"]["actual"]}` / `{goal_gaps["ecosystem_goal"]["target"]}` (gap: `{goal_gaps["ecosystem_goal"]["gap"]}`)
- latest_frozen_count: `{goal_gaps["frozen_goal"]["actual"]}` / `{goal_gaps["frozen_goal"]["target"]}` (gap: `{goal_gaps["frozen_goal"]["gap"]}`)
- frozen_40_streak: `{goal_gaps["frozen_40_streak_goal"]["actual"]}` / `{goal_gaps["frozen_40_streak_goal"]["target"]}` (gap: `{goal_gaps["frozen_40_streak_goal"]["gap"]}`)

## Formal Task Set

- task_count: `{formal_manifest["task_count"]}`
- source_type_counts: `{formal_manifest["source_type_counts"]}`
- ecosystem_count: `{formal_manifest["ecosystem_count"]}`

### Ecosystems

{ecosystems}

## Challenge Task Set

- challenge_manifest: `{challenge_manifest["path"]}`
- task_count: `{challenge_manifest["task_count"]}`
- source_type_counts: `{challenge_manifest["source_type_counts"]}`
- ecosystem_count: `{challenge_manifest["ecosystem_count"]}`

### Challenge Tasks

{challenge_tasks}

## Frozen Manifests

- latest_frozen_task_count: `{frozen_manifests["latest_frozen_task_count"]}`

### Available Frozen Sets

{frozen_sets}

## Frozen 40 Streak

- baseline_policy_id: `{frozen_40_streak["baseline_policy_id"]}`
- baseline_eval_present: `{frozen_40_streak["baseline_eval_present"]}`
- longest_streak_length: `{frozen_40_streak["longest_streak_length"]}`
- longest_streak_versions: `{frozen_40_streak["longest_streak_versions"]}`
- qualifying_versions: `{frozen_40_streak["qualifying_versions"]}`
- reason: `{frozen_40_streak["reason"]}`
"""


def analyze_benchmark_maturity(
    *,
    repo_root: Path = REPO_ROOT,
    formal_manifest: str | Path = "benchmarks/manifests/real_issue_tasks.json",
    challenge_manifest: str | Path = "benchmarks/manifests/real_issue_tasks_challenge_v1.json",
    candidate_file: str | Path = "benchmarks/real_world_candidates.json",
    frozen_manifest_glob: str = "real_issue_tasks_frozen_*_v1.json",
    output_dir: str | Path = "logs/summaries",
    run_label: str | None = None,
) -> dict:
    output_directory = (repo_root / output_dir).resolve() if not Path(output_dir).is_absolute() else Path(output_dir).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    summary = build_benchmark_maturity_summary(
        repo_root=repo_root,
        formal_manifest_path=(repo_root / formal_manifest).resolve()
        if not Path(formal_manifest).is_absolute()
        else Path(formal_manifest).resolve(),
        challenge_manifest_path=(repo_root / challenge_manifest).resolve()
        if not Path(challenge_manifest).is_absolute()
        else Path(challenge_manifest).resolve(),
        candidate_file=(repo_root / candidate_file).resolve()
        if not Path(candidate_file).is_absolute()
        else Path(candidate_file).resolve(),
        frozen_manifest_glob=frozen_manifest_glob,
        summary_dir=output_directory,
    )
    audit_id = _next_summary_id(output_directory, run_label=run_label)
    summary["audit_id"] = audit_id

    summary_json_path = output_directory / f"{audit_id}.json"
    summary_md_path = output_directory / f"{audit_id}.md"
    write_json(summary_json_path, summary)
    write_text(summary_md_path, build_benchmark_maturity_markdown(summary))

    return {
        "audit_id": audit_id,
        "summary_json_path": str(summary_json_path),
        "summary_md_path": str(summary_md_path),
        "summary": summary,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计 Benchmark Maturity v1 目标当前完成度。")
    parser.add_argument(
        "--formal-manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="正式真实任务 manifest 路径",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="候选数据集路径",
    )
    parser.add_argument(
        "--challenge-manifest",
        default="benchmarks/manifests/real_issue_tasks_challenge_v1.json",
        help="challenge 任务 manifest 路径",
    )
    parser.add_argument(
        "--frozen-manifest-glob",
        default="real_issue_tasks_frozen_*_v1.json",
        help="冻结 manifest 的 glob 模式",
    )
    parser.add_argument("--output-dir", default="logs/summaries", help="输出目录")
    parser.add_argument("--run-label", default=None, help="可选标签，例如 maturity")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = analyze_benchmark_maturity(
        repo_root=REPO_ROOT,
        formal_manifest=args.formal_manifest,
        challenge_manifest=args.challenge_manifest,
        candidate_file=args.candidate_file,
        frozen_manifest_glob=args.frozen_manifest_glob,
        output_dir=args.output_dir,
        run_label=args.run_label,
    )
    summary = output["summary"]
    goal_gaps = summary["goal_gaps"]
    print("=== Benchmark Maturity Audit Summary ===")
    print(f"audit_id: {output['audit_id']}")
    print(f"formal_task_count: {goal_gaps['formal_task_goal']['actual']}")
    print(f"challenge_task_count: {summary['challenge_manifest']['task_count']}")
    print(f"ecosystem_count: {goal_gaps['ecosystem_goal']['actual']}")
    print(f"latest_frozen_count: {goal_gaps['frozen_goal']['actual']}")
    print(f"frozen_40_streak: {goal_gaps['frozen_40_streak_goal']['actual']}")
    print(f"summary_json_path: {output['summary_json_path']}")
    print(f"summary_md_path: {output['summary_md_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
