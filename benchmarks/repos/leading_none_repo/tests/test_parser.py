"""leading_none_repo 的回归测试。"""

import unittest

from leading_none_repo.parser import parse_items


class ParseItemsTests(unittest.TestCase):
    def test_empty_input_returns_empty_list(self) -> None:
        self.assertEqual(parse_items([]), [])

    def test_leading_none_items_are_ignored(self) -> None:
        self.assertEqual(parse_items([None, " A ", "B "]), ["a", "b"])

    def test_middle_none_items_are_ignored(self) -> None:
        self.assertEqual(parse_items([" A ", None, "B "]), ["a", "b"])
