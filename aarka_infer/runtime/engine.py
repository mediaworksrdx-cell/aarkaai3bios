"""
AARKA Infer Core Engine Orchestrator
Coordinates model loading, tokenization, KV cache prefix management,
asynchronous scheduling, metrics collection, and inference dispatch.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from aarka_infer.backends.base import BaseBackend
from aarka_infer.backends.llama_cpp_backend import LlamaCppBackend
from aarka_infer.backends.mock_backend import MockBackend
from aarka_infer.backends.vllm_backend import VLLMBackend
from aarka_infer.config import settings
from aarka_infer.runtime.kv_cache import KVCacheManager
from aarka_infer.runtime.metrics import InferenceMetricsTracker
from aarka_infer.runtime.model_loader import AarkaModelLoader, VerificationReport
from aarka_infer.runtime.sampler import SamplingParams
from aarka_infer.runtime.scheduler import AsyncRequestScheduler, RequestPriority
from aarka_infer.runtime.tokenizer import AarkaTokenizer

logger = logging.getLogger("aarka_infer.engine")


class AarkaInferEngine:
    """The central inference-serving orchestrator for AARKAA-3B."""

    _instance: Optional[AarkaInferEngine] = None

    def __init__(self):
        self.model_loader = AarkaModelLoader()
        self.tokenizer = AarkaTokenizer()
        self.kv_cache = KVCacheManager()
        self.scheduler = AsyncRequestScheduler()
        self.metrics = InferenceMetricsTracker()
        self.backend: Optional[BaseBackend] = None
        self.verification_report: Optional[VerificationReport] = None
        self._initialized = False
        self._init_lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> AarkaInferEngine:
        """Singleton accessor for in-process engine reuse."""
        if cls._instance is None:
            cls._instance = AarkaInferEngine()
        return cls._instance

    async def initialize(self, force_backend: Optional[str] = None) -> bool:
        """Initializes model verifier, backend hardware, and tokenizer."""
        async with self._init_lock:
            if self._initialized and self.backend and self.backend.is_healthy():
                return True

            logger.info("Initializing AARKA Infer Engine...")
            self.verification_report = self.model_loader.resolve_model(force_backend=force_backend)
            backend_type = self.verification_report.backend_type

            if backend_type == "llama_cpp" and self.verification_report.model_path:
                self.backend = LlamaCppBackend(self.verification_report.model_path)
            elif backend_type == "vllm":
                self.backend = VLLMBackend(settings.vllm_api_url)
            else:
                self.backend = MockBackend()

            ok = await self.backend.initialize()
            if not ok and backend_type != "mock":
                logger.warning("Selected backend '%s' failed initialization, falling back to verified mock", backend_type)
                self.backend = MockBackend()
                await self.backend.initialize()

            self._initialized = True
            logger.info("AARKA Infer initialized successfully with backend '%s'", self.backend.name)
            return True

    async def generate_stream(
        self,
        prompt: str,
        params: Optional[SamplingParams] = None,
        priority: RequestPriority = RequestPriority.HIGH,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[str, None]:
        """Streams tokens directly from a raw text prompt with active Radix KV caching."""
        if not self._initialized:
            await self.initialize()

        sampling = params or SamplingParams()
        # If prompt is not already formatted as ChatML, wrap it with standard user template
        if "<|im_start|>" not in prompt:
            formatted_prompt = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}],
                add_generation_prompt=True,
            )
        else:
            formatted_prompt = prompt

        prompt_tokens = self.tokenizer.encode(formatted_prompt)

        # Active KV Prefix Cache lookup
        matched_prefix, _ = self.kv_cache.match_prefix(prompt_tokens)

        # Enqueue via AsyncScheduler
        c_event = cancel_event or asyncio.Event()
        queued = await self.scheduler.submit_request(
            prompt=formatted_prompt,
            prompt_tokens=prompt_tokens,
            params=sampling,
            priority=priority,
            cancel_event=c_event,
        )

        trace = self.metrics.start_request(queued.request_id, len(prompt_tokens))

        try:
            # Wait for execution slot without blocking event loop
            await self.scheduler.acquire_slot(queued)
            self.metrics.mark_execution_start(trace)

            first_token_seen = False
            token_count = 0

            async for token_text in self.backend.generate_stream(
                prompt=formatted_prompt,
                prompt_tokens=prompt_tokens,
                params=sampling,
                cancel_event=c_event,
            ):
                if not first_token_seen:
                    self.metrics.mark_first_token(trace)
                    first_token_seen = True
                else:
                    self.metrics.mark_token(trace)

                token_count += 1
                yield token_text

            self.metrics.complete_request(trace, token_count)

            # Insert evaluated prompt into Radix Prefix Tree for subsequent reuse
            self.kv_cache.insert_prefix(prompt_tokens)

        except Exception as e:
            self.metrics.fail_request(trace)
            logger.error("Inference generation failed for request %s: %s", queued.request_id, e)
            raise
        finally:
            self.scheduler.release_slot(queued)

    async def generate(
        self,
        prompt: str,
        params: Optional[SamplingParams] = None,
        priority: RequestPriority = RequestPriority.HIGH,
    ) -> str:
        """Non-streaming complete generation for raw prompts."""
        collected: List[str] = []
        async for chunk in self.generate_stream(prompt, params=params, priority=priority):
            collected.append(chunk)
        return "".join(collected)

    async def chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        params: Optional[SamplingParams] = None,
        priority: RequestPriority = RequestPriority.HIGH,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[str, None]:
        """Formats conversational messages and streams tokens asynchronously."""
        if not self._initialized:
            await self.initialize()

        prompt = self.tokenizer.apply_chat_template(messages, tools=tools, add_generation_prompt=True)
        async for tok in self.generate_stream(
            prompt=prompt,
            params=params,
            priority=priority,
            cancel_event=cancel_event,
        ):
            yield tok

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        params: Optional[SamplingParams] = None,
        priority: RequestPriority = RequestPriority.HIGH,
    ) -> Dict[str, Any]:
        """Non-streaming complete conversational generation."""
        collected: List[str] = []
        async for chunk in self.chat_stream(messages, tools=tools, params=params, priority=priority):
            collected.append(chunk)

        content = "".join(collected)
        return {
            "content": content,
            "finish_reason": "stop",
            "model": settings.model_id,
        }

    def get_health(self) -> Dict[str, Any]:
        """Evaluates tiered system health and readiness."""
        backend_ok = self.backend.is_healthy() if self.backend else False
        is_real_weights = (
            self.backend is not None and self.backend.name in ("llama_cpp", "vllm")
        )

        # In production mode, readiness strictly requires real model weights
        ready = backend_ok
        if settings.strict_production_health and settings.environment == "production":
            ready = backend_ok and is_real_weights

        return {
            "status": "ok" if backend_ok else "unavailable",
            "ready": ready,
            "environment": settings.environment,
            "model_id": settings.model_id,
            "backend": self.backend.name if self.backend else "none",
            "is_real_weights": is_real_weights,
            "active_requests": self.scheduler.in_flight_count,
            "queue_depth": self.scheduler.queue_depth,
            "architecture_valid": (
                self.verification_report.architecture_matched
                if self.verification_report else False
            ),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Returns consolidated metrics across execution tracker and KV cache."""
        metrics_summary = self.metrics.get_summary()
        metrics_summary["kv_cache"] = self.kv_cache.get_stats()
        metrics_summary["scheduler"] = {
            "max_concurrent": self.scheduler.max_concurrent,
            "in_flight": self.scheduler.in_flight_count,
            "queue_depth": self.scheduler.queue_depth,
        }
        return metrics_summary
