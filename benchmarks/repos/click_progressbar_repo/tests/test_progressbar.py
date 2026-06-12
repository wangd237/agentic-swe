"""click progressbar 完成态回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from click_progressbar_repo.progressbar import render_progress_output


class ProgressbarTests(unittest.TestCase):
    def test_show_pos_uses_final_length_at_completion(self) -> None:
        rendered = render_progress_output(length=20, show_pos=True, update_min_steps=7)

        self.assertEqual(rendered, "20/20")

    def test_percentage_mode_still_reports_full_completion(self) -> None:
        rendered = render_progress_output(length=20, show_pos=False, update_min_steps=7)

        self.assertEqual(rendered, "100%")

    def test_divisible_update_min_steps_keeps_position_output(self) -> None:
        rendered = render_progress_output(length=20, show_pos=True, update_min_steps=5)

        self.assertEqual(rendered, "20/20")
