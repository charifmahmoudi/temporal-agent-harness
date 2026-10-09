"""Deterministic asyncio controls for the actual cleanup helper, not a Temporal emulator."""
import asyncio
import os

import pytest
from temporal_agent_harness.harness.agent_workflow import _cancel_and_settle

CORRECTED = os.environ.get('CANCELLATION_VARIANT') == 'corrected'


@pytest.mark.parametrize('behavior',['cancel','error','return'])
async def test_child_cleanup_outcome_is_discarded(behavior):
    started=asyncio.Event()
    async def child():
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            if behavior=='error':
                raise RuntimeError('cleanup error')
            if behavior=='return':
                return 'irrelevant result'
            raise
    task=asyncio.create_task(child())
    await started.wait()
    await _cancel_and_settle(task)
    assert task.done()
    assert asyncio.current_task().cancelling()==0


@pytest.mark.parametrize('second',['raise','return'])
async def test_caller_cancellation_is_distinct_from_child_cancellation(second):
    started=asyncio.Event()
    cleanup=asyncio.Event()
    async def child():
        started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cleanup.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                if second=='return':
                    return 'suppressed second cancellation'
                raise
    async def parent():
        task=asyncio.create_task(child())
        await started.wait()
        await _cancel_and_settle(task)
        return 'continued'
    parent_task=asyncio.create_task(parent())
    await cleanup.wait()
    parent_task.cancel()
    if CORRECTED:
        with pytest.raises(asyncio.CancelledError):
            await parent_task
        assert parent_task.cancelled()
    else:
        assert await parent_task=='continued'
        assert not parent_task.cancelled()
        assert parent_task.cancelling()==1
