from __future__ import annotations

from pathlib import Path

from app.tools.builtin.grep import grep


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
            "symbol": "test_value",
            "symbol_range": [1, 2],
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


def test_grep_scopes_to_package_and_returns_enclosing_function(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "pkg" / "service.py").write_text(
        "class Service:\n"
        "    def process(self):\n"
        "        needle = 1\n"
        "        return needle\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_service.py").write_text(
        "needle = 2\n", encoding="utf-8"
    )
    result = grep(str(repo), "needle", path_prefix="pkg", glob="*.py", max_results=2)

    assert result["ok"]
    assert result["data"]["match_count"] == 2
    assert result["data"]["match_files"] == ["pkg/service.py"]
    assert result["data"]["matches"][0]["symbol"] == "Service.process"
    assert result["data"]["matches"][0]["symbol_range"] == [2, 4]


def test_grep_rejects_unsafe_scope(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    result = grep(str(repo), "needle", path_prefix="../outside")
    assert not result["ok"]
    assert result["error"]["type"] == "invalid_scope"
