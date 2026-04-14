"""
AARKAAI Backend – Pydantic Request / Response Schemas

All user inputs are validated and sanitized.
"""
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Input Sanitization ──────────────────────────────────────────────────────

def _sanitize_text(text: str) -> str:
    """Strip control characters (except newlines/tabs) from user input."""
    # Remove NULL bytes and other dangerous control chars
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: str = Field(max_length=256)
    password: str = Field(min_length=6, max_length=128)
    name: Optional[str] = Field(default=None, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email format")
        return v.strip().lower()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: Optional[str] = None


# ─── Request ──────────────────────────────────────────────────────────────────


class PromptRequest(BaseModel):
    """Incoming user prompt (user_id is now extracted from JWT token in production)."""

    query: str = Field(
        default="",
        min_length=1,
        max_length=2000,
        description="The user's question or command (max 2000 chars)",
    )
    # user_id is removed from here because we extract it from the bearer token.
    session_id: str = Field(default="1", max_length=64, description="Session identifier")
    context: Optional[dict] = Field(default=None, description="Extra context payload")

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        return _sanitize_text(v.strip())

    @model_validator(mode="before")
    @classmethod
    def accept_prompt_or_query(cls, data):
        """Accept either 'prompt' or 'query' as the input field."""
        if isinstance(data, dict):
            if "prompt" in data and "query" not in data:
                data["query"] = data.pop("prompt")
        return data


# ─── Response ─────────────────────────────────────────────────────────────────


class PromptResponse(BaseModel):
    """Response returned to the client."""

    response: str
    intent: str
    confidence: float
    sources: list[str] = Field(default_factory=list)
    detected_language: str = Field(default="en", description="ISO 639-1 language code detected from user query")
    processing_time: float = Field(description="Seconds taken to process")


class HealthResponse(BaseModel):
    """System health check."""

    status: str
    version: str = "2.0.0"
    modules: dict = Field(default_factory=dict)


# ─── Internal DTOs ────────────────────────────────────────────────────────────


class FilterResult(BaseModel):
    """Output of the Semantic Filter."""

    domain: str
    confidence: float
    intent: str
    scores: dict = Field(default_factory=dict)


class FinanceResult(BaseModel):
    """Output of the Finance module."""

    tickers: list[str] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)
    summary: str = ""


class SearchResult(BaseModel):
    """Single web search result."""

    title: str
    url: str
    snippet: str


# ─── Admin ────────────────────────────────────────────────────────────────────


class AdminKnowledgeRequest(BaseModel):
    """Request payload for adding knowledge manually."""

    title: str = Field(max_length=256)
    category: str = Field(default="general", max_length=64)
    content: str = Field(max_length=5000)
    source: str = Field(default="system", max_length=64)

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return _sanitize_text(v)


class AdminUserMemoryRequest(BaseModel):
    """Request payload for adding user memory or system prompts."""

    user_id: str = Field(max_length=128)
    session_id: str = Field(max_length=64)
    prompt: str = Field(max_length=2000)


class RLHFRequest(BaseModel):
    """Request payload for submitting RLHF feedback."""

    conversation_id: Optional[int] = None
    user_id: str = Field(max_length=128)
    rating: int = Field(ge=-1, le=1, description="1 for positive, -1 for negative")
    correction: Optional[str] = Field(default=None, max_length=2000, description="Optional text correction to learn from")
