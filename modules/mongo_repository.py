"""
AARKAAI Backend – MongoDB Repository Layer (Atlas Flex)

Provides clean domain-driven repositories for all Aarka AI collections:
  - UserRepo
  - ConversationRepo
  - PersonalChatRepo
  - UserMemoryRepo
  - KnowledgeRepo
  - UserProfileRepo
  - RLHFRepo
  - TaskGoalRepo
  - PortfolioRepo & WatchlistRepo
  - MarketAlertRepo
  - UserSettingsRepo
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from pymongo import ReturnDocument, ASCENDING, DESCENDING

from modules.mongo_client import get_mongo_db

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── User Repository ──────────────────────────────────────────────────────────
class UserRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.users if db is not None else None

    @classmethod
    def get_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return None
        return coll.find_one({"id": user_id})

    @classmethod
    def get_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return None
        return coll.find_one({"email": email.lower().strip()})

    @classmethod
    def create_user(cls, user_id: str, email: str, password_hash: str, name: str = "", role: str = "user") -> Dict[str, Any]:
        coll = cls.get_collection()
        doc = {
            "id": user_id,
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "name": name,
            "role": role,
            "is_active": 1,
            "created_at": _utcnow(),
        }
        if coll is not None:
            coll.update_one({"id": user_id}, {"$set": doc}, upsert=True)
        return doc


# ─── Conversation Repository ──────────────────────────────────────────────────
class ConversationRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.conversation_history if db is not None else None

    @classmethod
    def add_entry(cls, user_id: str, query: str, response: str, session_id: str = "default", intent: str = "general", confidence: float = 0.0, source: str = "aarkaa-3b") -> Dict[str, Any]:
        coll = cls.get_collection()
        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "query": query,
            "response": response,
            "intent": intent,
            "confidence": confidence,
            "source": source,
            "timestamp": _utcnow(),
        }
        if coll is not None:
            result = coll.insert_one(doc)
            doc["_id"] = result.inserted_id
        return doc

    @classmethod
    def get_history(cls, user_id: str, session_id: str = "default", limit: int = 50) -> List[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return []
        cursor = coll.find({"user_id": user_id, "session_id": session_id}).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)


# ─── Personal Chat Repository ─────────────────────────────────────────────────
class PersonalChatRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.personal_chats if db is not None else None

    @classmethod
    def add_message(cls, user_id: str, message: str, role: str, session_id: str = "default") -> Dict[str, Any]:
        coll = cls.get_collection()
        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "role": role,
            "timestamp": _utcnow(),
        }
        if coll is not None:
            result = coll.insert_one(doc)
            doc["_id"] = result.inserted_id
        return doc

    @classmethod
    def get_messages(cls, user_id: str, session_id: str = "default", limit: int = 30) -> List[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return []
        cursor = coll.find({"user_id": user_id, "session_id": session_id}).sort("timestamp", ASCENDING).limit(limit)
        return list(cursor)


# ─── User Memory Repository ───────────────────────────────────────────────────
class UserMemoryRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.user_memory if db is not None else None

    @classmethod
    def set_memory(cls, user_id: str, key: str, value: str, category: str = "general") -> Dict[str, Any]:
        coll = cls.get_collection()
        doc = {
            "user_id": user_id,
            "key": key,
            "value": value,
            "category": category,
            "timestamp": _utcnow(),
        }
        if coll is not None:
            coll.update_one({"user_id": user_id, "key": key}, {"$set": doc}, upsert=True)
        return doc

    @classmethod
    def get_all_memories(cls, user_id: str) -> List[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return []
        return list(coll.find({"user_id": user_id}))


# ─── Knowledge / RAG Repository ───────────────────────────────────────────────
class KnowledgeRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.knowledge_entries if db is not None else None

    @classmethod
    def add_entry(cls, topic: str, content: str, user_id: Optional[str] = None, embedding: Optional[bytes] = None, source: str = "auto_learn") -> Dict[str, Any]:
        coll = cls.get_collection()
        doc = {
            "topic": topic,
            "content": content,
            "user_id": user_id,
            "embedding": embedding,
            "source": source,
            "timestamp": _utcnow(),
        }
        if coll is not None:
            res = coll.insert_one(doc)
            doc["_id"] = res.inserted_id
        return doc

    @classmethod
    def get_all(cls, limit: int = 100) -> List[Dict[str, Any]]:
        coll = cls.get_collection()
        if coll is None:
            return []
        return list(coll.find().sort("timestamp", DESCENDING).limit(limit))


# ─── Task Goal Repository ─────────────────────────────────────────────────────
class TaskGoalRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.task_goals if db is not None else None

    @classmethod
    def create_goal(cls, user_id: str, goal_text: str, task_dag: str, session_id: str = "default", scratchpad: str = "{}") -> Dict[str, Any]:
        coll = cls.get_collection()
        doc = {
            "user_id": user_id,
            "session_id": session_id,
            "goal_text": goal_text,
            "task_dag": task_dag,
            "scratchpad": scratchpad,
            "status": "pending",
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        if coll is not None:
            res = coll.insert_one(doc)
            doc["_id"] = res.inserted_id
        return doc


# ─── User Settings Repository ─────────────────────────────────────────────────
class UserSettingsRepo:
    @staticmethod
    def get_collection():
        db = get_mongo_db()
        return db.user_settings if db is not None else None

    @classmethod
    def get_settings(cls, user_id: str) -> Dict[str, Any]:
        coll = cls.get_collection()
        default_settings = {
            "user_id": user_id,
            "default_model": "aarkaa-7b",
            "response_style": "balanced",
            "theme": "dark",
            "language": "en",
            "streaming_enabled": 1,
            "reasoning_depth": "balanced",
            "updated_at": _utcnow(),
        }
        if coll is None:
            return default_settings

        doc = coll.find_one({"user_id": user_id})
        if doc is None:
            coll.insert_one(default_settings)
            return default_settings
        return doc

    @classmethod
    def update_settings(cls, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        coll = cls.get_collection()
        updates["updated_at"] = _utcnow()
        if coll is not None:
            return coll.find_one_and_update(
                {"user_id": user_id},
                {"$set": updates},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )
        return updates
