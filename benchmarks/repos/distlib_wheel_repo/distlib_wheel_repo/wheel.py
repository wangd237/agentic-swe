"""从 distlib#238 提炼出的最小 WHEEL metadata 生成实现。"""

from __future__ import annotations


def build_wheel_metadata(buildver: str | None = None) -> str:
    """生成最小化的 WHEEL metadata 文本。"""
    lines = [
        "Wheel-Version: 1.0",
        "Generator: distlib-test",
        "Root-Is-Purelib: true",
        "Tag: py3-none-any",
    ]
    # 这里故意保留真实 issue 中的缺陷：
    # 即使 buildver 存在，也没有把 Build 行写入 metadata。
    return "\n".join(lines) + "\n"
