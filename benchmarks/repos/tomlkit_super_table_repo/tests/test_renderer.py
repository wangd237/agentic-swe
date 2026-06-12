"""tomlkit super table dotted key 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_super_table_repo.renderer import render_document_with_dotted_key


class SuperTableRendererTests(unittest.TestCase):
    def test_dotted_key_keeps_super_table_prefix(self) -> None:
        result = render_document_with_dotted_key(
            parent_table="output",
            child_table="netcdf_scalar",
            value=5,
            dotted_key="csv.path",
            dotted_value="output.csv",
        )

        self.assertIn('output.csv.path = "output.csv"', result)
        self.assertNotIn('\ncsv.path = "output.csv"\n', result)

    def test_existing_child_table_is_preserved(self) -> None:
        result = render_document_with_dotted_key(
            parent_table="output",
            child_table="netcdf_scalar",
            value=5,
            dotted_key="csv.path",
            dotted_value="output.csv",
        )

        self.assertIn("[output.netcdf_scalar]", result)
        self.assertIn("value = 5", result)
