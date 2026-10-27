"""
AARKA Infer Asynchronous Request Scheduler
Provides concurrent request pooling, priority queues, cancellation tokens,
and continuous batching dispatch instead of global model lock serialization.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from aarka_infer.config import settings
from aarka_infer.runtime.sampler import SamplingParams

logger = logging.getLogger("aarka_infer.scheduler")


class RequestPriority(IntEnum):
    HIGH = 1        # Interactive chat, real-time user query
    NORMAL = 2      # Standard agentic reasoning
    BACKGROUND = 3  # Batch processing, embeddings, summarization


@dataclass(order=True)
class QueuedItem:
    priority: int
    timestamp: float
    request_id: str = field(compare=False)
    prompt: str = field(compare=False)
    prompt_tokens: List[int] = field(compare=False)
    params: SamplingParams = field(compare=False)
    future: asyncio.Future = field(compare=False)
    cancel_event: asyncio.Event = field(compare=False)


class AsyncRequestScheduler:
    """
    Manages non-blocking asynchronous request queueing and concurrent generation.
    Eliminates global threading lock serialization.
    """

    def __init__(
        self,
        max_concurrent: int = settings.max_concurrent_requests,
        queue_max_size: int = settings.queue_max_size,
        queue_timeout: float = settings.queue_timeout_seconds,
    ):
        self.max_concurrent = max_concurrent
        self.queue_max_size = queue_max_size
        self.queue_timeout = queue_timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._priority_queue: asyncio.PriorityQueue[QueuedItem] = asyncio.PriorityQueue(maxsize=queue_max_size)
        self._active_requests: Dict[str, QueuedItem] = {}
        self._is_running = True

    async def submit_request(
        self,
        prompt: str,
        prompt_tokens: List[int],
        params: SamplingParams,
        priority: RequestPriority = RequestPriority.HIGH,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> QueuedItem:
        """Enqueues an incoming inference request with SLA-aware timeout checking."""
        req_id = f"req_{uuid.uuid4().hex[:12]}"
        now = time.time()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        c_event = cancel_event or asyncio.Event()

        item = QueuedItem(
            priority=priority.value if hasattr(priority, "value") else int(priority),
            timestamp=now,
            request_id=req_id,
            prompt=prompt,
            prompt_tokens=prompt_tokens,
            params=params,
            future=future,
            cancel_event=c_event,
        )

        try:
            # Non-blocking queue check with timeout
            await asyncio.wait_for(
                self._priority_queue.put(item),
                timeout=2.0
            )
            self._active_requests[req_id] = item
            logger.debug("Request %s queued (priority=%s, depth=%d)", req_id, priority.name, self._priority_queue.qsize())
            return item
        except asyncio.TimeoutError:
            logger.warning("Request queue full! Rejected %s", req_id)
            raise asyncio.QueueFull("AARKA Infer queue capacity exceeded. Please retry shortly.")

    async def acquire_slot(self, item: QueuedItem) -> None:
        """Waits for concurrency slot or checks for timeout/cancellation."""
        wait_start = time.time()
        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.queue_timeout
            )
        except asyncio.TimeoutError:
            self.cancel_request(item.request_id)
            raise TimeoutError(f"Request {item.request_id} timed out waiting in queue for {self.queue_timeout}s")

    def release_slot(self, item: QueuedItem) -> None:
        """Releases concurrency slot upon request completion."""
        self._semaphore.release()
        self._active_requests.pop(item.request_id, None)

    def cancel_request(self, request_id: str) -> bool:
        """Triggers cancellation event on an active request."""
        item = self._active_requests.get(request_id)
        if item is not None:
            item.cancel_event.set()
            if not item.future.done():
                item.future.cancel()
            self._active_requests.pop(request_id, None)
            logger.info("Request %s cancelled by client", request_id)
            return True
        return False

    @property
    def queue_depth(self) -> int:
        return self._priority_queue.qsize()

    @property
    def in_flight_count(self) -> int:
        return self.max_concurrent - self._semaphore._value
