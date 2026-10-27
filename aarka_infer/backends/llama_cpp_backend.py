"""
AARKA Infer llama.cpp / GGUF Backend
Executes optimized local CPU/GPU inference for GGUF model files.
"""
from __future__ import annotations

import asyncio
import logging
import queue
import threading
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from aarka_infer.backends.base import BaseBackend
from aarka_infer.config import settings
from aarka_infer.runtime.sampler import SamplingParams

logger = logging.getLogger("aarka_infer.backend.llama_cpp")


class LlamaCppBackend(BaseBackend):
    """High-performance GGUF backend powered by llama-cpp-python."""

    def __init__(self, model_path: Path):
        self.model_path = model_path
        self._llm = None
        self._is_ready = False

    @property
    def name(self) -> str:
        return "llama_cpp"

    async def initialize(self) -> bool:
        """Loads the GGUF model into memory in a background thread."""
        logger.info("Initializing llama.cpp with model: %s", self.model_path)
        loop = asyncio.get_running_loop()

        def _load():
            try:
                from llama_cpp import Llama
                llm = Llama(
                    model_path=str(self.model_path),
                    n_ctx=settings.context_window,
                    n_threads=settings.n_threads,
                    n_gpu_layers=settings.n_gpu_layers,
                    verbose=False,
                )
                return llm
            except Exception as e:
                logger.error("Failed to load Llama GGUF model: %s", e)
                return None

        self._llm = await loop.run_in_executor(None, _load)
        self._is_ready = self._llm is not None
        return self._is_ready

    async def generate_stream(
        self,
        prompt: str,
        prompt_tokens: List[int],
        params: SamplingParams,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        """Streams generated tokens using background worker thread and async queue."""
        if self._llm is None:
            raise RuntimeError("llama.cpp backend is not initialized")

        token_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def _worker():
            try:
                generator = self._llm(
                    prompt=prompt,
                    max_tokens=params.max_tokens,
                    temperature=params.temperature,
                    top_p=params.top_p,
                    top_k=params.top_k,
                    repeat_penalty=params.repetition_penalty,
                    stop=params.stop,
                    stream=True,
                )

                for chunk in generator:
                    if cancel_event.is_set():
                        break
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("text", "")
                        if delta:
                            loop.call_soon_threadsafe(token_queue.put_nowait, delta)

                loop.call_soon_threadsafe(token_queue.put_nowait, None)
            except Exception as e:
                logger.error("Exception inside llama.cpp worker: %s", e)
                loop.call_soon_threadsafe(token_queue.put_nowait, None)

        # Run worker thread so main asyncio event loop remains non-blocking
        threading.Thread(target=_worker, daemon=True).start()

        while True:
            if cancel_event.is_set():
                break
            tok = await token_queue.get()
            if tok is None:
                break
            yield tok

    def is_healthy(self) -> bool:
        return self._is_ready and self._llm is not None

    def get_memory_usage(self) -> Dict[str, Any]:
        return {
            "model_path": str(self.model_path),
            "loaded": self._llm is not None,
            "threads": settings.n_threads,
            "gpu_layers": settings.n_gpu_layers,
        }
