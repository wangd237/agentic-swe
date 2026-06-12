"""packaging Requirement pickle 回归测试。"""

from __future__ import annotations

import pickle
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packaging_pickle_repo.requirements import Requirement


class RequirementPickleTests(unittest.TestCase):
    def test_pickle_preserves_prereleases_true(self) -> None:
        requirement = Requirement("foo>=1.0")
        requirement.specifier.prereleases = True

        loaded = pickle.loads(pickle.dumps(requirement))

        self.assertIs(loaded.specifier.prereleases, True)

    def test_pickle_preserves_prereleases_false(self) -> None:
        requirement = Requirement("foo>=1.0")
        requirement.specifier.prereleases = False

        loaded = pickle.loads(pickle.dumps(requirement))

        self.assertIs(loaded.specifier.prereleases, False)

    def test_pickle_keeps_default_none(self) -> None:
        requirement = Requirement("foo>=1.0")

        loaded = pickle.loads(pickle.dumps(requirement))

        self.assertIsNone(loaded.specifier.prereleases)
