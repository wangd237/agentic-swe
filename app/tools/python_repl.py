"""受控 Python 表达式求值工具。"""

from __future__ import annotations

import ast
from typing import Any


MAX_EXPRESSION_LENGTH = 500
MAX_RESULT_CHARS = 1200

SAFE_BUILTINS: dict[str, Any] = {
    "abs": abs,
    "bool": bool,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "repr": repr,
    "round": round,
    "sorted": sorted,
    "str": str,
    "sum": sum,
}

SAFE_GLOBALS: dict[str, Any] = {
    **SAFE_BUILTINS,
}

try:
    from packaging.version import Version, parse as parse_version
except Exception:  # pragma: no cover - depends on optional local environment
    Version = None
    parse_version = None
else:
    SAFE_GLOBALS["Version"] = Version
    SAFE_GLOBALS["parse_version"] = parse_version


class _SafetyValidator(ast.NodeVisitor):
    """限制表达式只能做只读计算和白名单函数调用。"""

    def __init__(self, allowed_call_names: set[str]) -> None:
        self.allowed_call_names = allowed_call_names

    def visit_Import(self, node: ast.Import) -> None:  # pragma: no cover - eval mode rejects this first
        raise ValueError("import is not allowed")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # pragma: no cover - eval mode rejects this first
        raise ValueError("import is not allowed")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith("_") or "__" in node.id:
            raise ValueError("private or dunder names are not allowed")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_") or "__" in node.attr:
            raise ValueError("private or dunder attributes are not allowed")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name):
            raise ValueError("only direct calls to whitelisted functions are allowed")
        if node.func.id not in self.allowed_call_names:
            raise ValueError(f"function is not allowed: {node.func.id}")
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        raise ValueError("lambda is not allowed")

    def visit_ListComp(self, node: ast.ListComp) -> None:
        raise ValueError("comprehensions are not allowed")

    def visit_SetComp(self, node: ast.SetComp) -> None:
        raise ValueError("comprehensions are not allowed")

    def visit_DictComp(self, node: ast.DictComp) -> None:
        raise ValueError("comprehensions are not allowed")

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        raise ValueError("comprehensions are not allowed")

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        raise ValueError("assignment expressions are not allowed")


def _reject_unsafe_source(expression: str) -> None:
    if not expression.strip():
        raise ValueError("expression is empty")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError(f"expression is too long; max {MAX_EXPRESSION_LENGTH} chars")
    if "\n" in expression or "\r" in expression:
        raise ValueError("only a single-line expression is allowed")
    if ";" in expression:
        raise ValueError("semicolon is not allowed")
    if "__" in expression:
        raise ValueError("dunder access is not allowed")
    if "import" in expression:
        raise ValueError("import is not allowed")


def _safe_eval(expression: str) -> Any:
    _reject_unsafe_source(expression)
    tree = ast.parse(expression, mode="eval")
    _SafetyValidator(set(SAFE_GLOBALS)).visit(tree)
    compiled = compile(tree, filename="<python_repl>", mode="eval")
    return eval(compiled, {"__builtins__": {}}, SAFE_GLOBALS)


def python_repl(expression: str) -> dict[str, Any]:
    """求值一个受控 Python 单行表达式，用于查询第三方库行为。"""

    try:
        result = _safe_eval(str(expression))
        result_repr = repr(result)
        truncated = len(result_repr) > MAX_RESULT_CHARS
        if truncated:
            result_repr = f"{result_repr[:MAX_RESULT_CHARS]}\n...<truncated>"
        return {
            "ok": True,
            "tool_name": "python_repl",
            "summary": f"表达式求值成功：{result_repr}",
            "data": {
                "expression": expression,
                "result_repr": result_repr,
                "result_type": type(result).__name__,
                "truncated": truncated,
            },
            "error": None,
        }
    except SyntaxError as error:
        return {
            "ok": False,
            "tool_name": "python_repl",
            "summary": "表达式语法无效。",
            "data": {"expression": expression},
            "error": {"type": "invalid_expression", "message": str(error)},
        }
    except ValueError as error:
        return {
            "ok": False,
            "tool_name": "python_repl",
            "summary": f"表达式被安全策略拒绝：{error}",
            "data": {"expression": expression},
            "error": {"type": "unsafe_expression", "message": str(error)},
        }
    except Exception as error:
        return {
            "ok": False,
            "tool_name": "python_repl",
            "summary": f"表达式执行失败：{error}",
            "data": {"expression": expression},
            "error": {"type": "evaluation_error", "message": str(error)},
        }
