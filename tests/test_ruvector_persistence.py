"""
RuVector Comprehensive Persistence, Numeric Validation, and Benchmark Test Suite.
Verifies real disk persistence, restart survivability, SHA-256 tamper detection,
dimension enforcement, finite number checks, thread safety, and empirical benchmarking.
"""

import math
import os
import threading
import pytest
from modules.sparc.ruvector import RuVectorEngine, VectorRecord


@pytest.fixture
def temp_index_file(tmp_path):
    return str(tmp_path / "ruvec_test.bin")


def test_ruvector_insert_and_deterministic_search():
    """Verifies cosine similarity calculation and top-k ranking."""
    engine = RuVectorEngine(dimension=4)
    engine.insert("doc1", [1.0, 0.0, 0.0, 0.0], {"title": "Doc 1"})
    engine.insert("doc2", [0.0, 1.0, 0.0, 0.0], {"title": "Doc 2"})
    engine.insert("doc3", [0.7071, 0.7071, 0.0, 0.0], {"title": "Doc 3"})

    assert engine.size() == 3

    # Query closest to doc1
    results = engine.search([1.0, 0.0, 0.0, 0.0], top_k=2)
    assert len(results) == 2
    assert results[0].id == "doc1"
    assert math.isclose(results[0].score, 1.0, abs_tol=1e-4)
    assert results[1].id == "doc3"
    assert results[1].score > 0.7


def test_ruvector_dimension_validation():
    """Verifies that vector dimension mismatch raises ValueError."""
    engine = RuVectorEngine(dimension=4)

    with pytest.raises(ValueError, match="Vector dimension mismatch"):
        engine.insert("bad_dim", [1.0, 2.0])

    with pytest.raises(ValueError, match="Vector dimension mismatch"):
        engine.search([1.0, 2.0, 3.0, 4.0, 5.0])


def test_ruvector_finite_numeric_validation():
    """Verifies that NaN, Inf, and non-numeric values are rejected."""
    engine = RuVectorEngine(dimension=3)

    # NaN rejection
    with pytest.raises(ValueError, match="non-finite value"):
        engine.insert("nan_vec", [1.0, float("nan"), 0.0])

    # Infinity rejection
    with pytest.raises(ValueError, match="non-finite value"):
        engine.insert("inf_vec", [1.0, float("inf"), 0.0])

    # Non-numeric type rejection
    with pytest.raises(TypeError, match="not a numeric float/int"):
        engine.insert("str_vec", [1.0, "invalid", 0.0])


def test_ruvector_empty_and_null_inputs():
    """Verifies that empty IDs and None vectors fail closed."""
    engine = RuVectorEngine(dimension=3)

    with pytest.raises(ValueError, match="record_id must be a non-empty string"):
        engine.insert("", [1.0, 0.0, 0.0])

    with pytest.raises(ValueError, match="Vector cannot be None"):
        engine.insert("valid_id", None)


def test_ruvector_disk_persistence_and_restart(temp_index_file):
    """Verifies that indexed vectors, IDs, and metadata survive process restarts."""
    dim = 20
    engine_writer = RuVectorEngine(dimension=dim, storage_path=temp_index_file)

    for i in range(20):
        vec = [0.0] * dim
        vec[i] = 1.0  # Unique one-hot vector for each item
        engine_writer.insert(f"rec_{i}", vec, {"index": i, "tag": f"item_{i}"})

    assert engine_writer.size() == 20
    saved_path = engine_writer.save_to_disk()
    assert os.path.exists(saved_path)

    # Simulate fresh restart with a new engine instance loading from file
    engine_reader = RuVectorEngine(dimension=dim, storage_path=temp_index_file)
    assert engine_reader.size() == 20

    # Verify record content and metadata fidelity
    rec0 = engine_reader.get("rec_0")
    assert rec0 is not None
    assert rec0.metadata.get("index") == 0
    assert rec0.metadata.get("tag") == "item_0"

    # Verify search recall on restored index (rec_0 should be strictly top 1)
    query = [1.0] + [0.0] * (dim - 1)
    results = engine_reader.search(query, top_k=3)
    assert len(results) >= 1
    assert results[0].id == "rec_0"
    assert math.isclose(results[0].score, 1.0, abs_tol=1e-4)


def test_ruvector_file_corruption_detection(temp_index_file):
    """Verifies that file tampering and checksum mismatches are caught."""
    engine = RuVectorEngine(dimension=4, storage_path=temp_index_file)
    engine.insert("test_1", [1.0, 0.0, 0.0, 0.0], {"meta": "val"})
    engine.save_to_disk()

    # Tamper with file: corrupt one byte in the JSON payload
    with open(temp_index_file, "r+b") as f:
        f.seek(-5, os.SEEK_END)
        f.write(b"X")

    tampered_engine = RuVectorEngine(dimension=4)
    with pytest.raises(ValueError, match="Corrupted vector index"):
        tampered_engine.load_from_disk(temp_index_file)


def test_ruvector_concurrency():
    """Verifies thread safety during concurrent insertions and queries."""
    engine = RuVectorEngine(dimension=4)
    errors = []

    def worker(worker_id: int):
        try:
            for i in range(25):
                rec_id = f"w{worker_id}_{i}"
                vec = [float(worker_id + 1), float(i), 0.5, 0.1]
                engine.insert(rec_id, vec, {"w": worker_id, "i": i})
                results = engine.search([1.0, 1.0, 0.5, 0.1], top_k=2)
                assert len(results) > 0
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    assert engine.size() == 100


def test_ruvector_benchmark_execution():
    """Verifies benchmark executes real timers and reports non-zero throughput."""
    engine = RuVectorEngine(dimension=16)
    for i in range(50):
        vec = [(i + j) % 10 * 0.1 for j in range(16)]
        engine.insert(f"item_{i}", vec, {"num": i})

    report = engine.benchmark(n_queries=30, top_k=5)
    assert report["dataset_size"] == 50
    assert report["query_count"] == 30
    assert report["throughput_qps"] > 0
    assert report["latency_p50_ms"] >= 0
    assert report["latency_mean_ms"] >= 0
    assert "platform" in report["hardware"]


def test_ruvector_text_embedding_cross_process_reproducibility():
    """
    CRITICAL DETERMINISM CHECK:
    Verifies that embed_text_deterministic produces identical vector outputs across
    different Python process restarts and different PYTHONHASHSEED seeds (SHA-256 backed).
    """
    import subprocess
    import sys
    import json

    code = (
        "import json, sys\n"
        "from modules.sparc.ruvector import RuVectorEngine\n"
        "engine = RuVectorEngine(dimension=16)\n"
        "vec = engine.embed_text_deterministic('institutional market portfolio allocation')\n"
        "sys.stdout.write(json.dumps(vec))\n"
    )

    env1 = dict(os.environ, PYTHONHASHSEED="42")
    env2 = dict(os.environ, PYTHONHASHSEED="999999")

    out1 = subprocess.check_output([sys.executable, "-c", code], env=env1).decode("utf-8")
    out2 = subprocess.check_output([sys.executable, "-c", code], env=env2).decode("utf-8")

    vec1 = json.loads(out1)
    vec2 = json.loads(out2)

    assert len(vec1) == 16
    assert len(vec2) == 16
    assert vec1 == vec2, "Text embeddings differed across Python process seeds!"
