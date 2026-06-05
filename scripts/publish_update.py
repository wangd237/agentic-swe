"""将当前更新提交并推送到远端仓库。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def run_git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    # 统一走仓库根目录执行，避免脚本从别处调用时找不到 .git。
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def ensure_success(result: subprocess.CompletedProcess[str], step_name: str) -> None:
    if result.returncode == 0:
        return
    stderr = result.stderr.strip()
    stdout = result.stdout.strip()
    detail = stderr or stdout or "未知错误"
    raise RuntimeError(f"{step_name} 失败：{detail}")


def has_pending_changes() -> bool:
    result = run_git_command(["status", "--porcelain"])
    ensure_success(result, "检查工作区状态")
    return bool(result.stdout.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="提交当前更新并可选推送到远端。")
    parser.add_argument(
        "--message",
        required=True,
        help="提交信息",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="远端名称，默认 origin",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="分支名称，默认 main",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="只提交，不执行 push",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    add_result = run_git_command(["add", "-A"])
    ensure_success(add_result, "暂存文件")

    if not has_pending_changes():
        print("没有可提交的变更。")
        return 0

    commit_result = run_git_command(["commit", "-m", args.message])
    ensure_success(commit_result, "创建提交")
    print(commit_result.stdout.strip())

    if args.no_push:
        print("已按要求跳过 push。")
        return 0

    push_result = run_git_command(["push", args.remote, args.branch])
    ensure_success(push_result, "推送到远端")
    print(push_result.stdout.strip() or push_result.stderr.strip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
