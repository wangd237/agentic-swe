import pytest
import trio


async def test_start_error_retains_explicit_cause():
    cause = LookupError("root cause")

    async def child(*, task_status=trio.TASK_STATUS_IGNORED):
        raise RuntimeError("startup failed") from cause

    with pytest.raises(BaseExceptionGroup) as caught:
        async with trio.open_nursery() as nursery:
            await nursery.start(child)

    assert len(caught.value.exceptions) == 1
    assert caught.value.exceptions[0].__cause__ is cause
