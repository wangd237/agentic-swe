"""jinja async loop repr 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jinja_async_repr_repo.runtime import AsyncLoopContext


class AsyncLoopContextTests(unittest.TestCase):
    def test_repr_does_not_expose_coroutine_object(self) -> None:
        context = AsyncLoopContext(index=1, length=3)

        rendered = repr(context)

        self.assertNotIn("coroutine object", rendered)
        self.assertEqual(rendered, "<AsyncLoopContext 1/3>")

    def test_repr_keeps_index_prefix(self) -> None:
        context = AsyncLoopContext(index=2, length=4)

        rendered = repr(context)

        self.assertTrue(rendered.startswith("<AsyncLoopContext 2/"))
