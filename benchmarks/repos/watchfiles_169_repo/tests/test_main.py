import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from watchfiles.main import FileEvent, should_emit_reload


class WatchfilesEnvironmentReloadRegressionTests(unittest.TestCase):
    """覆盖 watchfiles#169 的最小稳定回归面。"""

    def test_metadata_write_on_linux_like_environment_should_still_reload_target(self) -> None:
        event = FileEvent(kind="metadata-write", path="foobar.py")

        result = should_emit_reload(
            event,
            target_path="foobar.py",
            source_environment="wsl",
        )

        self.assertTrue(result)

    def test_unrelated_path_should_not_reload(self) -> None:
        event = FileEvent(kind="modified", path="other.py")

        result = should_emit_reload(
            event,
            target_path="foobar.py",
            source_environment="windows",
        )

        self.assertFalse(result)

    def test_normal_modified_event_still_reloads(self) -> None:
        event = FileEvent(kind="modified", path="foobar.py")

        result = should_emit_reload(
            event,
            target_path="foobar.py",
            source_environment="windows",
        )

        self.assertTrue(result)
