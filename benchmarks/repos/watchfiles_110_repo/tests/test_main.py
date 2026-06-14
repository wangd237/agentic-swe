import asyncio
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from watchfiles.main import FakeRustNotify, FakeStopEvent, run_awatch_loop


class WatchfilesCtrlCRegressionTests(unittest.TestCase):
    """覆盖 watchfiles#110 的最小稳定回归面。"""

    def test_stop_requested_during_watch_should_exit_without_waiting_for_event(self) -> None:
        async def scenario() -> str:
            watcher = FakeRustNotify(sleep_steps=6)
            stop_event = FakeStopEvent()

            async def on_iteration(_iteration: int) -> None:
                # 模拟进入 watch 之后很快收到 Ctrl+C。
                await asyncio.sleep(0)
                stop_event.set()

            return await run_awatch_loop(
                watcher,
                stop_event=stop_event,
                on_iteration=on_iteration,
            )

        result = asyncio.run(scenario())
        self.assertEqual(result, "stopped")

    def test_stop_before_entering_watch_exits_immediately(self) -> None:
        async def scenario() -> tuple[str, int]:
            watcher = FakeRustNotify(sleep_steps=6)
            stop_event = FakeStopEvent()
            stop_event.set()
            result = await run_awatch_loop(watcher, stop_event=stop_event)
            return result, watcher.watch_call_count

        result, watch_call_count = asyncio.run(scenario())
        self.assertEqual(result, "stopped")
        self.assertEqual(watch_call_count, 0)

    def test_without_stop_request_event_path_still_works(self) -> None:
        async def scenario() -> tuple[str, int]:
            watcher = FakeRustNotify(sleep_steps=3)
            stop_event = FakeStopEvent()
            result = await run_awatch_loop(watcher, stop_event=stop_event)
            return result, watcher.watch_call_count

        result, watch_call_count = asyncio.run(scenario())
        self.assertEqual(result, "filesystem-event")
        self.assertEqual(watch_call_count, 1)
