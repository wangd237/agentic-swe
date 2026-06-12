"""pytest caplog filtering 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pytest_caplog_filter_repo.logging_utils import CapturingHandler, filtering


class CaplogFilteringTests(unittest.TestCase):
    def test_nested_same_filter_keeps_outer_filter_active(self) -> None:
        handler = CapturingHandler()

        def suppress_all(_: str) -> bool:
            return False

        with filtering(handler, suppress_all):
            handler.emit("outer-before-inner")
            with filtering(handler, suppress_all):
                handler.emit("inner")
            handler.emit("outer-after-inner")

        self.assertEqual(handler.records, [])

    def test_preexisting_filter_is_not_removed_by_context_exit(self) -> None:
        handler = CapturingHandler()

        def suppress_all(_: str) -> bool:
            return False

        handler.add_filter(suppress_all)
        with filtering(handler, suppress_all):
            handler.emit("inside")
        handler.emit("after")

        self.assertEqual(handler.records, [])

    def test_context_restores_unfiltered_emission_after_outer_exit(self) -> None:
        handler = CapturingHandler()

        def suppress_all(_: str) -> bool:
            return False

        with filtering(handler, suppress_all):
            handler.emit("blocked")
        handler.emit("visible")

        self.assertEqual(handler.records, ["visible"])
