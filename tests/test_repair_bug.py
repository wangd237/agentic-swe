from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.llm_agent import LLMCodeAgent
from app.agent.llm_config import LLMConfig
from scripts import repair_bug


def write_text(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class FakeRepairClient:
    def __init__(self, fixed_content: str) -> None:
        self.fixed_content = fixed_content
        self._call_count = 0

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {"type": "text", "text": "先复现失败。"},
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "run_tests",
                        "input": {"timeout_sec": 30},
                    },
                ]
            }
        if self._call_count == 2:
            return {
                "content": [
                    {"type": "text", "text": "根据失败测试修改候选实现文件。"},
                    {
                        "type": "tool_use",
                        "id": "tool_2",
                        "name": "write_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "content": self.fixed_content,
                        },
                    },
                ]
            }
        return {
            "content": [
                {"type": "text", "text": "自动验证已经完成，输出最终结果。"},
            ]
        }


def test_build_user_task_uses_relative_repo_path_and_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    local_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    local_repo.mkdir(parents=True)

    task = repair_bug.build_user_task(
        repo_path=local_repo,
        issue="Parser drops the last item\nMore details here.",
        test_command="python -m pytest tests/test_parser.py -q",
        test_source="explicit",
        task_id="user_demo",
        repo_root=repo_root,
    )

    payload = task.to_dict()
    assert payload["task_id"] == "user_demo"
    assert payload["repo_name"] == "demo_repo"
    assert payload["repo_path"] == "benchmarks/repos/demo_repo"
    assert payload["issue_title"] == "Parser drops the last item"
    assert payload["issue_text"] == "Parser drops the last item\nMore details here."
    assert payload["test_command"] == "python -m pytest tests/test_parser.py -q"
    assert payload["source_type"] == "user_local"
    assert payload["metadata"]["test_command_source"] == "explicit"
    assert payload["metadata"]["verification_strength"] == "normal"


def test_discover_test_command_prefers_explicit_command(tmp_path: Path) -> None:
    command, source = repair_bug.discover_test_command(
        tmp_path,
        explicit_test="python -m pytest tests/test_specific.py -q",
    )

    assert command == "python -m pytest tests/test_specific.py -q"
    assert source == "explicit"


def test_discover_test_command_detects_pytest_from_tests_dir(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()

    command, source = repair_bug.discover_test_command(tmp_path)

    assert command == "python -m pytest -q"
    assert source == "pytest_auto"


def test_discover_test_command_uses_weak_fallback_without_tests(tmp_path: Path) -> None:
    command, source = repair_bug.discover_test_command(tmp_path)

    assert command == "python -m pytest -q"
    assert source == "pytest_fallback"


def test_parse_github_repo_url_supports_https_and_git_suffix() -> None:
    assert repair_bug.parse_github_repo_url("https://github.com/psf/requests.git") == ("psf", "requests")
    assert repair_bug.parse_github_repo_url("https://github.com/pallets/flask") == ("pallets", "flask")


def test_parse_github_issue_url_extracts_repo_and_issue_number() -> None:
    assert repair_bug.parse_github_issue_url("https://github.com/owner/repo/issues/123") == ("owner", "repo", 123)


def test_run_repair_bug_writes_task_and_calls_agent(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    local_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    write_text(local_repo / "tests" / "test_demo.py", "def test_demo():\n    assert True\n")
    policy_path = repo_root / "optimization" / "policy_versions" / "policy.json"
    write_text(policy_path, "{}")
    calls: dict[str, object] = {}

    def fake_run_agent(*, task_path: str | Path, repo_root: str | Path, policy_path: str | Path | None = None) -> dict:
        calls["task_path"] = Path(task_path)
        calls["repo_root"] = Path(repo_root)
        calls["policy_path"] = Path(policy_path) if policy_path is not None else None
        return {
            "result": {
                "run_id": "run_001",
                "final_status": "success",
            },
            "run_paths": {
                "summary_md_path": str(Path(repo_root) / "logs" / "trajectories" / "user_demo" / "run_001" / "summary.md"),
                "trace_json_path": str(Path(repo_root) / "logs" / "trajectories" / "user_demo" / "run_001" / "trace.json"),
                "result_json_path": str(Path(repo_root) / "logs" / "trajectories" / "user_demo" / "run_001" / "result.json"),
            },
        }

    monkeypatch.setattr(repair_bug, "run_agent", fake_run_agent)

    output = repair_bug.run_repair_bug(
        repo=local_repo,
        issue="Fix demo bug",
        policy=policy_path,
        task_id="user_demo",
        repo_root=repo_root,
    )

    task_path = Path(output["task_path"])
    task_payload = json.loads(task_path.read_text(encoding="utf-8"))
    assert task_path == repo_root / "logs" / "user_tasks" / "user_demo.json"
    assert task_payload["repo_path"] == "benchmarks/repos/demo_repo"
    assert task_payload["test_command"] == "python -m pytest -q"
    assert task_payload["metadata"]["test_command_source"] == "pytest_auto"
    assert calls["task_path"] == task_path
    assert calls["repo_root"] == repo_root
    assert calls["policy_path"] == policy_path
    assert output["result"]["final_status"] == "success"


def test_run_repair_bug_smoke_runs_llm_agent_core_with_fake_client(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path
    local_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"
    fixed_content = "def value():\n    return 1\n"

    write_text(local_repo / "demo_pkg" / "__init__.py", "")
    write_text(local_repo / "demo_pkg" / "app.py", "def value():\n    return 0\n")
    write_text(
        local_repo / "tests" / "test_app.py",
        "from demo_pkg.app import value\n\n\ndef test_value():\n    assert value() == 1\n",
    )
    write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "fake-client smoke policy",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "max_steps": 5,
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    def fake_run_agent(
        *,
        task_path: str | Path,
        repo_root: str | Path,
        policy_path: str | Path | None = None,
    ) -> dict:
        agent = LLMCodeAgent(
            llm_config=LLMConfig(model="fake-model", max_iterations=5),
            client=FakeRepairClient(fixed_content),
        )
        return agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)

    monkeypatch.setattr(repair_bug, "run_agent", fake_run_agent)

    output = repair_bug.run_repair_bug(
        repo=local_repo,
        issue="value() should return 1",
        test=f'"{sys.executable}" -m pytest tests/test_app.py -q',
        policy=policy_path,
        task_id="user_smoke_demo",
        repo_root=repo_root,
    )

    run_test_steps = [
        step for step in output["run_output"]["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    full_verify_steps = [
        step for step in run_test_steps
        if step["tool_input"].get("verification_scope") == "full"
    ]

    assert output["final_status"] == "success"
    assert output["result"]["patch_applied"] is True
    assert output["result"]["pre_test_exit_code"] != 0
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["tool_stats"]["verification_strength"] == "full"
    assert output["result"]["tool_stats"]["final_phase"] == "final"
    assert output["result"]["tool_stats"]["agent_core_metrics"]["phase_completion_rate"] == 1.0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["pre_repro_rate"] == 1.0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["write_before_repro_count"] == 0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["success_full_verify_rate"] == 1.0
    assert full_verify_steps


def test_run_repair_bug_smoke_reports_weak_fallback_verification(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path
    local_repo = repo_root / "benchmarks" / "repos" / "weak_repo"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"
    fixed_content = "def value():\n    return 1\n"

    write_text(local_repo / "demo_pkg" / "__init__.py", "")
    write_text(local_repo / "demo_pkg" / "app.py", "def value():\n    return 0\n")
    write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "fake-client weak fallback policy",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "max_steps": 3,
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    def fake_run_agent(
        *,
        task_path: str | Path,
        repo_root: str | Path,
        policy_path: str | Path | None = None,
    ) -> dict:
        agent = LLMCodeAgent(
            llm_config=LLMConfig(model="fake-model", max_iterations=3),
            client=FakeRepairClient(fixed_content),
        )
        return agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)

    monkeypatch.setattr(repair_bug, "run_agent", fake_run_agent)

    output = repair_bug.run_repair_bug(
        repo=local_repo,
        issue="value() should return 1",
        policy=policy_path,
        task_id="user_weak_demo",
        repo_root=repo_root,
    )

    assert output["fallback_warning"] is True
    assert output["test_command_source"] == "pytest_fallback"
    assert output["final_status"] == "success_weak_verification"
    assert output["result"]["incomplete_reason"] == "weak_verification"
    assert output["result"]["patch_applied"] is True
    assert output["result"]["tool_stats"]["verification_strength"] == "weak"
    assert output["result"]["tool_stats"]["agent_core_metrics"]["weak_success_rate"] == 1.0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["success_full_verify_rate"] == 0.0


def test_run_repair_bug_clones_github_repo_and_points_task_at_clone(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    policy_path = repo_root / "optimization" / "policy_versions" / "policy.json"
    write_text(policy_path, "{}")
    calls: dict[str, object] = {}

    def fake_run(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        encoding: str,
        errors: str,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls["clone_command"] = command
        destination = Path(command[-1])
        write_text(destination / "tests" / "test_demo.py", "def test_demo():\n    assert True\n")
        return subprocess.CompletedProcess(command, 0, stdout="cloned", stderr="")

    def fake_run_agent(*, task_path: str | Path, repo_root: str | Path, policy_path: str | Path | None = None) -> dict:
        calls["task_path"] = Path(task_path)
        calls["repo_root"] = Path(repo_root)
        calls["policy_path"] = Path(policy_path) if policy_path is not None else None
        return {
            "result": {"run_id": "run_001", "final_status": "success"},
            "run_paths": {
                "summary_md_path": str(Path(repo_root) / "logs" / "summary.md"),
                "trace_json_path": str(Path(repo_root) / "logs" / "trace.json"),
                "result_json_path": str(Path(repo_root) / "logs" / "result.json"),
            },
        }

    monkeypatch.setattr(repair_bug.subprocess, "run", fake_run)
    monkeypatch.setattr(repair_bug, "run_agent", fake_run_agent)

    output = repair_bug.run_repair_bug(
        repo="https://github.com/owner/demo",
        issue="Fix demo bug",
        policy=policy_path,
        task_id="user_github_demo",
        repo_root=repo_root,
    )

    clone_command = calls["clone_command"]
    assert clone_command[:4] == ["git", "clone", "--depth", "1"]
    assert clone_command[4] == "https://github.com/owner/demo"
    cloned_repo_path = Path(output["cloned_repo_path"])
    assert cloned_repo_path == repo_root / "logs" / "github_repos" / cloned_repo_path.parent.name / "repo"
    assert cloned_repo_path.exists()
    task_payload = json.loads(Path(output["task_path"]).read_text(encoding="utf-8"))
    assert task_payload["repo_path"] == cloned_repo_path.relative_to(repo_root).as_posix()
    assert task_payload["source_type"] == "user_github"
    assert task_payload["metadata"]["input_repo_url"] == "https://github.com/owner/demo"
    assert task_payload["metadata"]["cloned_repo_path"] == str(cloned_repo_path)
    assert output["summary_path"].endswith("summary.md")


def test_run_repair_bug_fetches_issue_url_and_derives_repo_when_repo_omitted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path
    policy_path = repo_root / "optimization" / "policy_versions" / "policy.json"
    write_text(policy_path, "{}")
    calls: dict[str, object] = {}

    def fake_fetch_issue(*, owner: str, repo_name: str, issue_number: int) -> str:
        calls["issue"] = (owner, repo_name, issue_number)
        return "Fetched issue title\n\nFetched issue body."

    def fake_clone(repo_url: str, *, owner: str, repo_name: str, repo_root: Path, clones_dir: str | Path = repair_bug.DEFAULT_GITHUB_REPOS_DIR) -> Path:
        calls["clone"] = (repo_url, owner, repo_name)
        destination = repo_root / "logs" / "github_repos" / "owner_demo_20260101T000000Z" / "repo"
        write_text(destination / "tests" / "test_demo.py", "def test_demo():\n    assert True\n")
        return destination

    def fake_run_agent(**_: object) -> dict:
        return {
            "result": {"run_id": "run_001", "final_status": "success"},
            "run_paths": {
                "summary_md_path": str(repo_root / "logs" / "summary.md"),
                "trace_json_path": str(repo_root / "logs" / "trace.json"),
                "result_json_path": str(repo_root / "logs" / "result.json"),
            },
        }

    monkeypatch.setattr(repair_bug, "fetch_github_issue_text", fake_fetch_issue)
    monkeypatch.setattr(repair_bug, "clone_github_repo", fake_clone)
    monkeypatch.setattr(repair_bug, "run_agent", fake_run_agent)

    output = repair_bug.run_repair_bug(
        issue_url="https://github.com/owner/demo/issues/123",
        issue="Extra reproduction details.",
        policy=policy_path,
        task_id="user_issue_demo",
        repo_root=repo_root,
    )

    task_payload = json.loads(Path(output["task_path"]).read_text(encoding="utf-8"))
    assert calls["issue"] == ("owner", "demo", 123)
    assert calls["clone"] == ("https://github.com/owner/demo", "owner", "demo")
    assert "Fetched issue title" in task_payload["issue_text"]
    assert "User supplied additional context:\nExtra reproduction details." in task_payload["issue_text"]
    assert task_payload["metadata"]["issue_url"] == "https://github.com/owner/demo/issues/123"
    assert task_payload["metadata"]["github_issue"] == {"owner": "owner", "repo": "demo", "number": 123}


def test_main_returns_success_and_prints_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    repo_root = tmp_path
    local_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    write_text(local_repo / "tests" / "test_demo.py", "def test_demo():\n    assert True\n")
    policy_path = repo_root / "optimization" / "policy_versions" / "policy.json"
    write_text(policy_path, "{}")

    def fake_run_agent(**_: object) -> dict:
        return {
            "result": {
                "run_id": "run_001",
                "final_status": "success",
                "tool_stats": {
                    "llm_usage": {
                        "total_tokens": 1234,
                    },
                },
            },
            "run_paths": {
                "summary_md_path": str(repo_root / "logs" / "summary.md"),
                "trace_json_path": str(repo_root / "logs" / "trace.json"),
                "result_json_path": str(repo_root / "logs" / "result.json"),
            },
        }

    monkeypatch.setattr(repair_bug, "REPO_ROOT", repo_root)
    monkeypatch.setattr(repair_bug, "run_agent", fake_run_agent)

    exit_code = repair_bug.main(
        [
            "--repo",
            str(local_repo),
            "--issue",
            "Fix demo bug",
            "--policy",
            str(policy_path),
            "--task-id",
            "user_demo",
            "--tasks-dir",
            str(repo_root / "logs" / "user_tasks"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "=== Repair Bug Run Summary ===" in captured.out
    assert "task_path:" in captured.out
    assert "final_status: success" in captured.out
    assert "verification_strength:" in captured.out
    assert "incomplete_reason:" in captured.out
    assert "pre_test_exit_code:" in captured.out
    assert "post_test_exit_code:" in captured.out
    assert "llm_total_tokens: 1234" in captured.out
    assert "summary_path:" in captured.out
    assert "trace_path:" in captured.out
    assert "result_path:" in captured.out
