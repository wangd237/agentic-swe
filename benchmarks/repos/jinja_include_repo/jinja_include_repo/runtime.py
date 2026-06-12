"""从 jinja#2108 提炼出的最小 include without context 实现。"""

from __future__ import annotations


def _render_include_template(template_name: str, caller_context: dict[str, object], *, with_context: bool) -> str:
    """渲染被 include 的最小模板。"""
    if template_name != "test.html":
        raise ValueError(f"unknown template: {template_name}")

    if with_context:
        return str(caller_context.get("value", ""))

    return "TEST"


def _render_include_template_stream(template_name: str, caller_context: dict[str, object], *, with_context: bool):
    """以生成器形式返回 include 模板结果，模拟模板运行时的流式输出。"""
    yield _render_include_template(template_name, caller_context, with_context=with_context)


def render_macro_with_include_without_context() -> str:
    """模拟 macro 内部执行 include without context。"""
    caller_context = {"value": "OUTER"}

    # 这里故意保留真实 issue 中的缺陷：
    # macro 内部的 include without context 错误把生成器对象直接格式化成字符串，
    # 导致最终结果出现 `<generator object ...>`，而不是 include 模板的真实输出。
    stream = _render_include_template_stream("test.html", caller_context, with_context=False)
    return f"{stream}"


def render_macro_with_include() -> str:
    """模拟 macro 内部执行普通 include。"""
    caller_context = {"value": "OUTER"}
    return _render_include_template("test.html", caller_context, with_context=True)


def render_top_level_include_without_context() -> str:
    """模拟顶层执行 include without context。"""
    caller_context = {"value": "OUTER"}
    return _render_include_template("test.html", caller_context, with_context=False)
