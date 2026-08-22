"""
AARKAAI Backend – Pydantic Request / Response Schemas

All user inputs are validated and sanitized.
"""
import re
from typing import Optional, Union

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
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[str] = None
    name: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="The refresh token issued at login")


class LogoutRequest(BaseModel):
    access_token: Optional[str] = Field(default=None, description="Access token JTI to revoke")
    refresh_token: Optional[str] = Field(default=None, description="Refresh token to revoke")


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = Field(default=None, description="Google ID Token from client SDK")
    access_token: Optional[str] = Field(default=None, description="Google OAuth access token from client SDK")


# ─── Request ──────────────────────────────────────────────────────────────────


class PromptRequest(BaseModel):
    """Incoming user prompt (user_id is now extracted from JWT token in production)."""

    query: str = Field(
        default="",
        min_length=1,
        max_length=32000,
        description="The user's question or command (max 32000 chars)",
    )
    # user_id is removed from here because we extract it from the bearer token.
    session_id: str = Field(default="1", max_length=128, description="Session identifier")
    context: Optional[dict] = Field(default=None, description="Extra context payload")
    mode: Optional[str] = Field(default="production", description="Execution mode: 'production' or 'benchmark'")
    model_override: Optional[str] = Field(default=None, description="Optional model provider override: 'gemini', 'claude', 'aarkaa-7b'")

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

    conversation_id: Optional[Union[int, str]] = None
    user_id: Optional[str] = Field(default=None, max_length=128)
    rating: int = Field(ge=-1, le=1, description="1 for positive, -1 for negative")
    correction: Optional[str] = Field(default=None, max_length=2000, description="Optional text correction to learn from")


# ─── Strategy ─────────────────────────────────────────────────────────────────


class StrategyRequest(BaseModel):
    """Request payload for the /strategy endpoint."""
    symbol: str = Field(description="Ticker symbol, e.g. 'SBIN.NS' or 'RELIANCE.NS'")
    risk_reward: float = Field(default=5.0, ge=1.0, le=20.0, description="Target risk-to-reward ratio (e.g., 5.0 = 1:5)")
    period: str = Field(default="6mo", description="Historical data period for analysis")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()


class StrategyResponse(BaseModel):
    """Response from the /strategy endpoint."""
    symbol: str
    signal: str
    indicators: dict = Field(default_factory=dict)
    strategy: dict = Field(default_factory=dict)
    technical_summary: str = ""
    strategy_summary: str = ""
    subscription: dict = Field(default_factory=dict, description="Subscription access info")
    processing_time: float = 0.0



# ─── Settings ─────────────────────────────────────────────────────────────────


class UserSettingsUpdate(BaseModel):
    """Request payload for updating user settings (all fields optional)."""
    default_model: Optional[str] = Field(default=None, description="Default AI model")
    response_style: Optional[str] = Field(default=None, description="concise | balanced | detailed | professional")
    theme: Optional[str] = Field(default=None, description="dark | light | auto")
    language: Optional[str] = Field(default=None, description="ISO 639-1 language code")
    streaming_enabled: Optional[bool] = Field(default=None, description="Enable token streaming")
    reasoning_depth: Optional[str] = Field(default=None, description="fast | balanced | deep | low | medium | high")
    about_you: Optional[str] = Field(default=None, description="User role / industry profile")
    system_directives: Optional[str] = Field(default=None, description="Account-wide system prompt instructions")
    extended_thinking: Optional[bool] = Field(default=None, description="Enable extended DAG thinking")
    thinking_budget: Optional[int] = Field(default=None, description="Maximum thinking budget tokens")
    web_search_enabled: Optional[bool] = Field(default=None, description="Enable live web search")
    deep_research_enabled: Optional[bool] = Field(default=None, description="Enable deep research mode")
    market_data_enabled: Optional[bool] = Field(default=None, description="Enable live market data")


class UserSettingsResponse(BaseModel):
    """Response containing user settings."""
    user_id: str
    default_model: str = "aarka-2.0"
    response_style: str = "balanced"
    theme: str = "dark"
    language: str = "en"
    streaming_enabled: bool = True
    reasoning_depth: str = "balanced"
    about_you: Optional[str] = None
    system_directives: Optional[str] = None
    extended_thinking: bool = True
    thinking_budget: int = 4096
    web_search_enabled: bool = True
    deep_research_enabled: bool = True
    market_data_enabled: bool = True
    updated_at: Optional[str] = None


# ─── Skills ───────────────────────────────────────────────────────────────────


class SkillModel(BaseModel):
    """Request payload for creating or updating a skill."""
    name: str = Field(max_length=128)
    content: str = Field(max_length=51200, description="Skill SKILL.md content (max 50KB)")


class TestRequestModel(BaseModel):
    """Request payload for testing a skill with a prompt."""
    prompt: str = Field(max_length=2000)
