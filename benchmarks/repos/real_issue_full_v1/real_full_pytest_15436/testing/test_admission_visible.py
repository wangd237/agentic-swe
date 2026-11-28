import pytest

pytest_plugins = ["pytester"]


def test_widened_child_fixture_finishes_before_parent(pytester):
    pytester.makepyfile(
        """
        import pytest

        events = []

        @pytest.fixture(scope="module", params=["alpha", "beta"])
        def parent(request):
            resource = {"name": request.param, "live": True}
            yield resource
            resource["live"] = False

        @pytest.fixture
        def child(parent):
            yield parent
            assert parent["live"], "child finalized after its parent"

        @pytest.mark.parametrize("child", [None], indirect=True, scope="module")
        def test_uses_child(child, parent):
            assert child is parent
        """
    )
    result = pytester.runpytest("-q")
    result.assert_outcomes(passed=2)
