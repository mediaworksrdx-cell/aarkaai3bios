"""
AARKAAI – RAG Engine (SQLite + sentence-transformers)

Stores & retrieves knowledge entries using embedding-based
cosine similarity computed in NumPy.
"""
from __future__ import annotations

import logging
import struct
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from config import EMBEDDING_DIM
from database import KnowledgeEntry, SessionLocal

logger = logging.getLogger(__name__)

# ─── Lazy globals ─────────────────────────────────────────────────────────────
_embedding_fn = None  # callable(text) → np.ndarray


def init(embed_fn) -> None:
    """
    Initialise the RAG engine with an embedding function.

    Parameters
    ----------
    embed_fn : callable
        text → np.ndarray of shape (EMBEDDING_DIM,)
    """
    global _embedding_fn
    _embedding_fn = embed_fn
    logger.info("RAG engine initialised (dim=%d)", EMBEDDING_DIM)


# ─── Embedding serialisation ─────────────────────────────────────────────────


def _serialize(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def _deserialize(blob: bytes) -> np.ndarray:
    n = len(blob) // 4  # float32 = 4 bytes
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


# ─── Storage ──────────────────────────────────────────────────────────────────


def store_knowledge(topic: str, content: str, source: str = "auto_learn") -> None:
    """
    Embed and store a knowledge entry.
    """
    if _embedding_fn is None:
        logger.warning("RAG not initialised – skipping store")
        return

    vec = _embedding_fn(content)
    blob = _serialize(vec)

    session: Session = SessionLocal()
    try:
        entry = KnowledgeEntry(
            topic=topic,
            content=content,
            embedding=blob,
            source=source,
        )
        session.add(entry)
        session.commit()
        logger.info("Stored knowledge: %s (%d chars)", topic, len(content))
    except Exception as exc:
        session.rollback()
        logger.error("store_knowledge failed: %s", exc)
    finally:
        session.close()


# ─── Retrieval ────────────────────────────────────────────────────────────────


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    Semantic search over knowledge entries.

    Returns list of dicts with keys: id, topic, content, score, source
    """
    if _embedding_fn is None:
        return []

    q_vec = _embedding_fn(query)

    session: Session = SessionLocal()
    try:
        entries = session.query(KnowledgeEntry).filter(
            KnowledgeEntry.embedding.isnot(None)
        ).all()

        if not entries:
            return []

        scored: list[tuple[float, KnowledgeEntry]] = []
        for entry in entries:
            try:
                e_vec = _deserialize(entry.embedding)
                # Cosine similarity
                dot = float(np.dot(q_vec, e_vec))
                norm = float(np.linalg.norm(q_vec) * np.linalg.norm(e_vec))
                sim = dot / norm if norm > 0 else 0.0
                scored.append((sim, entry))
            except Exception:
                continue

        # Sort descending by similarity
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, entry in scored[:top_k]:
            # Threshold to prevent injecting irrelevant garbage into the prompt context
            if sim < 0.35:
                continue
                
            results.append({
                "id": entry.id,
                "topic": entry.topic,
                "content": entry.content,
                "score": round(sim, 4),
                "source": entry.source,
            })

        return results
    finally:
        session.close()


def get_context(query: str, top_k: int = 3) -> str:
    """
    Get a formatted context string for the query from the knowledge base.
    """
    results = search(query, top_k=top_k)
    if not results:
        return ""

    lines = []
    for r in results:
        lines.append(f"[{r['topic']}] (relevance: {r['score']}):\n{r['content']}")

    return "\n\n---\n\n".join(lines)


def get_entry_count() -> int:
    """Return total number of knowledge entries."""
    session: Session = SessionLocal()
    try:
        return session.query(KnowledgeEntry).count()
    finally:
        session.close()
