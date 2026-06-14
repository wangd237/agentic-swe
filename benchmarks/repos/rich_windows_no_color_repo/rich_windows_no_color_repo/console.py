"""从 rich#2457 提炼出的最小 Windows-like no_color 回归实现。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowsConsoleFeatures:
    """只保留当前回归题所需的最小 Windows 控制台特性。"""

    vt: bool = False
    truecolor: bool = False


class Console:
    """模拟 Rich 在不同控制台能力下的最小着色输出行为。"""

    def __init__(
        self,
        *,
        no_color: bool = False,
        legacy_windows: bool = False,
        features: WindowsConsoleFeatures | None = None,
    ) -> None:
        self.no_color = no_color
        self.legacy_windows = legacy_windows
        self.features = features or WindowsConsoleFeatures()

    def render(self, text: str, *, style: str | None = None) -> str:
        """把文本渲染成最小可观察输出。"""

        if style is None:
            return text

        if self.legacy_windows and not self.features.vt:
            # 这里故意保留 rich#2457 的缺陷：Windows 旧控制台分支忽略 no_color。
            return f"<WIN:{style}>{text}</WIN:{style}>"

        if self.no_color:
            return text

        return f"\x1b[31m{text}\x1b[0m"
