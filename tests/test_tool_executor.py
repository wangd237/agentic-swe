from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from app.agent.policy import DEFAULT_POLICY
from app.agent.tool_executor import ToolExecutor


def _executor(repo_path: Path, original_repo_path: Path | None = None) -> ToolExecutor:
    return ToolExecutor(
        repo_path=repo_path,
        original_repo_path=original_repo_path or repo_path,
        policy_config=DEFAULT_POLICY,
        test_command="python -m pytest -q",
    )


def test_tool_executor_checkpoints_and_undoes_write_file(tmp_path: Path) -> None:
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
    assert write_result["checkpoint"] == {
        "step": 1,
        "relative_path": "pkg/app.py",
        "existed": True,
    }
    assert undo_result["ok"] is True
    assert undo_result["data"]["reverted_files"] == ["pkg/app.py"]
    assert target_path.read_text(encoding="utf-8") == "value = 1\n"


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
    assert write_result["checkpoint"]["existed"] is False
    assert undo_result["ok"] is True
    assert not target_path.exists()


def test_tool_executor_failed_edit_does_not_create_undoable_checkpoint(tmp_path: Path) -> None:
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
    assert undo_result["error"]["type"] == "no_checkpoint"
    assert target_path.read_text(encoding="utf-8") == "value = 1\nvalue = 1\n"


def test_tool_executor_cleans_checkpoint_when_write_fails_after_snapshot(tmp_path: Path) -> None:
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
    assert undo_result["error"]["type"] == "no_checkpoint"
    assert not (repo_path / ".agent_checkpoints" / "step_1").exists()
    assert target_path.read_text(encoding="utf-8") == "value = 1\n"


def test_tool_executor_checkpoints_are_hidden_from_show_diff(tmp_path: Path) -> None:
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
    assert ".agent_checkpoints" not in diff_result["data"]["diff_text"]


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
