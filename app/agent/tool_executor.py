"""LLM agent 工具执行器。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agent.policy import PolicyConfig
from app.tools.list_files import list_files
from app.tools.read_file import read_file
from app.tools.run_tests import run_tests
from app.tools.search_code import search_code
from app.tools.show_diff import show_diff
from app.tools.write_file import write_file


class ToolExecutor:
    """把字符串工具名分发到现有工具实现。"""

    def __init__(
        self,
        *,
        repo_path: str | Path,
        original_repo_path: str | Path,
        policy_config: PolicyConfig,
    ) -> None:
        self.repo_path = str(repo_path)
        self.original_repo_path = str(original_repo_path)
        self.policy_config = policy_config

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """执行单次工具调用。"""

        if tool_name == "list_files":
            return list_files(
                self.repo_path,
                recursive=bool(tool_input.get("recursive", True)),
            )
        if tool_name == "search_code":
            return search_code(
                self.repo_path,
                query=str(tool_input.get("query", "")),
            )
        if tool_name == "read_file":
            return read_file(
                self.repo_path,
                relative_path=str(tool_input.get("relative_path", "")),
                max_chars=int(tool_input.get("max_chars", 6000)),
            )
        if tool_name == "run_tests":
            return run_tests(
                self.repo_path,
                command=str(tool_input.get("command", "")),
                timeout_sec=int(tool_input.get("timeout_sec", 120)),
                additional_pytest_flags=self.policy_config.pytest_additional_flags,
            )
        if tool_name == "write_file":
            return write_file(
                self.repo_path,
                relative_path=str(tool_input.get("relative_path", "")),
                content=str(tool_input.get("content", "")),
            )
        if tool_name == "show_diff":
            return show_diff(
                self.repo_path,
                original_repo_path=self.original_repo_path,
            )
        raise RuntimeError(f"未知工具：{tool_name}")

    @staticmethod
    def summarize_for_model(result: dict[str, Any], *, max_chars: int) -> str:
        """把工具结果压成适合回喂给模型的文本。"""

        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if len(payload) <= max_chars:
            return payload
        return f"{payload[:max_chars]}\n...<truncated>"

