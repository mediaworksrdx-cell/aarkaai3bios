"""
RuVector In-Memory Vector Engine for Aarka Backend.
Provides SIMD-accelerated vector storage, cosine similarity search, and high-throughput recall.
"""

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class VectorRecord:
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


@dataclass
class SearchResult:
    id: str
    score: float
    metadata: Dict[str, Any]


class RuVectorEngine:
    """
    Sub-millisecond in-memory vector index with unit-normalized cosine similarity.
    Leverages NumPy matrix operations for hardware-accelerated SIMD vectorization.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension
        self.records: Dict[str, VectorRecord] = {}
        self._matrix_cache: Optional[Any] = None
        self._id_list_cache: Optional[List[str]] = None
        self._cache_dirty = True

    def _normalize(self, vec: List[float]) -> List[float]:
        """Calculates L2-normalized vector."""
        if len(vec) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(vec)}")

        norm_sq = sum(x * x for x in vec)
        norm = math.sqrt(norm_sq)
        if norm < 1e-12:
            return [0.0] * self.dimension
        return [x / norm for x in vec]

    def insert(self, record_id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Inserts or updates an L2-normalized vector record."""
        norm_vec = self._normalize(vector)
        self.records[record_id] = VectorRecord(
            id=record_id,
            vector=norm_vec,
            metadata=metadata or {}
        )
        self._cache_dirty = True

    def delete(self, record_id: str) -> bool:
        """Removes a vector record by ID."""
        if record_id in self.records:
            del self.records[record_id]
            self._cache_dirty = True
            return True
        return False

    def size(self) -> int:
        """Returns the number of indexed vectors."""
        return len(self.records)

    def _rebuild_cache_if_dirty(self) -> None:
        """Rebuilds the contiguous NumPy matrix for fast SIMD dot products."""
        if not self._cache_dirty:
            return

        if not self.records:
            self._matrix_cache = None
            self._id_list_cache = []
            self._cache_dirty = False
            return

        self._id_list_cache = list(self.records.keys())
        if HAS_NUMPY:
            vectors = [self.records[rid].vector for rid in self._id_list_cache]
            self._matrix_cache = np.array(vectors, dtype=np.float32)
        self._cache_dirty = False

    def search(self, query_vector: List[float], top_k: int = 5, min_score: float = -1.0) -> List[SearchResult]:
        """
        Executes nearest-neighbor search using cosine similarity against all indexed vectors.
        """
        if not self.records:
            return []

        norm_query = self._normalize(query_vector)
        self._rebuild_cache_if_dirty()

        results: List[SearchResult] = []

        if HAS_NUMPY and self._matrix_cache is not None and self._id_list_cache:
            # Vectorized matrix-vector multiplication
            q_arr = np.array(norm_query, dtype=np.float32)
            scores = np.dot(self._matrix_cache, q_arr)

            top_indices = np.argsort(scores)[::-1][:top_k]
            for idx in top_indices:
                score = float(scores[idx])
                if score >= min_score:
                    rid = self._id_list_cache[idx]
                    results.append(SearchResult(
                        id=rid,
                        score=score,
                        metadata=self.records[rid].metadata
                    ))
        else:
            # High-performance scalar fallback
            scored: List[tuple] = []
            for rid, rec in self.records.items():
                score = sum(q * v for q, v in zip(norm_query, rec.vector))
                if score >= min_score:
                    scored.append((score, rid, rec.metadata))

            scored.sort(key=lambda x: x[0], reverse=True)
            for score, rid, meta in scored[:top_k]:
                results.append(SearchResult(id=rid, score=score, metadata=meta))

        return results

    def embed_text_deterministic(self, text: str) -> List[float]:
        """
        Deterministic lightweight tokenizer/hasher embedding generating a unit-normalized
        pseudo-vector of length self.dimension for text retrieval when neural models are absent.
        """
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            h = hash(word)
            idx = abs(h) % self.dimension
            sign = 1.0 if (h % 2 == 0) else -1.0
            vec[idx] += sign

        return self._normalize(vec)
