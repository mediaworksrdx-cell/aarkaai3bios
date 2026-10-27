"""
AARKA Infer vLLM GPU Backend
Connects to vLLM OpenAI-compatible server for continuous batching and multi-GPU serving.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from aarka_infer.backends.base import BaseBackend
from aarka_infer.config import settings
from aarka_infer.runtime.sampler import SamplingParams

logger = logging.getLogger("aarka_infer.backend.vllm")


class VLLMBackend(BaseBackend):
    """High-throughput vLLM backend client supporting continuous batching."""

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = (api_url or settings.vllm_api_url or "http://localhost:8000/v1").rstrip("/")
        self._is_ready = False
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        return "vllm"

    async def initialize(self) -> bool:
        """Pings the vLLM server to verify model availability."""
        self._client = httpx.AsyncClient(timeout=60.0)
        try:
            resp = await self._client.get(f"{self.api_url}/models", timeout=5.0)
            if resp.status_code == 200:
                self._is_ready = True
                logger.info("Successfully connected to vLLM endpoint at %s", self.api_url)
                return True
        except Exception as e:
            logger.warning("vLLM endpoint at %s unreachable: %s", self.api_url, e)

        self._is_ready = False
        return False

    async def generate_stream(
        self,
        prompt: str,
        prompt_tokens: List[int],
        params: SamplingParams,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        """Streams tokens from vLLM /v1/completions endpoint."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)

        payload = {
            "model": settings.model_id,
            "prompt": prompt,
            "max_tokens": params.max_tokens,
            "temperature": params.temperature,
            "top_p": params.top_p,
            "stop": params.stop,
            "stream": True,
        }

        try:
            async with self._client.stream(
                "POST",
                f"{self.api_url}/completions",
                json=payload,
                timeout=60.0,
            ) as response:
                async for line in response.aiter_lines():
                    if cancel_event.is_set():
                        break
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if choices:
                            text = choices[0].get("text", "")
                            if text:
                                yield text
                    except Exception:
                        pass
        except Exception as e:
            logger.error("Error communicating with vLLM backend: %s", e)
            raise

    def is_healthy(self) -> bool:
        return self._is_ready

    def get_memory_usage(self) -> Dict[str, Any]:
        return {
            "api_url": self.api_url,
            "connected": self._is_ready,
        }
