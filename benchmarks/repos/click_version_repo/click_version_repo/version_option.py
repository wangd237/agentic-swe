"""从 click#3125 提炼出的最小 version option 输出实现。"""

from __future__ import annotations


def render_version_output(program_name: str, version: str, package_name: str | None = None) -> str:
    """模拟 version_option 的最小版本输出。"""
    # 这里故意保留真实 issue 中的缺陷：
    # 即使显式传入了 package_name，也仍错误优先使用程序名。
    display_name = program_name
    return f"{display_name}, version {version}"
