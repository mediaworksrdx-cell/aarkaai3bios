"""
AARKA Infer Application Engine Adapter
Seamlessly connects the existing AARKAAI application (modules/aarkaa_engine.py)
to the high-performance AARKA Infer runtime without breaking existing callers.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional

from aarka_infer.config import settings
from aarka_infer.runtime.engine import AarkaInferEngine
from aarka_infer.runtime.sampler import SamplingParams

logger = logging.getLogger("aarka_infer.adapter.engine")


class AarkaaLegacyAdapter:
    """Provides backward-compatible interface for modules/aarkaa_engine.py callers."""

    def __init__(self):
        self.engine = AarkaInferEngine.get_instance()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        seed: Optional[int] = None,
        stop: Optional[List[str]] = None,
    ) -> str:
        """Synchronous generation compatibility wrapper."""
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            stop=stop or ["<|im_end|>", "<|endoftext|>"],
        )

        async def _call():
            await self.engine.initialize()
            return await self.engine.generate(prompt, params=params)

        return self._run_coroutine_sync(_call())

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> Generator[str, None, None]:
        """Synchronous token generator compatibility wrapper."""
        import queue
        import threading

        token_queue: queue.Queue[Optional[str]] = queue.Queue()
        stop_event = threading.Event()

        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or ["<|im_end|>", "<|endoftext|>"],
        )

        def _producer_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)

            async def _run():
                await self.engine.initialize()
                async for tok in self.engine.generate_stream(prompt, params=params):
                    if stop_event.is_set():
                        break
                    token_queue.put(tok)

            try:
                new_loop.run_until_complete(_run())
            except Exception as e:
                logger.error("Error in AarkaaLegacyAdapter sync stream: %s", e)
            finally:
                token_queue.put(None)
                new_loop.close()

        thread = threading.Thread(target=_producer_thread, daemon=True)
        thread.start()

        try:
            while True:
                tok = token_queue.get()
                if tok is None:
                    break
                yield tok
        finally:
            stop_event.set()

    async def generate_stream_async(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        """Native async token generator for FastAPI endpoints."""
        await self.engine.initialize()
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or ["<|im_end|>", "<|endoftext|>"],
        )
        async for tok in self.engine.generate_stream(prompt, params=params):
            yield tok

    def _run_coroutine_sync(self, coro):
        """Safely executes an async coroutine synchronously, even if an event loop is already running in the current thread."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                def _in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                return pool.submit(_in_thread).result()
        else:
            local_loop = self._get_or_create_loop()
            return local_loop.run_until_complete(coro)

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """Retrieves or starts a compatible event loop for sync callers."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
