"""Harness 运行时辅助结构。"""

import shutil
import subprocess
from datetime import datetime, timezone
from random import randint
from dataclasses import asdict, dataclass
from pathlib import Path

from app.runtime.git_workspace import initialize_git_workspace


COPY_IGNORE_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".ruff_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "build",
    "dist",
    "htmlcov",
    "logs",
    "node_modules",
    "venv",
    "__pycache__",
}

COPY_IGNORE_PATTERNS = (
    ".pytest_tmp*",
    "*.egg-info",
)


def ignore_workspace_copy_artifacts(src: str, names: list[str]) -> set[str]:
    ignored = set(shutil.ignore_patterns(*COPY_IGNORE_PATTERNS)(src, names))
    ignored.update(name for name in names if name in COPY_IGNORE_DIR_NAMES)
    return ignored


@dataclass(slots=True)
class RunPaths:
    # 这个结构固定一次任务运行的关键产物位置，避免后续阶段频繁改路径协议。
    task_id: str
    run_id: str
    run_dir: Path
    workspace_dir: Path
    task_json_path: Path
    result_json_path: Path
    trace_json_path: Path
    patch_diff_path: Path
    summary_md_path: Path
    test_stdout_path: Path
    test_stderr_path: Path
    pre_test_stdout_path: Path
    pre_test_stderr_path: Path
    post_test_stdout_path: Path
    post_test_stderr_path: Path

    def to_dict(self) -> dict[str, str]:
        # 统一把路径结构转成可序列化字典，便于日志和调试输出。
        return {
            key: str(value)
            for key, value in asdict(self).items()
        }


def ensure_within_boundary(base_dir: str | Path, target_path: str | Path) -> Path:
    # 所有运行时文件操作最终都应受边界约束，防止路径逃逸。
    base = Path(base_dir).resolve()
    target = Path(target_path).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"路径超出允许边界: {target}")
    return target


def build_run_paths(log_root: str | Path, task_id: str, run_id: str) -> RunPaths:
    # 按固定协议生成 run 目录结构，后续 result / trace / patch 都复用这里。
    base_dir = Path(log_root).resolve() / task_id / run_id
    workspace_dir = base_dir / "workspace"
    return RunPaths(
        task_id=task_id,
        run_id=run_id,
        run_dir=base_dir,
        workspace_dir=workspace_dir,
        task_json_path=base_dir / "task.json",
        result_json_path=base_dir / "result.json",
        trace_json_path=base_dir / "trace.json",
        patch_diff_path=base_dir / "patch.diff",
        summary_md_path=base_dir / "summary.md",
        test_stdout_path=base_dir / "test_stdout.txt",
        test_stderr_path=base_dir / "test_stderr.txt",
        pre_test_stdout_path=base_dir / "pre_test_stdout.txt",
        pre_test_stderr_path=base_dir / "pre_test_stderr.txt",
        post_test_stdout_path=base_dir / "post_test_stdout.txt",
        post_test_stderr_path=base_dir / "post_test_stderr.txt",
    )


def copy_repo_to_workspace(
    source_repo_path: str | Path,
    workspace_path: str | Path,
    *,
    test_patch_path: str | Path | None = None,
) -> None:
    # 复制 benchmark repo 时显式忽略缓存目录，并为 agent 写入建立本地 git baseline。
    shutil.copytree(
        Path(source_repo_path),
        Path(workspace_path),
        dirs_exist_ok=True,
        ignore=ignore_workspace_copy_artifacts,
    )
    initialize_git_workspace(workspace_path)
    _apply_test_patch(workspace_path, test_patch_path)
    _pip_install_editable(workspace_path)


def _apply_test_patch(workspace_path: str | Path, test_patch_path: str | Path | None) -> None:
    """Apply SWE-bench test.patch so fail-to-pass tests exist before agent runs."""
    if test_patch_path is None:
        return
    patch = Path(test_patch_path)
    if not patch.exists():
        return
    try:
        subprocess.run(
            ["git", "apply", str(patch)],
            cwd=str(workspace_path),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def _pip_install_editable(workspace_path: str | Path) -> None:
    """Try pip install -e . so repo packages are importable in tests."""
    workspace = Path(workspace_path)
    for candidate in ("setup.py", "setup.cfg", "pyproject.toml"):
        if not (workspace / candidate).exists():
            continue
        try:
            subprocess.run(
                ["python", "-m", "pip", "install", "-e", ".", "-q"],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass
        return


def next_run_id(task_runs_dir: str | Path) -> str:
    # 顺序编号在连续实验中容易出现目录争用，这里改成时间戳+随机后缀保证追加安全。
    run_dir = Path(task_runs_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    while True:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        candidate = f"run_{timestamp}_{randint(0, 9999):04d}"
        if not (run_dir / candidate).exists():
            return candidate

