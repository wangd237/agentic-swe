"""Phase 3 的单任务 patch 闭环入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# 这里手动把仓库根目录加入导入路径，保证直接运行脚本时也能找到 app 包。
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.executor import run_agent


def build_parser() -> argparse.ArgumentParser:
    # 当前入口脚本执行 patch 闭环，并把产物落到 logs/trajectories 下。
    parser = argparse.ArgumentParser(description="运行单条任务的 patch 闭环 Agent。")
    parser.add_argument(
        "--task",
        required=True,
        help="任务 JSON 文件路径，例如 benchmarks/tasks/task_001.json",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="策略配置文件路径，例如 optimization/policy_versions/baseline.json",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    run_output = run_agent(task_path=args.task, repo_root=REPO_ROOT, policy_path=REPO_ROOT / args.policy if args.policy else None)
    task = run_output["task"]
    result = run_output["result"]
    run_paths = run_output["run_paths"]

    print("=== Patch Run Summary ===")
    print(f"task_id: {task['task_id']}")
    print(f"run_id: {result['run_id']}")
    print(f"final_status: {result['final_status']}")
    print(f"issue_title: {task['issue_title']}")
    print(f"policy_id: {result['tool_stats']['policy_id']}")
    print(f"recommended_files: {', '.join(result['recommended_files']) or '(none)'}")
    print(f"total_tool_calls: {result['tool_stats']['total_tool_calls']}")
    print(f"trace_path: {run_paths['trace_json_path']}")
    print(f"result_path: {run_paths['result_json_path']}")
    print(f"summary_path: {run_paths['summary_md_path']}")
    print("phase_status: Phase 3 patch loop complete")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
