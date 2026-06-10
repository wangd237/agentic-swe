"""packaging Requirement extra 规范化回归测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_requirement_repo.requirements import Requirement


class RequirementStringTests(unittest.TestCase):
    def test_standalone_extra_is_normalized(self) -> None:
        requirement = Requirement('mariadb>=1.0.1; extra == "mariadb_connector"')

        self.assertEqual(
            str(requirement),
            'mariadb>=1.0.1; extra == "mariadb-connector"',
        )

    def test_extra_inside_compound_marker_is_also_normalized(self) -> None:
        requirement = Requirement(
            'mariadb>=1.0.1; python_version >= "3.12" and extra == "mariadb_connector"'
        )

        self.assertEqual(
            str(requirement),
            'mariadb>=1.0.1; python_version >= "3.12" and extra == "mariadb-connector"',
        )

    def test_already_normalized_extra_is_preserved(self) -> None:
        requirement = Requirement('mariadb>=1.0.1; extra == "mariadb-connector"')

        self.assertEqual(
            str(requirement),
            'mariadb>=1.0.1; extra == "mariadb-connector"',
        )
