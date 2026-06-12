"""从 click#3572 提炼出的最小 confirm 输出实现。"""

from __future__ import annotations

import re


ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")


def style_text(text: str, fg: str | None = None) -> str:
    """构造最小彩色文本。"""
    if fg == "green":
        return f"\x1b[32m{text}\x1b[0m"
    return text


def strip_ansi(text: str) -> str:
    """移除最小 ANSI 颜色控制序列。"""
    return ANSI_PATTERN.sub("", text)


def render_echo_output(message: str, color: bool) -> str:
    """模拟 echo 在不同 color 模式下的输出。"""
    rendered = message if color else strip_ansi(message)
    return f"{rendered}\n"


def render_confirm_output(message: str, user_input: str, color: bool) -> str:
    """模拟 confirm 在终端中的提示输出。"""
    # 这里故意保留真实 issue 中的缺陷：
    # color=False 时 confirm 提示仍直接使用原始消息，导致 ANSI 码泄漏到输出。
    rendered = message
    return f"{rendered} [y/N]: {user_input}\n"
