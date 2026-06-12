"""tomlkit 注释锚点回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tomlkit_comment_anchor_repo.renderer import render_routes_with_inserted_subtables


class CommentAnchorRendererTests(unittest.TestCase):
    def test_comment_stays_with_second_route_after_appending_subtables(self) -> None:
        rendered = render_routes_with_inserted_subtables()

        expected = "\n".join(
            [
                "## My POST route comment",
                "[[routes]]",
                "method = 'POST'",
                "path = '/my/post/path'",
                "topic = 'my-topic.0'",
                "",
                "[routes.rate_limit]",
                "enabled = true",
                "",
                "[routes.rate_limit.requests]",
                "per_second = 25",
                "",
                "## My GET route comment",
                "[[routes]]",
                "method = 'GET'",
                "path = '/my/get/path/{key}'",
                "topic = 'my-topic.1'",
                "",
            ]
        )

        self.assertEqual(rendered, expected)

    def test_inserted_subtables_stay_after_first_route(self) -> None:
        rendered = render_routes_with_inserted_subtables()

        self.assertIn("[routes.rate_limit]\nenabled = true", rendered)
        self.assertLess(rendered.index("[routes.rate_limit]"), rendered.index("## My GET route comment"))

    def test_original_second_route_content_is_preserved(self) -> None:
        rendered = render_routes_with_inserted_subtables()

        self.assertIn("path = '/my/get/path/{key}'", rendered)
        self.assertIn("topic = 'my-topic.1'", rendered)
