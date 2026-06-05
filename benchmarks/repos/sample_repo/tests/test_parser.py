"""sample_repo 的最小回归测试。"""

import unittest

from sample_repo.parser import parse_items


class ParseItemsTests(unittest.TestCase):
    # 这个用例当前会失败，后续将作为 Agent 修复目标。
    def test_empty_input_returns_empty_list(self) -> None:
        self.assertEqual(parse_items([]), [])

    def test_non_empty_items_are_normalized(self) -> None:
        self.assertEqual(parse_items([" A ", "B "]), ["a", "b"])
