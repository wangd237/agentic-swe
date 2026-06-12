"""click usage 换行回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from click_usage_repo.formatting import wrap_usage


class UsageFormattingTests(unittest.TestCase):
    def test_hyphenated_option_is_not_split_across_lines(self) -> None:
        rendered = wrap_usage(
            program_name="program",
            options=[
                "--enable-verbose-logging",
                "--output-file-path",
                "--max-retry-count",
                "--disable-cache-mode",
                "--config-file-location",
                "--user-auth-token",
                "--auto-update-interval",
                "--force-overwrite-existing",
                "--network-timeout-seconds",
                "--debug-trace-enabled",
            ],
            width=65,
        )

        self.assertNotIn("--max-\n", rendered)
        self.assertNotIn("--config-file-\n", rendered)
        self.assertNotIn("--network-timeout-\n", rendered)
        self.assertIn("--max-retry-count", rendered)
        self.assertIn("--config-file-location", rendered)
        self.assertIn("--network-timeout-seconds", rendered)

    def test_space_based_wrapping_still_occurs(self) -> None:
        rendered = wrap_usage(
            program_name="program",
            options=[
                "--enable-verbose-logging",
                "--output-file-path",
                "--max-retry-count",
            ],
            width=50,
        )

        self.assertGreaterEqual(len(rendered.splitlines()), 2)
        self.assertNotIn("retry-count --output", rendered)

    def test_short_usage_stays_on_single_line(self) -> None:
        rendered = wrap_usage(
            program_name="program",
            options=["--verbose"],
            width=65,
        )

        self.assertEqual(rendered, "Usage: program --verbose")
