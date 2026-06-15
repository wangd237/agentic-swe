from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.agent.llm_agent import LLMCodeAgent
from app.agent.llm_config import LLMConfig
from app.agent.policy import PolicyConfig


class FakeLLMClient:
    def __init__(self) -> None:
        self._call_count = 0

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "run_tests",
                        "input": {
                            "command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
                            "timeout_sec": 30,
                        },
                    }
                ]
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "测试已经通过，当前任务完成。",
                }
            ]
        }


class FakeWriteThenStopClient:
    def __init__(self, fixed_file_content: str) -> None:
        self._call_count = 0
        self.fixed_file_content = fixed_file_content

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "run_tests",
                        "input": {
                            "command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
                            "timeout_sec": 30,
                        },
                    }
                ]
            }
        if self._call_count == 2:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_2",
                        "name": "write_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "content": self.fixed_file_content,
                        },
                    }
                ]
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "自动验证已通过，当前任务完成。",
                }
            ]
        }


class FakeWriteOnceClient:
    def __init__(self, fixed_file_content: str) -> None:
        self.fixed_file_content = fixed_file_content

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        return {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_1",
                    "name": "write_file",
                    "input": {
                        "relative_path": "demo_pkg/app.py",
                        "content": self.fixed_file_content,
                    },
                }
            ]
        }


class FakeEditThenStopClient:
    def __init__(self) -> None:
        self._call_count = 0

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "edit_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "old_string": "    return 1",
                            "new_string": "    return 2",
                        },
                    }
                ]
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "自动验证已通过，当前任务完成。",
                }
            ]
        }


class FakeUnsafeCommandClient:
    def __init__(self, unsafe_command: str) -> None:
        self.unsafe_command = unsafe_command

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        return {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_unsafe",
                    "name": "run_tests",
                    "input": {
                        "command": self.unsafe_command,
                        "timeout_sec": 30,
                    },
                }
            ]
        }


class FakeParallelReadClient:
    def __init__(self) -> None:
        self._call_count = 0
        self.observed_tool_result_ids: list[str] = []

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_read_app",
                        "name": "read_file",
                        "input": {"relative_path": "demo_pkg/app.py"},
                    },
                    {
                        "type": "tool_use",
                        "id": "tool_read_test",
                        "name": "read_file",
                        "input": {"relative_path": "tests/test_app.py"},
                    },
                ]
            }
        latest_message = messages[-1]
        self.observed_tool_result_ids = [
            block["tool_use_id"]
            for block in latest_message["content"]
            if block.get("type") == "tool_result"
        ]
        return {
            "content": [
                {
                    "type": "text",
                    "text": "我已经完成观察，但不需要修改。",
                }
            ]
        }


class FakeBadToolClient:
    def __init__(self) -> None:
        self._call_count = 0

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_bad",
                        "name": "read_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "max_chars": "not-an-int",
                        },
                    }
                ]
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "无法继续。",
                }
            ]
        }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_llm_agent_marks_test_only_run_as_no_patch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "__init__.py",
        "",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "def test_ok():\n    assert True\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["tests/test_app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=3),
        client=FakeLLMClient(),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    assert output["result"]["final_status"] == "incomplete"
    assert output["result"]["incomplete_reason"] == "no_patch"
    assert output["result"]["patch_applied"] is False
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["tool_stats"]["agent_type"] == "llm"
    assert output["result"]["tool_stats"]["llm_provider"] == "openai_compatible"
    assert output["result"]["tool_stats"]["llm_model"] == "fake-model"
    assert output["trace"]["total_tool_calls"] == 1


def test_llm_agent_parallelizes_same_turn_read_only_tools(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "def value():\n    return 1\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "from demo_pkg.app import value\n\n\ndef test_value():\n    assert value() == 1\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )
    client = FakeParallelReadClient()
    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=3),
        client=client,
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    read_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "read_file"
    ]
    parallel_group_ids = {
        step["tool_metrics"].get("parallel_group_id")
        for step in read_steps
    }
    assert len(read_steps) == 2
    assert parallel_group_ids == {"iter_1_parallel_1"}
    assert client.observed_tool_result_ids == ["tool_read_app", "tool_read_test"]


def test_llm_agent_auto_verifies_after_write_before_success(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "__init__.py",
        "",
    )
    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "def value():\n    return 0\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "from demo_pkg.app import value\n\n\ndef test_value():\n    assert value() == 1\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=5),
        client=FakeWriteThenStopClient("def value():\n    return 1\n"),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    run_test_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    assert output["result"]["final_status"] == "success"
    assert output["result"]["incomplete_reason"] == ""
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["patch_applied"] is True
    assert len(run_test_steps) == 2


def test_llm_agent_auto_verifies_after_edit_before_success(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "__init__.py",
        "",
    )
    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "def value():\n    return 1\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "from demo_pkg.app import value\n\n\ndef test_value():\n    assert value() == 2\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=5),
        client=FakeEditThenStopClient(),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    edit_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "edit_file"
    ]
    run_test_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    assert output["result"]["final_status"] == "success"
    assert output["result"]["incomplete_reason"] == ""
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["patch_applied"] is True
    assert output["result"]["tool_stats"]["workspace_generation"] == 1
    assert len(edit_steps) == 1
    assert edit_steps[0]["tool_metrics"]["ok"] is True
    assert len(run_test_steps) == 1


def test_llm_agent_classifies_failed_tests_after_patch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "__init__.py",
        "",
    )
    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "def value():\n    return 0\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "from demo_pkg.app import value\n\n\ndef test_value():\n    assert value() == 1\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=5),
        client=FakeWriteThenStopClient("def value():\n    return 2\n"),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    assert output["result"]["final_status"] == "incomplete"
    assert output["result"]["incomplete_reason"] == "failed_tests"
    assert output["result"]["patch_applied"] is True
    assert output["result"]["post_test_exit_code"] != 0


def test_llm_agent_classifies_max_iterations_with_unverified_patch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "__init__.py",
        "",
    )
    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "def value():\n    return 0\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "from demo_pkg.app import value\n\n\ndef test_value():\n    assert value() == 1\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=1),
        client=FakeWriteOnceClient("def value():\n    return 1\n"),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    assert output["result"]["final_status"] == "incomplete"
    assert output["result"]["incomplete_reason"] == "max_iterations"
    assert output["result"]["patch_applied"] is True
    assert output["result"]["post_test_exit_code"] is None


def test_llm_agent_prioritizes_max_iterations_without_patch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "def test_ok():\n    assert True\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["tests/test_app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=1),
        client=FakeLLMClient(),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    assert output["result"]["final_status"] == "incomplete"
    assert output["result"]["incomplete_reason"] == "max_iterations"
    assert output["result"]["patch_applied"] is False
    assert output["result"]["post_test_exit_code"] == 0


def test_llm_agent_ignores_model_supplied_test_command(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"
    marker_path = benchmark_repo / "unsafe_marker.txt"

    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "def test_ok():\n    assert True\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["tests/test_app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "max_steps": 1,
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    unsafe_command = (
        f'"{sys.executable}" -c "from pathlib import Path; '
        f"Path({str(marker_path)!r}).write_text('unsafe')\""
    )
    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=1),
        client=FakeUnsafeCommandClient(unsafe_command),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    run_test_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    assert output["result"]["post_test_exit_code"] == 0
    assert run_test_steps[0]["tool_input"]["command"] == unsafe_command
    assert run_test_steps[0]["tool_metrics"]["ok"] is True
    assert not marker_path.exists()


def test_llm_agent_returns_artifacts_after_bad_tool_input(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "def value():\n    return 1\n",
    )
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest tests/test_app.py -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "semi_real",
            "metadata": {},
        },
    )
    _write_json(
        policy_path,
        {
            "policy_id": "llm_demo",
            "description": "demo",
            "max_steps": 2,
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=2),
        client=FakeBadToolClient(),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    bad_tool_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "read_file"
    ]
    assert output["result"]["final_status"] == "incomplete"
    assert bad_tool_steps[0]["tool_metrics"]["ok"] is False
    assert output["run_paths"]["result_json_path"]
    assert Path(output["run_paths"]["result_json_path"]).exists()


def test_llm_config_uses_policy_env_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CUSTOM_MODEL_ENV", "custom-model-from-env")
    policy = PolicyConfig(
        policy_id="llm_custom_provider",
        description="custom provider",
        agent_type="llm",
        llm_provider="openai_compatible",
        llm_model="policy-model",
        llm_api_key_env="CUSTOM_API_KEY",
        llm_base_url_env="CUSTOM_BASE_URL",
        llm_model_env="CUSTOM_MODEL_ENV",
        llm_base_url="https://example.test/v1",
    )

    config = LLMConfig.from_policy(policy)

    assert config.provider == "openai_compatible"
    assert config.model == "policy-model"
    assert config.api_key_env == "CUSTOM_API_KEY"
    assert config.base_url_env == "CUSTOM_BASE_URL"
    assert config.model_env == "CUSTOM_MODEL_ENV"
    assert config.default_base_url == "https://example.test/v1"


def test_llm_config_uses_policy_max_steps() -> None:
    policy = PolicyConfig(
        policy_id="llm_custom_provider",
        description="custom provider",
        agent_type="llm",
        max_steps=3,
        llm_provider="openai_compatible",
    )

    config = LLMConfig.from_policy(policy)

    assert config.max_iterations == 3


def test_llm_config_uses_model_env_as_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CUSTOM_MODEL_ENV", "custom-model-from-env")
    policy = PolicyConfig(
        policy_id="llm_custom_provider",
        description="custom provider",
        agent_type="llm",
        llm_provider="openai_compatible",
        llm_api_key_env="CUSTOM_API_KEY",
        llm_base_url_env="CUSTOM_BASE_URL",
        llm_model_env="CUSTOM_MODEL_ENV",
        llm_base_url="https://example.test/v1",
    )

    config = LLMConfig.from_policy(policy)

    assert config.model == "custom-model-from-env"
