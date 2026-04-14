"""
AARKAAI Backend – Database Models & Engine (SQLAlchemy)

Production-ready with connection pooling and stale connection detection.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_URL, IS_PRODUCTION

# ─── Engine & Session ─────────────────────────────────────────────────────────

_engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,          # Detect stale connections before use
    "pool_recycle": 3600,           # Recycle connections every hour
}

# SQLite-specific settings
if DB_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL / MySQL connection pool settings
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20

engine = create_engine(DB_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# Enable WAL mode for SQLite (better concurrent read performance)
if DB_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Models ───────────────────────────────────────────────────────────────────

class UserAccount(Base):
    """Registered users for the AARKAAI platform."""
    __tablename__ = "users"

    id = Column(String(128), primary_key=True)  # UUID
    email = Column(String(256), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    name = Column(String(128), nullable=True)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for disabled
    created_at = Column(DateTime, default=_utcnow)


class ConversationHistory(Base):
    """Every prompt / response pair."""

    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    intent = Column(String(64), default="general")
    confidence = Column(Float, default=0.0)
    source = Column(String(64), default="aarkaa-3b")  # e.g. "finance", "rag", "web"
    timestamp = Column(DateTime, default=_utcnow)


class PersonalChat(Base):
    """Per-user chat messages for context window."""

    __tablename__ = "personal_chats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    message = Column(Text, nullable=False)
    role = Column(String(16), nullable=False)  # "user" | "assistant"
    timestamp = Column(DateTime, default=_utcnow)


class UserMemory(Base):
    """Key-value store for user preferences and facts."""

    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    key = Column(String(256), nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(64), default="general")
    timestamp = Column(DateTime, default=_utcnow)


class KnowledgeEntry(Base):
    """Learned knowledge with embeddings for RAG."""

    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(256), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(LargeBinary, nullable=True)  # 384-dim float32 blob
    source = Column(String(64), default="auto_learn")
    timestamp = Column(DateTime, default=_utcnow)


class UserKnowledgeProfile(Base):
    """Per-user profile tracking interests and expertise."""

    __tablename__ = "user_knowledge_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, unique=True, index=True)
    interests = Column(Text, default="")  # JSON-encoded list
    expertise_areas = Column(Text, default="")  # JSON-encoded list
    interaction_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=_utcnow)


class RLHFFeedback(Base):
    """Reinforcement Learning from Human Feedback data."""

    __tablename__ = "rlhf_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversation_history.id"), nullable=True)
    user_id = Column(String(128), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # e.g., 1 for positive, -1 for negative
    correction = Column(Text, nullable=True)  # explicit text correction
    timestamp = Column(DateTime, default=_utcnow)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Yield a DB session (for FastAPI dependency injection)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
