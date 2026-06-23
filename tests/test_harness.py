from __future__ import annotations

from pathlib import Path

from app.runtime import harness


def write_text(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_copy_repo_to_workspace_ignores_runtime_artifacts(tmp_path: Path, monkeypatch) -> None:
    source_repo = tmp_path / "source"
    workspace = tmp_path / "workspace"
    write_text(source_repo / "package" / "module.py", "VALUE = 1\n")
    write_text(source_repo / "logs" / "trajectories" / "run" / "result.json", "{}")
    write_text(source_repo / ".pytest_tmp_case" / "workspace" / "nested.txt", "noise")
    write_text(source_repo / ".venv" / "pyvenv.cfg", "noise")
    write_text(source_repo / "venv" / "pyvenv.cfg", "noise")
    write_text(source_repo / "__pycache__" / "module.pyc", "noise")
    write_text(source_repo / ".ruff_cache" / "CACHEDIR.TAG", "noise")

    initialized: list[Path] = []

    def fake_initialize_git_workspace(workspace_path: str | Path) -> None:
        initialized.append(Path(workspace_path))

    monkeypatch.setattr(harness, "initialize_git_workspace", fake_initialize_git_workspace)

    harness.copy_repo_to_workspace(source_repo, workspace)

    assert (workspace / "package" / "module.py").exists()
    assert not (workspace / "logs").exists()
    assert not (workspace / ".pytest_tmp_case").exists()
    assert not (workspace / ".venv").exists()
    assert not (workspace / "venv").exists()
    assert not (workspace / "__pycache__").exists()
    assert not (workspace / ".ruff_cache").exists()
    assert initialized == [workspace]
