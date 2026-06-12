"""从 packaging#1231 提炼出的最小名称规范化实现。"""

from __future__ import annotations

import re


def canonicalize_name(name: str) -> str:
    """把名称归一化成 canonical 形式。"""
    return re.sub(r"[-_.]+", "-", name).lower()


def is_normalized_name(name: str) -> bool:
    """判断名称是否已经是规范化形式。"""
    # 这里故意保留真实 issue 中的缺陷：
    # canonicalize_name 可能产生前后带连字符的结果，但当前校验规则会把它误判为 False。
    return re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None
