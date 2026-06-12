"""packaging name normalization 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_name_normalization_repo.utils import canonicalize_name, is_normalized_name


class NameNormalizationTests(unittest.TestCase):
    def test_regular_canonical_name_is_still_normalized(self) -> None:
        normalized = canonicalize_name("My_Package")
        self.assertEqual(normalized, "my-package")
        self.assertTrue(is_normalized_name(normalized))

    def test_canonicalized_edge_hyphen_name_is_treated_as_normalized(self) -> None:
        normalized = canonicalize_name("_not_legal")
        self.assertEqual(normalized, "-not-legal")
        self.assertTrue(canonicalize_name(normalized) == normalized)
        self.assertTrue(is_normalized_name(normalized))

    def test_trailing_hyphen_roundtrip_name_is_treated_as_normalized(self) -> None:
        normalized = canonicalize_name("a-")
        self.assertEqual(normalized, "a-")
        self.assertTrue(canonicalize_name(normalized) == normalized)
        self.assertTrue(is_normalized_name(normalized))
