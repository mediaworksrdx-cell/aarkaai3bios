"""
AARKA Infer Router Dispatcher Adapter
Integrates with modules/ai_router.py to route general 3B inference queries
directly to the unified AARKA Infer serving runtime.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from aarka_infer.runtime.engine import AarkaInferEngine
from aarka_infer.runtime.sampler import SamplingParams
from aarka_infer.runtime.scheduler import RequestPriority

logger = logging.getLogger("aarka_infer.adapter.router")


class InferRouterDispatcher:
    """Dispatches routed prompts from AI Router to AARKA Infer."""

    def __init__(self):
        self.engine = AarkaInferEngine.get_instance()

    async def dispatch(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Any:
        """Processes request through AARKA Infer with high priority."""
        params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        if stream:
            return self.engine.chat_stream(
                messages=messages,
                params=params,
                priority=RequestPriority.HIGH,
            )

        resp = await self.engine.chat(
            messages=messages,
            params=params,
            priority=RequestPriority.HIGH,
        )
        content_text = resp.get("content", "")
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "model": resp.get("model", "aarkaa-3b"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content_text,
                    },
                    "finish_reason": resp.get("finish_reason", "stop"),
                }
            ],
            "content": content_text,
        }
