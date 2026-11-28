import pytest

from anyio import ClosedResourceError, create_memory_object_stream, create_task_group, fail_after, wait_all_tasks_blocked


async def test_closing_receive_stream_wakes_its_blocked_reader():
    send, receive = create_memory_object_stream[int](0)
    with send, receive, fail_after(1):
        async with create_task_group() as group:
            async def reader():
                with pytest.raises(ClosedResourceError):
                    await receive.receive()

            group.start_soon(reader)
            await wait_all_tasks_blocked()
            await receive.aclose()
