"""
AARKAAI Backend – MongoDB Client Manager (Atlas / Flex Cluster)

Provides thread-safe PyMongo connection pooling, automatic index setup,
and collection accessors for all Aarka AI collections.
"""
from __future__ import annotations

import logging
from typing import Optional
from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT

import config

logger = logging.getLogger(__name__)

_client: Optional[MongoClient] = None
_db = None


def get_mongo_client() -> Optional[MongoClient]:
    """Return singleton PyMongo MongoClient instance or None if MONGODB_URI is not set."""
    global _client
    if not config.MONGODB_URI:
        return None

    if _client is None:
        try:
            logger.info("Connecting to MongoDB Atlas Flex cluster...")
            _client = MongoClient(
                config.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
                maxPoolSize=50,
                minPoolSize=5,
                retryWrites=True,
                w="majority",
            )
            # Test connection
            _client.admin.command("ping")
            logger.info("✓ Connected to MongoDB Atlas Flex successfully.")
        except Exception as exc:
            logger.error("Failed to connect to MongoDB Atlas Flex: %s", exc)
            _client = None
            return None
    return _client


def get_mongo_db():
    """Return the primary MongoDB database object ('aarkaai')."""
    global _db
    if _db is not None:
        return _db

    client = get_mongo_client()
    if client is not None:
        _db = client[config.MONGODB_DB_NAME]
        init_mongo_indexes(_db)
        return _db
    return None


def init_mongo_indexes(db) -> None:
    """Create indexes for all collections if they do not exist."""
    try:
        # Users collection
        db.users.create_index([("email", ASCENDING)], unique=True, sparse=True)
        db.users.create_index([("id", ASCENDING)], unique=True)

        # Conversation history
        db.conversation_history.create_index([("user_id", ASCENDING), ("session_id", ASCENDING)])
        db.conversation_history.create_index([("timestamp", DESCENDING)])

        # Personal chats
        db.personal_chats.create_index([("user_id", ASCENDING), ("session_id", ASCENDING)])
        db.personal_chats.create_index([("timestamp", ASCENDING)])

        # User memory
        db.user_memory.create_index([("user_id", ASCENDING), ("key", ASCENDING)], unique=True)

        # Knowledge entries (RAG)
        db.knowledge_entries.create_index([("user_id", ASCENDING)])
        db.knowledge_entries.create_index([("topic", ASCENDING)])
        db.knowledge_entries.create_index([("content", TEXT)])

        # User profiles
        db.user_knowledge_profiles.create_index([("user_id", ASCENDING)], unique=True)

        # RLHF feedback
        db.rlhf_feedback.create_index([("user_id", ASCENDING)])
        db.rlhf_feedback.create_index([("conversation_id", ASCENDING)])

        # Task goals
        db.task_goals.create_index([("user_id", ASCENDING), ("session_id", ASCENDING)])
        db.task_goals.create_index([("status", ASCENDING)])

        # Portfolio holdings & Watchlist
        db.portfolio_holdings.create_index([("user_id", ASCENDING), ("symbol", ASCENDING)], unique=True)
        db.watchlist_items.create_index([("user_id", ASCENDING), ("symbol", ASCENDING)], unique=True)
        db.market_alerts.create_index([("user_id", ASCENDING), ("symbol", ASCENDING)])

        # User settings
        db.user_settings.create_index([("user_id", ASCENDING)], unique=True)

        logger.info("✓ MongoDB collection indexes verified successfully.")
    except Exception as exc:
        logger.error("Failed to initialize MongoDB indexes: %s", exc)
