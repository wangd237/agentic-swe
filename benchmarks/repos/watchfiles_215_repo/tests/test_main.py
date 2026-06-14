import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from watchfiles.main import FileEvent, evaluate_single_file_watch


class WatchfilesVimSaveRegressionTests(unittest.TestCase):
    """覆盖 watchfiles#215 的最小稳定回归面。"""

    def test_vim_style_save_should_still_reload_and_keep_watching_target(self) -> None:
        decision = evaluate_single_file_watch(
            [
                FileEvent(kind="modify-name-from", path="config.yaml"),
                FileEvent(kind="metadata", path="config.yaml"),
                FileEvent(kind="remove", path="config.yaml"),
            ],
            target_path="config.yaml",
        )

        self.assertTrue(decision.should_reload)
        self.assertTrue(decision.continue_watching)

    def test_directory_style_replace_sequence_should_continue_watching(self) -> None:
        decision = evaluate_single_file_watch(
            [
                FileEvent(kind="modify-name-from", path="config.yaml"),
                FileEvent(kind="metadata", path="config.yaml"),
            ],
            target_path="config.yaml",
        )

        self.assertTrue(decision.should_reload)
        self.assertTrue(decision.continue_watching)

    def test_unrelated_path_should_not_reload_target(self) -> None:
        decision = evaluate_single_file_watch(
            [
                FileEvent(kind="modified", path="other.yaml"),
            ],
            target_path="config.yaml",
        )

        self.assertFalse(decision.should_reload)
        self.assertTrue(decision.continue_watching)
