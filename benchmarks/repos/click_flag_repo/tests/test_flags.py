"""Click negative flag 回归测试。"""

from __future__ import annotations

import unittest

from click_flag_repo.core import resolve_negative_flag


class NegativeFlagTests(unittest.TestCase):
    def test_default_true_does_not_force_flag_value(self) -> None:
        self.assertTrue(resolve_negative_flag(default=True, flag_value=False, provided=False))

    def test_provided_flag_value_is_used(self) -> None:
        self.assertFalse(resolve_negative_flag(default=True, flag_value=False, provided=True))
