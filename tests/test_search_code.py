"""Regression coverage for progressive literal code search."""

from pathlib import Path

from app.tools.builtin.search_code import search_code


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_search_code_returns_enclosing_symbol_and_scoped_matches(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(
        repo / "pkg" / "service.py",
        "class Service:\n"
        "    def process_request(self):\n"
        "        raise RuntimeError('needle')\n"
        "    def other(self):\n"
        "        return 'needle'\n",
    )
    _write(repo / "tests" / "test_service.py", "message = 'needle'\n")
    result = search_code(str(repo), "needle", path_prefix="pkg", glob="*.py")

    assert result["ok"]
    assert result["data"]["match_count"] == 2
    assert result["data"]["returned_match_count"] == 2
    assert result["data"]["match_files"] == ["pkg/service.py"]
    assert result["data"]["matches"][0]["symbol"] == "Service.process_request"
    assert result["data"]["matches"][0]["symbol_range"] == [2, 3]
    assert result["data"]["matches"][1]["symbol"] == "Service.other"
    assert result["data"]["matches"][1]["symbol_range"] == [4, 5]


def test_search_code_is_bounded_but_reports_total_match_count(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "pkg" / "values.py", "".join(f"needle_{i} = 1\n" for i in range(20)))
    result = search_code(str(repo), "needle", max_results=3)
    assert result["ok"]
    assert result["data"]["match_count"] == 20
    assert len(result["data"]["matches"]) == 3
    assert result["data"]["returned_match_count"] == 3
    assert result["data"]["truncated"] is True


def test_search_code_handles_invalid_syntax_and_empty_scopes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "pkg" / "broken.py", "def broken(:\n  needle\n")
    invalid_py = search_code(str(repo), "needle", path_prefix="pkg", glob="*.py")
    assert invalid_py["ok"]
    assert "symbol" not in invalid_py["data"]["matches"][0]

    no_match = search_code(str(repo), "needle", path_prefix="not-there")
    assert no_match["ok"]
    assert no_match["data"]["match_count"] == 0

    invalid_scope = search_code(str(repo), "needle", path_prefix="../outside")
    assert not invalid_scope["ok"]
    assert invalid_scope["error"]["type"] == "invalid_scope"


def test_search_code_searches_only_requested_file_when_path_prefix_is_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _write(repo / "pkg" / "one.py", "needle = 1\n")
    _write(repo / "pkg" / "two.py", "needle = 2\n")
    result = search_code(str(repo), "needle", path_prefix="pkg/two.py")
    assert result["data"]["match_files"] == ["pkg/two.py"]
