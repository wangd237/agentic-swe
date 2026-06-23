"""LLM agent 工具执行器。"""

from __future__ import annotations

import json
from typing import Any

from app.agent.policy import PolicyConfig
from app.runtime.git_workspace import commit_workspace_path, undo_last_workspace_commit
from app.tools.grep import grep
from app.tools.list_files import list_files
from app.tools.read_file import read_file
from app.tools.edit_file import edit_file
from app.tools.python_repl import python_repl
from app.tools.run_tests import run_tests
from app.tools.search_code import search_code
from app.tools.show_diff import show_diff
from app.tools.write_file import write_file


SCRATCH_FILE_NAMES = {"debug.py", "tmp.py", "scratch.py", "probe.py"}
SCRATCH_FILE_REJECTION_MESSAGE = (
    "Temporary debug/probe files are not supported in this agent workspace. "
    "Do not create debug.py/tmp.py/scratch.py/probe.py; use read_file, grep, "
    "run_tests failure output, and edit_file on the target source file instead."
)


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
            if tool_name == "grep":
                return grep(
                    self.repo_path,
                    pattern=str(tool_input.get("pattern", "")),
                    glob=tool_input.get("glob"),
                    max_results=int(tool_input.get("max_results", 20)),
                )
            if tool_name == "read_file":
                return read_file(
                    self.repo_path,
                    relative_path=str(tool_input.get("relative_path", "")),
                    max_chars=int(tool_input.get("max_chars", 6000)),
                    start_line=(
                        int(tool_input["start_line"])
                        if tool_input.get("start_line") is not None
                        else None
                    ),
                    end_line=(
                        int(tool_input["end_line"])
                        if tool_input.get("end_line") is not None
                        else None
                    ),
                )
            if tool_name == "run_tests":
                return run_tests(
                    self.repo_path,
                    command=self.test_command,
                    timeout_sec=int(tool_input.get("timeout_sec", 120)),
                    additional_pytest_flags=self.policy_config.pytest_additional_flags,
                )
            if tool_name == "python_repl":
                return python_repl(
                    expression=str(tool_input.get("expression", "")),
                )
            if tool_name == "write_file":
                relative_path = str(tool_input.get("relative_path", ""))
                if self._is_scratch_file(relative_path):
                    return self._tool_error_result(
                        tool_name=tool_name,
                        tool_input=tool_input,
                        error_type="scratch_file_not_allowed",
                        message=SCRATCH_FILE_REJECTION_MESSAGE,
                    )
                result = write_file(
                    self.repo_path,
                    relative_path=relative_path,
                    content=str(tool_input.get("content", "")),
                )
                if result.get("ok"):
                    result = result | {
                        "commit": self._commit_write(
                            tool_name=tool_name,
                            relative_path=relative_path,
                        )
                    }
                return result
            if tool_name == "edit_file":
                relative_path = str(tool_input.get("relative_path", ""))
                result = edit_file(
                    self.repo_path,
                    relative_path=relative_path,
                    old_string=str(tool_input.get("old_string", "")),
                    new_string=str(tool_input.get("new_string", "")),
                )
                if result.get("ok"):
                    result = result | {
                        "commit": self._commit_write(
                            tool_name=tool_name,
                            relative_path=relative_path,
                        )
                    }
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

    def _commit_write(self, *, tool_name: str, relative_path: str) -> dict[str, str]:
        normalized_relative_path = str(relative_path).replace("\\", "/")
        commit_hash = commit_workspace_path(
            self.repo_path,
            relative_path=normalized_relative_path,
            message=f"{tool_name}: {normalized_relative_path}",
        )
        return {
            "hash": commit_hash,
            "message": f"{tool_name}: {normalized_relative_path}",
            "relative_path": normalized_relative_path,
        }

    @staticmethod
    def _is_scratch_file(relative_path: str) -> bool:
        normalized_relative_path = str(relative_path).replace("\\", "/")
        return normalized_relative_path.split("/")[-1] in SCRATCH_FILE_NAMES

    def _undo_last_write(self) -> dict[str, Any]:
        try:
            reverted_commit = undo_last_workspace_commit(self.repo_path)
        except RuntimeError as error:
            return {
                "ok": False,
                "tool_name": "undo",
                "summary": "没有可回滚的写操作。",
                "data": {"reverted_files": []},
                "error": {
                    "type": "no_commit",
                    "message": str(error),
                },
            }

        return {
            "ok": True,
            "tool_name": "undo",
            "summary": "已回滚最近一次写操作。",
            "data": {
                "reverted_commit": reverted_commit,
                "reverted_files": [],
            },
            "error": None,
        }

    @staticmethod
    def summarize_for_model(result: dict[str, Any], *, max_chars: int) -> str:
        """把工具结果压成适合回喂给模型的文本。"""

        tool_name = result.get("tool_name")
        payload: dict[str, Any] = {
            "ok": result.get("ok", False),
            "tool_name": tool_name,
            "summary": result.get("summary", ""),
            "error": result.get("error"),
        }
        data = result.get("data", {})

        if tool_name == "run_tests" and result.get("ok", False):
            payload["data"] = {
                "exit_code": data.get("exit_code"),
                "duration_sec": data.get("duration_sec"),
            }
            return ToolExecutor._json_for_model(payload, max_chars=max_chars)

        failure_summary = result.get("data", {}).get("failure_summary")
        if tool_name == "run_tests" and failure_summary and not result.get("ok", False):
            payload["failure_summary"] = ToolExecutor._compact_failure_summary_for_model(failure_summary)
            payload["exit_code"] = data.get("exit_code")
            return ToolExecutor._json_for_model(
                payload,
                max_chars=max(max_chars, 12000 if "context_diff" in failure_summary else max_chars),
            )

        if tool_name == "read_file" and result.get("ok", False):
            char_count = int(data.get("char_count", 0) or 0)
            content = data.get("content", "")
            payload["data"] = {
                "relative_path": data.get("relative_path"),
                "line_count": data.get("line_count"),
                "start_line": data.get("start_line"),
                "end_line": data.get("end_line"),
                "char_count": char_count,
                "returned_line_count": data.get("returned_line_count"),
                "truncated": data.get("truncated", False),
                "content": content if char_count <= 20000 else (
                    str(content)[:2000]
                    + "\n...<large file; ask read_file for a smaller range after adding offset/limit support>"
                ),
            }
            return ToolExecutor._json_for_model(
                payload,
                max_chars=max(max_chars, min(char_count + 1000, 24000)),
            )

        if tool_name == "list_files" and result.get("ok", False):
            payload["data"] = {
                "recursive": data.get("recursive"),
                "count": data.get("count"),
                "files": data.get("files", []),
            }
            return ToolExecutor._json_for_model(payload, max_chars=max(max_chars, 8000))

        if tool_name in {"search_code", "grep"} and result.get("ok", False):
            matches = data.get("matches", [])
            payload["data"] = {
                "query": data.get("query") or data.get("pattern"),
                "match_count": data.get("match_count", len(matches)),
                "match_files": data.get("match_files", []),
                "matches": matches[:50],
                "truncated_matches": max(len(matches) - 50, 0),
            }
            return ToolExecutor._json_for_model(payload, max_chars=max_chars)

        if tool_name == "python_repl" and result.get("ok", False):
            payload["data"] = {
                "expression": data.get("expression"),
                "result_repr": data.get("result_repr"),
                "result_type": data.get("result_type"),
                "truncated": data.get("truncated", False),
            }
            return ToolExecutor._json_for_model(payload, max_chars=max_chars)

        if tool_name == "show_diff" and result.get("ok", False):
            payload["data"] = {
                "changed_files": data.get("changed_files", []),
                "diff_text": data.get("diff_text", ""),
            }
            return ToolExecutor._json_for_model(payload, max_chars=max(max_chars, 20000))

        if tool_name in {"write_file", "edit_file", "undo"} and result.get("ok", False):
            compact_data = {
                key: value
                for key, value in data.items()
                if key not in {"content", "old_content", "new_content"}
            }
            payload["data"] = compact_data
            if "commit" in result:
                payload["commit"] = result["commit"]
            relative_path = str(compact_data.get("relative_path", "")).replace("\\", "/")
            if tool_name == "write_file" and ToolExecutor._is_scratch_file(relative_path):
                payload["scratch_file_warning"] = (
                    "Temporary debug/probe files are not supported. Use read_file, grep, "
                    "run_tests failure output, and edit_file on the target source file instead."
                )
            return ToolExecutor._json_for_model(payload, max_chars=max_chars)

        return ToolExecutor._json_for_model(result, max_chars=max_chars)

    @staticmethod
    def _json_for_model(payload: dict[str, Any], *, max_chars: int) -> str:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        if len(text) <= max_chars:
            return text
        return f"{text[:max_chars]}\n...<truncated>"

    @staticmethod
    def _compact_failure_summary_for_model(failure_summary: dict[str, Any]) -> dict[str, Any]:
        compact_summary = {
            "short_summary": failure_summary.get("short_summary", ""),
            "failed_tests": failure_summary.get("failed_tests", []),
            "assertion_lines": failure_summary.get("assertion_lines", []),
            "locations": failure_summary.get("locations", []),
        }
        if "context_diff" in failure_summary:
            compact_summary["context_diff_changed_files"] = failure_summary.get(
                "context_diff_changed_files",
                [],
            )
            compact_summary["context_diff"] = failure_summary.get("context_diff", "")
        if "output_excerpt" in failure_summary:
            compact_summary["output_excerpt"] = failure_summary.get("output_excerpt", "")
        return compact_summary
