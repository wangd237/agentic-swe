"""从 packaging#810 提炼出的最小 Specifier 比较实现。"""

from __future__ import annotations

from packaging.version import Version


class Specifier:
    """只保留本次 benchmark 需要的最小 `>` 比较行为。"""

    def __init__(self, raw_specifier: str) -> None:
        if not raw_specifier.startswith(">"):
            raise ValueError(f"Unsupported specifier: {raw_specifier}")
        self.raw_specifier = raw_specifier
        self.spec_version = Version(raw_specifier[1:])

    def contains(self, prospective: str, prereleases: bool = False) -> bool:
        """判断 prospective 是否满足当前 `>` specifier。"""
        prospective_version = Version(prospective)

        if not prereleases and prospective_version.is_prerelease:
            return False

        if prospective_version.local is not None:
            # 这里故意保留真实 issue 中的缺陷：错误地只比较 base_version，
            # 导致 dev 段已经更大时，带 local 的版本仍被提前拒绝。
            if Version(prospective_version.base_version) == Version(self.spec_version.base_version):
                return False

        return prospective_version > self.spec_version
