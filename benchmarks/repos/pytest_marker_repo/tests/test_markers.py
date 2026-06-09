"""pytest closest marker 回归测试。"""

from __future__ import annotations

import unittest

from pytest_marker_repo.markers import Marker, get_closest_marker


class ClosestMarkerTests(unittest.TestCase):
    def test_child_marker_overrides_parent_marker(self) -> None:
        markers = [
            Marker("some_mark", data=0),
            Marker("some_mark", data=1),
        ]

        marker = get_closest_marker(markers, "some_mark")

        self.assertIsNotNone(marker)
        self.assertEqual(marker.kwargs["data"], 1)

    def test_parent_marker_is_used_when_child_missing(self) -> None:
        markers = [Marker("some_mark", data=0)]

        marker = get_closest_marker(markers, "some_mark")

        self.assertIsNotNone(marker)
        self.assertEqual(marker.kwargs["data"], 0)
