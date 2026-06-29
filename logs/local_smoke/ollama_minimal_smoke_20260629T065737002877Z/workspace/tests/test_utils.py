"""requests quoted charset 回归测试。"""

from __future__ import annotations

import unittest

from requests_encoding_repo.utils import get_encoding_from_headers


class HeaderEncodingTests(unittest.TestCase):
    def test_unquoted_charset_is_detected(self) -> None:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        self.assertEqual(get_encoding_from_headers(headers), "utf-8")

    def test_double_quoted_charset_is_detected(self) -> None:
        headers = {"Content-Type": 'text/html; charset="utf-8"'}
        self.assertEqual(get_encoding_from_headers(headers), "utf-8")

    def test_single_quoted_charset_is_detected(self) -> None:
        headers = {"Content-Type": "text/html; charset='utf-8'"}
        self.assertEqual(get_encoding_from_headers(headers), "utf-8")
