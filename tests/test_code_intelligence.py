from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from app.agent.code_intelligence import (
    CodebaseMemoryCliBackend,
    NullCodeIntelligenceBackend,
    SHADOW_COPY_PATH_LENGTH_THRESHOLD,
    build_code_intelligence_backend,
)
from app.agent.memory import LocalizationCandidate
from app.agent.policy import PolicyConfig


def test_null_code_intelligence_backend_is_disabled(tmp_path: Path) -> None:
    result = NullCodeIntelligenceBackend().collect_localization_hints(
        repo_path=tmp_path,
        issue_text="Parser should handle empty input",
    )

    assert result.backend == "none"
    assert result.enabled is False
    assert result.fallback_reason == "backend_disabled"
    assert result.metrics["graph_tool_calls_total"] == 0


def test_policy_defaults_keep_code_intelligence_disabled() -> None:
    policy = PolicyConfig(policy_id="test", description="test")

    backend = build_code_intelligence_backend(policy)

    assert isinstance(backend, NullCodeIntelligenceBackend)
    assert policy.code_intelligence_backend == "none"
    assert policy.codebase_memory_binary == "codebase-memory-mcp"
    assert policy.codebase_memory_index_mode == "fast"
    assert policy.codebase_memory_always_shadow_copy is True


def test_codebase_memory_cli_backend_falls_back_when_binary_missing(tmp_path: Path) -> None:
    backend = CodebaseMemoryCliBackend(binary="definitely-missing-codebase-memory-mcp")

    result = backend.collect_localization_hints(
        repo_path=tmp_path,
        issue_text="HostnameValidator rejects single label hostnames",
        max_results=1,
    )

    assert result.enabled is True
    assert result.available is False
    assert result.fallback_reason == "binary_not_found"
    assert result.metrics["index_attempted"] is False


def test_codebase_memory_cli_backend_compacts_search_results(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "codebase-memory-mcp"
    binary.write_text("", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_which(_: str) -> str:
        return str(binary)

    def fake_runner(args, capture_output, text, timeout, check, env, **kwargs):
        calls.append(args)
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")
        if args[2] == "index_repository":
            payload = json.loads(args[3])
            assert payload["mode"] == "fast"
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "project": "sample-project",
                        "status": "indexed",
                        "nodes": 11,
                        "edges": 17,
                    }
                ),
                stderr="",
            )
        if args[2] == "search_graph":
            payload = json.loads(args[3])
            assert payload["project"] == "sample-project"
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "results": [
                            {
                                "file": "demo_pkg/hostname.py",
                                "name": "HostnameValidator",
                                "label": "Class",
                            }
                        ]
                    }
                ),
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr("app.agent.code_intelligence.shutil.which", fake_which)
    backend = CodebaseMemoryCliBackend(binary="codebase-memory-mcp", runner=fake_runner)

    result = backend.collect_localization_hints(
        repo_path=tmp_path,
        issue_text="HostnameValidator rejects single label hostnames",
        max_results=1,
    )

    assert result.available is True
    assert result.backend_version == "codebase-memory-mcp 0.8.1"
    assert result.candidates[0].relative_path == "demo_pkg/hostname.py"
    assert "Graph-assisted localization hints" in result.compact_hints
    assert result.metrics["index_success"] is True
    assert result.metrics["indexed_project"] == "sample-project"
    assert result.metrics["indexed_node_count"] == 11
    assert result.metrics["indexed_edge_count"] == 17
    assert result.metrics["graph_search_graph_calls"] == 1
    assert calls[1][1:3] == ["cli", "index_repository"]
    assert calls[2][1:3] == ["cli", "search_graph"]


def test_codebase_memory_cli_backend_compact_hints_are_token_budgeted() -> None:
    candidates = [
        LocalizationCandidate(
            relative_path=f"pkg/module_{index}.py",
            reason=f"graph_search:Function:symbol_{index}",
            evidence=[
                "codebase-memory-mcp search_graph query `VeryLongSymbolName` returned rank "
                f"{index} with extra verbose details that should stay in metrics only."
            ],
            confidence=0.95 - (index * 0.05),
        )
        for index in range(5)
    ]

    compact_hints = CodebaseMemoryCliBackend.build_compact_hints(candidates)

    lines = compact_hints.splitlines()
    assert lines[0] == "Graph-assisted localization hints:"
    assert len(lines) == 4
    assert "conf=0.95" in lines[1]
    assert "evidence=" not in compact_hints
    assert "VeryLongSymbolName" not in compact_hints
    assert "pkg/module_3.py" not in compact_hints


def test_codebase_memory_cli_backend_reranks_source_files_before_tests(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "codebase-memory-mcp"
    binary.write_text("", encoding="utf-8")

    def fake_which(_: str) -> str:
        return str(binary)

    def fake_runner(args, capture_output, text, timeout, check, env, **kwargs):
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")
        if args[2] == "index_repository":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps({"project": "sample-project", "nodes": 2, "edges": 1}),
                stderr="",
            )
        if args[2] == "search_graph":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "results": [
                            {"file_path": "tests/test_utils.py", "name": "test_charset", "label": "Function"},
                            {"file_path": "demo_pkg/utils.py", "name": "get_charset", "label": "Function"},
                        ]
                    }
                ),
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr("app.agent.code_intelligence.shutil.which", fake_which)
    backend = CodebaseMemoryCliBackend(binary="codebase-memory-mcp", runner=fake_runner)

    result = backend.collect_localization_hints(
        repo_path=tmp_path,
        issue_text="get_charset fails for quoted charset",
        max_results=2,
    )

    assert [candidate.relative_path for candidate in result.candidates] == [
        "demo_pkg/utils.py",
        "tests/test_utils.py",
    ]
    assert "file=demo_pkg/utils.py" in result.compact_hints.splitlines()[1]


def test_codebase_memory_cli_backend_augments_test_candidate_with_implementation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo = tmp_path / "repo"
    (repo / "tests").mkdir(parents=True)
    (repo / "setup.py").write_text("def get_install_requires():\n    return []\n", encoding="utf-8")
    (repo / "tests" / "test_setup.py").write_text("def test_setup():\n    assert True\n", encoding="utf-8")
    binary = tmp_path / "codebase-memory-mcp"
    binary.write_text("", encoding="utf-8")

    def fake_which(_: str) -> str:
        return str(binary)

    def fake_runner(args, capture_output, text, timeout, check, env, **kwargs):
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")
        if args[2] == "index_repository":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps({"project": "sample-project", "nodes": 2, "edges": 1}),
                stderr="",
            )
        if args[2] == "search_graph":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "results": [
                            {"file_path": "tests/test_setup.py", "name": "test_setup", "label": "Function"}
                        ]
                    }
                ),
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr("app.agent.code_intelligence.shutil.which", fake_which)
    backend = CodebaseMemoryCliBackend(binary="codebase-memory-mcp", runner=fake_runner)

    result = backend.collect_localization_hints(
        repo_path=repo,
        issue_text="get_install_requires should allow urllib3 2",
        max_results=2,
    )

    assert [candidate.relative_path for candidate in result.candidates] == [
        "setup.py",
        "tests/test_setup.py",
    ]
    assert result.candidates[0].reason == "graph_test_mapping:tests/test_setup.py"
    assert "file=setup.py" in result.compact_hints.splitlines()[1]


def test_build_codebase_memory_cli_backend_uses_policy_index_mode() -> None:
    policy = PolicyConfig(
        policy_id="test",
        description="test",
        code_intelligence_backend="codebase_memory_cli",
        codebase_memory_binary="custom-codebase-memory",
        codebase_memory_index_mode="",
        code_intelligence_timeout_sec=3,
    )

    backend = build_code_intelligence_backend(policy)

    assert isinstance(backend, CodebaseMemoryCliBackend)
    assert backend.binary == "custom-codebase-memory"
    assert backend.timeout_sec == 3
    assert backend.index_mode == ""
    assert backend.always_use_shadow_copy is True


def test_codebase_memory_cli_backend_extracts_json_from_mixed_output() -> None:
    payload = CodebaseMemoryCliBackend._extract_json_object(
        '{"project":"sample","status":"indexed","nodes":2}\n'
        "level=info msg=mem.init budget_mb=10\n"
    )

    assert payload == {"project": "sample", "status": "indexed", "nodes": 2}


def test_codebase_memory_cli_backend_prefers_code_like_search_symbols() -> None:
    symbols = CodebaseMemoryCliBackend.extract_search_symbols(
        "HostnameValidator rejects single label hostnames in `parse_hostname`",
        {"possible_symbols": ["validate_hostname"]},
    )

    assert symbols == ["validate_hostname", "parse_hostname", "HostnameValidator"]
    assert "single" not in symbols
    assert "label" not in symbols


def test_codebase_memory_cli_backend_uses_shadow_copy_for_long_repo_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    long_repo = tmp_path
    while len(str(long_repo.resolve())) <= SHADOW_COPY_PATH_LENGTH_THRESHOLD:
        long_repo = long_repo / "very_long_repo_segment"
    (long_repo / "demo_pkg").mkdir(parents=True)
    (long_repo / ".git").mkdir()
    (long_repo / "__pycache__").mkdir()
    (long_repo / "demo_pkg" / "hostname.py").write_text("class HostnameValidator:\n    pass\n", encoding="utf-8")
    (long_repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (long_repo / "__pycache__" / "ignored.pyc").write_text("ignored", encoding="utf-8")
    binary = tmp_path / "codebase-memory-mcp"
    binary.write_text("", encoding="utf-8")
    indexed_repo_paths: list[Path] = []

    def fake_which(_: str) -> str:
        return str(binary)

    def fake_runner(args, capture_output, text, timeout, check, env, **kwargs):
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")
        if args[2] == "index_repository":
            payload = json.loads(args[3])
            indexed_repo_path = Path(payload["repo_path"])
            indexed_repo_paths.append(indexed_repo_path)
            assert indexed_repo_path != long_repo.resolve()
            assert len(str(indexed_repo_path)) < len(str(long_repo.resolve()))
            assert (indexed_repo_path / "demo_pkg" / "hostname.py").exists()
            assert not (indexed_repo_path / ".git").exists()
            assert not (indexed_repo_path / "__pycache__").exists()
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps({"project": "shadow-project", "nodes": 1, "edges": 0}),
                stderr="",
            )
        if args[2] == "search_graph":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "results": [
                            {
                                "file_path": "demo_pkg/hostname.py",
                                "name": "HostnameValidator",
                                "label": "Class",
                            }
                        ]
                    }
                ),
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr("app.agent.code_intelligence.shutil.which", fake_which)
    backend = CodebaseMemoryCliBackend(binary="codebase-memory-mcp", runner=fake_runner)

    result = backend.collect_localization_hints(
        repo_path=long_repo,
        issue_text="HostnameValidator fails",
    )

    assert indexed_repo_paths
    assert result.metrics["index_used_shadow_copy"] is True
    assert result.metrics["index_repo_path"] == str(indexed_repo_paths[0])
    assert result.candidates[0].relative_path == "demo_pkg/hostname.py"


def test_codebase_memory_cli_backend_uses_shadow_copy_by_default_for_short_repo_path(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    index_repo_path, shadow_root, used_shadow_copy = CodebaseMemoryCliBackend._prepare_index_repo_path(repo)

    try:
        assert used_shadow_copy is True
        assert shadow_root is not None
        assert index_repo_path != repo.resolve()
        assert index_repo_path.name == "repo"
    finally:
        if shadow_root is not None:
            import shutil

            shutil.rmtree(shadow_root, ignore_errors=True)


def test_codebase_memory_cli_backend_uses_json_hint_for_failed_tool(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "codebase-memory-mcp"
    binary.write_text("", encoding="utf-8")

    def fake_which(_: str) -> str:
        return str(binary)

    def fake_runner(args, capture_output, text, timeout, check, env, **kwargs):
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="codebase-memory-mcp 0.8.1\n", stderr="")
        return subprocess.CompletedProcess(
            args,
            1,
            stdout=(
                "level=info msg=mem.init\n"
                '{"status":"error","hint":"Pipeline failed. Try mode=fast."}\n'
            ),
            stderr="level=error msg=pipeline.err phase=dump\n",
        )

    monkeypatch.setattr("app.agent.code_intelligence.shutil.which", fake_which)
    backend = CodebaseMemoryCliBackend(binary="codebase-memory-mcp", runner=fake_runner)

    result = backend.collect_localization_hints(
        repo_path=tmp_path,
        issue_text="HostnameValidator rejects single label hostnames",
    )

    assert result.available is True
    assert result.fallback_reason == "backend_error:Pipeline failed. Try mode=fast."


def test_codebase_memory_cli_backend_falls_back_when_home_root_unwritable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fallback_home = tmp_path / "code_intelligence_home"

    def fake_mkdir(self, parents=False, exist_ok=False):  # noqa: ANN001
        if self in {fallback_home, tmp_path}:
            return None
        raise PermissionError("blocked")

    monkeypatch.setattr("app.agent.code_intelligence.gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(Path, "mkdir", fake_mkdir)

    env = CodebaseMemoryCliBackend._default_env(tmp_path / "blocked_home")

    assert Path(env["HOME"]) == fallback_home
    assert env["USERPROFILE"] == str(fallback_home)
    assert os.environ.get("HOME") != str(fallback_home)
