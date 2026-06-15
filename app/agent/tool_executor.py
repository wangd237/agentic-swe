"""LLM agent 工具执行器。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.agent.policy import PolicyConfig
from app.tools.common import resolve_repo_relative_path, resolve_repo_path
from app.tools.list_files import list_files
from app.tools.read_file import read_file
from app.tools.edit_file import edit_file
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
        test_command: str,
    ) -> None:
        self.repo_path = str(repo_path)
        self.original_repo_path = str(original_repo_path)
        self.policy_config = policy_config
        self.test_command = test_command
        self._write_step_index = 0
        self._checkpoint_stack: list[dict[str, Any]] = []

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """执行单次工具调用。"""

        try:
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
                    command=self.test_command,
                    timeout_sec=int(tool_input.get("timeout_sec", 120)),
                    additional_pytest_flags=self.policy_config.pytest_additional_flags,
                )
            if tool_name == "write_file":
                checkpoint = self._checkpoint_before_write(
                    relative_path=str(tool_input.get("relative_path", "")),
                    tool_name=tool_name,
                )
                result = write_file(
                    self.repo_path,
                    relative_path=str(tool_input.get("relative_path", "")),
                    content=str(tool_input.get("content", "")),
                ) | {"checkpoint": self._checkpoint_result(checkpoint)}
                self._finalize_checkpoint(checkpoint, keep=bool(result.get("ok")))
                return result
            if tool_name == "edit_file":
                checkpoint = self._checkpoint_before_write(
                    relative_path=str(tool_input.get("relative_path", "")),
                    tool_name=tool_name,
                )
                result = edit_file(
                    self.repo_path,
                    relative_path=str(tool_input.get("relative_path", "")),
                    old_string=str(tool_input.get("old_string", "")),
                    new_string=str(tool_input.get("new_string", "")),
                ) | {"checkpoint": self._checkpoint_result(checkpoint)}
                self._finalize_checkpoint(checkpoint, keep=bool(result.get("ok")))
                return result
            if tool_name == "show_diff":
                return show_diff(
                    self.repo_path,
                    original_repo_path=self.original_repo_path,
                )
            if tool_name == "undo":
                return self._undo_last_write()
        except Exception as error:
            return self._tool_error_result(
                tool_name=tool_name,
                tool_input=tool_input,
                error_type="tool_exception",
                message=str(error),
            )
        return self._tool_error_result(
            tool_name=tool_name,
            tool_input=tool_input,
            error_type="unknown_tool",
            message=f"未知工具：{tool_name}",
        )

    @staticmethod
    def _tool_error_result(
        *,
        tool_name: str,
        tool_input: dict[str, Any],
        error_type: str,
        message: str,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "tool_name": tool_name,
            "summary": f"工具调用失败：{message}",
            "data": {
                "tool_input": tool_input,
            },
            "error": {
                "type": error_type,
                "message": message,
            },
        }

    def _checkpoint_before_write(self, *, relative_path: str, tool_name: str) -> dict[str, Any]:
        resolved_repo_path = resolve_repo_path(self.repo_path)
        target_path = resolve_repo_relative_path(resolved_repo_path, relative_path)
        normalized_relative_path = str(relative_path).replace("\\", "/")
        self._write_step_index += 1
        step_dir = resolved_repo_path / ".agent_checkpoints" / f"step_{self._write_step_index}"
        checkpoint_path = step_dir / normalized_relative_path
        existed = target_path.exists()
        checkpoint_record: dict[str, Any] = {
            "step": self._write_step_index,
            "tool_name": tool_name,
            "relative_path": normalized_relative_path,
            "existed": existed,
            "checkpoint_path": str(checkpoint_path),
            "step_dir": str(step_dir),
        }
        if existed:
            if not target_path.is_file():
                raise IsADirectoryError(f"目标不是文件: {relative_path}")
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, checkpoint_path)
        else:
            step_dir.mkdir(parents=True, exist_ok=True)
        return checkpoint_record

    @staticmethod
    def _checkpoint_result(checkpoint_record: dict[str, Any]) -> dict[str, Any]:
        return {
            "step": checkpoint_record["step"],
            "relative_path": checkpoint_record["relative_path"],
            "existed": checkpoint_record["existed"],
        }

    def _finalize_checkpoint(self, checkpoint_record: dict[str, Any], *, keep: bool) -> None:
        if keep:
            self._checkpoint_stack.append(checkpoint_record)
            return
        shutil.rmtree(checkpoint_record["step_dir"], ignore_errors=True)

    def _undo_last_write(self) -> dict[str, Any]:
        if not self._checkpoint_stack:
            return {
                "ok": False,
                "tool_name": "undo",
                "summary": "没有可回滚的写操作。",
                "data": {"reverted_files": []},
                "error": {
                    "type": "no_checkpoint",
                    "message": "没有可回滚的写操作。",
                },
            }

        checkpoint_record = self._checkpoint_stack.pop()
        resolved_repo_path = resolve_repo_path(self.repo_path)
        relative_path = checkpoint_record["relative_path"]
        target_path = resolve_repo_relative_path(resolved_repo_path, relative_path)
        if checkpoint_record["existed"]:
            checkpoint_path = Path(checkpoint_record["checkpoint_path"])
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(checkpoint_path, target_path)
        elif target_path.exists():
            target_path.unlink()

        return {
            "ok": True,
            "tool_name": "undo",
            "summary": f"已回滚最近一次写操作：{relative_path}。",
            "data": {
                "step": checkpoint_record["step"],
                "reverted_files": [relative_path],
                "restored_from_existing_file": checkpoint_record["existed"],
            },
            "error": None,
        }

    @staticmethod
    def summarize_for_model(result: dict[str, Any], *, max_chars: int) -> str:
        """把工具结果压成适合回喂给模型的文本。"""

        failure_summary = result.get("data", {}).get("failure_summary")
        if result.get("tool_name") == "run_tests" and failure_summary and not result.get("ok", False):
            payload = json.dumps(
                {
                    "ok": result.get("ok", False),
                    "tool_name": result.get("tool_name"),
                    "summary": result.get("summary", ""),
                    "failure_summary": failure_summary,
                    "exit_code": result.get("data", {}).get("exit_code"),
                },
                ensure_ascii=False,
                indent=2,
            )
            if len(payload) <= max_chars:
                return payload
            return f"{payload[:max_chars]}\n...<truncated>"

        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if len(payload) <= max_chars:
            return payload
        return f"{payload[:max_chars]}\n...<truncated>"
