"""
AARKA Infer API Schemas
OpenAI-compatible and native request/response schemas.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatCompletionRequest(BaseModel):
    model: str = "rthshr/aarkaa-3b-v1"
    messages: List[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=40)
    repetition_penalty: float = Field(default=1.15, ge=1.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32768)
    stream: bool = False
    stop: Optional[List[str]] = None
    seed: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatChoice]
    usage: UsageInfo


class ChoiceDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChunkChoice(BaseModel):
    index: int = 0
    delta: ChoiceDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChunkChoice]


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = 1718000000
    owned_by: str = "synthetix-analytics"


class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelCard]


class HealthResponse(BaseModel):
    status: str
    ready: bool
    environment: str
    model_id: str
    backend: str
    is_real_weights: bool
    active_requests: int
    queue_depth: int
    architecture_valid: bool
