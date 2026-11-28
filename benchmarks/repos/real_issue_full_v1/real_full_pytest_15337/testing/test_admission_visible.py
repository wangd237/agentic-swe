import unittest

from _pytest.nodeid import NodeId


class TestNewNodeId(unittest.TestCase):
    def test_new_identifier_formats_twice(self):
        node = NodeId(path="tests/test_case.py", names=("TestCase", "test_value"))
        expected = "tests/test_case.py::TestCase::test_value"
        self.assertEqual(str(node), expected)
        self.assertEqual(str(node), expected)
