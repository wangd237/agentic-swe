"""Git-backed workspace helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from app.tools.common import resolve_repo_path


GIT_IDENTITY_ARGS = [
    "-c",
    "user.name=Agent Workspace",
    "-c",
    "user.email=agent-workspace@example.invalid",
]


def run_git(repo_path: str | Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    resolved_repo_path = resolve_repo_path(repo_path)
    return subprocess.run(
        ["git", "-C", str(resolved_repo_path), *GIT_IDENTITY_ARGS, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def require_git_success(
    repo_path: str | Path,
    args: list[str],
    *,
    action: str,
) -> subprocess.CompletedProcess[str]:
    completed_process = run_git(repo_path, args)
    if completed_process.returncode != 0:
        details = (completed_process.stderr or completed_process.stdout).strip()
        raise RuntimeError(f"{action} 失败: {details}")
    return completed_process


def initialize_git_workspace(workspace_path: str | Path) -> None:
    resolved_workspace_path = resolve_repo_path(workspace_path)
    require_git_success(resolved_workspace_path, ["init"], action="初始化 git workspace")
    require_git_success(resolved_workspace_path, ["add", "-A"], action="暂存初始 workspace")
    require_git_success(
        resolved_workspace_path,
        ["commit", "--allow-empty", "--no-gpg-sign", "-m", "initial"],
        action="提交初始 workspace",
    )
    require_git_success(resolved_workspace_path, ["tag", "-f", "initial"], action="标记初始 workspace")


def commit_workspace_path(repo_path: str | Path, *, relative_path: str, message: str) -> str:
    normalized_relative_path = str(relative_path).replace("\\", "/")
    require_git_success(repo_path, ["add", "--", normalized_relative_path], action="暂存 workspace 写入")
    commit = require_git_success(
        repo_path,
        ["commit", "--allow-empty", "--no-gpg-sign", "-m", message],
        action="提交 workspace 写入",
    )
    commit_hash = require_git_success(repo_path, ["rev-parse", "--short", "HEAD"], action="读取提交哈希")
    return commit_hash.stdout.strip() or commit.stdout.strip()


def has_commits_after_initial(repo_path: str | Path) -> bool:
    head = require_git_success(repo_path, ["rev-parse", "HEAD"], action="读取 HEAD").stdout.strip()
    initial = require_git_success(repo_path, ["rev-parse", "initial"], action="读取 initial").stdout.strip()
    return head != initial


def undo_last_workspace_commit(repo_path: str | Path) -> str:
    if not has_commits_after_initial(repo_path):
        raise RuntimeError("没有可回滚的写操作。")
    previous_head = require_git_success(repo_path, ["rev-parse", "--short", "HEAD"], action="读取当前提交").stdout.strip()
    require_git_success(repo_path, ["reset", "--hard", "HEAD~1"], action="回滚 workspace 写入")
    return previous_head


def diff_since_initial(repo_path: str | Path) -> tuple[str, list[str]]:
    diff_text = require_git_success(
        repo_path,
        ["diff", "--no-ext-diff", "--no-color", "initial..HEAD", "--"],
        action="生成 workspace diff",
    ).stdout
    changed_files_output = require_git_success(
        repo_path,
        ["diff", "--name-only", "initial..HEAD", "--"],
        action="读取 workspace 变更文件",
    ).stdout
    changed_files = [
        line.strip().replace("\\", "/")
        for line in changed_files_output.splitlines()
        if line.strip()
    ]
    return diff_text, changed_files
