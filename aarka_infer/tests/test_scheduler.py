"""
Test suite for AARKA Infer Async Request Scheduler.
"""
import asyncio
import pytest
from aarka_infer.runtime.sampler import SamplingParams
from aarka_infer.runtime.scheduler import AsyncRequestScheduler, RequestPriority


def test_scheduler_submission_and_priority():
    async def _run():
        scheduler = AsyncRequestScheduler(max_concurrent=2, queue_max_size=10)

        item_bg = await scheduler.submit_request(
            prompt="Background task",
            prompt_tokens=[1, 2, 3],
            params=SamplingParams(),
            priority=RequestPriority.BACKGROUND,
        )

        item_high = await scheduler.submit_request(
            prompt="High priority chat",
            prompt_tokens=[4, 5, 6],
            params=SamplingParams(),
            priority=RequestPriority.HIGH,
        )

        assert scheduler.queue_depth == 2

        # High priority item must dequeue first from priority queue
        first_out = await scheduler._priority_queue.get()
        assert first_out.request_id == item_high.request_id

        second_out = await scheduler._priority_queue.get()
        assert second_out.request_id == item_bg.request_id

    asyncio.run(_run())


def test_scheduler_cancellation():
    async def _run():
        scheduler = AsyncRequestScheduler(max_concurrent=2)
        cancel_evt = asyncio.Event()

        item = await scheduler.submit_request(
            prompt="Task to cancel",
            prompt_tokens=[1, 2],
            params=SamplingParams(),
            cancel_event=cancel_evt,
        )

        assert not cancel_evt.is_set()
        ok = scheduler.cancel_request(item.request_id)
        assert ok is True
        assert cancel_evt.is_set()

    asyncio.run(_run())
