"""
AARKAAI Pipeline package.

Public API:
    process_query(query, user_id, session_id, mode) -> PromptResponse
    stream_query(query, user_id, session_id, mode, model_override) -> AsyncGenerator

The pipeline was refactored from a single 3,200-line module into this package.
Backward compatibility: `from pipeline import process_query` works unchanged.
"""
from pipeline.circuit_breaker import (  # noqa: F401
    _CircuitBreaker,
    _web_breaker,
    _finance_breaker,
    _SCREENER_AVAILABLE,
    _screener_agent,
)
from pipeline.helpers import *  # noqa: F401,F403
from pipeline.context import ContextResult  # noqa: F401
from pipeline.post_process import _post_process  # noqa: F401
from pipeline.core import process_query, stream_query  # noqa: F401

__all__ = ["process_query", "stream_query"]
