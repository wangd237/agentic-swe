"""运行真实 issue 任务集的批量评测流水线。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.batch_runner import load_task_paths, run_batch
from evals.batch_eval import run_batch_eval
from evals.compare_evals import compare_eval_summaries
from scripts.analyze_benchmark_maturity import analyze_benchmark_maturity
from scripts.stability_recheck import run_stability_recheck


def load_candidate_dataset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_candidate_by_issue(dataset: dict, repo_full_name: str, issue_number: int) -> dict | None:
    for candidate in dataset.get("candidates", []):
        if (
            candidate.get("repo_full_name") == repo_full_name
            and candidate.get("issue_number") == issue_number
        ):
            return candidate
    return None


def summarize_candidate_statuses(
    dataset: dict,
    *,
    completed_candidate_ids: set[str] | None = None,
) -> dict[str, int]:
    completed_candidate_ids = completed_candidate_ids or set()
    summary: dict[str, int] = {}
    for candidate in dataset.get("candidates", []):
        status = candidate.get("status", "unknown")
        if (
            status == "accepted"
            and candidate.get("candidate_id") in completed_candidate_ids
        ):
            status = "completed"
        summary[status] = summary.get(status, 0) + 1
    return dict(sorted(summary.items()))


def collect_completed_candidate_ids(task_paths: list[Path], batch_output: dict) -> set[str]:
    batch_tasks = batch_output.get("batch_summary", {}).get("tasks", [])
    success_task_ids = {
        item["task_id"]
        for item in batch_tasks
        if item.get("final_status") == "success"
    }
    completed_candidate_ids: set[str] = set()
    for task_path in task_paths:
        payload = json.loads(task_path.read_text(encoding="utf-8"))
        if payload.get("task_id") not in success_task_ids:
            continue
        candidate_id = payload.get("metadata", {}).get("candidate_id")
        if candidate_id:
            completed_candidate_ids.add(candidate_id)
    return completed_candidate_ids


def summarize_manifest_tasks(task_paths: list[Path]) -> dict[str, int]:
    total = len(task_paths)
    semi_real_count = 0
    real_issue_count = 0
    synthetic_count = 0

    for task_path in task_paths:
        payload = json.loads(task_path.read_text(encoding="utf-8"))
        source_type = payload.get("source_type")
        if source_type == "semi_real":
            semi_real_count += 1
        elif source_type == "real_issue":
            real_issue_count += 1
        elif source_type == "synthetic":
            synthetic_count += 1

    return {
        "task_count": total,
        "semi_real_count": semi_real_count,
        "real_issue_count": real_issue_count,
        "synthetic_count": synthetic_count,
    }


def infer_eval_prefix_from_manifest(manifest_path: Path) -> str | None:
    # 目前先对 frozen manifest 做自动前缀推断，满足 B2 默认场景。
    match = re.search(r"frozen_(\d+)", manifest_path.stem)
    if match is None:
        return None
    return f"batch_eval_frozen{match.group(1)}"


def find_latest_eval_for_policy(
    *,
    summary_dir: Path,
    eval_prefix: str | None,
    policy_id: str | None,
) -> Path | None:
    if eval_prefix is None or not policy_id:
        return None

    matched_paths: list[Path] = []
    for path in summary_dir.glob(f"{eval_prefix}*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("policy_id") == policy_id:
            matched_paths.append(path)

    if not matched_paths:
        return None
    return sorted(matched_paths, key=lambda item: item.name)[-1]


def build_maturity_headline(maturity_output: dict) -> str:
    summary = maturity_output["summary"]
    goal_gaps = summary["goal_gaps"]

    formal_actual = goal_gaps["formal_task_goal"]["actual"]
    formal_target = goal_gaps["formal_task_goal"]["target"]
    challenge_actual = int(summary.get("challenge_manifest", {}).get("task_count", 0))
    eco_actual = goal_gaps["ecosystem_goal"]["actual"]
    eco_target = goal_gaps["ecosystem_goal"]["target"]
    frozen_actual = goal_gaps["frozen_goal"]["actual"]
    frozen_target = goal_gaps["frozen_goal"]["target"]
    streak_actual = goal_gaps["frozen_40_streak_goal"]["actual"]
    streak_target = goal_gaps["frozen_40_streak_goal"]["target"]

    all_met = all(
        item["met"]
        for item in (
            goal_gaps["formal_task_goal"],
            goal_gaps["ecosystem_goal"],
            goal_gaps["frozen_goal"],
            goal_gaps["frozen_40_streak_goal"],
        )
    )
    # Windows 默认 gbk 终端不稳定支持 Unicode 勾叉，这里统一降级成 ASCII。
    status = "OK" if all_met else "FAIL"
    return (
        f"maturity: formal={formal_actual}/{formal_target} "
        f"challenge={challenge_actual} "
        f"eco={eco_actual}/{eco_target} "
        f"frozen={frozen_actual}/{frozen_target} "
        f"streak={streak_actual}/{streak_target} {status}"
    )


def run_real_issue_eval_pipeline(
    *,
    repo_root: Path,
    manifest_path: Path,
    tasks_dir: Path,
    candidate_file: Path,
    policy_path: Path,
    run_label: str,
    compare_against_eval: Path | None = None,
    compare_label: str | None = None,
    stability_check: bool = False,
    stability_repetitions: int = 3,
    stability_manifest_path: Path | None = None,
    maturity_formal_manifest_path: Path | None = None,
) -> dict:
    summaries_dir = repo_root / "logs" / "summaries"
    task_paths = load_task_paths(tasks_dir=tasks_dir, manifest_path=manifest_path)
    batch_output = run_batch(
        repo_root=repo_root,
        task_paths=task_paths,
        policy_path=policy_path,
        run_label=run_label,
    )
    batch_summary_path = Path(batch_output["summary_json_path"])

    eval_output = run_batch_eval(
        batch_summary_path=batch_summary_path,
        output_dir=repo_root / "logs" / "summaries",
        run_label=run_label,
    )

    compare_output = None
    if compare_against_eval is not None:
        compare_output = compare_eval_summaries(
            baseline_eval_path=compare_against_eval,
            improved_eval_path=eval_output["summary_json_path"],
            output_dir=repo_root / "logs" / "summaries",
            run_label=compare_label or run_label,
        )

    stability_output = None
    stability_warning = None
    if stability_check:
        effective_stability_manifest = stability_manifest_path or manifest_path
        previous_eval_path = find_latest_eval_for_policy(
            summary_dir=summaries_dir,
            eval_prefix=infer_eval_prefix_from_manifest(effective_stability_manifest),
            policy_id=eval_output["eval_summary"].get("policy_id"),
        )
        stability_output = run_stability_recheck(
            repo_root=repo_root,
            manifest_path=effective_stability_manifest,
            tasks_dir=tasks_dir,
            policy_path=policy_path,
            repetitions=stability_repetitions,
            output_dir=summaries_dir,
            run_label=f"{run_label}_stability",
            baseline_eval_path=previous_eval_path,
        )
        band_check = stability_output["summary"].get("baseline_stability_band_check")
        if band_check is not None and not band_check["within_band"]:
            stability_warning = (
                "previous_eval_outside_stability_band: "
                f"{band_check['baseline_average_duration_sec']} not in "
                f"[{band_check['lower_bound_sec']}, {band_check['upper_bound_sec']}]"
            )

    maturity_output = analyze_benchmark_maturity(
        repo_root=repo_root,
        formal_manifest=(
            maturity_formal_manifest_path
            if maturity_formal_manifest_path is not None
            else repo_root / "benchmarks" / "manifests" / "real_issue_tasks.json"
        ),
        output_dir=summaries_dir,
        run_label="maturity",
    )

    candidate_dataset = load_candidate_dataset(candidate_file)
    completed_candidate_ids = collect_completed_candidate_ids(task_paths, batch_output)
    return {
        "task_summary": summarize_manifest_tasks(task_paths),
        "candidate_status_summary": summarize_candidate_statuses(
            candidate_dataset,
            completed_candidate_ids=completed_candidate_ids,
        ),
        "batch_output": batch_output,
        "eval_output": eval_output,
        "compare_output": compare_output,
        "stability_output": stability_output,
        "stability_warning": stability_warning,
        "maturity_output": maturity_output,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行真实 issue 任务集的 batch/eval/compare 流水线。")
    parser.add_argument(
        "--manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="真实 issue 任务清单路径",
    )
    parser.add_argument(
        "--tasks-dir",
        default="benchmarks/tasks",
        help="任务目录路径",
    )
    parser.add_argument(
        "--candidate-file",
        default="benchmarks/real_world_candidates.json",
        help="真实 issue 候选清单路径",
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="本次运行使用的策略文件路径",
    )
    parser.add_argument(
        "--run-label",
        required=True,
        help="本次真实 issue 流水线使用的 run label，例如 realissuev8",
    )
    parser.add_argument(
        "--compare-against-eval",
        default=None,
        help="可选：用于 compare 的 baseline eval JSON 路径",
    )
    parser.add_argument(
        "--compare-label",
        default=None,
        help="可选：compare 报告标签，默认复用 run-label",
    )
    parser.add_argument(
        "--stability-check",
        action="store_true",
        help="完成主评测后，额外执行同版复跑稳定性验证",
    )
    parser.add_argument(
        "--stability-repetitions",
        type=int,
        default=3,
        help="稳定性复跑次数，默认 3",
    )
    parser.add_argument(
        "--stability-manifest",
        default="benchmarks/manifests/real_issue_tasks_frozen_40_v1.json",
        help="稳定性验证使用的 manifest，默认 frozen_40",
    )
    parser.add_argument(
        "--maturity-formal-manifest",
        default="benchmarks/manifests/real_issue_tasks.json",
        help="maturity 审计使用的正式任务 manifest，默认正式主集",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    pipeline_output = run_real_issue_eval_pipeline(
        repo_root=REPO_ROOT,
        manifest_path=(REPO_ROOT / args.manifest).resolve(),
        tasks_dir=(REPO_ROOT / args.tasks_dir).resolve(),
        candidate_file=(REPO_ROOT / args.candidate_file).resolve(),
        policy_path=(REPO_ROOT / args.policy).resolve(),
        run_label=args.run_label,
        compare_against_eval=(
            (REPO_ROOT / args.compare_against_eval).resolve()
            if args.compare_against_eval
            else None
        ),
        compare_label=args.compare_label,
        stability_check=args.stability_check,
        stability_repetitions=args.stability_repetitions,
        stability_manifest_path=(
            (REPO_ROOT / args.stability_manifest).resolve()
            if args.stability_manifest
            else None
        ),
        maturity_formal_manifest_path=(
            (REPO_ROOT / args.maturity_formal_manifest).resolve()
            if args.maturity_formal_manifest
            else None
        ),
    )

    print("=== Real Issue Eval Pipeline Summary ===")
    print(f"manifest_task_count: {pipeline_output['task_summary']['task_count']}")
    print(f"semi_real_count: {pipeline_output['task_summary']['semi_real_count']}")
    print(f"candidate_status_summary: {pipeline_output['candidate_status_summary']}")
    print(f"batch_summary_json_path: {pipeline_output['batch_output']['summary_json_path']}")
    print(f"eval_summary_json_path: {pipeline_output['eval_output']['summary_json_path']}")
    if pipeline_output["compare_output"] is not None:
        print(f"compare_summary_json_path: {pipeline_output['compare_output']['summary_json_path']}")
        print(f"compare_id: {pipeline_output['compare_output']['compare_id']}")
    else:
        print("compare_summary_json_path: None")
    if pipeline_output["stability_output"] is not None:
        stability_summary = pipeline_output["stability_output"]["summary"]
        print(f"stability_summary_json_path: {pipeline_output['stability_output']['summary_json_path']}")
        print(
            "stability_check: "
            f"enabled=True repetitions={stability_summary['repetitions']} "
            f"conclusion={stability_summary['conclusion']} "
            f"mean={stability_summary['aggregate']['average_duration_mean_sec']} "
            f"std={stability_summary['aggregate']['average_duration_std_sec']} "
            f"outlier_count={stability_summary['outlier_count']} "
            f"functional_consistent={stability_summary['functional_consistency']['functional_consistent']}"
        )
        if pipeline_output["stability_warning"] is not None:
            print(f"stability_warning: {pipeline_output['stability_warning']}")
    else:
        print("stability_summary_json_path: None")
    print(build_maturity_headline(pipeline_output["maturity_output"]))
    print(f"maturity_summary_json_path: {pipeline_output['maturity_output']['summary_json_path']}")
    print("phase_status: Phase 6 real issue eval pipeline complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
