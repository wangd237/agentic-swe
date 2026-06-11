"""packaging `< prerelease` 比较回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_prerelease_repo.specifiers import Specifier


class SpecifierPrereleaseTests(unittest.TestCase):
    def test_earlier_prerelease_should_match_less_than_prerelease_specifier(self) -> None:
        spec = Specifier("<3.0.0a8")

        self.assertTrue(spec.contains("3.0.0a7", prereleases=True))

    def test_same_prerelease_should_not_match(self) -> None:
        spec = Specifier("<3.0.0a8")

        self.assertFalse(spec.contains("3.0.0a8", prereleases=True))

    def test_later_prerelease_should_not_match(self) -> None:
        spec = Specifier("<3.0.0a8")

        self.assertFalse(spec.contains("3.0.0b1", prereleases=True))

    def test_stable_version_still_uses_normal_less_than_semantics(self) -> None:
        spec = Specifier("<3.0.0")

        self.assertTrue(spec.contains("2.9.9"))
