"""Separate child cleanup outcomes from cancellation of the waiting caller."""

import asyncio

import pytest

from temporal_agent_harness.harness.agent_workflow import _cancel_and_settle


@pytest.mark.parametrize("behavior", ["cancel", "error", "return"])
async def test_child_cleanup_outcome_is_discarded(behavior):
    started = asyncio.Event()

    async def child():
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if behavior == "error":
                raise RuntimeError("cleanup error")
            if behavior == "return":
                return "irrelevant result"
            raise

    task = asyncio.create_task(child())
    await started.wait()
    await _cancel_and_settle(task)
    assert task.done()
    assert asyncio.current_task().cancelling() == 0


@pytest.mark.parametrize("second", ["raise", "return"])
async def test_caller_cancellation_is_distinct_from_child_cancellation(second):
    started = asyncio.Event()
    cleanup = asyncio.Event()

    async def child():
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cleanup.set()  # First request is the helper cancelling its child.
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                # The caller's request also reaches the child it is awaiting.
                if second == "return":
                    return "suppressed second cancellation"
                raise

    async def parent():
        task = asyncio.create_task(child())
        await started.wait()
        await _cancel_and_settle(task)
        return "continued"

    parent_task = asyncio.create_task(parent())
    await cleanup.wait()
    parent_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await parent_task
    assert parent_task.cancelled()


async def test_pending_caller_cancellation_before_helper_entry():
    started = asyncio.Event()

    async def child():
        started.set()
        await asyncio.Event().wait()

    async def parent():
        task = asyncio.create_task(child())
        await started.wait()
        asyncio.current_task().cancel()
        await _cancel_and_settle(task)
        return "continued"

    parent_task = asyncio.create_task(parent())
    with pytest.raises(asyncio.CancelledError):
        await parent_task


async def test_explicitly_cleared_caller_cancellation_allows_child_cleanup():
    async def parent():
        current = asyncio.current_task()
        current.cancel()
        try:
            await asyncio.sleep(0)
        except asyncio.CancelledError:
            current.uncancel()  # Explicit opt-in to consume this caller request.
        task = asyncio.create_task(asyncio.sleep(0))
        await _cancel_and_settle(task)
        return current.cancelling()

    assert await asyncio.create_task(parent()) == 0
