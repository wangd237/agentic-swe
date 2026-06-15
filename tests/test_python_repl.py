from __future__ import annotations

from app.tools.python_repl import python_repl


def test_python_repl_evaluates_single_safe_expression() -> None:
    result = python_repl("Version('4.1.0a2.dev1235+local').base_version")

    assert result["ok"] is True
    assert result["data"]["result_repr"] == "'4.1.0'"
    assert result["data"]["result_type"] == "str"


def test_python_repl_rejects_import() -> None:
    result = python_repl("__import__('os').system('echo unsafe')")

    assert result["ok"] is False
    assert result["error"]["type"] == "unsafe_expression"
    assert "dunder" in result["error"]["message"]


def test_python_repl_rejects_semicolon() -> None:
    result = python_repl("1 + 1; 2 + 2")

    assert result["ok"] is False
    assert result["error"]["type"] == "unsafe_expression"
    assert "semicolon" in result["error"]["message"]


def test_python_repl_rejects_dunder_attribute() -> None:
    result = python_repl("Version('1.0').__class__")

    assert result["ok"] is False
    assert result["error"]["type"] == "unsafe_expression"
    assert "dunder" in result["error"]["message"]


def test_python_repl_rejects_attribute_call() -> None:
    result = python_repl("'abc'.upper()")

    assert result["ok"] is False
    assert result["error"]["type"] == "unsafe_expression"
    assert "direct calls" in result["error"]["message"]


def test_python_repl_rejects_multiline() -> None:
    result = python_repl("1 + 1\n2 + 2")

    assert result["ok"] is False
    assert result["error"]["type"] == "unsafe_expression"
    assert "single-line" in result["error"]["message"]
