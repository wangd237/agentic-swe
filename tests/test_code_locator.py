from __future__ import annotations

from pathlib import Path

from app.agent.code_locator import build_symbol_index, implementation_candidates_for_test_path, rank_candidates


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_implementation_candidates_for_test_path_uses_imports(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "demo_pkg" / "parser.py", "def parse_items(items):\n    return items\n")
    write_text(
        repo / "tests" / "test_parser.py",
        "from demo_pkg.parser import parse_items\n\n"
        "def test_parse_items():\n"
        "    assert parse_items([]) == []\n",
    )

    candidates = implementation_candidates_for_test_path("tests/test_parser.py", repo)

    assert candidates[0] == "demo_pkg/parser.py"


def test_implementation_candidates_for_test_path_uses_mirrored_setup_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "setup.py", "def get_install_requires():\n    return []\n")
    write_text(repo / "tests" / "test_setup.py", "def test_setup():\n    assert True\n")

    candidates = implementation_candidates_for_test_path("tests/test_setup.py", repo)

    assert candidates == ["setup.py"]


def test_rank_candidates_prioritizes_implementation_from_failing_test(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "demo_pkg" / "parser.py", "def parse_items(items):\n    return items\n")
    write_text(
        repo / "tests" / "test_parser.py",
        "from demo_pkg.parser import parse_items\n\n"
        "def test_empty():\n"
        "    assert parse_items([]) == []\n",
    )
    failure_summary = {
        "failed_tests": ["tests/test_parser.py::test_empty - AssertionError"],
        "locations": [{"path": "tests/test_parser.py", "line": 4, "error": "AssertionError"}],
        "assertion_lines": ["assert parse_items([]) == []"],
    }

    candidates = rank_candidates(
        repo_path=repo,
        issue_text="parse_items should handle empty input",
        failure_summary=failure_summary,
    )

    assert candidates[0].relative_path == "demo_pkg/parser.py"
    assert "test_import_mapping" in candidates[0].reason or "failed_test_import_mapping" in candidates[0].reason


def test_rank_candidates_uses_symbol_matches_and_search_hits(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "demo_pkg" / "hostname.py", "class HostnameValidator:\n    pass\n")
    write_text(repo / "demo_pkg" / "utils.py", "VALUE = 1\n")

    symbol_index = build_symbol_index(repo)
    candidates = rank_candidates(
        repo_path=repo,
        issue_text="HostnameValidator rejects single label hostnames",
        search_match_files=["demo_pkg/utils.py"],
    )

    assert "hostnamevalidator" in symbol_index["demo_pkg/hostname.py"]
    assert candidates[0].relative_path == "demo_pkg/hostname.py"
    assert any(candidate.relative_path == "demo_pkg/utils.py" for candidate in candidates)
