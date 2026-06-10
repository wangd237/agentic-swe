"""从 jsonschema#1121 提炼出的最小 hostname 格式检查实现。"""

from __future__ import annotations


def is_valid_hostname(value: str) -> bool:
    """返回给定字符串是否满足最小 hostname 规则。"""
    # 这里故意保留真实 issue 中的缺陷：空字符串会在底层检查阶段直接抛出 ValueError。
    labels = _split_hostname_labels(value)
    if any(not label or not label.replace("-", "").isalnum() for label in labels):
        return False
    return True


def _split_hostname_labels(value: str) -> list[str]:
    """把 hostname 拆成 labels。"""
    if value == "":
        raise ValueError("hostname must not be empty")
    return value.split(".")
