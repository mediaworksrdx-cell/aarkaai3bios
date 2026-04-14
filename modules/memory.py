"""
AARKAAI – Memory System

CRUD operations across conversation_history, personal_chats,
user_memory, and user_knowledge_profiles tables.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database import (
    ConversationHistory,
    PersonalChat,
    SessionLocal,
    UserKnowledgeProfile,
    UserMemory,
    RLHFFeedback,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Conversation History ────────────────────────────────────────────────────


def store_conversation(
    user_id: str,
    query: str,
    response: str,
    intent: str = "general",
    confidence: float = 0.0,
    source: str = "aarkaa-3b",
) -> None:
    """Store a conversation turn."""
    session: Session = SessionLocal()
    try:
        entry = ConversationHistory(
            user_id=user_id,
            query=query,
            response=response,
            intent=intent,
            confidence=confidence,
            source=source,
        )
        session.add(entry)

        # Also save to personal_chats for context window
        session.add(PersonalChat(user_id=user_id, message=query, role="user"))
        session.add(PersonalChat(user_id=user_id, message=response, role="assistant"))

        session.commit()
        logger.debug("Stored conversation for user %s", user_id)
    except Exception as exc:
        session.rollback()
        logger.error("store_conversation failed: %s", exc)
    finally:
        session.close()


def get_recent_conversations(user_id: str, limit: int = 15) -> list[dict]:
    """Fetch the most recent conversations for a user."""
    session: Session = SessionLocal()
    try:
        rows = (
            session.query(ConversationHistory)
            .filter(ConversationHistory.user_id == user_id)
            .order_by(ConversationHistory.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "query": r.query,
                "response": r.response,
                "intent": r.intent,
                "confidence": r.confidence,
                "source": r.source,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in reversed(rows)  # chronological order
        ]
    finally:
        session.close()


def get_conversation_count(user_id: str) -> int:
    """Total conversations for a user."""
    session: Session = SessionLocal()
    try:
        return (
            session.query(ConversationHistory)
            .filter(ConversationHistory.user_id == user_id)
            .count()
        )
    finally:
        session.close()


# ─── Personal Chats (Context Window) ─────────────────────────────────────────


def get_chat_context(user_id: str, limit: int = 10) -> list[dict]:
    """Get recent chat messages for context window."""
    session: Session = SessionLocal()
    try:
        rows = (
            session.query(PersonalChat)
            .filter(PersonalChat.user_id == user_id)
            .order_by(PersonalChat.timestamp.desc())
            .limit(limit * 2)  # user + assistant pairs
            .all()
        )
        return [
            {"role": r.role, "message": r.message}
            for r in reversed(rows)
        ]
    finally:
        session.close()


# ─── User Memory (Key-Value) ─────────────────────────────────────────────────


def update_user_memory(
    user_id: str, key: str, value: str, category: str = "general"
) -> None:
    """Upsert a key-value memory entry for a user."""
    session: Session = SessionLocal()
    try:
        existing = (
            session.query(UserMemory)
            .filter(UserMemory.user_id == user_id, UserMemory.key == key)
            .first()
        )
        if existing:
            existing.value = value
            existing.category = category
            existing.timestamp = _utcnow()
        else:
            session.add(
                UserMemory(user_id=user_id, key=key, value=value, category=category)
            )
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error("update_user_memory failed: %s", exc)
    finally:
        session.close()


def get_user_memories(user_id: str, category: Optional[str] = None) -> list[dict]:
    """Fetch all memory entries for a user, optionally filtered by category."""
    session: Session = SessionLocal()
    try:
        q = session.query(UserMemory).filter(UserMemory.user_id == user_id)
        if category:
            q = q.filter(UserMemory.category == category)
        rows = q.order_by(UserMemory.timestamp.desc()).all()
        return [
            {"key": r.key, "value": r.value, "category": r.category}
            for r in rows
        ]
    finally:
        session.close()


# ─── User Knowledge Profiles ─────────────────────────────────────────────────


def get_user_profile(user_id: str) -> dict:
    """Get or create a user profile."""
    session: Session = SessionLocal()
    try:
        profile = (
            session.query(UserKnowledgeProfile)
            .filter(UserKnowledgeProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            profile = UserKnowledgeProfile(
                user_id=user_id,
                interests="[]",
                expertise_areas="[]",
                interaction_count=0,
            )
            session.add(profile)
            session.commit()

        return {
            "user_id": profile.user_id,
            "interests": json.loads(profile.interests or "[]"),
            "expertise_areas": json.loads(profile.expertise_areas or "[]"),
            "interaction_count": profile.interaction_count,
            "last_updated": (
                profile.last_updated.isoformat() if profile.last_updated else None
            ),
        }
    finally:
        session.close()


def update_user_profile(
    user_id: str,
    interests: Optional[list[str]] = None,
    expertise_areas: Optional[list[str]] = None,
    increment_count: bool = True,
) -> None:
    """Update a user's knowledge profile."""
    session: Session = SessionLocal()
    try:
        profile = (
            session.query(UserKnowledgeProfile)
            .filter(UserKnowledgeProfile.user_id == user_id)
            .first()
        )
        if profile is None:
            profile = UserKnowledgeProfile(user_id=user_id)
            session.add(profile)

        if interests is not None:
            existing = json.loads(profile.interests or "[]")
            merged = list(dict.fromkeys(existing + interests))  # deduplicate
            profile.interests = json.dumps(merged)

        if expertise_areas is not None:
            existing = json.loads(profile.expertise_areas or "[]")
            merged = list(dict.fromkeys(existing + expertise_areas))
            profile.expertise_areas = json.dumps(merged)

        if increment_count:
            profile.interaction_count = (profile.interaction_count or 0) + 1

        profile.last_updated = _utcnow()
        session.commit()
        logger.debug("Updated profile for user %s", user_id)
    except Exception as exc:
        session.rollback()
        logger.error("update_user_profile failed: %s", exc)
    finally:
        session.close()


# ─── RLHF ────────────────────────────────────────────────────────────────────


def store_rlhf_feedback(
    user_id: str,
    rating: int,
    conversation_id: Optional[int] = None,
    correction: Optional[str] = None,
) -> None:
    """Store RLHF feedback and optionally auto-learn from explicit text corrections."""
    session: Session = SessionLocal()
    try:
        feedback = RLHFFeedback(
            user_id=user_id,
            conversation_id=conversation_id,
            rating=rating,
            correction=correction,
        )
        session.add(feedback)
        session.commit()
        logger.info("Stored RLHF feedback for user %s (rating=%d)", user_id, rating)

        # Auto-learn from explicit negative corrections
        if rating < 0 and correction:
            from modules import rag
            topic = f"RLHF Correction for User {user_id}"
            if conversation_id:
                topic += f" (Conv {conversation_id})"
            rag.store_knowledge(
                topic=topic,
                content=correction,
                source="rlhf",
            )
            logger.info("Auto-learned RLHF correction: %s", topic)

    except Exception as exc:
        session.rollback()
        logger.error("store_rlhf_feedback failed: %s", exc)
    finally:
        session.close()
