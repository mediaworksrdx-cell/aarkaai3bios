"""
AARKAAI Backend – Context Compilation

Builds the full context window for LLM inference by combining:
- Conversation history (recent turns)
- User profile and memory
- RAG-retrieved knowledge
- Agent-specific system prompts
- Tool definitions and results
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default context budget (characters)
DEFAULT_CONTEXT_BUDGET = 6000


def build_context(
    query: str,
    user_id: str,
    session_id: str = "default",
    max_history_turns: int = 10,
    context_budget: int = DEFAULT_CONTEXT_BUDGET,
    include_rag: bool = True,
    include_memory: bool = True,
    agent_type: Optional[str] = None,
) -> dict[str, Any]:
    """Build the full context dictionary for LLM inference.
    
    Returns a dict with keys:
        system_prompt: str
        history: list[dict]  
        rag_context: str
        user_profile: str
        tool_definitions: list[dict]
        budget_remaining: int
    """
    context: dict[str, Any] = {
        "system_prompt": "",
        "history": [],
        "rag_context": "",
        "user_profile": "",
        "tool_definitions": [],
        "budget_remaining": context_budget,
    }
    
    # 1. Load conversation history
    try:
        from database import SessionLocal, PersonalChat
        session = SessionLocal()
        try:
            recent = (
                session.query(PersonalChat)
                .filter(
                    PersonalChat.user_id == user_id,
                    PersonalChat.session_id == session_id,
                )
                .order_by(PersonalChat.timestamp.desc())
                .limit(max_history_turns)
                .all()
            )
            context["history"] = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(recent)
            ]
        finally:
            session.close()
    except Exception as e:
        logger.warning("Failed to load history: %s", e)
    
    # 2. Load user memory/profile
    if include_memory:
        try:
            from modules.memory import get_user_profile_text
            profile = get_user_profile_text(user_id)
            if profile:
                context["user_profile"] = profile
        except Exception as e:
            logger.warning("Failed to load user memory: %s", e)
    
    # 3. RAG retrieval
    if include_rag:
        try:
            from modules.rag import retrieve_context
            rag_text = retrieve_context(query, user_id=user_id)
            if rag_text:
                context["rag_context"] = rag_text
        except Exception as e:
            logger.warning("Failed RAG retrieval: %s", e)
    
    # 4. Calculate remaining budget
    used = sum(
        len(str(v))
        for v in [context["history"], context["rag_context"], context["user_profile"]]
    )
    context["budget_remaining"] = max(0, context_budget - used)
    
    return context
