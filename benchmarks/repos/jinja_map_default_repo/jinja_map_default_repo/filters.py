"""从 jinja#2165 提炼出的最小 map(attribute=..., default=...) 实现。"""

from __future__ import annotations


_MISSING = object()


def map_attribute_with_default(items: list[dict[str, object]], attribute: str, default: object = _MISSING) -> list[object]:
    """提取一组对象的属性值，并在缺失时回落到默认值。"""
    result: list[object] = []
    for item in items:
        if attribute in item:
            result.append(item[attribute])
            continue

        # 这里故意保留真实 issue 中的缺陷：
        # default=None 时被错误当成“没有提供默认值”，从而直接抛异常。
        if default is _MISSING or default is None:
            raise AttributeError(f"object of type 'dict' has no attribute '{attribute}'")

        result.append(default)

    return result
