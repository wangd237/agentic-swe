"""distlib wheel metadata 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from distlib_wheel_repo.wheel import build_wheel_metadata


class WheelMetadataTests(unittest.TestCase):
    def test_build_tag_is_written_to_metadata(self) -> None:
        metadata = build_wheel_metadata(buildver="1foo")

        self.assertIn("Build: 1foo\n", metadata)

    def test_build_line_is_omitted_when_not_provided(self) -> None:
        metadata = build_wheel_metadata(buildver=None)

        self.assertNotIn("Build:", metadata)

    def test_core_metadata_lines_remain_present(self) -> None:
        metadata = build_wheel_metadata(buildver="1foo")

        self.assertIn("Wheel-Version: 1.0\n", metadata)
        self.assertIn("Generator: distlib-test\n", metadata)
        self.assertIn("Tag: py3-none-any\n", metadata)
