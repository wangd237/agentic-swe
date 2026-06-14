import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from watchfiles.main import WatchfilesRustInternalError, dispatch_event_handler_error


class WatchfilesIgnorePermissionDeniedTests(unittest.TestCase):
    """覆盖 watchfiles#266 的最小稳定回归面。"""

    def test_current_bug_file_not_found_still_raises_wrapped_error(self) -> None:
        def error_handler(_error: Exception) -> None:
            raise FileNotFoundError("mounted path disappeared")

        with self.assertRaises(WatchfilesRustInternalError) as exc_info:
            dispatch_event_handler_error(
                RuntimeError("watcher error"),
                ignore_permission_denied=True,
                error_handler=error_handler,
            )

        self.assertIn("mounted path disappeared", str(exc_info.exception))

    def test_permission_error_is_ignored_when_flag_enabled(self) -> None:
        def error_handler(_error: Exception) -> None:
            raise PermissionError("permission denied")

        result = dispatch_event_handler_error(
            RuntimeError("watcher error"),
            ignore_permission_denied=True,
            error_handler=error_handler,
        )

        self.assertIsNone(result)

    def test_os_error_still_raises_when_flag_disabled(self) -> None:
        def error_handler(_error: Exception) -> None:
            raise FileNotFoundError("mounted path disappeared")

        with self.assertRaises(WatchfilesRustInternalError):
            dispatch_event_handler_error(
                RuntimeError("watcher error"),
                ignore_permission_denied=False,
                error_handler=error_handler,
            )
