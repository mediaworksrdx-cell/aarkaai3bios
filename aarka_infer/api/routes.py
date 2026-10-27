"""
AARKA Infer FastAPI Routes
Handles /v1/chat/completions, /v1/models, /health, /health/ready, and /metrics.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse

from aarka_infer.api.schemas import (
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    HealthResponse,
    ModelCard,
    ModelListResponse,
    UsageInfo,
)
from aarka_infer.api.streaming import format_sse_stream
from aarka_infer.config import settings
from aarka_infer.runtime.engine import AarkaInferEngine
from aarka_infer.runtime.sampler import SamplingParams

logger = logging.getLogger("aarka_infer.api.routes")
router = APIRouter()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(req: ChatCompletionRequest, request: Request):
    """OpenAI-compatible Chat Completion endpoint supporting streaming & batching."""
    engine = AarkaInferEngine.get_instance()

    # Reconcile requested model against 3B defaults
    model_name = req.model
    if model_name in settings.model_aliases or not model_name:
        model_name = settings.model_id

    sampling_params = SamplingParams(
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        top_p=req.top_p,
        top_k=req.top_k,
        repetition_penalty=req.repetition_penalty,
        seed=req.seed,
        stop=req.stop or ["<|im_end|>", "<|endoftext|>"],
        stream=req.stream,
    )

    msg_dicts = [m.model_dump() for m in req.messages]

    # Handle Streaming Mode
    if req.stream:
        token_gen = engine.chat_stream(
            messages=msg_dicts,
            tools=req.tools,
            params=sampling_params,
        )
        return StreamingResponse(
            format_sse_stream(token_gen, model_name),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Handle Non-Streaming Mode
    try:
        result = await engine.chat(
            messages=msg_dicts,
            tools=req.tools,
            params=sampling_params,
        )
        content = result["content"]
        prompt_tokens = engine.tokenizer.count_tokens(msg_dicts)
        completion_tokens = len(engine.tokenizer.encode(content))

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
            model=model_name,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
    except Exception as e:
        logger.error("Chat completion error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference generation failure: {str(e)}",
        )


@router.get("/v1/models", response_model=ModelListResponse)
async def list_models():
    """Lists supported model identifiers."""
    cards = [
        ModelCard(id=settings.model_id),
        ModelCard(id="aarkaa-3b"),
        ModelCard(id="aarkaa-ai/aarkaa-3b"),
    ]
    return ModelListResponse(data=cards)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe returning engine diagnostic state."""
    engine = AarkaInferEngine.get_instance()
    info = engine.get_health()
    return HealthResponse(**info)


@router.get("/health/ready")
async def readiness_check():
    """
    Strict production readiness probe.
    Returns HTTP 200 only if the model is ready.
    In production mode, returns HTTP 503 if running on a mock/stub.
    """
    engine = AarkaInferEngine.get_instance()
    info = engine.get_health()

    if not info["ready"]:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "reason": "Model weights unmounted or backend not ready for production traffic",
                "details": info,
            },
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content={"ready": True, "details": info})


@router.get("/metrics")
async def get_metrics():
    """Exposes real performance telemetry: TTFT, ITL, TPS, KV Cache, RAM/VRAM."""
    engine = AarkaInferEngine.get_instance()
    return engine.get_metrics()
