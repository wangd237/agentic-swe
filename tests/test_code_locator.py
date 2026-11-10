from __future__ import annotations

from pathlib import Path

from app.codebase.locator import build_symbol_index, implementation_candidates_for_test_path, rank_candidates
from app.codebase.repo_map import build_initial_repo_map
from app.core.state import LocalizationCandidate


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

def test_initial_repo_map_outlines_symbols_and_obeys_budget(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    write_text(
        repo / "pkg" / "service.py",
        "class Service:\n"
        "    def process_request(self, data):\n"
        "        return data\n"
        "    def validate(self, data):\n"
        "        return True\n",
    )
    candidates = [
        LocalizationCandidate(relative_path="pkg/service.py", confidence=0.8),
        LocalizationCandidate(relative_path="../outside.py", confidence=0.7),
    ]
    outline = build_initial_repo_map(repo, candidates, "process_request fails")

    assert "REPO_MAP" in outline
    assert "pkg/service.py" in outline
    assert "Service.process_request: L2-L3" in outline
    assert "Service.validate: L4-L5" in outline
    assert "../outside.py" not in outline
    assert build_initial_repo_map(repo, candidates, "bug", max_chars=20) == ""
    assert len(build_initial_repo_map(repo, candidates, "bug", max_chars=300)) <= 300


def test_ranking_prioritizes_first_application_frame_over_downstream_exceptions(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "src" / "packaging" / "markers.py", "def _eval_op():\n    pass\n")
    write_text(repo / "src" / "packaging" / "specifiers.py", "def contains():\n    pass\n")
    write_text(repo / "src" / "packaging" / "version.py", "class InvalidVersion(Exception):\n    pass\n")
    write_text(repo / "src" / "packaging" / "metadata.py", "def parse_email():\n    pass\n")
    write_text(
        repo / "tests" / "test_issue.py",
        "from src.packaging.markers import _eval_op\n"
        "def test_invalid_extra():\n    _eval_op()\n",
    )
    graph = [
        LocalizationCandidate(relative_path="src/packaging/metadata.py", confidence=0.99),
        LocalizationCandidate(relative_path="src/packaging/markers.py", confidence=0.99),
    ]
    traceback = [
        {"path": "tests\\test_issue.py", "line": 3},
        {"path": "src\\packaging\\markers.py", "line": 180},
        {"path": "src\\packaging\\specifiers.py", "line": 552},
        {"path": "src\\packaging\\version.py", "line": 202},
    ]
    kwargs = dict(
        repo_path=repo,
        issue_text="InvalidVersion while evaluating extra marker",
        existing_candidates=graph,
        search_match_files=["src/packaging/markers.py"],
        search_symbol_files=["src/packaging/markers.py"],
        read_files=["src/packaging/markers.py"],
    )
    first = rank_candidates(**kwargs, failure_summary={"locations": traceback})
    repeated = rank_candidates(
        **kwargs, failure_summary={"locations": traceback * 5}
    )

    assert first[0].relative_path == "src/packaging/markers.py"
    assert first[0].confidence < 1.0
    assert [item.relative_path for item in first] == [
        item.relative_path for item in repeated
    ]
    assert [item.confidence for item in first] == [
        item.confidence for item in repeated
    ]
    assert "failure_location" in first[0].reason
    assert "symbol_search_hit" in first[0].reason


def test_ranking_is_stable_across_refreshes_using_original_graph_hints(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "pkg" / "first.py", "def process():\n    pass\n")
    write_text(repo / "pkg" / "second.py", "def helper():\n    pass\n")
    graph = [LocalizationCandidate(relative_path="pkg/second.py", confidence=0.85)]
    kwargs = {
        "repo_path": repo,
        "issue_text": "process fails",
        "existing_candidates": graph,
        "search_match_files": ["pkg/first.py"],
    }
    first = rank_candidates(**kwargs)
    second = rank_candidates(**kwargs)
    assert first == second
    assert all(item.confidence < 1 for item in first)
    assert all("existing:existing:" not in item.reason for item in first)
    assert any(item.relative_path == "pkg/second.py" for item in first)


def test_ranking_distinguishes_symbol_search_from_plain_text_hit(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "pkg" / "a.py", "needle = 1\n")
    write_text(repo / "pkg" / "b.py", "def handle():\n    needle = 2\n")
    candidates = rank_candidates(
        repo_path=repo, search_match_files=["pkg/a.py", "pkg/b.py"],
        search_symbol_files=["pkg/b.py"],
    )
    assert candidates[0].relative_path == "pkg/b.py"
    assert candidates[0].confidence > candidates[1].confidence


def test_issue_symbol_only_candidate_preserves_reflector_confidence_floor(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    write_text(repo / "demo_pkg" / "app.py", "def value():\n    return 0\n")
    ranked = rank_candidates(repo_path=repo, issue_text="value() should return 1")

    assert ranked[0].relative_path == "demo_pkg/app.py"
    # The existing reflection gate treats a modified candidate <0.4 as weak.
    assert 0.4 <= ranked[0].confidence < 1.0
