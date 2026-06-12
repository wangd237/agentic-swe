"""tomlkit 代理删除回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_proxy_repo.proxy import OutOfOrderTableProxy, render_table


class OutOfOrderTableProxyTests(unittest.TestCase):
    def test_pop_removes_key_from_underlying_table(self) -> None:
        data = {"name": '"dummy"', "version": '"0.0.0"', "url": '""'}
        proxy = OutOfOrderTableProxy(data)

        removed = proxy.pop("url")

        self.assertEqual(removed, '""')
        self.assertNotIn("url", data)
        self.assertEqual(render_table(data), 'name = "dummy"\nversion = "0.0.0"')

    def test_pop_keeps_other_keys_intact(self) -> None:
        data = {"name": '"dummy"', "version": '"0.0.0"'}
        proxy = OutOfOrderTableProxy(data)

        proxy.pop("name")

        self.assertEqual(data["version"], '"0.0.0"')
