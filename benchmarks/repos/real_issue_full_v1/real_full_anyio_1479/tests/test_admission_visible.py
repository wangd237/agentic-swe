from _pytest.pytester import Pytester

pytest_plugins = ["pytester"]


def test_async_callback_failure_retains_callback_description(testdir: Pytester):
    testdir.makepyfile(
        """
        import asyncio
        import pytest

        @pytest.fixture
        def anyio_backend():
            return "asyncio"

        @pytest.mark.anyio
        async def test_bad_callback():
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            future.set_result(1)
            loop.call_soon(future.set_exception, RuntimeError("late"))
            await asyncio.sleep(0)
        """
    )
    result = testdir.runpytest("-v", "-p", "anyio", "-p", "no:asyncio", "-p", "no:trio")
    result.assert_outcomes(failed=1)
    assert "Exception in callback Future.set_exception" in result.stdout.str()
