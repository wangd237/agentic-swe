from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from app.agent.llm_agent import LLMCodeAgent
from app.agent.llm_config import LLMConfig
from app.agent.llm_prompts import build_system_prompt
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
                        "type": "text",
                        "text": "我会先运行测试确认当前状态。",
                    },
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


class FakeReproduceThenWriteClient:
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


class FakeWriteThenRunTestsWithoutDiffClient:
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
                        "input": {"timeout_sec": 30},
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
        if self._call_count == 3:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "tool_3",
                        "name": "run_tests",
                        "input": {"timeout_sec": 30},
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


class FakeWriteOnceThenStopClient:
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
                    "text": "弱验证路径下已完成静态修复，请按弱验证结果输出。",
                }
            ]
        }


class FakeOverrideWriteThenStopClient:
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
                            "relative_path": "demo_pkg/config.py",
                            "content": self.fixed_file_content,
                            "localization_override_reason": (
                                "the failing behavior depends on a configuration helper not imported by the tests."
                            ),
                        },
                    }
                ]
            }
        return {
            "content": [
                {
                    "type": "text",
                    "text": "override 定位证据已记录，当前任务完成。",
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


class FakeThreeSimilarEditsClient:
    def __init__(self) -> None:
        self._call_count = 0
        self.observed_notice = ""

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count <= 3:
            return {
                "content": [
                    {
                        "type": "tool_use",
                        "id": f"tool_{self._call_count}",
                        "name": "edit_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "old_string": f"VALUE = {self._call_count - 1}",
                            "new_string": f"VALUE = {self._call_count}",
                        },
                    }
                ]
            }
        latest_message = json.dumps(messages[-1], ensure_ascii=False)
        if "ANTI_LOOP_NOTICE" in latest_message:
            self.observed_notice = latest_message
        return {
            "content": [
                {
                    "type": "text",
                    "text": "我已收到反循环提醒，先停止。",
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


class FakeLongContextClient:
    def __init__(self) -> None:
        self._call_count = 0
        self.observed_final_call_messages: list[dict] = []

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self._call_count += 1
        if self._call_count == 1:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "我先读取文件，确认当前实现。",
                    },
                    {
                        "type": "tool_use",
                        "id": "tool_1",
                        "name": "read_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "max_chars": 6000,
                        },
                    },
                ]
            }
        if self._call_count == 2:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "我再读取一次文件，制造需要压缩的中间上下文。",
                    },
                    {
                        "type": "tool_use",
                        "id": "tool_2",
                        "name": "read_file",
                        "input": {
                            "relative_path": "demo_pkg/app.py",
                            "max_chars": 6000,
                        },
                    },
                ]
            }
        self.observed_final_call_messages = messages
        return {
            "content": [
                {
                    "type": "text",
                    "text": "我已经完成观察，但不需要修改。",
                }
            ]
        }


class FakeCaptureInitialPromptClient:
    def __init__(self) -> None:
        self.initial_user_prompt = ""

    def create_message(self, *, system_prompt: str, messages: list[dict], tools: list[dict]) -> dict:
        self.initial_user_prompt = str(messages[0]["content"])
        return {
            "content": [
                {
                    "type": "text",
                    "text": "未完成：只检查初始提示。",
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
    assert output["result"]["pre_test_exit_code"] == 0
    assert output["result"]["post_test_exit_code"] is None
    assert output["result"]["tool_stats"]["agent_type"] == "llm"
    assert output["result"]["tool_stats"]["llm_provider"] == "openai_compatible"
    assert output["result"]["tool_stats"]["llm_model"] == "fake-model"
    assert output["result"]["tool_stats"]["agent_core_metrics"]["pre_repro_rate"] == 1.0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["write_before_repro_count"] == 0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["success_full_verify_rate"] == 0.0
    assert output["result"]["tool_stats"]["final_phase"] == "final"
    assert output["trace"]["total_tool_calls"] == 1
    planning_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "planning"
    ]
    assert len(planning_steps) == 1
    assert planning_steps[0]["observation"] == "我会先运行测试确认当前状态。"
    assert planning_steps[0]["state_snapshot"]["hypotheses"] == [
        "我会先运行测试确认当前状态。"
    ]
    assert planning_steps[0]["tool_metrics"]["planned_tool_count"] == 1
    assert all("phase" in step for step in output["trace"]["steps"])
    assert output["trace"]["steps"][0]["phase"] == "understand"
    assert output["trace"]["steps"][-1]["action_type"] == "finalize"
    assert output["trace"]["steps"][-1]["phase"] == "final"


def test_llm_agent_injects_retrieved_strategy_memory_into_initial_prompt(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"
    memory_path = repo_root / "logs" / "agent_memory" / "strategy_memory.jsonl"

    _write_text(benchmark_repo / "demo_pkg" / "parser.py", "def parse_items(value):\n    return value\n")
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "parse_items bug",
            "issue_text": "parse_items fails for empty input",
            "test_command": f'"{sys.executable}" -m pytest -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/parser.py"],
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
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(
        json.dumps(
            {
                "task_id": "old_task",
                "run_id": "run_001",
                "created_at": "2026-06-22T00:00:00+00:00",
                "final_status": "success",
                "failure_mode": "parse_items empty",
                "likely_cause": "fixed",
                "successful": True,
                "modified_files": ["demo_pkg/parser.py"],
                "top_localization_evidence": [
                    {
                        "relative_path": "demo_pkg/parser.py",
                        "reason": "grep_hit",
                        "evidence": ["parse_items matched this file"],
                        "confidence": 0.9,
                    }
                ],
                "patch_style": "single_edit",
                "verification_strength": "full",
                "metrics": {},
                "trace_path": "old_trace.json",
                "result_path": "old_result.json",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    client = FakeCaptureInitialPromptClient()
    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=1),
        client=client,
    )

    output = agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)

    memory_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "memory_retrieval"
    ]
    assert "STRATEGY_MEMORY_HINTS" in client.initial_user_prompt
    assert "demo_pkg/parser.py" in client.initial_user_prompt
    assert len(memory_steps) == 1
    assert memory_steps[0]["tool_metrics"]["memory_task_ids"] == ["old_task"]
    assert memory_steps[0]["evidence_ids"] == ["memory:old_task:run_001"]


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
    assert len(run_test_steps) == 3


def test_llm_agent_auto_verification_runs_targeted_before_full_tests(tmp_path: Path) -> None:
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
    targeted_steps = [
        step for step in run_test_steps
        if step["tool_input"].get("verification_scope") == "targeted"
    ]
    full_steps = [
        step for step in run_test_steps
        if step["tool_input"].get("verification_scope") == "full"
    ]

    assert output["result"]["final_status"] == "success"
    assert output["result"]["pre_test_exit_code"] != 0
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["tool_stats"]["verification_records"]["pre"]["exit_code"] == output["result"]["pre_test_exit_code"]
    assert output["result"]["tool_stats"]["verification_records"]["post"]["exit_code"] == 0
    assert len(run_test_steps) == 3
    assert len(targeted_steps) == 1
    assert len(full_steps) == 1
    assert "tests/test_app.py::test_value" in targeted_steps[0]["tool_input"]["command"]
    assert targeted_steps[0]["step_index"] < full_steps[0]["step_index"]
    assert output["result"]["tool_stats"]["verification_strength"] == "full"
    assert output["result"]["tool_stats"]["final_phase"] == "final"
    assert output["result"]["tool_stats"]["agent_core_metrics"]["phase_completion_rate"] == 1.0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["localization_precision_at_3"] == 1.0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["patch_changed_file_count"] == 1
    assert targeted_steps[0]["evidence_ids"] == ["run_tests:targeted:exit_0"]
    assert full_steps[0]["evidence_ids"] == ["run_tests:full:exit_0"]
    assert output["trace"]["steps"][-1]["evidence_ids"] == ["final:success", "verification:full"]
    memory_path = Path(output["result"]["tool_stats"]["strategy_memory_path"])
    memory_payload = json.loads(memory_path.read_text(encoding="utf-8").splitlines()[-1])
    assert memory_payload["task_id"] == "task_demo"
    assert memory_payload["run_id"] == output["result"]["run_id"]
    assert memory_payload["successful"] is True
    assert memory_payload["patch_style"] in {"single_file_rewrite", "rewrite_sequence"}


def test_llm_agent_blocks_patch_verification_tests_before_show_diff(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(benchmark_repo / "demo_pkg" / "__init__.py", "")
    _write_text(benchmark_repo / "demo_pkg" / "app.py", "def value():\n    return 0\n")
    _write_text(benchmark_repo / "demo_pkg" / "config.py", "VALUE = 0\n")
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
        llm_config=LLMConfig(model="fake-model", max_iterations=6),
        client=FakeWriteThenRunTestsWithoutDiffClient("def value():\n    return 1\n"),
    )

    output = agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)

    run_test_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    blocked_steps = [
        step for step in run_test_steps
        if step["tool_metrics"].get("ok") is False
        and "show_diff" in step["observation"]
    ]
    show_diff_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "show_diff"
    ]

    assert blocked_steps
    assert show_diff_steps
    assert blocked_steps[0]["step_index"] < show_diff_steps[0]["step_index"]
    assert output["result"]["final_status"] == "success"


def test_llm_agent_downgrades_success_for_weak_fallback_verification(tmp_path: Path) -> None:
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
            "test_command": f'"{sys.executable}" -m pytest -q',
            "success_criteria": "tests pass",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "user_local",
            "metadata": {
                "test_command_source": "pytest_fallback",
                "verification_strength": "weak",
            },
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

    assert output["result"]["final_status"] == "success_weak_verification"
    assert output["result"]["incomplete_reason"] == "weak_verification"
    assert output["result"]["patch_applied"] is True
    assert output["result"]["post_test_exit_code"] == 0
    assert output["result"]["tool_stats"]["verification_strength"] == "weak"
    audit_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "verification_audit"
    ]
    assert len(audit_steps) == 1
    assert audit_steps[0]["reflection_type"] == "weak_verification"
    assert audit_steps[0]["tool_metrics"]["requires_full_verification"] is True
    assert "audit:weak_verification" in audit_steps[0]["evidence_ids"]


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
    assert output["result"]["tool_stats"]["write_before_repro_count"] == 0
    assert len(edit_steps) == 1
    assert edit_steps[0]["tool_metrics"]["ok"] is True
    assert edit_steps[0]["phase"] in {"patch", "verify"}
    assert len(run_test_steps) == 3


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
    run_test_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    reflection_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "reflection"
    ]
    assert "context_diff" in run_test_steps[-1]["observation"]
    assert "+    return 2" in run_test_steps[-1]["observation"]
    assert len(reflection_steps) == 1
    assert reflection_steps[0]["reflection_type"] in {"partial_fix", "wrong_hypothesis"}
    assert "REFLECTION_DECISION" in reflection_steps[0]["observation"]


def test_llm_agent_auto_undoes_when_reflection_requests_it(tmp_path: Path) -> None:
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
            "max_patch_files": 0,
            "agent_type": "llm",
            "patch_strategy": "baseline",
            "llm_provider": "openai_compatible",
            "llm_model": "fake-model",
            "pytest_additional_flags": [],
        },
    )

    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=5),
        client=FakeWriteThenStopClient("def value():\n    return 0  # unchanged behavior\n"),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    reflection_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "reflection"
    ]
    undo_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "undo"
    ]
    assert reflection_steps
    assert reflection_steps[0]["reflection_type"] == "overfit"
    assert reflection_steps[0]["tool_metrics"]["should_undo"] is True
    assert undo_steps
    assert undo_steps[0]["tool_metrics"]["ok"] is True
    assert output["result"]["patch_applied"] is False


def test_llm_agent_blocks_repeated_edits_before_reproduction(tmp_path: Path) -> None:
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
        "VALUE = 0\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "def test_value():\n    assert True\n",
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
    client = FakeThreeSimilarEditsClient()
    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=5),
        client=client,
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
    anti_loop_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "anti_loop"
    ]
    assert edit_steps
    assert all(step["tool_metrics"]["ok"] is False for step in edit_steps)
    assert "tool_policy_violation" in edit_steps[0]["observation"]
    assert anti_loop_steps == []
    assert output["result"]["tool_stats"]["workspace_generation"] == 0


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
    assert output["result"]["patch_applied"] is False
    assert output["result"]["post_test_exit_code"] is None
    write_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "write_file"
    ]
    assert write_steps[0]["tool_metrics"]["ok"] is False


def test_llm_agent_final_verifies_last_iteration_write(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(benchmark_repo / "demo_pkg" / "__init__.py", "")
    _write_text(benchmark_repo / "demo_pkg" / "app.py", "def value():\n    return 0\n")
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
        llm_config=LLMConfig(model="fake-model", max_iterations=2),
        client=FakeReproduceThenWriteClient("def value():\n    return 1\n"),
    )

    output = agent.run(task_path=task_path, repo_root=repo_root, policy_path=policy_path)

    run_test_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "run_tests"
    ]
    final_verification_steps = [
        step for step in run_test_steps
        if step["tool_input"].get("source") == "final_pending_verification"
    ]

    assert output["result"]["final_status"] == "success"
    assert output["result"]["tool_stats"]["max_iterations_reached"] is True
    assert output["result"]["tool_stats"]["workspace_generation"] == 1
    assert output["result"]["tool_stats"]["verified_generation"] == 1
    assert output["result"]["post_test_exit_code"] == 0
    assert final_verification_steps
    assert final_verification_steps[0]["tool_input"]["verification_scope"] == "full"


def test_llm_agent_allows_weak_static_patch_but_keeps_weak_status(tmp_path: Path) -> None:
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
    _write_json(
        task_path,
        {
            "task_id": "task_demo",
            "repo_name": "demo_repo",
            "repo_path": "benchmarks/repos/demo_repo",
            "issue_title": "demo issue",
            "issue_text": "demo body",
            "test_command": f'"{sys.executable}" -m pytest -q',
            "success_criteria": "best effort static fix",
            "difficulty": "easy",
            "tags": ["demo"],
            "target_files_hint": ["demo_pkg/app.py"],
            "source_type": "user_local",
            "metadata": {
                "test_command_source": "pytest_fallback",
                "verification_strength": "weak",
            },
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
        client=FakeWriteOnceThenStopClient("def value():\n    return 1\n"),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    write_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "write_file"
    ]
    assert write_steps
    assert write_steps[0]["tool_metrics"]["ok"] is True
    assert write_steps[0]["state_snapshot"]["reproduction_evidence_kind"] == "weak_static"
    assert output["result"]["final_status"] == "success_weak_verification"
    assert output["result"]["incomplete_reason"] == "weak_verification"
    assert output["result"]["patch_applied"] is True
    assert output["result"]["tool_stats"]["verification_strength"] == "weak"
    assert output["result"]["tool_stats"]["agent_core_metrics"]["weak_success_rate"] == 1.0
    audit_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "verification_audit"
    ]
    assert len(audit_steps) == 1
    assert audit_steps[0]["tool_input"]["verification_strength"] == "weak"


def test_llm_agent_records_localization_override_candidate(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(benchmark_repo / "demo_pkg" / "__init__.py", "")
    _write_text(benchmark_repo / "demo_pkg" / "app.py", "def value():\n    return 0\n")
    _write_text(
        benchmark_repo / "demo_pkg" / "other.py",
        "from demo_pkg.app import value\n",
    )
    _write_text(
        benchmark_repo / "tests" / "test_app.py",
        "from demo_pkg.other import value\n\n\ndef test_value():\n    assert value() == 1\n",
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
            "target_files_hint": ["demo_pkg/other.py"],
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
        client=FakeOverrideWriteThenStopClient("VALUE = 1\n"),
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    write_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "write_file"
    ]
    assert write_steps
    assert write_steps[0]["tool_metrics"]["ok"] is True
    localization_candidates = write_steps[0]["state_snapshot"]["localization_candidates"]
    override_candidates = [
        candidate for candidate in localization_candidates
        if candidate["relative_path"] == "demo_pkg/config.py"
    ]
    assert override_candidates
    assert override_candidates[0]["reason"] == "localization_override"


def test_llm_agent_blocks_premature_write_before_reproduction(tmp_path: Path) -> None:
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
            "max_steps": 1,
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

    write_steps = [
        step for step in output["trace"]["steps"]
        if step["tool_name"] == "write_file"
    ]
    assert len(write_steps) == 1
    assert write_steps[0]["tool_metrics"]["ok"] is False
    assert write_steps[0]["tool_metrics"]["policy_blocked"] is True
    assert "tool_policy_violation" in write_steps[0]["observation"]
    assert output["result"]["patch_applied"] is False
    assert output["result"]["tool_stats"]["workspace_generation"] == 0
    assert output["result"]["tool_stats"]["write_before_repro_count"] == 0
    assert output["result"]["tool_stats"]["agent_core_metrics"]["policy_violation_count"] == 1


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
    assert output["result"]["pre_test_exit_code"] == 0
    assert output["result"]["post_test_exit_code"] is None


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
    assert output["result"]["pre_test_exit_code"] == 0
    assert output["result"]["post_test_exit_code"] is None
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


def test_llm_agent_compresses_context_when_message_budget_is_exceeded(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo_root"
    benchmark_repo = repo_root / "benchmarks" / "repos" / "demo_repo"
    task_path = repo_root / "benchmarks" / "tasks" / "task_demo.json"
    policy_path = repo_root / "optimization" / "policy_versions" / "llm_demo.json"

    _write_text(
        benchmark_repo / "demo_pkg" / "app.py",
        "VALUE = '" + ("x" * 2000) + "'\n",
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
    client = FakeLongContextClient()
    agent = LLMCodeAgent(
        llm_config=LLMConfig(model="fake-model", max_iterations=3, max_context_chars=1000),
        client=client,
    )

    output = agent.run(
        task_path=task_path,
        repo_root=repo_root,
        policy_path=policy_path,
    )

    compression_steps = [
        step for step in output["trace"]["steps"]
        if step["action_type"] == "context_compression"
    ]
    assert compression_steps
    assert output["result"]["tool_stats"]["context_compression_count"] >= 1
    assert any(
        message.get("role") == "system"
        and "Earlier context has been summarized" in message.get("content", "")
        for message in client.observed_final_call_messages
    )


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
        llm_max_context_chars=1234,
    )

    config = LLMConfig.from_policy(policy)

    assert config.max_iterations == 3
    assert config.max_context_chars == 1234


def test_llm_config_default_iterations_match_target2_budget() -> None:
    config = LLMConfig()

    assert config.max_iterations == 16


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


def test_llm_agent_classifies_model_reported_incomplete_task() -> None:
    final_status, incomplete_reason = LLMCodeAgent._classify_final_state(
        patch_applied=True,
        last_test_exit_code=0,
        verified_generation=1,
        workspace_generation=1,
        ever_used_tool=True,
        max_iterations_reached=False,
        model_reported_incomplete=True,
    )

    assert final_status == "incomplete"
    assert incomplete_reason == "task_incomplete"


def test_llm_agent_classifies_verified_weak_static_patch_as_success_candidate() -> None:
    final_status, incomplete_reason = LLMCodeAgent._classify_final_state(
        patch_applied=True,
        last_test_exit_code=5,
        verified_generation=1,
        workspace_generation=1,
        ever_used_tool=True,
        max_iterations_reached=False,
        model_reported_incomplete=False,
        reproduction_evidence_kind="weak_static",
        verification_strength="weak",
    )

    assert final_status == "success"
    assert incomplete_reason == ""


def test_system_prompt_guides_subtask_decomposition() -> None:
    prompt = build_system_prompt()

    assert "步骤清单" in prompt
    assert "更新进度" in prompt


def test_system_prompt_discourages_leaking_scratch_files() -> None:
    prompt = build_system_prompt()

    assert "debug.py" in prompt
    assert "不要创建" in prompt
    assert "不支持执行任意调试脚本" in prompt
    assert "不要反复写调试脚本" in prompt
    assert "edit_file 修复" in prompt


def test_system_prompt_describes_python_repl_boundaries() -> None:
    prompt = build_system_prompt()

    assert "python_repl" in prompt
    assert "第三方库" in prompt
    assert "不能 import" in prompt
    assert "不能使用分号" in prompt
    assert "dunder" in prompt


def test_system_prompt_requires_reflection_after_failed_tests() -> None:
    prompt = build_system_prompt()

    assert "run_tests 返回失败" in prompt
    assert "先用文本解释失败原因" in prompt
    assert "不要跳过分析直接修改" in prompt


def test_system_prompt_requires_phase_workflow_and_diff_before_verify() -> None:
    prompt = build_system_prompt()

    assert "UNDERSTAND -> REPRODUCE -> LOCALIZE -> PATCH -> VERIFY -> FINAL" in prompt
    assert "不要在复现或定位之前修改文件" in prompt
    assert "localization_override_reason" in prompt
    assert "任何 write_file/edit_file 后" in prompt
    assert "必须先 show_diff，再运行 run_tests 验证" in prompt
