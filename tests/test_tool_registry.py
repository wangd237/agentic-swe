"""Registry integration: tool lookup must never weaken phase authorization."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.agent.tool_loop import AgentToolMixin
from app.core.state import AgentState
from app.core.policy_config import PolicyConfig
from app.tools.definitions import build_tool_definitions
from app.tools.executor import ToolExecutor
from app.tools.policy import ALLOWED_TOOLS_BY_PHASE, ToolPolicy
from app.tools.registry import ToolRegistry, get_tool_registry
from app.tools.router import build_tools_for_state
from app.tools.validator import validate_tool_call


def test_registry_has_one_handler_for_every_model_tool() -> None:
    registry = get_tool_registry()
    public_tools = build_tool_definitions()
    names = [tool["name"] for tool in public_tools]
    assert len(names) == len(set(names)) == 11
    assert set(names) == {spec.name for spec in registry.all_specs()}
    for definition in public_tools:
        assert "handler_name" not in definition
        assert "risk_level" not in definition
        assert validate_tool_call(definition["name"], {}) is None or (
            validate_tool_call(definition["name"], {})["error"]["type"] == "schema_validation_error"
        )
    for spec in registry.all_specs():
        assert callable(getattr(ToolExecutor, spec.handler_name, None))


def test_registry_risk_classification_is_not_a_permission_grant() -> None:
    registry = get_tool_registry()
    assert registry.get("read_file").risk_level == "read"
    assert registry.get("run_tests").risk_level == "execute"
    assert registry.get("edit_file").risk_level == "modify"
    assert registry.get("undo").risk_level == "modify"

    # Registration doesn't grant a write permission in the understand phase.
    state = AgentState(phase="understand")
    assert "edit_file" not in {tool["name"] for tool in build_tools_for_state(state)}
    denied = ToolPolicy().validate(
        state=state,
        tool_name="edit_file",
        tool_input={"relative_path": "pkg/app.py", "old_string": "a", "new_string": "b"},
    )
    assert denied is not None and denied["error"]["type"] == "tool_policy_violation"


def test_unconfigured_new_tool_is_denied_by_existing_policy() -> None:
    synthetic = {
        "name": "new_business_tool",
        "description": "Not authorized",
        "input_schema": {"type": "object", "properties": {}},
        "handler_name": "_handle_new_business_tool",
        "risk_level": "execute",
        "is_read_only": False,
        "is_concurrency_safe": False,
    }
    assert ToolRegistry([synthetic]).get("new_business_tool") is not None
    assert "new_business_tool" not in {t for names in ALLOWED_TOOLS_BY_PHASE.values() for t in names}
    state = AgentState(phase="patch")
    denied = ToolPolicy().validate(state=state, tool_name="new_business_tool", tool_input={})
    assert denied is not None and denied["error"]["type"] == "tool_policy_violation"


@pytest.mark.parametrize("field,value", [
    ("name", "read_file"),
    ("risk_level", "unsafe"),
    ("handler_name", "not_a_handler"),
])
def test_registry_rejects_invalid_or_duplicate_registration(field, value) -> None:
    entry = deepcopy(get_tool_registry().all_specs()[0].model_definition())
    entry["handler_name"] = "_handle_list_files"
    entry["risk_level"] = "read"
    if field == "name":
        with pytest.raises(ValueError, match="Duplicate"):
            ToolRegistry([entry, deepcopy(entry)])
    else:
        entry[field] = value
        with pytest.raises(ValueError):
            ToolRegistry([entry])


def test_policy_denies_write_before_executor_is_reached(tmp_path: Path) -> None:
    executor = Mock()
    state = AgentState(phase="understand")
    response = AgentToolMixin._execute_tool_block(
        tool_executor=executor,
        tool_policy=ToolPolicy(),
        state=state,
        block={
            "name": "write_file",
            "input": {"relative_path": "app.py", "content": "unsafe"},
        },
    )
    assert response["tool_result"]["error"]["type"] == "tool_policy_violation"
    executor.execute.assert_not_called()


def test_registry_dispatch_preserves_existing_read_file_behavior(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "hello.py").write_text("hello world\n", encoding="utf-8")
    executor = ToolExecutor(
        repo_path=repo_path,
        original_repo_path=repo_path,
        policy_config=PolicyConfig(policy_id="registry_smoke", description="smoke"),
        test_command="pytest -q",
    )
    result = executor.execute("read_file", {"relative_path": "hello.py"})
    assert result["ok"] is True
    assert "hello world" in result["data"]["content"]
    unknown = executor.execute("does_not_exist", {})
    assert unknown["error"]["type"] == "unknown_tool"
