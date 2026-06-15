"""工具层公共辅助函数。"""

from pathlib import Path


DEFAULT_IGNORED_DIRS = {
    ".git",
    ".agent_checkpoints",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
}

TEXT_FILE_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".rst",
}


def resolve_repo_path(repo_path: str | Path) -> Path:
    # 所有工具都显式校验 repo_path，避免后续逻辑在不存在目录上继续执行。
    resolved = Path(repo_path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"仓库路径不存在: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"仓库路径不是目录: {resolved}")
    return resolved


def resolve_repo_relative_path(repo_path: str | Path, relative_path: str | Path) -> Path:
    # 统一限制相对路径只能落在当前 repo 内，防止路径逃逸。
    base_path = resolve_repo_path(repo_path)
    target_path = (base_path / relative_path).resolve()
    if not target_path.is_relative_to(base_path):
        raise ValueError(f"路径超出仓库边界: {relative_path}")
    return target_path


def should_skip_path(path: Path) -> bool:
    # 第一版只做目录级过滤，先排除明显无关内容。
    return any(part in DEFAULT_IGNORED_DIRS for part in path.parts)


def is_likely_text_file(path: Path) -> bool:
    # 观察型 Agent 当前只需要优先处理常见文本文件。
    return path.suffix.lower() in TEXT_FILE_EXTENSIONS or path.suffix == ""
