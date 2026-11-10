"""Lightweight candidate ranking for code localization."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core.state import LocalizationCandidate
from app.tools.builtin.common import resolve_repo_path, should_skip_path

PYTHON_SUFFIX = ".py"
TEST_DIR_PARTS = {"test", "tests", "testing"}
TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
LOW_VALUE_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "should",
    "return",
    "returns",
    "error",
    "test",
    "tests",
    "issue",
    "bug",
    "fix",
    "none",
    "true",
    "false",
}


@dataclass(slots=True)
class CandidateScore:
    relative_path: str
    # Independent evidence channels: repeated frames/calls cannot add weight.
    signals: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def add(self, *, signal: str, score: float, reason: str, evidence: str) -> None:
        self.signals[signal] = max(self.signals.get(signal, 0.0), score)
        if reason not in self.reasons:
            self.reasons.append(reason)
        if evidence and evidence not in self.evidence:
            self.evidence.append(evidence)

    def to_candidate(self) -> LocalizationCandidate:
        # A ranking heuristic, NOT a calibrated probability. The rational
        # transform avoids 1.0 saturation while preserving the existing
        # reflector's >=0.4 threshold for a direct issue-symbol match.
        raw_score = sum(self.signals.values())
        confidence = round(raw_score / (raw_score + 2.5), 3)
        return LocalizationCandidate(
            relative_path=self.relative_path,
            reason=", ".join(self.reasons),
            evidence=self.evidence,
            confidence=confidence,
        )


def extract_issue_tokens(*parts: str) -> set[str]:
    tokens: set[str] = set()
    for part in parts:
        for token in TOKEN_PATTERN.findall(part):
            normalized = token.lower()
            if normalized not in LOW_VALUE_TOKENS:
                tokens.add(normalized)
    return tokens


def is_test_path(relative_path: str) -> bool:
    path = Path(relative_path)
    lower_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return bool(lower_parts & TEST_DIR_PARTS) or name.startswith("test_") or name.endswith("_test.py")


def normalize_relative_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def implementation_candidates_for_test_path(test_path: str, repo_path: str | Path) -> list[str]:
    """Infer likely implementation files imported or mirrored by a Python test file."""

    normalized_test_path = normalize_relative_path(test_path)
    repo = resolve_repo_path(repo_path)
    full_test_path = repo / normalized_test_path
    candidates: list[str] = []
    if not full_test_path.exists() or full_test_path.suffix != PYTHON_SUFFIX:
        return candidates

    try:
        tree = ast.parse(full_test_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        tree = ast.Module(body=[], type_ignores=[])

    for node in ast.walk(tree):
        module_name = ""
        if isinstance(node, ast.ImportFrom) and node.module:
            module_name = node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                candidate = module_name_to_path(module_name, repo)
                if candidate and candidate not in candidates:
                    candidates.append(candidate)
            continue

        candidate = module_name_to_path(module_name, repo)
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    test_file_name = full_test_path.name
    stem = test_file_name.removeprefix("test_").removesuffix("_test.py").removesuffix(".py")
    if stem:
        for path in repo.rglob(f"{stem}.py"):
            relative_path = normalize_relative_path(path.relative_to(repo))
            if relative_path != normalized_test_path and not should_skip_path(path.relative_to(repo)):
                if relative_path not in candidates:
                    candidates.append(relative_path)

    return candidates


def module_name_to_path(module_name: str, repo: Path) -> str | None:
    if not module_name:
        return None
    parts = module_name.split(".")
    module_path = repo.joinpath(*parts).with_suffix(PYTHON_SUFFIX)
    package_path = repo.joinpath(*parts) / "__init__.py"
    for path in (module_path, package_path):
        if not path.exists() or should_skip_path(path.relative_to(repo)):
            continue
        return normalize_relative_path(path.relative_to(repo))
    return None


def build_symbol_index(repo_path: str | Path) -> dict[str, set[str]]:
    """Return relative Python file -> discovered class/function/import symbols."""

    repo = resolve_repo_path(repo_path)
    index: dict[str, set[str]] = {}
    for path in repo.rglob("*.py"):
        relative_path = path.relative_to(repo)
        if should_skip_path(relative_path):
            continue
        symbols: set[str] = set()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.add(node.name.lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                symbols.add(node.module.split(".")[-1].lower())
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols.add(alias.name.split(".")[-1].lower())
        if symbols:
            index[normalize_relative_path(relative_path)] = symbols
    return index


def rank_candidates(
    *,
    repo_path: str | Path,
    issue_text: str = "",
    target_files_hint: list[str] | None = None,
    failure_summary: dict[str, Any] | None = None,
    search_match_files: list[str] | None = None,
    search_symbol_files: list[str] | None = None,
    read_files: list[str] | None = None,
    existing_candidates: list[LocalizationCandidate] | None = None,
    max_candidates: int = 5,
) -> list[LocalizationCandidate]:
    """Rank files from independent evidence, without feeding rankings back as priors.

    `existing_candidates` is intended for initial external graph hints; callers
    must pass the ORIGINAL graph candidates on subsequent refreshes, rather than
    this function's output. Tool results from repeated runs share evidence
    channels and therefore cannot inflate their own confidence.
    """
    scores: dict[str, CandidateScore] = {}

    def score_path(
        relative_path: str, *, signal: str, score: float, reason: str, evidence: str
    ) -> None:
        normalized = normalize_relative_path(relative_path).strip()
        if not normalized:
            return
        scores.setdefault(normalized, CandidateScore(relative_path=normalized)).add(
            signal=signal,
            score=score,
            reason=reason,
            evidence=evidence,
        )

    for path in set(target_files_hint or []):
        score_path(path, signal="task_hint", score=3.0, reason="task_hint",
                   evidence="Task listed this file as a hint.")

    # Graph candidates are stable priors, not the previous ranking's confidence.
    for candidate in existing_candidates or []:
        score_path(
            candidate.relative_path,
            signal="graph_prior",
            score=0.5 + 2.0 * max(0.0, min(candidate.confidence, 1.0)),
            reason=candidate.reason or "graph_prior",
            evidence="Initial external localization candidate.",
        )

    failure_summary = failure_summary or {}
    locations = failure_summary.get("locations", []) or []
    # A failure stack generally starts in the failing test and enters project
    # code before descending to generic parsing/exception helpers. Prefer its
    # first implementation file, without assuming the final throw site is root.
    first_implementation = next(
        (
            normalize_relative_path(str(location.get("path", "")))
            for location in locations
            if location.get("path")
            and not is_test_path(normalize_relative_path(str(location["path"])))
        ),
        None,
    )
    for location in locations:
        path = str(location.get("path", ""))
        if not path:
            continue
        normalized = normalize_relative_path(path)
        if is_test_path(normalized):
            score_path(
                normalized, signal="failing_test_location", score=0.4,
                reason="failure_location",
                evidence=f"Test output pointed at {normalized}:{location.get('line')}.",
            )
            for implementation_path in implementation_candidates_for_test_path(normalized, repo_path):
                score_path(
                    implementation_path, signal="test_import_mapping", score=2.5,
                    reason="test_import_mapping",
                    evidence=f"Inferred implementation from failing test {normalized}.",
                )
        else:
            # Only one score per file across all stack frames and failed tests.
            direct = normalized == first_implementation
            score_path(
                normalized,
                signal="traceback_location",
                score=3.3 if direct else 1.1,
                reason="failure_location",
                evidence=f"Test traceback includes {normalized}:{location.get('line')} "
                         f"({'first application frame' if direct else 'downstream frame'}).",
            )

    for failed_test in failure_summary.get("failed_tests", []) or []:
        test_path = normalize_relative_path(
            str(failed_test).split("::", 1)[0].split(" - ", 1)[0]
        )
        if test_path.endswith(PYTHON_SUFFIX):
            score_path(
                test_path, signal="failed_test", score=0.4,
                reason="failed_test",
                evidence=f"Pytest reported failed test {failed_test}.",
            )
            for implementation_path in implementation_candidates_for_test_path(test_path, repo_path):
                score_path(
                    implementation_path, signal="test_import_mapping", score=2.5,
                    reason="failed_test_import_mapping",
                    evidence=f"Inferred implementation from failed test {test_path}.",
                )

    for path in set(search_match_files or []):
        score_path(path, signal="search_hit", score=1.25, reason="search_hit",
                   evidence="Search or grep matched this file.")
    for path in set(search_symbol_files or []):
        score_path(path, signal="symbol_search_hit", score=1.6,
                   reason="symbol_search_hit",
                   evidence="Search matched an enclosing Python symbol with line range.")
    # Reading a file is weak evidence: the LLM may inspect the wrong candidate.
    for path in set(read_files or []):
        score_path(path, signal="file_read", score=0.35,
                   reason="file_read", evidence="Agent inspected this file.")

    issue_tokens = extract_issue_tokens(issue_text)
    if issue_tokens:
        symbol_index = build_symbol_index(repo_path)
        for path, symbols in symbol_index.items():
            overlaps = sorted(issue_tokens & symbols)
            if overlaps:
                score_path(
                    path, signal="issue_symbol", score=min(1.5 + len(overlaps) * 0.2, 2.1),
                    reason="symbol_match",
                    evidence=f"Issue tokens matched symbols: {', '.join(overlaps[:5])}.",
                )

    ranked = sorted(
        (score.to_candidate() for score in scores.values()),
        key=lambda candidate: (
            candidate.confidence,
            not is_test_path(candidate.relative_path),
            candidate.relative_path,
        ),
        reverse=True,
    )
    return ranked[:max_candidates]
