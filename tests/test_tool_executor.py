from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from app.agent.policy import DEFAULT_POLICY
from app.agent.tool_executor import ToolExecutor
from app.agent.tool_definitions import build_tool_definitions
from app.runtime.git_workspace import initialize_git_workspace, run_git


def _executor(
    repo_path: Path,
    original_repo_path: Path | None = None,
    *,
    initialize_git: bool = True,
) -> ToolExecutor:
    if initialize_git:
        initialize_git_workspace(repo_path)
    return ToolExecutor(
        repo_path=repo_path,
        original_repo_path=original_repo_path or repo_path,
        policy_config=DEFAULT_POLICY,
        test_command="python -m pytest -q",
    )


def _git_log(repo_path: Path) -> list[str]:
    result = run_git(repo_path, ["log", "--pretty=%s"])
    assert result.returncode == 0
    return result.stdout.splitlines()


def test_tool_executor_commits_and_undoes_write_file(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("value = 1\n", encoding="utf-8")
    executor = _executor(repo_path)

    write_result = executor.execute(
        "write_file",
        {"relative_path": "pkg/app.py", "content": "value = 2\n"},
    )
    undo_result = executor.execute("undo", {})

    assert write_result["ok"] is True
    assert write_result["commit"]["message"] == "write_file: pkg/app.py"
    assert write_result["commit"]["relative_path"] == "pkg/app.py"
    assert undo_result["ok"] is True
    assert undo_result["data"]["reverted_commit"] == write_result["commit"]["hash"]
    assert target_path.read_text(encoding="utf-8") == "value = 1\n"
    assert _git_log(repo_path) == ["initial"]


def test_tool_executor_undo_removes_new_file(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    target_path = repo_path / "pkg" / "new_file.py"
    executor = _executor(repo_path)

    write_result = executor.execute(
        "write_file",
        {"relative_path": "pkg/new_file.py", "content": "value = 2\n"},
    )
    undo_result = executor.execute("undo", {})

    assert write_result["ok"] is True
    assert write_result["commit"] == {
        "hash": write_result["commit"]["hash"],
        "message": "write_file: pkg/new_file.py",
        "relative_path": "pkg/new_file.py",
    }
    assert undo_result["ok"] is True
    assert not target_path.exists()
    assert _git_log(repo_path) == ["initial"]


def test_tool_executor_failed_edit_does_not_create_undoable_commit(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("value = 1\nvalue = 1\n", encoding="utf-8")
    executor = _executor(repo_path)

    edit_result = executor.execute(
        "edit_file",
        {
            "relative_path": "pkg/app.py",
            "old_string": "value = 1",
            "new_string": "value = 2",
        },
    )
    undo_result = executor.execute("undo", {})

    assert edit_result["ok"] is False
    assert edit_result["error"]["type"] == "old_string_not_unique"
    assert undo_result["ok"] is False
    assert undo_result["error"]["type"] == "no_commit"
    assert target_path.read_text(encoding="utf-8") == "value = 1\nvalue = 1\n"


def test_tool_executor_failed_write_does_not_create_undoable_commit(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("value = 1\n", encoding="utf-8")
    executor = _executor(repo_path)
    failed_result = {
        "ok": False,
        "tool_name": "write_file",
        "summary": "写入文件时发生异常。",
        "data": {
            "repo_path": str(repo_path),
            "relative_path": "pkg/app.py",
            "content_length": 10,
        },
        "error": {"type": "unknown_error", "message": "boom"},
    }

    with patch("app.agent.tool_executor.write_file", return_value=failed_result):
        write_result = executor.execute(
            "write_file",
            {"relative_path": "pkg/app.py", "content": "value = 2\n"},
        )
    undo_result = executor.execute("undo", {})

    assert write_result["ok"] is False
    assert write_result["error"]["type"] == "unknown_error"
    assert undo_result["ok"] is False
    assert undo_result["error"]["type"] == "no_commit"
    assert target_path.read_text(encoding="utf-8") == "value = 1\n"
    assert _git_log(repo_path) == ["initial"]


def test_tool_executor_rejects_scratch_write_without_commit(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    executor = _executor(repo_path)

    write_result = executor.execute(
        "write_file",
        {"relative_path": "debug.py", "content": "print('probe')\n"},
    )
    undo_result = executor.execute("undo", {})

    assert write_result["ok"] is False
    assert write_result["error"]["type"] == "scratch_file_not_allowed"
    assert "edit_file" in write_result["error"]["message"]
    assert not (repo_path / "debug.py").exists()
    assert undo_result["ok"] is False
    assert undo_result["error"]["type"] == "no_commit"
    assert _git_log(repo_path) == ["initial"]


def test_tool_executor_rejects_nested_scratch_write(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    executor = _executor(repo_path)

    write_result = executor.execute(
        "write_file",
        {"relative_path": "pkg\\tmp.py", "content": "print('probe')\n"},
    )

    assert write_result["ok"] is False
    assert write_result["error"]["type"] == "scratch_file_not_allowed"
    assert not (repo_path / "pkg" / "tmp.py").exists()
    assert _git_log(repo_path) == ["initial"]


def test_tool_executor_show_diff_uses_git_initial_baseline(tmp_path: Path) -> None:
    original_repo_path = tmp_path / "original"
    repo_path = tmp_path / "repo"
    original_target_path = original_repo_path / "pkg" / "app.py"
    target_path = repo_path / "pkg" / "app.py"
    original_target_path.parent.mkdir(parents=True)
    target_path.parent.mkdir(parents=True)
    original_target_path.write_text("value = 1\n", encoding="utf-8")
    target_path.write_text("value = 1\n", encoding="utf-8")
    executor = _executor(repo_path, original_repo_path)

    executor.execute(
        "write_file",
        {"relative_path": "pkg/app.py", "content": "value = 2\n"},
    )
    diff_result = executor.execute("show_diff", {})

    assert diff_result["ok"] is True
    assert diff_result["data"]["changed_files"] == ["pkg/app.py"]
    assert "diff --git a/pkg/app.py b/pkg/app.py" in diff_result["data"]["diff_text"]
    assert "+value = 2" in diff_result["data"]["diff_text"]


def test_tool_executor_dispatches_grep(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("def test_value():\n    return False\n", encoding="utf-8")
    executor = _executor(repo_path)

    result = executor.execute("grep", {"pattern": r"def\s+test_\w+", "glob": "*.py"})

    assert result["ok"] is True
    assert result["data"]["matches"][0]["relative_path"] == "pkg/app.py"
    assert result["data"]["matches"][0]["line_number"] == 1


def test_tool_executor_dispatches_read_file_line_range(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    target_path = repo_path / "pkg" / "app.py"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("one\ntwo\nthree\nfour\n", encoding="utf-8")
    executor = _executor(repo_path)

    result = executor.execute(
        "read_file",
        {
            "relative_path": "pkg/app.py",
            "start_line": 2,
            "end_line": 3,
        },
    )

    assert result["ok"] is True
    assert result["data"]["content"] == "two\nthree\n"
    assert result["data"]["start_line"] == 2
    assert result["data"]["end_line"] == 3


def test_tool_executor_dispatches_python_repl(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    executor = _executor(repo_path)

    result = executor.execute(
        "python_repl",
        {"expression": "Version('4.1.0a2.dev1235+local').base_version"},
    )

    assert result["ok"] is True
    assert result["data"]["result_repr"] == "'4.1.0'"


def test_tool_executor_summarize_for_model_compacts_python_repl() -> None:
    result = {
        "ok": True,
        "tool_name": "python_repl",
        "summary": "表达式求值成功。",
        "data": {
            "expression": "Version('1.0').base_version",
            "result_repr": "'1.0'",
            "result_type": "str",
            "truncated": False,
            "extra_noise": "x" * 1000,
        },
        "error": None,
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=500)
    payload = json.loads(summary)

    assert payload["data"] == {
        "expression": "Version('1.0').base_version",
        "result_repr": "'1.0'",
        "result_type": "str",
        "truncated": False,
    }


def test_tool_executor_summarize_for_model_prefers_failure_summary() -> None:
    result = {
        "ok": False,
        "tool_name": "run_tests",
        "summary": "测试失败：tests/test_app.py::test_value。",
        "data": {
            "exit_code": 1,
            "stdout": "very noisy output\n" * 1000,
            "stderr": "",
            "failure_summary": {
                "failed_tests": ["tests/test_app.py::test_value - assert 1 == 2"],
                "assertion_lines": ["assert value() == 2", "assert 1 == 2"],
                "locations": [
                    {
                        "path": "tests/test_app.py",
                        "line": 4,
                        "error": "AssertionError",
                    }
                ],
                "short_summary": "失败测试: tests/test_app.py::test_value - assert 1 == 2",
            },
        },
        "error": {"type": "test_failure", "message": "failed"},
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=800)

    assert "failure_summary" in summary
    assert "tests/test_app.py::test_value" in summary
    assert "assert 1 == 2" in summary
    assert "very noisy output" not in summary


def test_tool_executor_summarize_for_model_preserves_failure_context_diff() -> None:
    result = {
        "ok": False,
        "tool_name": "run_tests",
        "summary": "测试失败：tests/test_app.py::test_value。",
        "data": {
            "exit_code": 1,
            "stdout": "very noisy output\n" * 1000,
            "stderr": "",
            "failure_summary": {
                "failed_tests": ["tests/test_app.py::test_value - assert 2 == 1"],
                "assertion_lines": ["assert value() == 1", "assert 2 == 1"],
                "locations": [
                    {
                        "path": "tests/test_app.py",
                        "line": 5,
                        "error": "AssertionError",
                    }
                ],
                "short_summary": "断言: assert value() == 1",
                "output_excerpt": "very noisy output\n" * 1000,
                "context_diff_changed_files": ["demo_pkg/app.py"],
                "context_diff": "diff --git a/demo_pkg/app.py b/demo_pkg/app.py\n+    return 2\n",
            },
        },
        "error": {"type": "test_failure", "message": "failed"},
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=800)

    assert "context_diff" in summary
    assert "+    return 2" in summary
    assert summary.index("context_diff") < summary.index("output_excerpt")


def test_tool_executor_summarize_for_model_compacts_successful_run_tests() -> None:
    result = {
        "ok": True,
        "tool_name": "run_tests",
        "summary": "测试命令执行成功，目标测试已通过。",
        "data": {
            "exit_code": 0,
            "duration_sec": 1.2,
            "stdout": "test passed\n" * 1000,
            "stderr": "",
        },
        "error": None,
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=500)

    assert "测试命令执行成功" in summary
    assert "exit_code" in summary
    assert "test passed" not in summary


def test_tool_executor_summarize_for_model_preserves_read_file_content() -> None:
    content = "line\n" * 300
    result = {
        "ok": True,
        "tool_name": "read_file",
        "summary": "已读取文件 demo.py，共 300 行。",
        "data": {
            "relative_path": "demo.py",
            "content": content,
            "line_count": 300,
            "start_line": 10,
            "end_line": 309,
            "char_count": len(content),
            "returned_line_count": 300,
            "truncated": False,
        },
        "error": None,
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=200)
    payload = json.loads(summary)

    assert payload["data"]["content"] == content
    assert payload["data"]["start_line"] == 10
    assert payload["data"]["end_line"] == 309
    assert payload["data"]["returned_line_count"] == 300
    assert "...<truncated>" not in summary


def test_read_file_tool_schema_exposes_line_range() -> None:
    read_file_schema = next(
        tool for tool in build_tool_definitions()
        if tool["name"] == "read_file"
    )

    properties = read_file_schema["input_schema"]["properties"]
    assert properties["start_line"]["minimum"] == 1
    assert properties["end_line"]["minimum"] == 1
    assert "局部上下文" in read_file_schema["description"]


def test_tool_executor_summarize_for_model_strips_write_content() -> None:
    result = {
        "ok": True,
        "tool_name": "write_file",
        "summary": "已写入文件 demo.py。",
        "data": {
            "relative_path": "demo.py",
            "content_length": 1000,
            "content": "secret content",
        },
        "commit": {
            "hash": "abc1234",
            "message": "write_file: demo.py",
            "relative_path": "demo.py",
        },
        "error": None,
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=500)

    assert "write_file: demo.py" in summary
    assert "content_length" in summary
    assert "secret content" not in summary


def test_tool_executor_summarize_for_model_warns_for_scratch_write() -> None:
    result = {
        "ok": True,
        "tool_name": "write_file",
        "summary": "已写入文件 debug.py。",
        "data": {
            "relative_path": "debug.py",
            "content_length": 100,
        },
        "commit": {
            "hash": "abc1234",
            "message": "write_file: debug.py",
            "relative_path": "debug.py",
        },
        "error": None,
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=1000)
    payload = json.loads(summary)

    assert "scratch_file_warning" in payload
    assert "not supported" in payload["scratch_file_warning"]
    assert "grep" in payload["scratch_file_warning"]
    assert "target source file" in payload["scratch_file_warning"]


def test_tool_executor_summarize_for_model_limits_grep_matches() -> None:
    matches = [
        {
            "relative_path": "demo.py",
            "line_number": index + 1,
            "line_text": f"value_{index} = {index}",
        }
        for index in range(60)
    ]
    result = {
        "ok": True,
        "tool_name": "grep",
        "summary": "正则 `value_\\d+` 命中 60 处。",
        "data": {
            "pattern": r"value_\d+",
            "matches": matches,
            "match_count": 60,
            "match_files": ["demo.py"],
        },
        "error": None,
    }

    summary = ToolExecutor.summarize_for_model(result, max_chars=10000)
    payload = json.loads(summary)

    assert payload["data"]["query"] == r"value_\d+"
    assert len(payload["data"]["matches"]) == 50
    assert payload["data"]["truncated_matches"] == 10
