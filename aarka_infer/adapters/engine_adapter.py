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
        loop = self._get_or_create_loop()
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            stop=stop or ["<|im_end|>", "<|endoftext|>"],
        )

        async def _call():
            await self.engine.initialize()
            messages = [{"role": "user", "content": prompt}]
            resp = await self.engine.chat(messages, params=params)
            return resp["content"]

        return loop.run_until_complete(_call())

    def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
    ) -> Generator[str, None, None]:
        """Synchronous token generator compatibility wrapper."""
        loop = self._get_or_create_loop()
        params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or ["<|im_end|>", "<|endoftext|>"],
        )

        async def _init():
            await self.engine.initialize()

        loop.run_until_complete(_init())
        messages = [{"role": "user", "content": prompt}]

        # Run async stream via event loop
        async_gen = self.engine.chat_stream(messages, params=params)

        try:
            while True:
                token = loop.run_until_complete(async_gen.__anext__())
                yield token
        except StopAsyncIteration:
            pass

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
        messages = [{"role": "user", "content": prompt}]
        async for tok in self.engine.chat_stream(messages, params=params):
            yield tok

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """Retrieves or starts a compatible event loop for sync callers."""
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop
