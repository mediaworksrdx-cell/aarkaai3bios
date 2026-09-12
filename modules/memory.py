"""
AARKAAI – Memory System

CRUD operations across conversation_history, personal_chats,
user_memory, and user_knowledge_profiles tables.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Union

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
    session_id: str,
    query: str,
    response: str,
    intent: str = "general",
    confidence: float = 0.0,
    source: str = "aarkaa-3b",
) -> None:
    """Store a conversation turn."""
    import config
    if config.MONGODB_URI:
        from modules.mongo_repository import ConversationRepo, PersonalChatRepo
        ConversationRepo.add_entry(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=response,
            intent=intent,
            confidence=confidence,
            source=source,
        )
        PersonalChatRepo.add_message(user_id=user_id, session_id=session_id, message=query, role="user")
        PersonalChatRepo.add_message(user_id=user_id, session_id=session_id, message=response, role="assistant")
        logger.debug("Stored conversation in MongoDB for user %s", user_id)
        return

    session: Session = SessionLocal()
    try:
        entry = ConversationHistory(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=response,
            intent=intent,
            confidence=confidence,
            source=source,
        )
        session.add(entry)

        # Also save to personal_chats for context window
        session.add(PersonalChat(user_id=user_id, session_id=session_id, message=query, role="user"))
        session.add(PersonalChat(user_id=user_id, session_id=session_id, message=response, role="assistant"))

        session.commit()
        logger.debug("Stored conversation for user %s", user_id)
    except Exception as exc:
        session.rollback()
        logger.error("store_conversation failed: %s", exc)
    finally:
        session.close()


def get_recent_conversations(user_id: str, limit: int = 15) -> list[dict]:
    """Fetch the most recent conversations for a user."""
    import config
    if config.MONGODB_URI:
        from modules.mongo_repository import ConversationRepo
        docs = ConversationRepo.get_history(user_id=user_id, limit=limit)
        return [
            {
                "id": str(r.get("_id", r.get("id"))),
                "query": r.get("query", ""),
                "response": r.get("response", ""),
                "intent": r.get("intent", "general"),
                "confidence": r.get("confidence", 0.0),
                "source": r.get("source", "aarkaa-3b"),
                "timestamp": r["timestamp"].isoformat() if isinstance(r.get("timestamp"), datetime) else r.get("timestamp"),
            }
            for r in reversed(docs)
        ]

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
    import config
    if config.MONGODB_URI:
        from modules.mongo_repository import ConversationRepo
        coll = ConversationRepo.get_collection()
        return coll.count_documents({"user_id": user_id}) if coll is not None else 0

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


def get_chat_context(user_id: str, session_id: str, limit: int = 10) -> list[dict]:
    """Get recent chat messages for context window, filtering out any poisoned refusal loops."""
    import config
    refusal_markers = [
        "attempt to override my instructions",
        "bypass my guidelines",
        "bypass my actual system instructions",
        "won't follow embedded",
        "operating under my actual system instructions",
        "operating under my original instructions",
        "designed to keep your data private and compliant",
        "attempt to manipulate my instructions",
        "normal, legitimate request with no attempt",
        "data governance & provenance contract",
        "data lineage & provenance",
        "authoritative data lineage",
    ]
    if config.MONGODB_URI:
        from modules.mongo_repository import PersonalChatRepo
        docs = PersonalChatRepo.get_messages(user_id=user_id, session_id=session_id, limit=limit * 2)
        return [
            {"role": r.get("role"), "message": r.get("message")}
            for r in docs
            if not any(k in (r.get("message") or "").lower() for k in refusal_markers)
        ]

    session: Session = SessionLocal()
    try:
        rows = (
            session.query(PersonalChat)
            .filter(PersonalChat.user_id == user_id, PersonalChat.session_id == session_id)
            .order_by(PersonalChat.timestamp.desc())
            .limit(limit * 2)  # user + assistant pairs
            .all()
        )
        return [
            {"role": r.role, "message": r.message}
            for r in reversed(rows)
            if not any(k in (r.message or "").lower() for k in refusal_markers)
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

from pydantic import BaseModel, Field, field_validator

class RLHFCorrectionSchema(BaseModel):
    correction: str = Field(..., min_length=5, max_length=1000)

    @field_validator("correction")
    @classmethod
    def check_safety(cls, v: str) -> str:
        forbidden = ["/run", "sudo ", "rm -rf", "exec ", "mkfs", "dd if="]
        v_low = v.lower()
        if any(cmd in v_low for cmd in forbidden):
            raise ValueError("Safety violation: Input contains prohibited system commands.")
        return v


def store_rlhf_feedback(
    user_id: str,
    rating: int,
    conversation_id: Optional[Union[int, str]] = None,
    correction: Optional[str] = None,
    session_id: Optional[str] = None,
) -> None:
    """Store RLHF feedback and optionally auto-learn from explicit text corrections."""
    clean_correction = correction.strip() if (correction and correction.strip()) else None
    if clean_correction:
        # Validate correction via Pydantic schema
        RLHFCorrectionSchema(correction=clean_correction)

    import config
    # 1. Store in MongoDB if enabled
    if config.MONGODB_URI:
        try:
            from modules.mongo_repository import RLHFRepo
            RLHFRepo.add_entry(
                user_id=user_id,
                rating=rating,
                conversation_id=str(conversation_id) if conversation_id is not None else None,
                session_id=session_id or (str(conversation_id) if conversation_id is not None else None),
                correction=clean_correction,
            )
            logger.info("Stored RLHF feedback in MongoDB for user %s (rating=%d)", user_id, rating)
        except Exception as mongo_exc:
            logger.error("MongoDB store_rlhf_feedback failed: %s", mongo_exc)

    # 2. Store in SQLite for local persistence or dual-mode
    int_conv_id = None
    if conversation_id is not None:
        try:
            int_conv_id = int(conversation_id)
        except (ValueError, TypeError):
            int_conv_id = None

    session: Session = SessionLocal()
    try:
        feedback = RLHFFeedback(
            user_id=user_id,
            conversation_id=int_conv_id,
            rating=rating,
            correction=clean_correction,
        )
        session.add(feedback)
        session.commit()
        logger.info("Stored RLHF feedback in SQLite for user %s (rating=%d)", user_id, rating)
    except Exception as exc:
        session.rollback()
        logger.error("store_rlhf_feedback failed: %s", exc)
        if not config.MONGODB_URI:
            raise exc
    finally:
        session.close()

    # 3. Auto-learn from explicit negative corrections
    if rating < 0 and clean_correction:
        from modules import rag
        topic = "Global System Correction (RLHF)"
        if conversation_id:
            topic += f" (Conv {conversation_id})"
        elif session_id:
            topic += f" (Session {session_id})"
        try:
            rag.store_knowledge(
                topic=topic,
                content=clean_correction,
                source="rlhf",
                user_id=user_id,
            )
            logger.info("Auto-learned RLHF correction: %s", topic)
        except Exception as rag_exc:
            logger.warning("Failed to auto-store RLHF correction in RAG: %s", rag_exc)



# ─── User Fact Extraction ────────────────────────────────────────────────────

def extract_user_facts(user_id: str, query: str) -> None:
    """Extract and upsert user facts from the query using pattern matching."""
    import re
    query_clean = query.strip()
    
    # Common patterns: key -> list of patterns (regexes) with capture groups
    patterns = {
        "name": [
            r"(?i)\bmy name is\s+([A-Za-z]+)",
            r"(?i)\bcall me\s+([A-Za-z]+)",
            r"(?i)\bi am\s+([A-Za-z]+)(?:\s+and\s+i|\s+from|\s+working|$)"
        ],
        "location": [
            r"(?i)\bi live in\s+([A-Za-z\s]+)",
            r"(?i)\bi am from\s+([A-Za-z\s]+)"
        ],
        "occupation": [
            r"(?i)\bi work as a\s+([A-Za-z\s]+)",
            r"(?i)\bi work as an\s+([A-Za-z\s]+)",
            r"(?i)\bi am a\s+(developer|engineer|programmer|student|teacher|doctor|designer|analyst)\b"
        ]
    }
    
    for category, regex_list in patterns.items():
        for pattern in regex_list:
            match = re.search(pattern, query_clean)
            if match:
                value = match.group(1).strip()
                # Clean up any trailing punctuation or unwanted words
                value = re.sub(r"[.,\/#!$%\^&\*;:{}=\-_`~()]+$", "", value).strip()
                if value:
                    logger.info("Extracted user memory fact: %s -> %s", category, value)
                    update_user_memory(user_id, key=f"user_{category}", value=value, category="user_fact")
                    break


def get_user_facts_prompt(user_id: str) -> str:
    """Retrieve user facts and format them as a string block for prompt injection."""
    memories = get_user_memories(user_id, category="user_fact")
    if not memories:
        return ""
    
    lines = ["[User Profile / Known Facts]"]
    for mem in memories:
        # e.g. user_name -> Name
        label = mem["key"].replace("user_", "").capitalize()
        lines.append(f"{label}: {mem['value']}")
    
    return "\n".join(lines)

