"""Lightweight candidate ranking for code localization."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agent.memory import LocalizationCandidate
from app.tools.common import resolve_repo_path, should_skip_path


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
    score: float = 0.0
    reasons: list[str] | None = None
    evidence: list[str] | None = None

    def add(self, *, score: float, reason: str, evidence: str) -> None:
        self.score += score
        self.reasons = self.reasons or []
        self.evidence = self.evidence or []
        if reason not in self.reasons:
            self.reasons.append(reason)
        if evidence and evidence not in self.evidence:
            self.evidence.append(evidence)

    def to_candidate(self) -> LocalizationCandidate:
        confidence = min(round(self.score / 5.0, 3), 1.0)
        return LocalizationCandidate(
            relative_path=self.relative_path,
            reason=", ".join(self.reasons or []),
            evidence=self.evidence or [],
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
    existing_candidates: list[LocalizationCandidate] | None = None,
    max_candidates: int = 5,
) -> list[LocalizationCandidate]:
    scores: dict[str, CandidateScore] = {}

    def score_path(relative_path: str, *, score: float, reason: str, evidence: str) -> None:
        normalized = normalize_relative_path(relative_path)
        if not normalized:
            return
        scores.setdefault(normalized, CandidateScore(relative_path=normalized)).add(
            score=score,
            reason=reason,
            evidence=evidence,
        )

    for path in target_files_hint or []:
        score_path(path, score=3.0, reason="task_hint", evidence="Task listed this file as a hint.")

    for candidate in existing_candidates or []:
        score_path(
            candidate.relative_path,
            score=max(candidate.confidence * 3.0, 0.5),
            reason=f"existing:{candidate.reason or 'candidate'}",
            evidence="Existing agent state already tracked this candidate.",
        )

    failure_summary = failure_summary or {}
    for location in failure_summary.get("locations", []) or []:
        path = str(location.get("path", ""))
        if not path:
            continue
        score = 2.0 if is_test_path(path) else 4.0
        score_path(
            path,
            score=score,
            reason="failure_location",
            evidence=f"Test output pointed at {path}:{location.get('line')}.",
        )
        if is_test_path(path):
            for implementation_path in implementation_candidates_for_test_path(path, repo_path):
                score_path(
                    implementation_path,
                    score=3.5,
                    reason="test_import_mapping",
                    evidence=f"Inferred implementation from failing test {path}.",
                )

    for failed_test in failure_summary.get("failed_tests", []) or []:
        test_path = str(failed_test).split("::", 1)[0].split(" - ", 1)[0]
        if test_path.endswith(PYTHON_SUFFIX):
            score_path(
                test_path,
                score=1.5,
                reason="failed_test",
                evidence=f"Pytest reported failed test {failed_test}.",
            )
            for implementation_path in implementation_candidates_for_test_path(test_path, repo_path):
                score_path(
                    implementation_path,
                    score=3.0,
                    reason="failed_test_import_mapping",
                    evidence=f"Inferred implementation from failed test {test_path}.",
                )

    for path in search_match_files or []:
        score_path(path, score=1.5, reason="search_hit", evidence="Search/grep matched this file.")

    issue_tokens = extract_issue_tokens(issue_text)
    if issue_tokens:
        symbol_index = build_symbol_index(repo_path)
        for path, symbols in symbol_index.items():
            overlaps = sorted(issue_tokens & symbols)
            if overlaps:
                score_path(
                    path,
                    score=min(2.0 + len(overlaps) * 0.4, 4.0),
                    reason="symbol_match",
                    evidence=f"Issue tokens matched symbols: {', '.join(overlaps[:5])}.",
                )

    ranked = sorted(
        (score.to_candidate() for score in scores.values()),
        key=lambda candidate: (candidate.confidence, not is_test_path(candidate.relative_path), candidate.relative_path),
        reverse=True,
    )
    return ranked[:max_candidates]
