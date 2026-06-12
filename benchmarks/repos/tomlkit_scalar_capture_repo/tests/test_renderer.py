"""tomlkit table replaced by scalar 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_scalar_capture_repo.renderer import render_document_with_scalar_replacement


class ScalarReplacementRendererTests(unittest.TestCase):
    def test_scalar_replacement_stays_at_top_level(self) -> None:
        result = render_document_with_scalar_replacement()

        self.assertIn("\nb = 2\n[c]\n", result)
        self.assertNotIn("[a]\naa = 1\nb = 2\n", result)

    def test_neighbor_table_is_preserved(self) -> None:
        result = render_document_with_scalar_replacement()

        self.assertIn("[c]\ncc = 3\n", result)

    def test_original_parent_table_is_preserved(self) -> None:
        result = render_document_with_scalar_replacement()

        self.assertIn("[a]\naa = 1\n", result)
