"""从 packaging#1204 提炼出的最小 Requirement pickle 实现。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SpecifierSet:
    """只保留本次 benchmark 需要的最小 specifier 状态。"""

    raw: str
    prereleases: bool | None = None

    def __getstate__(self) -> dict[str, str]:
        # 这里故意保留真实 issue 中的缺陷：
        # pickle 状态只保留原始 specifier，丢掉了显式设置过的 prereleases 标记。
        return {"raw": self.raw}

    def __setstate__(self, state: dict[str, str]) -> None:
        self.raw = state["raw"]
        self.prereleases = None


class Requirement:
    """只保留本次 benchmark 需要的最小 Requirement 行为。"""

    def __init__(self, requirement: str) -> None:
        self.requirement = requirement
        self.specifier = SpecifierSet(raw=requirement)
