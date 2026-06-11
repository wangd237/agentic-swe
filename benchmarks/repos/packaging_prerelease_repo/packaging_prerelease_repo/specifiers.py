"""从 packaging#788 提炼出的最小 prerelease specifier 比较实现。"""

from __future__ import annotations

from packaging.version import Version


class Specifier:
    """只保留本次 benchmark 需要的最小 `<` 比较行为。"""

    def __init__(self, raw_specifier: str) -> None:
        if not raw_specifier.startswith("<"):
            raise ValueError(f"Unsupported specifier: {raw_specifier}")
        self.raw_specifier = raw_specifier
        self.spec_version = Version(raw_specifier[1:])

    def contains(self, prospective: str, prereleases: bool = False) -> bool:
        """判断 prospective 是否满足当前 `<` specifier。"""
        prospective_version = Version(prospective)

        if prospective_version == self.spec_version:
            return False

        if prospective_version.is_prerelease and self.spec_version.is_prerelease:
            # 这里故意保留真实 issue 中的缺陷：
            # 当前实现把“specifier 本身是 prerelease”的场景也直接拒绝掉，
            # 从而错误排除了更早的合法 prerelease 版本。
            return False

        if not prereleases and prospective_version.is_prerelease:
            return False

        return prospective_version < self.spec_version
