from __future__ import annotations

from pathlib import Path

from app.tools.read_file import read_file


def test_read_file_returns_requested_line_range(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text(
        "line 1\nline 2\nline 3\nline 4\nline 5\n",
        encoding="utf-8",
    )

    result = read_file(
        str(repo_path),
        "pkg/app.py",
        start_line=2,
        end_line=4,
    )

    assert result["ok"] is True
    assert result["summary"] == "已读取文件 pkg/app.py 第 2-4 行，共 5 行。"
    assert result["data"]["content"] == "line 2\nline 3\nline 4\n"
    assert result["data"]["line_count"] == 5
    assert result["data"]["start_line"] == 2
    assert result["data"]["end_line"] == 4
    assert result["data"]["returned_line_count"] == 3


def test_read_file_line_range_respects_max_chars(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    result = read_file(
        str(repo_path),
        "pkg/app.py",
        max_chars=8,
        start_line=1,
        end_line=3,
    )

    assert result["ok"] is True
    assert result["data"]["content"] == "alpha\nbe"
    assert result["data"]["truncated"] is True
    assert result["data"]["returned_char_count"] == 8


def test_read_file_rejects_invalid_line_range(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("line 1\n", encoding="utf-8")

    result = read_file(
        str(repo_path),
        "pkg/app.py",
        start_line=4,
        end_line=2,
    )

    assert result["ok"] is False
    assert result["error"]["type"] == "invalid_line_range"
    assert "end_line" in result["error"]["message"]
