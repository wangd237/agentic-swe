"""requests urllib3 兼容性回归测试。"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


def _load_setup_module():
    setup_path = Path(__file__).resolve().parent.parent / "setup.py"
    spec = importlib.util.spec_from_file_location("requests_compat_setup", setup_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DependencyConstraintTests(unittest.TestCase):
    def test_urllib3_v2_is_allowed_for_python37_plus(self) -> None:
        module = _load_setup_module()
        install_requires = module.get_install_requires()
        self.assertIn("urllib3>=1.21.1,<3", install_requires)

    def test_core_requirements_remain_present(self) -> None:
        module = _load_setup_module()
        install_requires = module.get_install_requires()
        self.assertIn("certifi>=2017.4.17", install_requires)
