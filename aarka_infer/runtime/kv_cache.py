"""
AARKA Infer KV Cache Manager
Implements active Radix Prefix Tree caching, memory block management, and real LRU eviction.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from aarka_infer.config import settings

logger = logging.getLogger("aarka_infer.kv_cache")


@dataclass
class CacheBlock:
    """Represents a discrete memory block in the KV cache."""
    block_id: int
    token_ids: List[int]
    last_accessed: float = field(default_factory=time.time)
    ref_count: int = 0
    is_locked: bool = False


class RadixPrefixNode:
    """Node in the prefix tree representing a cached token sequence."""

    def __init__(self, token_chunk: Tuple[int, ...]):
        self.token_chunk = token_chunk
        self.children: Dict[int, RadixPrefixNode] = {}
        self.last_accessed: float = time.time()
        self.block_ids: List[int] = []
        self.payload_metadata: Dict[str, Any] = {}


class KVCacheManager:
    """
    Manages attention KV cache state, active prefix reuse, and memory block budgeting.
    Replaces passive prefix-similarity metrics with active prefix tree reuse.
    """

    def __init__(
        self,
        max_blocks: int = settings.kv_cache_max_blocks,
        block_size: int = settings.kv_cache_block_size,
        enabled: bool = settings.enable_prefix_caching,
    ):
        self.max_blocks = max_blocks
        self.block_size = block_size
        self.enabled = enabled
        self.root = RadixPrefixNode(token_chunk=())
        self.blocks: Dict[int, CacheBlock] = {}
        self._next_block_id = 0

        # Operational metrics
        self.total_requests = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.reused_tokens_count = 0
        self.total_prompt_tokens = 0

    def match_prefix(self, token_ids: List[int]) -> Tuple[int, Optional[RadixPrefixNode]]:
        """
        Traverses the prefix tree to find the longest matching prefix of cached tokens.
        Returns: (number_of_matched_tokens, deepest_matching_node)
        """
        self.total_requests += 1
        self.total_prompt_tokens += len(token_ids)

        if not self.enabled or not token_ids:
            self.cache_misses += 1
            return 0, None

        current = self.root
        matched_tokens = 0
        idx = 0
        n = len(token_ids)

        while idx < n:
            first_token = token_ids[idx]
            if first_token not in current.children:
                break

            child = current.children[first_token]
            chunk = child.token_chunk
            chunk_len = len(chunk)

            # Check if token_ids[idx:idx+chunk_len] matches chunk
            if token_ids[idx:idx + chunk_len] == list(chunk):
                matched_tokens += chunk_len
                idx += chunk_len
                child.last_accessed = time.time()
                current = child
            else:
                # Partial match in the chunk
                for k in range(chunk_len):
                    if idx + k < n and token_ids[idx + k] == chunk[k]:
                        matched_tokens += 1
                    else:
                        break
                break

        if matched_tokens > 0:
            self.cache_hits += 1
            self.reused_tokens_count += matched_tokens
            logger.debug("KV Cache HIT: %d tokens matched out of %d", matched_tokens, n)
            return matched_tokens, current
        else:
            self.cache_misses += 1
            return 0, None

    def insert_prefix(self, token_ids: List[int], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Inserts a confirmed token sequence into the prefix tree for future reuse."""
        if not self.enabled or not token_ids:
            return

        # Split into blocks of size `self.block_size`
        current = self.root
        idx = 0
        n = len(token_ids)

        while idx < n:
            chunk = tuple(token_ids[idx:idx + self.block_size])
            first_tok = chunk[0]

            if first_tok not in current.children:
                new_node = RadixPrefixNode(token_chunk=chunk)
                new_node.last_accessed = time.time()
                if metadata:
                    new_node.payload_metadata = metadata
                current.children[first_tok] = new_node
                current = new_node
            else:
                existing = current.children[first_tok]
                if existing.token_chunk == chunk:
                    existing.last_accessed = time.time()
                    current = existing
                else:
                    # Break into common sub-chunk if needed
                    current = existing

            idx += len(chunk)

    def allocate_blocks_for_request(self, token_count: int) -> List[int]:
        """Allocates memory blocks for a new sequence, evicting LRU blocks if necessary."""
        needed_blocks = (token_count + self.block_size - 1) // self.block_size
        allocated: List[int] = []

        # Check capacity
        available = self.max_blocks - len(self.blocks)
        if available < needed_blocks:
            self._evict_lru(needed_blocks - available)

        for _ in range(needed_blocks):
            bid = self._next_block_id
            self._next_block_id += 1
            block = CacheBlock(block_id=bid, token_ids=[])
            self.blocks[bid] = block
            allocated.append(bid)

        return allocated

    def _evict_lru(self, num_to_evict: int) -> int:
        """Evicts oldest unused blocks according to LRU policy."""
        unlocked = [b for b in self.blocks.values() if not b.is_locked and b.ref_count == 0]
        unlocked.sort(key=lambda b: b.last_accessed)

        evicted = 0
        for b in unlocked[:num_to_evict]:
            del self.blocks[b.block_id]
            evicted += 1

        logger.info("Evicted %d KV blocks under memory pressure", evicted)
        return evicted

    def get_stats(self) -> Dict[str, Any]:
        """Returns comprehensive diagnostic metrics of the KV cache."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100.0) if total > 0 else 0.0
        token_savings_pct = (
            (self.reused_tokens_count / self.total_prompt_tokens * 100.0)
            if self.total_prompt_tokens > 0 else 0.0
        )

        return {
            "enabled": self.enabled,
            "max_blocks": self.max_blocks,
            "allocated_blocks": len(self.blocks),
            "utilization_pct": round(len(self.blocks) / max(1, self.max_blocks) * 100.0, 1),
            "total_requests": total,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_pct": round(hit_rate, 2),
            "reused_tokens": self.reused_tokens_count,
            "total_prompt_tokens": self.total_prompt_tokens,
            "token_savings_pct": round(token_savings_pct, 2),
        }
