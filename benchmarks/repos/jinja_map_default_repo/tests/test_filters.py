"""jinja map(attribute, default) 回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from jinja_map_default_repo.filters import map_attribute_with_default


class MapAttributeDefaultTests(unittest.TestCase):
    def test_default_none_is_used_for_missing_attribute(self) -> None:
        result = map_attribute_with_default([{}], "foo", default=None)

        self.assertEqual(result, [None])

    def test_falsey_non_none_default_is_still_used(self) -> None:
        result = map_attribute_with_default([{}], "foo", default=0)

        self.assertEqual(result, [0])

    def test_existing_attribute_is_not_overridden(self) -> None:
        result = map_attribute_with_default([{"foo": "bar"}], "foo", default=None)

        self.assertEqual(result, ["bar"])
