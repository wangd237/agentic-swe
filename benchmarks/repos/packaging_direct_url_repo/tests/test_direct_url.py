"""packaging direct url 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_direct_url_repo.direct_url import DirectUrl


class DirectUrlTests(unittest.TestCase):
    def test_uppercase_file_scheme_is_accepted(self) -> None:
        direct_url = DirectUrl.from_dict({"url": "FILE:///tmp/demo", "info_type": "file"})

        self.assertEqual(direct_url.url, "FILE:///tmp/demo")

    def test_single_slash_file_scheme_is_accepted(self) -> None:
        direct_url = DirectUrl.from_dict({"url": "file:/tmp/demo", "info_type": "file"})

        self.assertEqual(direct_url.url, "file:/tmp/demo")

    def test_non_file_scheme_is_not_reclassified(self) -> None:
        direct_url = DirectUrl.from_dict({"url": "https://example.com/demo.whl", "info_type": "archive"})

        self.assertEqual(direct_url.url, "https://example.com/demo.whl")
