from __future__ import annotations

from pathlib import Path

from app.tools.edit_file import edit_file


def test_edit_file_replaces_unique_old_string(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("def value():\n    return 1\n", encoding="utf-8")

    result = edit_file(
        str(repo_path),
        "pkg/app.py",
        "    return 1",
        "    return 2",
    )

    assert result["ok"] is True
    assert result["data"]["replacement_count"] == 1
    assert result["data"]["line_number"] == 2
    assert result["data"]["old_length"] == len("    return 1")
    assert result["data"]["new_length"] == len("    return 2")
    assert target_path.read_text(encoding="utf-8") == "def value():\n    return 2\n"


def test_edit_file_rejects_non_unique_old_string(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("value = 1\nother = 2\nvalue = 1\n", encoding="utf-8")

    result = edit_file(str(repo_path), "pkg/app.py", "value = 1", "value = 3")

    assert result["ok"] is False
    assert result["error"]["type"] == "old_string_not_unique"
    assert result["data"]["replacement_count"] == 2
    assert [match["line_number"] for match in result["data"]["matches"]] == [1, 3]
    assert target_path.read_text(encoding="utf-8") == "value = 1\nother = 2\nvalue = 1\n"


def test_edit_file_rejects_missing_old_string(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("value = 1\n", encoding="utf-8")

    result = edit_file(str(repo_path), "pkg/app.py", "missing", "replacement")

    assert result["ok"] is False
    assert result["error"]["type"] == "old_string_not_found"
    assert result["data"]["replacement_count"] == 0
    assert target_path.read_text(encoding="utf-8") == "value = 1\n"


def test_edit_file_rejects_path_escape(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    outside_path = tmp_path / "outside.py"
    outside_path.write_text("value = 1\n", encoding="utf-8")

    result = edit_file(str(repo_path), "../outside.py", "value = 1", "value = 2")

    assert result["ok"] is False
    assert result["error"]["type"] == "path_escape"
    assert outside_path.read_text(encoding="utf-8") == "value = 1\n"
