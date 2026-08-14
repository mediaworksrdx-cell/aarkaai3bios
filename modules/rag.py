"""
AARKAAI – RAG Engine (ChromaDB + sentence-transformers + cross-encoder reranking)

Stores & retrieves knowledge entries using ChromaDB's native
HNSW-indexed vector similarity search, with optional cross-encoder
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
import uuid
from datetime import datetime, timezone
from typing import Optional

import chromadb
import numpy as np

from config import (
    CHROMA_PERSIST_DIR,
    EMBEDDING_DIM,
    RAG_SIMILARITY_THRESHOLD,
    RAG_RERANKER_THRESHOLD,
    RAG_MAX_CONTEXT_CHARS,
    RAG_CANDIDATE_POOL_SIZE,
    RAG_KEYWORD_OVERLAP_MIN,
)

logger = logging.getLogger(__name__)

# ─── Lazy globals ─────────────────────────────────────────────────────────────
_embedding_fn = None  # callable(text) → np.ndarray
_reranker_fn = None   # callable(query, document) → float  (cross-encoder score)
_collection = None    # chromadb.Collection
_client = None        # chromadb.PersistentClient

# Sentinel value for global (non-user-specific) knowledge entries
_GLOBAL_USER = "__global__"

_COLLECTION_NAME = "aarkaai_knowledge"


def init(embed_fn, reranker_fn=None) -> None:
    """
    Initialise the RAG engine with an embedding function, optional reranker,
    and a ChromaDB persistent collection.

    Parameters
    ----------
    embed_fn : callable
        text → np.ndarray of shape (EMBEDDING_DIM,)
    reranker_fn : callable, optional
        (query, document) → float  – cross-encoder relevance score
    """
    global _embedding_fn, _reranker_fn, _collection, _client
    _embedding_fn = embed_fn
    _reranker_fn = reranker_fn

    try:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        _collection = _client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        mode = "reranker" if reranker_fn else "cosine-only"
        logger.info(
            "RAG engine initialised (ChromaDB at %s, dim=%d, mode=%s, entries=%d)",
            CHROMA_PERSIST_DIR, EMBEDDING_DIM, mode, _collection.count(),
        )
    except Exception as exc:
        logger.error("ChromaDB initialisation failed: %s", exc)
        _collection = None


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
    Embed and store a knowledge entry in ChromaDB with cosine deduplication.
    """
    if _embedding_fn is None or _collection is None:
        logger.warning("RAG not initialised – skipping store")
        return

    vec = _embedding_fn(content)
    doc_id = str(uuid.uuid4())
    effective_user = user_id if user_id else _GLOBAL_USER

    try:
        # Cosine distance deduplication check (distance <= 0.12 means similarity >= 0.88)
        if _collection.count() > 0:
            dup_check = _collection.query(
                query_embeddings=[vec.tolist()],
                n_results=1,
                include=["distances"]
            )
            if dup_check and "distances" in dup_check and dup_check["distances"] and dup_check["distances"][0]:
                closest_dist = dup_check["distances"][0][0]
                if closest_dist <= 0.12:
                    logger.info("Skipping duplicate knowledge store. Nearest neighbor cosine distance: %.4f", closest_dist)
                    return

        _collection.add(
            ids=[doc_id],
            embeddings=[vec.tolist()],
            documents=[content],
            metadatas=[{
                "user_id": effective_user,
                "topic": topic,
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        )
        logger.info("Stored knowledge: %s (%d chars) for user %s", topic, len(content), user_id)
    except Exception as exc:
        logger.error("store_knowledge failed: %s", exc)


# ─── Retrieval ────────────────────────────────────────────────────────────────


def search(query: str, top_k: int = 5, user_id: Optional[str] = None, query_domain: Optional[str] = None, source_filter: Optional[str] = None) -> list[dict]:
    """
    Semantic search over knowledge entries with ChromaDB, optional reranking and validation.

    Parameters
    ----------
    source_filter : str, optional
        If specified, restrict results to entries with this exact source value
        (e.g., 'architecture'). Overrides the default auto_learn exclusion.

    Returns list of dicts with keys: id, topic, content, score, reranker_score, source
    """
    if _embedding_fn is None or _collection is None:
        return []

    if _collection.count() == 0:
        return []

    q_vec = _embedding_fn(query)
    query_keywords = _extract_keywords(query)

    # ── Build ChromaDB where filter ──
    # 1. User scoping: user's own entries + global entries
    effective_user = user_id if user_id else _GLOBAL_USER
    user_filter = {
        "$or": [
            {"user_id": effective_user},
            {"user_id": _GLOBAL_USER},
        ]
    }

    # 2. Source filtering
    if source_filter:
        # Restrict to a specific source (e.g., 'architecture')
        source_clause = {"source": source_filter}
    else:
        # Default: exclude auto_learn entries
        source_clause = {"source": {"$ne": "auto_learn"}}

    where_filter = {
        "$and": [
            user_filter,
            source_clause,
        ]
    }

    # ── Phase 1: ChromaDB similarity search (HNSW-indexed) ──
    pool_size = RAG_CANDIDATE_POOL_SIZE if _reranker_fn else top_k
    # Request more candidates than needed so we can filter in post-processing
    n_results = min(pool_size * 2, _collection.count())

    try:
        results = _collection.query(
            query_embeddings=[q_vec.tolist()],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.error("ChromaDB query failed: %s", exc)
        return []

    if not results or not results["ids"] or not results["ids"][0]:
        return []

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # ChromaDB cosine distance = 1 - cosine_similarity, so convert back
    candidates = []
    for doc_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
        cosine_sim = 1.0 - dist
        candidates.append((cosine_sim, doc_id, doc, meta))

    # ── Phase 2: Filter by cosine threshold ──
    candidates = [(sim, did, doc, meta) for sim, did, doc, meta in candidates if sim >= RAG_SIMILARITY_THRESHOLD]
    if not candidates:
        logger.info("RAG: No candidates passed cosine threshold (%.2f) for query: %s", RAG_SIMILARITY_THRESHOLD, query[:60])
        return []

    # ── Phase 3: Keyword overlap validation & Domain consistency check ──
    validated: list[tuple[float, str, str, dict, float]] = []  # (cosine, id, doc, meta, keyword_overlap)
    for sim, did, doc, meta in candidates:
        topic = meta.get("topic", "")

        # Domain consistency check
        if query_domain:
            try:
                doc_text = (topic + " " + doc).lower()
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
                        topic[:40], query_domain, doc_domain,
                    )
                    continue
            except Exception as exc:
                logger.debug("Domain consistency check failed: %s", exc)

        doc_keywords = _extract_keywords(doc)
        keyword_overlap = _jaccard_similarity(query_keywords, doc_keywords)

        if keyword_overlap < RAG_KEYWORD_OVERLAP_MIN:
            logger.debug(
                "RAG: Rejected entry '%s' — keyword overlap %.3f < %.3f",
                topic[:40], keyword_overlap, RAG_KEYWORD_OVERLAP_MIN,
            )
            continue

        validated.append((sim, did, doc, meta, keyword_overlap))

    if not validated:
        logger.info("RAG: No candidates passed keyword overlap check for query: %s", query[:60])
        return []

    # ── Phase 4: Cross-encoder reranking (if available) ──
    final_results = []
    if _reranker_fn:
        reranked: list[tuple[float, float, str, str, dict, float]] = []
        for sim, did, doc, meta, kw_overlap in validated:
            try:
                rerank_score = _reranker_fn(query, doc)
                reranked.append((rerank_score, sim, did, doc, meta, kw_overlap))
            except Exception as exc:
                logger.debug("Reranker failed for entry %s: %s", did, exc)
                reranked.append((sim, sim, did, doc, meta, kw_overlap))

        reranked.sort(key=lambda x: x[0], reverse=True)

        for rerank_score, cosine_score, did, doc, meta, kw_overlap in reranked[:top_k]:
            if rerank_score < RAG_RERANKER_THRESHOLD:
                logger.debug(
                    "RAG: Rejected entry '%s' — reranker score %.3f < %.3f",
                    meta.get("topic", "")[:40], rerank_score, RAG_RERANKER_THRESHOLD,
                )
                continue

            final_results.append({
                "id": did,
                "topic": meta.get("topic", ""),
                "content": doc,
                "score": round(cosine_score, 4),
                "reranker_score": round(rerank_score, 4),
                "source": meta.get("source", ""),
            })
    else:
        # No reranker — use cosine scores directly
        validated.sort(key=lambda x: x[0], reverse=True)
        for sim, did, doc, meta, kw_overlap in validated[:top_k]:
            final_results.append({
                "id": did,
                "topic": meta.get("topic", ""),
                "content": doc,
                "score": round(sim, 4),
                "reranker_score": None,
                "source": meta.get("source", ""),
            })

    if final_results:
        logger.info(
            "RAG: Returning %d results (top score=%.3f, reranker=%s) for query: %s",
            len(final_results),
            final_results[0]["score"],
            final_results[0].get("reranker_score", "N/A"),
            query[:60],
        )
    return final_results


def get_context(query: str, top_k: int = 3, user_id: Optional[str] = None,
                max_chars: int = RAG_MAX_CONTEXT_CHARS, query_domain: Optional[str] = None,
                source_filter: Optional[str] = None) -> str:
    """
    Get a formatted context string for the query from the knowledge base.

    Enforces a maximum character budget to prevent context window bloat.
    """
    results = search(query, top_k=top_k, user_id=user_id, query_domain=query_domain, source_filter=source_filter)
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
    if _collection is None:
        return 0
    try:
        return _collection.count()
    except Exception:
        return 0

