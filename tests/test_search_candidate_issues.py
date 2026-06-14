from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import search_candidate_issues


def test_build_candidate_summary_ignores_code_blocks_for_family_guess() -> None:
    raw_issue = {
        "number": 2411,
        "title": "[BUG] UnicodeEncodeError on Windows with ruler.",
        "url": "https://github.com/Textualize/rich/issues/2411",
        "labels": [{"name": "bug"}],
        "state": "closed",
        "createdAt": "2022-07-20T21:45:49Z",
        "repository": {"owner": {"login": "Textualize"}, "name": "rich"},
        "body": """**Describe the bug**

When rendering a ruler on Windows, Rich raises `UnicodeEncodeError`.

```python
import subprocess

result = subprocess.run(("python", "rich_script.py"), check=True)
```
""",
    }

    summary = search_candidate_issues.build_candidate_summary(raw_issue, "Textualize/rich")

    assert summary["family"] == "解析与字符串语义"
    assert summary["recommendation"] == "medium"
    assert "并发或时序抖动" not in summary["risk_notes"]
    assert "跨平台稳定测试" in summary["risk_notes"]


def test_build_candidate_summary_ignores_urls_for_network_risk_guess() -> None:
    raw_issue = {
        "number": 3176,
        "title": "[BUG] Chunks of text go missing when writing Asian text (wrapping issue)",
        "url": "https://github.com/Textualize/rich/issues/3176",
        "labels": [{"name": "bug"}],
        "state": "closed",
        "createdAt": "2023-10-30T15:41:51Z",
        "repository": {"owner": {"login": "Textualize"}, "name": "rich"},
        "body": """### Description

(Originally reported in Textual: https://github.com/Textualize/textual/issues/3567)

When you print Asian text, portions of the text go missing.
This seems related to wrapping at the end of a line.
""",
    }

    summary = search_candidate_issues.build_candidate_summary(raw_issue, "Textualize/rich")

    assert summary["family"] == "解析与字符串语义"
    assert summary["recommendation"] == "medium"
    assert "重环境问题" not in summary["risk_notes"]


def test_normalize_target_family_supports_aliases() -> None:
    assert search_candidate_issues.normalize_target_family("async") == "并发与协程"
    assert search_candidate_issues.normalize_target_family("路径") == "文件路径与 IO"
    assert search_candidate_issues.normalize_target_family("priority") == "继承、优先级与控制流"


def test_build_search_query_expands_family_preset() -> None:
    query = search_candidate_issues.build_search_query(
        user_query="bug",
        target_family="并发与协程",
    )

    assert query == "bug"


def test_build_search_query_falls_back_when_family_unknown() -> None:
    query = search_candidate_issues.build_search_query(
        user_query=None,
        target_family="未知家族",
    )

    assert query == "bug"


def test_build_search_queries_expands_family_preset() -> None:
    queries = search_candidate_issues.build_search_queries(
        user_query="bug",
        target_family="并发与协程",
    )

    assert queries[0] == "bug"
    assert "bug asyncio" in queries
    assert 'bug "event loop"' in queries


def test_build_search_summary_records_target_family() -> None:
    summary = search_candidate_issues.build_search_summary(
        repo="trio/trio",
        query='bug (asyncio OR async)',
        target_family="并发与协程",
        state="closed",
        labels=["bug"],
        limit=5,
        candidates=[],
    )

    assert summary["target_family"] == "并发与协程"


def test_build_markdown_includes_target_family() -> None:
    summary = {
        "repo": "trio/trio",
        "query": 'bug (asyncio OR async)',
        "target_family": "并发与协程",
        "state": "closed",
        "labels": ["bug"],
        "candidate_count": 0,
        "family_counts": {},
        "recommendation_counts": {},
        "candidates": [],
    }

    markdown = search_candidate_issues.build_markdown(summary)

    assert "target_family: `并发与协程`" in markdown


def test_resolve_gh_token_prefers_keyring_when_env_token_is_not_github_like(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "invalid-token")
    monkeypatch.delenv("GH_TOKEN", raising=False)

    calls: list[dict[str, str] | None] = []

    def fake_run_gh_auth_token(*, extra_env: dict[str, str] | None = None) -> str | None:
        calls.append(extra_env)
        return "ghp_from_keyring"

    monkeypatch.setattr(search_candidate_issues, "_run_gh_auth_token", fake_run_gh_auth_token)

    token = search_candidate_issues._resolve_gh_token()

    assert token == "ghp_from_keyring"
    assert calls
    assert calls[0] is not None
    assert "GITHUB_TOKEN" not in calls[0]


def test_resolve_gh_token_prefers_env_when_it_looks_like_github_token(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_envtoken")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.setattr(search_candidate_issues, "_run_gh_auth_token", lambda **_: "ghp_from_keyring")

    token = search_candidate_issues._resolve_gh_token()

    assert token == "ghp_envtoken"


def test_run_gh_search_allows_logged_in_gh_without_exportable_token(monkeypatch) -> None:
    monkeypatch.setattr(search_candidate_issues, "_resolve_gh_token_candidates", lambda **_: [None])

    observed_env: dict[str, str] = {}

    class FakeCompletedProcess:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = json.dumps(
                [
                    {
                        "number": 1,
                        "title": "demo",
                        "url": "https://example.com/1",
                        "labels": [],
                        "state": "closed",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "body": "",
                        "repository": {"owner": {"login": "demo"}, "name": "repo"},
                    }
                ]
            ).encode("utf-8")
            self.stderr = b""

    def fake_run(command, cwd, capture_output, check, env):
        observed_env.update(env)
        return FakeCompletedProcess()

    monkeypatch.setattr(search_candidate_issues.subprocess, "run", fake_run)

    results = search_candidate_issues.run_gh_search(
        repo="demo/repo",
        queries=["bug"],
        state="closed",
        labels=["bug"],
        limit=1,
    )

    assert len(results) == 1
    assert "GITHUB_TOKEN" not in observed_env
    assert "GH_TOKEN" not in observed_env


def test_run_gh_search_injects_token_when_available(monkeypatch) -> None:
    monkeypatch.setattr(search_candidate_issues, "_resolve_gh_token_candidates", lambda **_: ["ghp_demo_token"])

    observed_env: dict[str, str] = {}

    class FakeCompletedProcess:
        def __init__(self) -> None:
            self.returncode = 0
            self.stdout = b"[]"
            self.stderr = b""

    def fake_run(command, cwd, capture_output, check, env):
        observed_env.update(env)
        return FakeCompletedProcess()

    monkeypatch.setattr(search_candidate_issues.subprocess, "run", fake_run)

    results = search_candidate_issues.run_gh_search(
        repo="demo/repo",
        queries=["bug"],
        state="closed",
        labels=[],
        limit=1,
    )

    assert results == []
    assert observed_env["GITHUB_TOKEN"] == "ghp_demo_token"


def test_resolve_gh_token_candidates_keeps_env_and_keyring_fallback(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_envtoken")
    monkeypatch.delenv("GH_TOKEN", raising=False)

    calls: list[dict[str, str] | None] = []

    def fake_run_gh_auth_token(*, extra_env: dict[str, str] | None = None) -> str | None:
        calls.append(extra_env)
        if extra_env is not None:
            return "ghp_from_keyring"
        return None

    monkeypatch.setattr(search_candidate_issues, "_run_gh_auth_token", fake_run_gh_auth_token)

    candidates = search_candidate_issues._resolve_gh_token_candidates()

    assert candidates == ["ghp_envtoken", "ghp_from_keyring", None]
    assert calls
    assert calls[0] is not None
    assert "GITHUB_TOKEN" not in calls[0]


def test_run_gh_search_falls_back_to_keyring_token_after_env_token_401(monkeypatch) -> None:
    monkeypatch.setattr(
        search_candidate_issues,
        "_resolve_gh_token_candidates",
        lambda **_: ["ghp_bad_env", "ghp_good_keyring", None],
    )

    observed_tokens: list[str | None] = []

    class FakeCompletedProcess:
        def __init__(self, *, returncode: int, stdout: bytes, stderr: bytes) -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(command, cwd, capture_output, check, env):
        token = env.get("GITHUB_TOKEN")
        observed_tokens.append(token)
        if token == "ghp_bad_env":
            return FakeCompletedProcess(
                returncode=1,
                stdout=b"",
                stderr=b'{"message":"Bad credentials","status":"401"}',
            )
        return FakeCompletedProcess(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "number": 2,
                        "title": "demo fallback",
                        "url": "https://example.com/2",
                        "labels": [],
                        "state": "closed",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "body": "",
                        "repository": {"owner": {"login": "demo"}, "name": "repo"},
                    }
                ]
            ).encode("utf-8"),
            stderr=b"",
        )

    monkeypatch.setattr(search_candidate_issues.subprocess, "run", fake_run)

    results = search_candidate_issues.run_gh_search(
        repo="demo/repo",
        queries=["bug"],
        state="closed",
        labels=[],
        limit=1,
    )

    assert len(results) == 1
    assert observed_tokens == ["ghp_bad_env", "ghp_good_keyring"]
