"""
AARKA Infer Base Backend Protocol
Abstract interface for pluggable inference backends.
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from aarka_infer.runtime.sampler import SamplingParams


class BaseBackend(ABC):
    """Abstract interface implemented by all AARKA Infer backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the backend implementation."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initializes hardware connections and loads model weights."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        prompt_tokens: List[int],
        params: SamplingParams,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        """Streams generated text tokens incrementally."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Returns True if the backend is ready to accept requests."""
        pass

    @abstractmethod
    def get_memory_usage(self) -> Dict[str, Any]:
        """Reports active memory usage for telemetry."""
        pass
