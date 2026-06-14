from __future__ import annotations

from pathlib import Path

from app.tools.write_file import write_file


def test_write_file_removes_parent_pycache(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    package_dir = repo_path / "demo_pkg"
    pycache_dir = package_dir / "__pycache__"
    pycache_dir.mkdir(parents=True)
    (pycache_dir / "app.cpython-312.pyc").write_bytes(b"cached")

    result = write_file(
        str(repo_path),
        "demo_pkg/app.py",
        "def value():\n    return 1\n",
    )

    assert result["ok"] is True
    assert result["data"]["removed_pycache_count"] == 1
    assert not pycache_dir.exists()
