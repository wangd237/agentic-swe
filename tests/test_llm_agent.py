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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_llm_agent_can_finish_after_tool_loop(tmp_path: Path) -> None:
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

    assert output["result"]["final_status"] == "success"
    assert output["result"]["tool_stats"]["agent_type"] == "llm"
    assert output["result"]["tool_stats"]["llm_provider"] == "openai_compatible"
    assert output["result"]["tool_stats"]["llm_model"] == "fake-model"
    assert output["trace"]["total_tool_calls"] == 1


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
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["patch_applied"] is True
    assert len(run_test_steps) == 2


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
