"""Phase 4 的批量任务运行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.batch_runner import load_task_paths, run_batch


def build_parser() -> argparse.ArgumentParser:
    # 第一版批量入口优先服务本地 benchmark 目录与 manifest。
    parser = argparse.ArgumentParser(description="运行一组任务的批量 patch 闭环。")
    parser.add_argument(
        "--tasks-dir",
        default="benchmarks/tasks",
        help="任务目录，默认使用 benchmarks/tasks",
    )
    parser.add_argument(
        "--manifest",
        default="benchmarks/manifests/dev_tasks.json",
        help="任务清单文件，默认使用 benchmarks/manifests/dev_tasks.json",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="策略配置文件路径，例如 optimization/policy_versions/baseline.json",
    )
    parser.add_argument(
        "--run-label",
        default=None,
        help="可选的批量运行标签，例如 baseline 或 improved",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest_path = REPO_ROOT / args.manifest
    task_paths = load_task_paths(
        tasks_dir=REPO_ROOT / args.tasks_dir,
        manifest_path=manifest_path if manifest_path.exists() else None,
    )
    batch_output = run_batch(
        repo_root=REPO_ROOT,
        task_paths=task_paths,
        policy_path=REPO_ROOT / args.policy if args.policy else None,
        run_label=args.run_label,
    )
    batch_summary = batch_output["batch_summary"]

    print("=== Batch Run Summary ===")
    print(f"batch_run_id: {batch_summary['batch_run_id']}")
    print(f"task_count: {batch_summary['task_count']}")
    print(f"success_count: {batch_summary['success_count']}")
    print(f"success_rate: {batch_summary['success_rate']}")
    print(f"summary_json_path: {batch_output['summary_json_path']}")
    print(f"summary_md_path: {batch_output['summary_md_path']}")
    print("phase_status: Phase 4 batch run complete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
