from __future__ import annotations

from pathlib import Path

from app.tools.grep import grep


def test_grep_finds_regex_matches_with_glob(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    source_path = repo_path / "pkg" / "app.py"
    test_path = repo_path / "tests" / "test_app.py"
    source_path.parent.mkdir(parents=True)
    test_path.parent.mkdir(parents=True)
    source_path.write_text(
        "import os\n\n"
        "def testable_value():\n"
        "    return False\n",
        encoding="utf-8",
    )
    test_path.write_text(
        "def test_value():\n"
        "    assert value() is False\n",
        encoding="utf-8",
    )

    result = grep(str(repo_path), r"def\s+test_\w+", glob="*.py", max_results=10)

    assert result["ok"] is True
    assert result["data"]["match_count"] == 1
    assert result["data"]["matches"] == [
        {
            "relative_path": "tests/test_app.py",
            "line_number": 1,
            "line_text": "def test_value():",
        }
    ]


def test_grep_limits_results_and_reports_total_count(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    source_path = repo_path / "pkg" / "app.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_text("\n".join(f"value_{index} = {index}" for index in range(5)), encoding="utf-8")

    result = grep(str(repo_path), r"value_\d+", max_results=2)

    assert result["ok"] is True
    assert result["data"]["match_count"] == 5
    assert result["data"]["returned_match_count"] == 2
    assert result["data"]["truncated"] is True


def test_grep_rejects_invalid_regex(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    result = grep(str(repo_path), r"(")

    assert result["ok"] is False
    assert result["error"]["type"] == "invalid_pattern"
