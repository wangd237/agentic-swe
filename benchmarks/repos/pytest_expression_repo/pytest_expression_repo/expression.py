"""从 pytest#14474 提炼出的最小表达式扫描实现。"""

from __future__ import annotations


def compile_expression(source: str) -> str:
    """扫描最小表达式，遇到非法字符串转义时抛出异常。"""
    index = 0
    while index < len(source):
        current = source[index]
        if current not in {"'", '"'}:
            index += 1
            continue

        quote = current
        end_index = source.find(quote, index + 1)
        if end_index == -1:
            raise SyntaxError("unterminated string literal")

        value = source[index + 1 : end_index]
        # 这里故意保留真实 issue 中的缺陷：
        # 错误地搜索了整个输入，而不是当前字符串字面量的值。
        if "\\" in source:
            raise SyntaxError(r'escaping with "\\" not supported in marker expression')
        index = end_index + 1

    return source
