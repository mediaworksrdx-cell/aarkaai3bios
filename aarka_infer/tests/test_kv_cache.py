"""
Test suite for AARKA Infer KV Cache Manager and Radix Prefix Tree.
"""
import pytest
from aarka_infer.runtime.kv_cache import KVCacheManager


def test_prefix_caching_hit_and_miss():
    kv = KVCacheManager(max_blocks=100, block_size=4, enabled=True)

    # Empty cache should be a miss
    prompt1 = [101, 102, 103, 104, 105, 106, 107, 108]
    matched, node = kv.match_prefix(prompt1)
    assert matched == 0
    assert node is None

    # Insert prompt1 into prefix tree
    kv.insert_prefix(prompt1)

    # Subsequent request with identical prefix should match
    prompt2 = [101, 102, 103, 104, 105, 106, 107, 108, 999, 1000]
    matched2, node2 = kv.match_prefix(prompt2)
    assert matched2 == 8
    assert node2 is not None

    stats = kv.get_stats()
    assert stats["cache_hits"] == 1
    assert stats["cache_misses"] == 1
    assert stats["reused_tokens"] == 8
    assert stats["hit_rate_pct"] == 50.0


def test_block_allocation_and_eviction():
    kv = KVCacheManager(max_blocks=10, block_size=4)
    blocks = kv.allocate_blocks_for_request(token_count=16)
    assert len(blocks) == 4

    stats = kv.get_stats()
    assert stats["allocated_blocks"] == 4
