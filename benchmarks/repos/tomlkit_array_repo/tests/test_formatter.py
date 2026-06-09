"""tomlkit 数组格式化回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_array_repo.formatter import append_value_to_array


class ArrayFormatterTests(unittest.TestCase):
    def test_append_preserves_single_comma_for_next_line_style(self) -> None:
        source = "\n".join(
            [
                " a = [",
                "       1 # comma is on the next line",
                "      ,2",
                "     ]",
                "",
            ]
        )

        result = append_value_to_array(source, 99)

        self.assertEqual(
            result,
            "\n".join(
                [
                    " a = [",
                    "       1 # comma is on the next line",
                    "      ,2",
                    "      ,99",
                    "     ]",
                    "",
                ]
            ),
        )

    def test_append_to_regular_style_keeps_regular_comma(self) -> None:
        source = "\n".join(
            [
                " a = [",
                "       1,",
                "       2",
                "     ]",
                "",
            ]
        )

        result = append_value_to_array(source, 3)

        self.assertEqual(
            result,
            "\n".join(
                [
                    " a = [",
                    "       1,",
                    "       2",
                    "       ,3",
                    "     ]",
                    "",
                ]
            ),
        )
