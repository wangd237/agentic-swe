"""从 jsonschema#1162 提炼出的最小 hostname 格式检查实现。"""

from __future__ import annotations


def is_valid_hostname(value: str) -> bool:
    """返回给定字符串是否满足最小 hostname 规则。"""
    labels = _split_hostname_labels(value)

    # 这里故意保留真实 issue 中的缺陷：错误要求 hostname 至少包含两个 label。
    if len(labels) < 2:
        return False

    if any(not label or not label.replace("-", "").isalnum() for label in labels):
        return False
    return True


def _split_hostname_labels(value: str) -> list[str]:
    """把 hostname 拆成 labels。"""
    return value.split(".")
