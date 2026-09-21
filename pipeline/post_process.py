"""
AARKAAI Pipeline – Post-Processing

Extracted from pipeline.py lines 3186-3217.
Handles conversation storage, user fact extraction, and auto-learn triggers.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _post_process(
    user_id: str,
    session_id: str,
    query: str,
    response: str,
    intent: str,
    confidence: float,
    source: str,
    memory_mod,
    auto_learn_mod,
) -> None:
    """Store conversation, extract user facts, and trigger auto-learn if needed."""
    try:
        memory_mod.store_conversation(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=response,
            intent=intent,
            confidence=confidence,
            source=source,
        )
        memory_mod.update_user_profile(user_id=user_id, increment_count=True)
        memory_mod.extract_user_facts(user_id=user_id, query=query)
    except Exception as exc:
        logger.error("Post-process store/fact extraction failed: %s", exc)

    try:
        auto_learn_mod.check_and_learn(user_id)
    except Exception as exc:
        logger.error("Auto-learn check failed: %s", exc)
