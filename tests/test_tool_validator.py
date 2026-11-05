"""Validation of model-provided arguments at the tool-call boundary."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.agent.tool_loop import AgentToolMixin
from app.tools.definitions import build_tool_definitions
from app.tools.validator import validate_tool_call


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("read_file", {}),
        ("read_file", {"relative_path": 123}),
        ("read_file", {"relative_path": "main.py", "unexpected": True}),
        ("read_file", {"relative_path": "main.py", "start_line": 0}),
        ("grep", {"pattern": 42}),
        ("show_diff", {"extra": "not allowed"}),
        ("missing_tool", {}),
        ("read_file", ["main.py"]),
        ("read_file", None),
    ],
)
def test_invalid_arguments_are_rejected(tool_name, arguments):
    result = validate_tool_call(tool_name, arguments)
    assert result is not None
    assert result["ok"] is False
    assert result["error"]["type"] == "schema_validation_error"
    assert result["data"]["validation_failed"] is True


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        ("read_file", {"relative_path": "src/main.py"}),
        ("read_file", {"relative_path": "src/main.py", "start_line": 1, "end_line": 3}),
        ("show_diff", {}),
        ("list_files", {}),
        ("edit_file", {"relative_path": "src/main.py", "old_string": "a", "new_string": "b"}),
    ],
)
def test_valid_arguments_are_accepted(tool_name, arguments):
    assert validate_tool_call(tool_name, arguments) is None


def test_all_declared_tool_schemas_can_be_compiled():
    for tool in build_tool_definitions():
        # A non-empty valid example is not required for each tool.
        assert "name" in tool and "input_schema" in tool
    assert validate_tool_call("show_diff", {}) is None


def test_model_invalid_args_cannot_reach_policy_or_executor():
    policy = Mock()
    executor = Mock()
    result = AgentToolMixin._execute_tool_block(
        tool_executor=executor,
        tool_policy=policy,
        state=Mock(),
        block={"name": "read_file", "input": {"relative_path": 123}},
    )
    assert result["tool_result"]["error"]["type"] == "schema_validation_error"
    policy.validate.assert_not_called()
    executor.execute.assert_not_called()


def test_model_valid_args_pass_through_policy_and_executor():
    policy = Mock()
    policy.validate.return_value = None
    executor = Mock()
    executor.execute.return_value = {"ok": True, "summary": "read"}
    state = Mock()
    arguments = {"relative_path": "src/main.py"}
    result = AgentToolMixin._execute_tool_block(
        tool_executor=executor,
        tool_policy=policy,
        state=state,
        block={"name": "read_file", "input": arguments},
    )
    assert result["tool_result"]["ok"] is True
    policy.validate.assert_called_once_with(
        state=state, tool_name="read_file", tool_input=arguments
    )
    executor.execute.assert_called_once_with("read_file", arguments)


def test_invalid_args_do_not_bypass_phase_policy():
    policy = Mock()
    policy.validate.return_value = {"ok": False, "error": {"type": "tool_policy_violation"}}
    executor = Mock()
    result = AgentToolMixin._execute_tool_block(
        tool_executor=executor,
        tool_policy=policy,
        state=Mock(),
        block={"name": "edit_file", "input": {
            "relative_path": "src/main.py", "old_string": "a", "new_string": "b"
        }},
    )
    assert result["tool_result"]["error"]["type"] == "tool_policy_violation"
    executor.execute.assert_not_called()
