pytest_plugins = ["pytester"]


def test_shared_mark_keeps_escaped_ids_stable(pytester):
    pytester.makepyfile(
        """
        import pytest

        @pytest.mark.parametrize("value", [1], ids=["left\tright"])
        class TestShared:
            def test_first(self, value):
                assert value == 1

            def test_second(self, value):
                assert value == 1
        """
    )
    result = pytester.runpytest("--collect-only", "-q")
    result.assert_outcomes()
    node_ids = [
        line for line in result.stdout.lines
        if line.startswith("test_shared_mark_keeps_escaped_ids_stable.py::TestShared::")
    ]
    assert len(node_ids) == 2
    assert node_ids[0].split("[", 1)[1] == node_ids[1].split("[", 1)[1]
