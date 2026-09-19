"""
AARKAAI Production Operational Tooling – Multi-Tier Rate Limiter (Gate 3).

Features:
- Sliding-window precision per IP, User, Code Mode, and MCP Tool.
- Redis-backed distributed sliding window across Gunicorn/Uvicorn multi-workers.
- Clean 429 calculation with exact Retry-After seconds.
- Memory leak free with automatic window expiration and eviction.
"""
from __future__ import annotations

import os
import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("aarkaai.rate_limiter")


class RateLimitExceededError(Exception):
    def __init__(self, key: str, limit: int, retry_after: int):
        super().__init__(f"Rate limit exceeded for '{key}' ({limit} req/window). Retry after {retry_after}s.")
        self.key = key
        self.limit = limit
        self.retry_after = retry_after


class BaseRateLimiter(ABC):
    @abstractmethod
    def check(self, key: str, limit: int, window_seconds: float = 60.0) -> Tuple[bool, int, int]:
        """Returns: (is_allowed, remaining_calls, retry_after_seconds)"""
        pass

    def enforce(self, key: str, limit: int, window_seconds: float = 60.0) -> None:
        allowed, remaining, retry_after = self.check(key, limit, window_seconds)
        if not allowed:
            raise RateLimitExceededError(key, limit, retry_after)


class SlidingWindowRateLimiter(BaseRateLimiter):
    """In-memory sliding window rate limiter. Process-local (not shared across workers)."""

    def __init__(self):
        self._windows: Dict[str, List[float]] = defaultdict(list)
        self._cleanup_counter = 0

    def check(self, key: str, limit: int, window_seconds: float = 60.0) -> Tuple[bool, int, int]:
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


class RedisRateLimiter(BaseRateLimiter):
    """Distributed Redis-backed sliding window rate limiter for multi-worker production deployments."""

    def __init__(self, redis_client):
        self._redis = redis_client

    def check(self, key: str, limit: int, window_seconds: float = 60.0) -> Tuple[bool, int, int]:
        now = time.time()
        cutoff = now - window_seconds
        redis_key = f"rl:op:{key}"

        try:
            pipe = self._redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, cutoff)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, int(window_seconds) + 2)
            results = pipe.execute()
            current_count = results[1]

            if current_count >= limit:
                # Rollback current insertion
                self._redis.zrem(redis_key, str(now))
                oldest_entries = self._redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest_entries:
                    oldest_time = float(oldest_entries[0][1])
                    retry_after = max(1, int(oldest_time + window_seconds - now))
                else:
                    retry_after = int(window_seconds)
                return False, 0, retry_after

            remaining = max(0, limit - (current_count + 1))
            return True, remaining, 0
        except Exception as exc:
            logger.warning("RedisRateLimiter failure: %s. Falling back to permit-through.", exc)
            return True, limit, 0


def get_rate_limiter() -> BaseRateLimiter:
    """
    Factory: returns RedisRateLimiter if REDIS_URL is configured and reachable,
    otherwise returns the process-local SlidingWindowRateLimiter with a logged warning.
    """
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis
            client = redis.from_url(redis_url, socket_connect_timeout=1)
            client.ping()
            logger.info("Operational rate limiter: connected to Redis backend (%s)", redis_url)
            return RedisRateLimiter(client)
        except Exception as e:
            logger.warning(
                "Operational rate limiter: Redis configured at %s but unreachable (%s). "
                "Falling back to process-local SlidingWindowRateLimiter. "
                "Warning: In multi-worker deployments (gunicorn -w 4), rate limits are not globally shared.",
                redis_url, e
            )
    else:
        logger.info(
            "Operational rate limiter: REDIS_URL not set; using process-local SlidingWindowRateLimiter."
        )

    return SlidingWindowRateLimiter()


# Global singleton instance
rate_limiter: BaseRateLimiter = get_rate_limiter()

