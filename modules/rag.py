"""
AARKAAI – RAG Engine (SQLite + sentence-transformers + cross-encoder reranking)

Stores & retrieves knowledge entries using embedding-based
cosine similarity computed in NumPy, with optional cross-encoder
reranking and post-retrieval relevance validation.

Hardening features:
  - Configurable similarity threshold (default 0.50)
  - Cross-encoder reranker for precision ranking
  - Keyword overlap (Jaccard) validation
  - Domain consistency check
  - Context budget cap to prevent prompt bloat
"""
from __future__ import annotations

import logging
import re
import struct
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

from config import (
    EMBEDDING_DIM,
    RAG_SIMILARITY_THRESHOLD,
    RAG_RERANKER_THRESHOLD,
    RAG_MAX_CONTEXT_CHARS,
    RAG_CANDIDATE_POOL_SIZE,
    RAG_KEYWORD_OVERLAP_MIN,
)
from database import KnowledgeEntry, SessionLocal

logger = logging.getLogger(__name__)

# ─── Lazy globals ─────────────────────────────────────────────────────────────
_embedding_fn = None  # callable(text) → np.ndarray
_reranker_fn = None   # callable(query, document) → float  (cross-encoder score)


def init(embed_fn, reranker_fn=None) -> None:
    """
    Initialise the RAG engine with an embedding function and optional reranker.

    Parameters
    ----------
    embed_fn : callable
        text → np.ndarray of shape (EMBEDDING_DIM,)
    reranker_fn : callable, optional
        (query, document) → float  – cross-encoder relevance score
    """
    global _embedding_fn, _reranker_fn
    _embedding_fn = embed_fn
    _reranker_fn = reranker_fn
    mode = "reranker" if reranker_fn else "cosine-only"
    logger.info("RAG engine initialised (dim=%d, mode=%s)", EMBEDDING_DIM, mode)


# ─── Embedding serialisation ─────────────────────────────────────────────────


def _serialize(vec: np.ndarray) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec.tolist())


def _deserialize(blob: bytes) -> np.ndarray:
    n = len(blob) // 4  # float32 = 4 bytes
    return np.array(struct.unpack(f"{n}f", blob), dtype=np.float32)


# ─── Keyword extraction & validation ─────────────────────────────────────────

_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "both", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "while", "about", "what", "which", "who", "whom", "this", "that",
    "these", "those", "i", "me", "my", "we", "our", "you", "your", "he",
    "him", "his", "she", "her", "it", "its", "they", "them", "their",
    "tell", "explain", "describe", "give", "show",
}


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text, removing stop words."""
    words = set(re.findall(r"\b[a-zA-Z]{2,}\b", text.lower()))
    return words - _STOP_WORDS


def _jaccard_similarity(query_keywords: set, doc_keywords: set) -> float:
    """Compute query keyword coverage/containment in the document."""
    if not query_keywords:
        return 1.0
    intersection = query_keywords & doc_keywords
    return len(intersection) / len(query_keywords)


# ─── Storage ──────────────────────────────────────────────────────────────────


def store_knowledge(topic: str, content: str, source: str = "auto_learn", user_id: Optional[str] = None) -> None:
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
            user_id=user_id,
            topic=topic,
            content=content,
            embedding=blob,
            source=source,
        )
        session.add(entry)
        session.commit()
        logger.info("Stored knowledge: %s (%d chars) for user %s", topic, len(content), user_id)
    except Exception as exc:
        session.rollback()
        logger.error("store_knowledge failed: %s", exc)
    finally:
        session.close()


# ─── Retrieval ────────────────────────────────────────────────────────────────


def search(query: str, top_k: int = 5, user_id: Optional[str] = None, query_domain: Optional[str] = None) -> list[dict]:
    """
    Semantic search over knowledge entries with optional reranking and validation.

    Returns list of dicts with keys: id, topic, content, score, reranker_score, source
    """
    if _embedding_fn is None:
        return []

    q_vec = _embedding_fn(query)
    query_keywords = _extract_keywords(query)

    session: Session = SessionLocal()
    try:
        filters = [
            KnowledgeEntry.embedding.isnot(None),
            KnowledgeEntry.source != "auto_learn"
        ]

        # Isolate user knowledge profiles.
        # Global entries (empty/system user_id) are accessible to all users.
        if user_id:
            filters.append(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None)) | (KnowledgeEntry.user_id == "")
            )
        else:
            filters.append(
                (KnowledgeEntry.user_id.is_(None)) | (KnowledgeEntry.user_id == "")
            )

        entries = session.query(KnowledgeEntry).filter(*filters).all()

        if not entries:
            return []

        # ── Phase 1: Cosine similarity retrieval (broad candidate pool) ──
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

        # Take a broader candidate pool for reranking
        pool_size = RAG_CANDIDATE_POOL_SIZE if _reranker_fn else top_k
        candidates = scored[:pool_size]

        # ── Phase 2: Filter by cosine threshold ──
        candidates = [(sim, entry) for sim, entry in candidates if sim >= RAG_SIMILARITY_THRESHOLD]
        if not candidates:
            logger.info("RAG: No candidates passed cosine threshold (%.2f) for query: %s", RAG_SIMILARITY_THRESHOLD, query[:60])
            return []

        # ── Phase 3: Keyword overlap validation & Domain consistency check ──
        validated: list[tuple[float, KnowledgeEntry, float]] = []  # (cosine, entry, keyword_overlap)
        for sim, entry in candidates:
            # Domain consistency check (fast keyword-based, no expensive ML calls)
            if query_domain:
                try:
                    doc_text = (entry.topic + " " + entry.content).lower()
                    _DOMAIN_KW_MAP = {
                        "finance": {"stock", "price", "market", "share", "crypto", "bitcoin", "trading", "investment", "dividend", "portfolio", "revenue", "earnings"},
                        "technology": {"python", "java", "code", "programming", "software", "api", "cloud", "database", "algorithm", "docker", "linux"},
                        "science": {"physics", "chemistry", "biology", "quantum", "atom", "molecule", "dna", "evolution", "experiment"},
                        "health": {"health", "medical", "disease", "symptom", "treatment", "medicine", "doctor", "hospital", "vaccine"},
                        "history": {"history", "war", "ancient", "civilization", "empire", "dynasty", "revolution", "medieval"},
                    }
                    doc_domain = "general"
                    best_hits = 0
                    for dom, kws in _DOMAIN_KW_MAP.items():
                        hits = sum(1 for kw in kws if kw in doc_text)
                        if hits > best_hits:
                            best_hits = hits
                            doc_domain = dom
                    if doc_domain != "general" and doc_domain != query_domain and best_hits >= 2:
                        logger.debug(
                            "RAG: Rejected entry '%s' — domain mismatch (query=%s, doc=%s)",
                            entry.topic[:40], query_domain, doc_domain,
                        )
                        continue
                except Exception as exc:
                    logger.debug("Domain consistency check failed: %s", exc)

            doc_keywords = _extract_keywords(entry.content)
            keyword_overlap = _jaccard_similarity(query_keywords, doc_keywords)

            if keyword_overlap < RAG_KEYWORD_OVERLAP_MIN:
                logger.debug(
                    "RAG: Rejected entry '%s' — keyword overlap %.3f < %.3f",
                    entry.topic[:40], keyword_overlap, RAG_KEYWORD_OVERLAP_MIN,
                )
                continue

            validated.append((sim, entry, keyword_overlap))

        if not validated:
            logger.info("RAG: No candidates passed keyword overlap check for query: %s", query[:60])
            return []

        # ── Phase 4: Cross-encoder reranking (if available) ──
        results = []
        if _reranker_fn:
            reranked: list[tuple[float, float, KnowledgeEntry, float]] = []
            for sim, entry, kw_overlap in validated:
                try:
                    rerank_score = _reranker_fn(query, entry.content)
                    reranked.append((rerank_score, sim, entry, kw_overlap))
                except Exception as exc:
                    logger.debug("Reranker failed for entry %d: %s", entry.id, exc)
                    # Fall back to cosine score as reranker score
                    reranked.append((sim, sim, entry, kw_overlap))

            # Sort by reranker score descending
            reranked.sort(key=lambda x: x[0], reverse=True)

            for rerank_score, cosine_score, entry, kw_overlap in reranked[:top_k]:
                if rerank_score < RAG_RERANKER_THRESHOLD:
                    logger.debug(
                        "RAG: Rejected entry '%s' — reranker score %.3f < %.3f",
                        entry.topic[:40], rerank_score, RAG_RERANKER_THRESHOLD,
                    )
                    continue

                results.append({
                    "id": entry.id,
                    "topic": entry.topic,
                    "content": entry.content,
                    "score": round(cosine_score, 4),
                    "reranker_score": round(rerank_score, 4),
                    "source": entry.source,
                })
        else:
            # No reranker — use cosine scores directly
            validated.sort(key=lambda x: x[0], reverse=True)
            for sim, entry, kw_overlap in validated[:top_k]:
                results.append({
                    "id": entry.id,
                    "topic": entry.topic,
                    "content": entry.content,
                    "score": round(sim, 4),
                    "reranker_score": None,
                    "source": entry.source,
                })

        if results:
            logger.info(
                "RAG: Returning %d results (top score=%.3f, reranker=%s) for query: %s",
                len(results),
                results[0]["score"],
                results[0].get("reranker_score", "N/A"),
                query[:60],
            )
        return results
    finally:
        session.close()


def get_context(query: str, top_k: int = 3, user_id: Optional[str] = None,
                max_chars: int = RAG_MAX_CONTEXT_CHARS, query_domain: Optional[str] = None) -> str:
    """
    Get a formatted context string for the query from the knowledge base.

    Enforces a maximum character budget to prevent context window bloat.
    """
    results = search(query, top_k=top_k, user_id=user_id, query_domain=query_domain)
    if not results:
        return ""

    lines = []
    total_chars = 0
    for r in results:
        entry_text = f"[{r['topic']}] (relevance: {r['score']}):\n{r['content']}"
        if total_chars + len(entry_text) > max_chars:
            # Truncate the last entry to fit within budget
            remaining = max_chars - total_chars
            if remaining > 100:  # Only include if there's meaningful space left
                lines.append(entry_text[:remaining] + "…")
            break
        lines.append(entry_text)
        total_chars += len(entry_text)

    return "\n\n---\n\n".join(lines)


def get_entry_count() -> int:
    """Return total number of knowledge entries."""
    session: Session = SessionLocal()
    try:
        return session.query(KnowledgeEntry).count()
    finally:
        session.close()
