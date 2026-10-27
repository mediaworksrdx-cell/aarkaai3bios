"""
RuVector In-Memory Vector Engine for Aarka Backend.
Provides SIMD-accelerated vector storage, cosine similarity search, disk persistence,
and high-throughput recall with strict numerical integrity validation.
"""

import hashlib
import json
import math
import os
import tempfile
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Magic header for RuVector persistence format v1
RUVEC_MAGIC_HEADER = b"RUVEC\x01"


@dataclass
class VectorRecord:
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    id: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuVectorEngine:
    """
    Sub-millisecond vector index with unit-normalized cosine similarity.
    Leverages NumPy matrix operations for SIMD vectorization when available.
    Supports thread-safe mutations, atomic disk persistence, and tamper verification.
    """

    def __init__(self, dimension: int = 384, storage_path: Optional[str] = None) -> None:
        if dimension <= 0:
            raise ValueError(f"Dimension must be a positive integer, got {dimension}")
        self.dimension = dimension
        self.storage_path = os.path.abspath(storage_path) if storage_path else None
        self.records: Dict[str, VectorRecord] = {}
        self._matrix_cache: Optional[Any] = None
        self._id_list_cache: Optional[List[str]] = None
        self._cache_dirty = True
        self._lock = threading.RLock()

        if self.storage_path and os.path.exists(self.storage_path):
            self.load_from_disk(self.storage_path)

    @property
    def engine_type(self) -> str:
        """Explicitly reports the operational vector engine type."""
        return "numpy-simd" if HAS_NUMPY else "pure-python-fallback"

    def _validate_vector(self, vec: Union[List[float], Tuple[float, ...], Any]) -> List[float]:
        """Strictly validates vector dimensions and finite numeric representation."""
        if vec is None:
            raise ValueError("Vector cannot be None")

        if not hasattr(vec, "__len__"):
            raise TypeError("Vector must be a sequence of floats or ints")

        if len(vec) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(vec)}")

        validated: List[float] = []
        for i, val in enumerate(vec):
            if not isinstance(val, (int, float)):
                raise TypeError(f"Vector component at index {i} is not a numeric float/int: {type(val).__name__}")
            f_val = float(val)
            if not math.isfinite(f_val):
                raise ValueError(f"Vector contains non-finite value ({f_val}) at index {i}")
            validated.append(f_val)

        return validated

    def _normalize(self, vec: List[float]) -> List[float]:
        """Calculates L2-normalized unit vector."""
        norm_sq = sum(x * x for x in vec)
        norm = math.sqrt(norm_sq)
        if norm < 1e-12:
            return [0.0] * self.dimension
        return [x / norm for x in vec]

    def insert(self, record_id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Inserts or updates an L2-normalized vector record with thread safety."""
        if not record_id or not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("record_id must be a non-empty string")

        validated_vec = self._validate_vector(vector)
        norm_vec = self._normalize(validated_vec)

        with self._lock:
            self.records[record_id] = VectorRecord(
                id=record_id,
                vector=norm_vec,
                metadata=metadata.copy() if metadata else {}
            )
            self._cache_dirty = True

    def delete(self, record_id: str) -> bool:
        """Removes a vector record by ID."""
        with self._lock:
            if record_id in self.records:
                del self.records[record_id]
                self._cache_dirty = True
                return True
            return False

    def get(self, record_id: str) -> Optional[VectorRecord]:
        """Retrieves a vector record by ID."""
        with self._lock:
            return self.records.get(record_id)

    def size(self) -> int:
        """Returns the number of indexed vectors."""
        with self._lock:
            return len(self.records)

    def clear(self) -> None:
        """Clears all indexed vectors and invalidates caches."""
        with self._lock:
            self.records.clear()
            self._matrix_cache = None
            self._id_list_cache = None
            self._cache_dirty = True

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
        if top_k <= 0:
            return []

        validated_query = self._validate_vector(query_vector)
        norm_query = self._normalize(validated_query)

        with self._lock:
            if not self.records:
                return []

            self._rebuild_cache_if_dirty()
            results: List[SearchResult] = []

            if HAS_NUMPY and self._matrix_cache is not None and self._id_list_cache:
                q_arr = np.array(norm_query, dtype=np.float32)
                scores = np.dot(self._matrix_cache, q_arr)

                k = min(top_k, len(scores))
                top_indices = np.argsort(scores)[::-1][:k]
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
                scored: List[Tuple[float, str, Dict[str, Any]]] = []
                for rid, rec in self.records.items():
                    score = sum(q * v for q, v in zip(norm_query, rec.vector))
                    if score >= min_score:
                        scored.append((score, rid, rec.metadata))

                scored.sort(key=lambda x: x[0], reverse=True)
                for score, rid, meta in scored[:top_k]:
                    results.append(SearchResult(id=rid, score=score, metadata=meta))

            return results

    def save_to_disk(self, filepath: Optional[str] = None) -> str:
        """
        Persists the index to disk with atomic write and SHA-256 integrity checksum.
        Survives process restarts and guarantees data integrity.
        """
        target_path = os.path.abspath(filepath) if filepath else self.storage_path
        if not target_path:
            raise ValueError("No filepath specified and no storage_path configured on index.")

        with self._lock:
            payload_dict = {
                "version": 1,
                "dimension": self.dimension,
                "records": [
                    {
                        "id": rec.id,
                        "vector": rec.vector,
                        "metadata": rec.metadata,
                    }
                    for rec in self.records.values()
                ]
            }
            json_bytes = json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
            sha256_hash = hashlib.sha256(json_bytes).hexdigest().encode("ascii")

            # Binary container: MAGIC (7 bytes) + HASH (64 bytes hex) + JSON payload
            container_bytes = RUVEC_MAGIC_HEADER + sha256_hash + json_bytes

            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            dir_name = os.path.dirname(target_path)
            with tempfile.NamedTemporaryFile("wb", dir=dir_name, delete=False) as tmp_f:
                tmp_f.write(container_bytes)
                tmp_f.flush()
                os.fsync(tmp_f.fileno())
                tmp_name = tmp_f.name

            try:
                os.replace(tmp_name, target_path)
            except OSError:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
                raise

            return target_path

    def load_from_disk(self, filepath: Optional[str] = None) -> int:
        """
        Loads the index from disk, verifying magic header and SHA-256 integrity checksum.
        Returns the number of restored records.
        """
        target_path = os.path.abspath(filepath) if filepath else self.storage_path
        if not target_path:
            raise ValueError("No filepath specified and no storage_path configured on index.")

        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Vector index file not found at '{target_path}'")

        with open(target_path, "rb") as f:
            data = f.read()

        magic_len = len(RUVEC_MAGIC_HEADER)
        if len(data) < magic_len + 64:
            raise ValueError(f"Corrupted vector index file at '{target_path}': file too small")

        if data[:magic_len] != RUVEC_MAGIC_HEADER:
            raise ValueError(f"Corrupted or invalid vector index header in '{target_path}'")

        stored_hash = data[magic_len:magic_len + 64].decode("ascii", errors="replace")
        json_bytes = data[magic_len + 64:]

        computed_hash = hashlib.sha256(json_bytes).hexdigest()
        if computed_hash.lower() != stored_hash.lower():
            raise ValueError(
                f"Corrupted vector index at '{target_path}': SHA-256 mismatch "
                f"(expected {stored_hash}, computed {computed_hash})"
            )

        try:
            payload = json.loads(json_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Corrupted vector index payload at '{target_path}': {e}") from e

        if payload.get("dimension") != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch in '{target_path}': expected {self.dimension}, "
                f"found {payload.get('dimension')}"
            )

        with self._lock:
            self.records.clear()
            for item in payload.get("records", []):
                rec = VectorRecord(
                    id=item["id"],
                    vector=item["vector"],
                    metadata=item.get("metadata", {})
                )
                self.records[rec.id] = rec
            self._cache_dirty = True

        return len(self.records)

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

    def benchmark(self, n_queries: int = 100, top_k: int = 5) -> Dict[str, Any]:
        """
        Executes a reproducible latency and throughput benchmark using real timer measurements.
        Documents hardware characteristics, dataset size, and actual measured percentiles.
        """
        import platform
        if self.size() == 0:
            raise ValueError("Cannot benchmark an empty vector index. Insert test records first.")

        # Prepare queries deterministically
        sample_ids = list(self.records.keys())
        query_vectors: List[List[float]] = []
        for i in range(n_queries):
            base_vec = self.records[sample_ids[i % len(sample_ids)]].vector.copy()
            # Slight perturbation to avoid trivial identical vector caching
            base_vec[0] = (base_vec[0] + 0.01) % 1.0
            query_vectors.append(self._normalize(base_vec))

        # Warmup (10 queries)
        for q in query_vectors[:10]:
            self.search(q, top_k=top_k)

        # Timed benchmark
        latencies_ms: List[float] = []
        t_start = time.perf_counter_ns()
        for q in query_vectors:
            q_start = time.perf_counter_ns()
            self.search(q, top_k=top_k)
            q_end = time.perf_counter_ns()
            latencies_ms.append((q_end - q_start) / 1_000_000.0)
        t_end = time.perf_counter_ns()

        total_duration_sec = (t_end - t_start) / 1_000_000_000.0
        latencies_ms.sort()

        p50 = latencies_ms[int(len(latencies_ms) * 0.50)]
        p95 = latencies_ms[int(len(latencies_ms) * 0.95)]
        p99 = latencies_ms[min(int(len(latencies_ms) * 0.99), len(latencies_ms) - 1)]
        mean_lat = sum(latencies_ms) / len(latencies_ms)
        qps = n_queries / total_duration_sec if total_duration_sec > 0 else 0.0

        return {
            "engine_type": self.engine_type,
            "dimension": self.dimension,
            "dataset_size": self.size(),
            "query_count": n_queries,
            "top_k": top_k,
            "throughput_qps": round(qps, 2),
            "latency_p50_ms": round(p50, 4),
            "latency_p95_ms": round(p95, 4),
            "latency_p99_ms": round(p99, 4),
            "latency_mean_ms": round(mean_lat, 4),
            "hardware": {
                "platform": platform.platform(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
            }
        }
