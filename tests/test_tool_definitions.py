from __future__ import annotations

from app.agent.tool_definitions import build_tool_definitions


def test_tool_definitions_include_python_repl_boundaries() -> None:
    tools = build_tool_definitions()
    python_repl_tool = next(tool for tool in tools if tool["name"] == "python_repl")

    assert "expression" in python_repl_tool["input_schema"]["required"]
    assert "import" in python_repl_tool["description"]
    assert "分号" in python_repl_tool["description"]
    assert "dunder" in python_repl_tool["description"]
