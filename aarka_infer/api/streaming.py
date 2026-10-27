"""
AARKA Infer Streaming SSE Formatter
Formats streaming tokens into OpenAI-compatible Server-Sent Events (SSE).
"""
from __future__ import annotations

import json
import time
import uuid
from typing import AsyncGenerator

from aarka_infer.api.schemas import ChatCompletionChunk, ChoiceDelta, ChunkChoice


async def format_sse_stream(
    token_generator: AsyncGenerator[str, None],
    model_id: str,
) -> AsyncGenerator[str, None]:
    """Wraps an async token generator into Server-Sent Event chunks."""
    req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())

    # Initial chunk with role
    first_chunk = ChatCompletionChunk(
        id=req_id,
        created=created_ts,
        model=model_id,
        choices=[ChunkChoice(index=0, delta=ChoiceDelta(role="assistant"))],
    )
    yield f"data: {first_chunk.model_dump_json()}\n\n"

    # Subsequent content delta chunks
    async for token in token_generator:
        chunk = ChatCompletionChunk(
            id=req_id,
            created=created_ts,
            model=model_id,
            choices=[ChunkChoice(index=0, delta=ChoiceDelta(content=token))],
        )
        yield f"data: {chunk.model_dump_json()}\n\n"

    # Final termination chunk with finish_reason
    final_chunk = ChatCompletionChunk(
        id=req_id,
        created=created_ts,
        model=model_id,
        choices=[ChunkChoice(index=0, delta=ChoiceDelta(), finish_reason="stop")],
    )
    yield f"data: {final_chunk.model_dump_json()}\n\n"
    yield "data: [DONE]\n\n"
