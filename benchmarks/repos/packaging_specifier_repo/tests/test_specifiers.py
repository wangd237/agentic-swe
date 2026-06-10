"""packaging Specifier dev/local 比较回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_specifier_repo.specifiers import Specifier


class SpecifierContainsTests(unittest.TestCase):
    def test_same_dev_without_local_is_not_greater(self) -> None:
        spec = Specifier(">4.1.0a2.dev1234")

        self.assertFalse(spec.contains("4.1.0a2.dev1234", prereleases=True))

    def test_next_dev_without_local_is_greater(self) -> None:
        spec = Specifier(">4.1.0a2.dev1234")

        self.assertTrue(spec.contains("4.1.0a2.dev1235", prereleases=True))

    def test_same_public_version_with_local_is_still_not_greater(self) -> None:
        spec = Specifier(">4.1.0a2.dev1234")

        self.assertFalse(spec.contains("4.1.0a2.dev1234+local", prereleases=True))

    def test_larger_dev_with_local_is_greater(self) -> None:
        spec = Specifier(">4.1.0a2.dev1234")

        self.assertTrue(spec.contains("4.1.0a2.dev1235+local", prereleases=True))
