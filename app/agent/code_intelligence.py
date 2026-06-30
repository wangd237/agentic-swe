"""Optional code intelligence backends for graph-assisted localization."""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir
from time import perf_counter
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from app.agent.code_locator import implementation_candidates_for_test_path
from app.agent.memory import LocalizationCandidate


SYMBOL_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
CODE_SPAN_PATTERN = re.compile(r"`([^`]+)`")
LOW_VALUE_SYMBOLS = {
    "assert",
    "error",
    "failed",
    "failure",
    "false",
    "issue",
    "none",
    "return",
    "should",
    "test",
    "true",
}
SHADOW_COPY_PATH_LENGTH_THRESHOLD = 140
SHADOW_COPY_IGNORE_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}
SHADOW_COPY_IGNORE_PATTERNS = (
    ".pytest_tmp*",
    "*.egg-info",
)


class CodeIntelligenceResult(BaseModel):
    """Structured result returned by optional code intelligence backends."""

    model_config = ConfigDict(extra="forbid")

    backend: str = "none"
    enabled: bool = False
    available: bool = False
    backend_version: str = ""
    backend_binary_path: str = ""
    fallback_reason: str = ""
    candidates: list[LocalizationCandidate] = Field(default_factory=list)
    compact_hints: str = ""
    metrics: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class CodeIntelligenceBackend(ABC):
    """Interface for optional graph/code-memory localization backends."""

    name = "base"

    @abstractmethod
    def collect_localization_hints(
        self,
        *,
        repo_path: str | Path,
        issue_text: str,
        failure_summary: dict[str, Any] | None = None,
        max_results: int = 8,
    ) -> CodeIntelligenceResult:
        """Return compact localization candidates for the current workspace."""

    @abstractmethod
    def search_graph_query(
        self,
        *,
        name_pattern: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        """Execute a graph search and return structured results."""

    @abstractmethod
    def is_indexed(self) -> bool:
        """Return True if the backend has an active, queryable index."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release any temporary resources (shadow copies, caches)."""


class NullCodeIntelligenceBackend(CodeIntelligenceBackend):
    """Default backend that preserves existing behavior."""

    name = "none"

    def collect_localization_hints(
        self,
        *,
        repo_path: str | Path,
        issue_text: str,
        failure_summary: dict[str, Any] | None = None,
        max_results: int = 8,
    ) -> CodeIntelligenceResult:
        return CodeIntelligenceResult(
            backend=self.name,
            enabled=False,
            available=False,
            fallback_reason="backend_disabled",
            metrics={
                "index_attempted": False,
                "index_success": False,
                "graph_tool_calls_total": 0,
                "graph_candidates_count": 0,
            },
        )

    def search_graph_query(
        self,
        *,
        name_pattern: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "tool_name": "search_graph",
            "summary": "Code intelligence backend is not enabled.",
            "data": {"results": [], "backend": "none"},
            "error": {
                "type": "backend_disabled",
                "message": "Code intelligence backend is not configured.",
            },
        }

    def is_indexed(self) -> bool:
        return False

    def cleanup(self) -> None:
        pass


@dataclass(slots=True)
class CodebaseMemoryCliBackend(CodeIntelligenceBackend):
    """Minimal CLI wrapper around codebase-memory-mcp.

    This backend intentionally stays narrow: it indexes a workspace, runs a
    graph search for high-signal symbols, and compacts the result into the
    existing LocalizationCandidate shape.
    """

    binary: str = "codebase-memory-mcp"
    timeout_sec: float = 10.0
    index_mode: str = "fast"
    always_use_shadow_copy: bool = True
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
    env: dict[str, str] | None = None

    name = "codebase_memory_cli"

    def __post_init__(self) -> None:
        self._indexed_project: str | None = None
        self._cached_binary_path: str = ""
        self._cached_env: dict[str, str] = {}
        self._shadow_root: Path | None = None

    @staticmethod
    def _ignore_shadow_copy_artifacts(src: str, names: list[str]) -> set[str]:
        ignored = set(shutil.ignore_patterns(*SHADOW_COPY_IGNORE_PATTERNS)(src, names))
        ignored.update(name for name in names if name in SHADOW_COPY_IGNORE_DIR_NAMES)
        return ignored

    @classmethod
    def _prepare_index_repo_path(
        cls,
        repo_path: str | Path,
        *,
        always_use_shadow_copy: bool = True,
    ) -> tuple[Path, Path | None, bool]:
        resolved_repo_path = Path(repo_path).resolve()
        if not always_use_shadow_copy and len(str(resolved_repo_path)) <= SHADOW_COPY_PATH_LENGTH_THRESHOLD:
            return resolved_repo_path, None, False
        shadow_base = Path.cwd().resolve()
        shadow_key = hashlib.sha1(str(resolved_repo_path).encode("utf-8")).hexdigest()[:10]
        shadow_root = shadow_base / ".code_intelligence_shadow" / shadow_key
        shadow_repo_path = shadow_root / "repo"
        if shadow_repo_path.exists():
            shutil.rmtree(shadow_repo_path)
        shutil.copytree(
            resolved_repo_path,
            shadow_repo_path,
            ignore=cls._ignore_shadow_copy_artifacts,
        )
        return shadow_repo_path, shadow_root, True

    def _binary_path(self) -> str:
        return shutil.which(self.binary) or ""

    @staticmethod
    def _default_env(home_root: str | Path | None = None) -> dict[str, str]:
        env = os.environ.copy()
        if home_root is not None:
            fallback_home = str(Path(home_root))
            generated_home = True
        else:
            fallback_home = env.get("HOME") or env.get("USERPROFILE")
            generated_home = False
            if not fallback_home:
                fallback_home = str(Path.cwd() / ".code_intelligence_home")
                generated_home = True
        try:
            Path(fallback_home).mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback_home = str(Path(gettempdir()) / "code_intelligence_home")
            Path(fallback_home).mkdir(parents=True, exist_ok=True)
            generated_home = True
        if generated_home:
            env["HOME"] = fallback_home
            env["USERPROFILE"] = fallback_home
        else:
            env.setdefault("HOME", fallback_home)
            env.setdefault("USERPROFILE", fallback_home)
        if generated_home:
            env["LOCALAPPDATA"] = str(Path(fallback_home).parent)
        else:
            env.setdefault("LOCALAPPDATA", str(Path(fallback_home).parent))
        Path(env["LOCALAPPDATA"]).mkdir(parents=True, exist_ok=True)
        return env

    def _run(self, args: list[str], *, env_override: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.runner(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_sec,
            check=False,
            env=env_override or self.env or self._default_env(),
        )

    def _availability(self) -> tuple[bool, str, str, str]:
        binary_path = self._binary_path()
        if not binary_path:
            return False, "", "", "binary_not_found"
        try:
            completed = self._run([binary_path, "--version"])
        except subprocess.TimeoutExpired:
            return False, binary_path, "", "version_timeout"
        except OSError as exc:
            return False, binary_path, "", f"version_error:{exc.__class__.__name__}"
        version = (completed.stdout or completed.stderr or "").strip().splitlines()
        return True, binary_path, version[0] if version else "unknown", ""

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            return {}
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        for line in stripped.splitlines():
            candidate = line.strip()
            if not candidate.startswith("{"):
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return {"text": stripped}

    def _cli_tool(
        self,
        binary_path: str,
        tool_name: str,
        payload: dict[str, Any],
        *,
        env_override: dict[str, str] | None = None,
    ) -> tuple[dict[str, Any], float]:
        started_at = perf_counter()
        completed = self._run([binary_path, "cli", tool_name, json.dumps(payload)], env_override=env_override)
        duration_sec = round(perf_counter() - started_at, 4)
        combined_output = "\n".join(part for part in [completed.stdout or "", completed.stderr or ""] if part)
        parsed_output = self._extract_json_object(combined_output)
        if completed.returncode != 0:
            if parsed_output.get("error") or parsed_output.get("hint"):
                error_text = parsed_output.get("error") or parsed_output.get("hint")
                raise RuntimeError(str(error_text))
            stderr = (completed.stderr or "").strip()
            raise RuntimeError(stderr or f"{tool_name} exited with {completed.returncode}")
        return parsed_output, duration_sec

    @staticmethod
    def extract_search_symbols(issue_text: str, failure_summary: dict[str, Any] | None = None) -> list[str]:
        symbols: list[str] = []
        for value in (failure_summary or {}).get("possible_symbols", []) or []:
            symbol = str(value).strip()
            if symbol and symbol not in symbols:
                symbols.append(symbol)
        for code_span in CODE_SPAN_PATTERN.findall(issue_text):
            for token in SYMBOL_PATTERN.findall(code_span):
                normalized = token.lower()
                if normalized in LOW_VALUE_SYMBOLS:
                    continue
                if token not in symbols:
                    symbols.append(token)
        for token in SYMBOL_PATTERN.findall(issue_text):
            normalized = token.lower()
            if normalized in LOW_VALUE_SYMBOLS:
                continue
            if token.islower() and "_" not in token:
                continue
            if token not in symbols:
                symbols.append(token)
        return symbols[:5]

    @staticmethod
    def _result_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        if isinstance(payload.get("results"), list):
            return [item for item in payload["results"] if isinstance(item, dict)]
        if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("results"), list):
            return [item for item in payload["data"]["results"] if isinstance(item, dict)]
        return []

    @staticmethod
    def _candidate_from_item(item: dict[str, Any], *, query: str, rank: int) -> LocalizationCandidate | None:
        path = (
            item.get("file")
            or item.get("path")
            or item.get("file_path")
            or item.get("relative_path")
            or item.get("filename")
            or ""
        )
        if not path:
            return None
        symbol = str(item.get("name") or item.get("qualified_name") or item.get("symbol") or query)
        label = str(item.get("label") or item.get("type") or "graph_node")
        confidence = max(0.95 - (rank * 0.08), 0.45)
        return LocalizationCandidate(
            relative_path=str(path).replace("\\", "/"),
            reason=f"graph_search:{label}:{symbol}",
            evidence=[f"codebase-memory-mcp search_graph query `{query}` returned rank {rank + 1}."],
            confidence=round(confidence, 3),
        )

    @staticmethod
    def _is_test_like_path(relative_path: str) -> bool:
        normalized = relative_path.replace("\\", "/").lower()
        parts = normalized.split("/")
        name = parts[-1] if parts else normalized
        return (
            "tests" in parts
            or "test" in parts
            or name.startswith("test_")
            or name.endswith("_test.py")
            or name == "conftest.py"
        )

    @staticmethod
    def _candidate_path_priority(candidate: LocalizationCandidate) -> tuple[float, float, str]:
        path = candidate.relative_path.replace("\\", "/")
        lower_path = path.lower()
        score = candidate.confidence
        if CodebaseMemoryCliBackend._is_test_like_path(path):
            score -= 0.18
        if lower_path.endswith("/__init__.py"):
            score -= 0.10
        if "." not in Path(path).name:
            score -= 0.14
        if lower_path.endswith(".py") and not CodebaseMemoryCliBackend._is_test_like_path(path):
            score += 0.04
        # Prefer src/ and lib/ directories (core implementation, not exceptions/tests/docs)
        if "/src/" in lower_path or "/lib/" in lower_path:
            score += 0.12
        # Penalize exception/error/type-only modules that are unlikely to be
        # the target of a bug fix even when they contain matching symbols.
        # Note: this is a heuristic — the real implementation file is usually
        # not in a file named 'exceptions.py' or 'types.py'.
        filename = lower_path.split("/")[-1] if "/" in lower_path else lower_path
        if filename in {"exceptions.py", "errors.py", "types.py", "compat.py"}:
            score -= 0.10

        return (round(score, 4), candidate.confidence, path)

    @classmethod
    def _rerank_candidates(cls, candidates: list[LocalizationCandidate]) -> list[LocalizationCandidate]:
        reranked = sorted(candidates, key=cls._candidate_path_priority, reverse=True)
        adjusted: list[LocalizationCandidate] = []
        for candidate in reranked:
            priority_score = cls._candidate_path_priority(candidate)[0]
            adjusted.append(
                candidate.model_copy(
                    update={
                        "confidence": round(max(min(priority_score, 0.99), 0.35), 3),
                        "evidence": [
                            *candidate.evidence,
                            "Graph candidate re-ranked to prefer implementation files over tests/packages.",
                        ]
                        if "Graph candidate re-ranked to prefer implementation files over tests/packages."
                        not in candidate.evidence
                        else candidate.evidence,
                    }
                )
            )
        return adjusted

    @classmethod
    def _augment_test_candidates(
        cls,
        candidates: list[LocalizationCandidate],
        *,
        repo_path: str | Path,
    ) -> list[LocalizationCandidate]:
        augmented = list(candidates)
        known_paths = {candidate.relative_path for candidate in augmented}
        for candidate in candidates:
            if not cls._is_test_like_path(candidate.relative_path):
                continue
            for implementation_path in implementation_candidates_for_test_path(candidate.relative_path, repo_path):
                if implementation_path in known_paths:
                    continue
                known_paths.add(implementation_path)
                augmented.append(
                    LocalizationCandidate(
                        relative_path=implementation_path,
                        reason=f"graph_test_mapping:{candidate.relative_path}",
                        evidence=[
                            "Inferred implementation candidate from graph-returned test file "
                            f"`{candidate.relative_path}`."
                        ],
                        confidence=max(candidate.confidence - 0.06, 0.45),
                    )
                )
        return augmented

    @staticmethod
    def build_compact_hints(candidates: list[LocalizationCandidate], *, max_items: int = 3) -> str:
        if not candidates:
            return ""
        lines = ["Graph-assisted localization hints:"]
        for index, candidate in enumerate(candidates[:max_items], start=1):
            lines.append(
                f"- #{index} file={candidate.relative_path} conf={candidate.confidence:.2f} "
                f"reason={candidate.reason}"
            )
        return "\n".join(lines)

    def collect_localization_hints(
        self,
        *,
        repo_path: str | Path,
        issue_text: str,
        failure_summary: dict[str, Any] | None = None,
        max_results: int = 8,
    ) -> CodeIntelligenceResult:
        available, binary_path, version, availability_error = self._availability()
        base_metrics: dict[str, Any] = {
            "index_attempted": False,
            "index_success": False,
            "index_duration_sec": None,
            "index_repo_path": str(Path(repo_path).resolve()),
            "index_used_shadow_copy": False,
            "env_home": "",
            "env_userprofile": "",
            "env_localappdata": "",
            "indexed_project": "",
            "indexed_node_count": None,
            "indexed_edge_count": None,
            "indexed_file_count": None,
            "graph_tool_calls_total": 0,
            "graph_search_graph_calls": 0,
            "graph_query_duration_sec_total": 0.0,
            "graph_result_raw_chars": 0,
            "graph_result_compact_chars": 0,
            "graph_candidates_count": 0,
        }
        if not available:
            return CodeIntelligenceResult(
                backend=self.name,
                enabled=True,
                available=False,
                backend_binary_path=binary_path,
                backend_version=version,
                fallback_reason=availability_error,
                metrics=base_metrics,
            )

        try:
            index_repo_path, shadow_root, used_shadow_copy = self._prepare_index_repo_path(
                repo_path,
                always_use_shadow_copy=self.always_use_shadow_copy,
            )
            repo_cache_env = self.env or self._default_env(index_repo_path.parent / ".code_intelligence_home")
            base_metrics["index_attempted"] = True
            base_metrics["index_repo_path"] = str(index_repo_path)
            base_metrics["index_used_shadow_copy"] = used_shadow_copy
            base_metrics["env_home"] = repo_cache_env.get("HOME", "")
            base_metrics["env_userprofile"] = repo_cache_env.get("USERPROFILE", "")
            base_metrics["env_localappdata"] = repo_cache_env.get("LOCALAPPDATA", "")
            index_request = {"repo_path": str(index_repo_path)}
            if self.index_mode:
                index_request["mode"] = self.index_mode
            try:
                index_payload, index_duration_sec = self._cli_tool(
                    binary_path,
                    "index_repository",
                    index_request,
                    env_override=repo_cache_env,
                )
                base_metrics["index_success"] = True
                base_metrics["index_duration_sec"] = index_duration_sec
                project_name = str(index_payload.get("project", ""))
                base_metrics["indexed_project"] = project_name
                base_metrics["indexed_node_count"] = index_payload.get("nodes")
                base_metrics["indexed_edge_count"] = index_payload.get("edges")
                base_metrics["indexed_file_count"] = index_payload.get("files")

                candidates: list[LocalizationCandidate] = []
                raw_chars = 0
                total_query_duration = 0.0
                for query in self.extract_search_symbols(issue_text, failure_summary):
                    payload, duration_sec = self._cli_tool(
                        binary_path,
                        "search_graph",
                        {
                            "project": project_name,
                            "name_pattern": f".*{re.escape(query)}.*",
                            "limit": max_results,
                        },
                        env_override=repo_cache_env,
                    )
                    base_metrics["graph_tool_calls_total"] += 1
                    base_metrics["graph_search_graph_calls"] += 1
                    total_query_duration += duration_sec
                    raw_chars += len(json.dumps(payload, ensure_ascii=False))
                    for rank, item in enumerate(self._result_items(payload)):
                        candidate = self._candidate_from_item(item, query=query, rank=rank)
                        if candidate and candidate.relative_path not in {c.relative_path for c in candidates}:
                            candidates.append(candidate)
                        if len(candidates) >= max_results:
                            break
                    if len(candidates) >= max_results:
                        break

                candidates = self._augment_test_candidates(candidates, repo_path=index_repo_path)
                candidates = self._rerank_candidates(candidates)
                compact_hints = self.build_compact_hints(candidates)
                base_metrics["graph_query_duration_sec_total"] = round(total_query_duration, 4)
                base_metrics["graph_result_raw_chars"] = raw_chars
                base_metrics["graph_result_compact_chars"] = len(compact_hints)
                base_metrics["graph_compaction_ratio"] = round(len(compact_hints) / raw_chars, 4) if raw_chars else 0.0
                base_metrics["graph_candidates_count"] = len(candidates)
                # Store indexed state so search_graph_query() can query later.
                self._cached_binary_path = binary_path
                self._indexed_project = project_name
                self._cached_env = repo_cache_env
                self._shadow_root = shadow_root
                return CodeIntelligenceResult(
                    backend=self.name,
                    enabled=True,
                    available=True,
                    backend_binary_path=binary_path,
                    backend_version=version,
                    fallback_reason="empty_results" if not candidates else "",
                    candidates=candidates,
                    compact_hints=compact_hints,
                    metrics=base_metrics,
                )
            finally:
                if shadow_root is not None:
                    self._shadow_root = shadow_root
        except subprocess.TimeoutExpired:
            base_metrics["index_success"] = False
            return CodeIntelligenceResult(
                backend=self.name,
                enabled=True,
                available=True,
                backend_binary_path=binary_path,
                backend_version=version,
                fallback_reason="backend_timeout",
                metrics=base_metrics,
            )
        except RuntimeError as exc:
            return CodeIntelligenceResult(
                backend=self.name,
                enabled=True,
                available=True,
                backend_binary_path=binary_path,
                backend_version=version,
                fallback_reason=f"backend_error:{str(exc)[:160]}",
                metrics=base_metrics,
            )

    def search_graph_query(
        self,
        *,
        name_pattern: str,
        max_results: int = 10,
    ) -> dict[str, Any]:
        if not self._indexed_project or not self._cached_binary_path:
            return {
                "ok": False,
                "tool_name": "search_graph",
                "summary": "Graph index is not available.",
                "data": {"results": [], "backend": self.name},
                "error": {
                    "type": "index_not_ready",
                    "message": "The codebase graph has not been indexed for this run.",
                },
            }
        try:
            payload, _duration_sec = self._cli_tool(
                self._cached_binary_path,
                "search_graph",
                {
                    "project": self._indexed_project,
                    "name_pattern": name_pattern,
                    "limit": max_results,
                },
                env_override=self._cached_env,
            )
            results: list[dict[str, Any]] = []
            for rank, item in enumerate(self._result_items(payload)):
                candidate_entry = self._candidate_from_item(item, query=name_pattern, rank=rank)
                if candidate_entry:
                    results.append({
                        "file": candidate_entry.relative_path,
                        "reason": candidate_entry.reason,
                        "confidence": candidate_entry.confidence,
                    })
            match_files = [entry["file"] for entry in results[:5]]
            summary_text = (
                f"Graph search for `{name_pattern}` matched {len(results)} results."
            )
            return {
                "ok": True,
                "tool_name": "search_graph",
                "summary": summary_text,
                "data": {
                    "query": name_pattern,
                    "match_count": len(results),
                    "match_files": match_files,
                    "matches": results[:max_results],
                },
                "error": None,
            }
        except (subprocess.TimeoutExpired, RuntimeError, OSError) as exc:
            return {
                "ok": False,
                "tool_name": "search_graph",
                "summary": f"Graph search failed: {exc}",
                "data": {"results": [], "match_files": [], "name_pattern": name_pattern},
                "error": {
                    "type": "graph_query_error",
                    "message": str(exc)[:200],
                },
            }

    def cleanup(self) -> None:
        if self._shadow_root is not None:
            shutil.rmtree(self._shadow_root, ignore_errors=True)
            self._shadow_root = None

    def is_indexed(self) -> bool:
        return self._indexed_project is not None and bool(self._cached_binary_path)


def build_code_intelligence_backend(policy_config: object) -> CodeIntelligenceBackend:
    """Build the optional code intelligence backend from policy settings."""

    backend_name = str(getattr(policy_config, "code_intelligence_backend", "none") or "none").strip().lower()
    if backend_name in {"", "none", "disabled", "null"}:
        return NullCodeIntelligenceBackend()
    if backend_name == CodebaseMemoryCliBackend.name:
        return CodebaseMemoryCliBackend(
            binary=str(getattr(policy_config, "codebase_memory_binary", "codebase-memory-mcp")),
            timeout_sec=float(getattr(policy_config, "code_intelligence_timeout_sec", 10.0)),
            index_mode=str(getattr(policy_config, "codebase_memory_index_mode", "fast") or ""),
            always_use_shadow_copy=bool(getattr(policy_config, "codebase_memory_always_shadow_copy", True)),
        )
    return NullCodeIntelligenceBackend()
