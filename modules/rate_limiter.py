"""
AARKAAI Production Operational Tooling – Multi-Tier Rate Limiter (Gate 3).

Features:
- Sliding-window precision per IP, User, Code Mode, and MCP Tool.
- Clean 429 calculation with exact Retry-After seconds.
- Memory leak free with automatic window expiration and eviction.
"""
from __future__ import annotations

import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

logger = logging.getLogger("aarkaai.rate_limiter")


class RateLimitExceededError(Exception):
    def __init__(self, key: str, limit: int, retry_after: int):
        super().__init__(f"Rate limit exceeded for '{key}' ({limit} req/window). Retry after {retry_after}s.")
        self.key = key
        self.limit = limit
        self.retry_after = retry_after


class SlidingWindowRateLimiter:
    def __init__(self):
        self._windows: Dict[str, List[float]] = defaultdict(list)
        self._cleanup_counter = 0

    def check(self, key: str, limit: int, window_seconds: float = 60.0) -> Tuple[bool, int, int]:
        """
        Check and record a request.
        Returns: (is_allowed, remaining_calls, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds

        # Periodic cleanup of completely stale keys every 100 checks
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            stale_keys = [k for k, timestamps in self._windows.items() if not timestamps or timestamps[-1] < cutoff]
            for k in stale_keys:
                del self._windows[k]

        # Prune old timestamps for this key
        valid_timestamps = [t for t in self._windows[key] if t > cutoff]
        self._windows[key] = valid_timestamps

        current_count = len(valid_timestamps)

        if current_count >= limit:
            oldest = valid_timestamps[0] if valid_timestamps else now
            retry_after = max(1, int(oldest + window_seconds - now))
            return False, 0, retry_after

        # Record this request
        self._windows[key].append(now)
        remaining = max(0, limit - (current_count + 1))
        return True, remaining, 0

    def enforce(self, key: str, limit: int, window_seconds: float = 60.0) -> None:
        allowed, remaining, retry_after = self.check(key, limit, window_seconds)
        if not allowed:
            raise RateLimitExceededError(key, limit, retry_after)


# Global singleton instance
rate_limiter = SlidingWindowRateLimiter()
