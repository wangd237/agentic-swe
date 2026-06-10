"""jsonschema 单标签 hostname 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jsonschema_single_label_hostname_repo.hostname import is_valid_hostname


class HostnameFormatTests(unittest.TestCase):
    def test_single_label_hostname_is_allowed(self) -> None:
        self.assertTrue(is_valid_hostname("localhost"))

    def test_multi_label_hostname_still_passes(self) -> None:
        self.assertTrue(is_valid_hostname("example.com"))

    def test_invalid_hostname_still_returns_false(self) -> None:
        self.assertFalse(is_valid_hostname("bad host"))
