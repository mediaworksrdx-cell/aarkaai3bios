"""
AARKAAI Backend – Production Middleware Stack

- API Key Authentication
- Rate Limiting (sliding window per IP)
- Request ID Tracking
"""
from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config import (
    API_KEY,
    API_KEY_HEADER,
    IS_PRODUCTION,
    PUBLIC_ROUTES,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_RPM,
)

logger = logging.getLogger(__name__)


# ─── API Key Authentication ──────────────────────────────────────────────────


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Validates the X-API-Key header on all non-public routes.
    Disabled when API_KEY is empty (development mode).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip if no API key is configured (dev mode)
        if not API_KEY:
            return await call_next(request)

        # Skip public routes
        path = request.url.path
        is_public = path in PUBLIC_ROUTES or any(path.startswith(r + "/") for r in PUBLIC_ROUTES if r != "/")
        if is_public:
            return await call_next(request)

        # Skip OPTIONS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Validate key or Authorization header
        provided_key = request.headers.get(API_KEY_HEADER, "")
        auth_header = request.headers.get("Authorization", "")
        has_bearer = auth_header.startswith("Bearer ")

        if provided_key != API_KEY and not has_bearer:
            logger.warning(
                "Unauthorized request to %s from %s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid or missing API key or Bearer token."},
            )

        return await call_next(request)


# ─── Rate Limiting ───────────────────────────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter per client IP.
    Limits requests to RATE_LIMIT_RPM per 60-second window.
    
    Uses Redis if available (shared across workers), falls back to
    in-memory per-process limiting with conservative multiplier.
    """

    def __init__(self, app, rpm: int = RATE_LIMIT_RPM):
        super().__init__(app)
        self.rpm = rpm
        self.window = 60.0  # seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._redis = None
        self._redis_checked = False
        # Stricter limits for auth endpoints
        self._auth_rpm = max(5, rpm // 6)
        # Periodic cleanup counter
        self._cleanup_counter = 0

    def _get_redis(self):
        """Lazy-init Redis connection; returns None if unavailable."""
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        try:
            import redis as redis_lib
            import os
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
            self._redis = redis_lib.from_url(redis_url, socket_connect_timeout=1)
            self._redis.ping()
            logger.info("Rate limiter: using Redis backend (%s)", redis_url)
        except Exception:
            self._redis = None
            logger.info("Rate limiter: Redis unavailable, using in-memory fallback")
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path

        # Skip health checks from rate limiting
        if path in {"/health", "/"}:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self.window

        # Use stricter limit for auth endpoints
        is_auth = path.startswith("/auth/")
        effective_rpm = self._auth_rpm if is_auth else self.rpm

        # Try Redis first
        r = self._get_redis()
        if r is not None:
            try:
                key = f"rl:{client_ip}:{path}" if is_auth else f"rl:{client_ip}"
                pipe = r.pipeline()
                pipe.zremrangebyscore(key, 0, cutoff)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, int(self.window) + 1)
                results = pipe.execute()
                current_count = results[1]

                if current_count >= effective_rpm:
                    r.zrem(key, str(now))  # rollback the added entry
                    retry_after = int(self.window)
                    logger.warning(
                        "Rate limit exceeded for %s on %s (%d/%d RPM)",
                        client_ip, path, current_count, effective_rpm,
                    )
                    return JSONResponse(
                        status_code=429,
                        content={"detail": f"Rate limit exceeded. Try again in {retry_after}s."},
                        headers={"Retry-After": str(retry_after)},
                    )
                return await call_next(request)
            except Exception as exc:
                logger.warning("Redis rate limit error (falling back): %s", exc)
                # Fall through to in-memory

        # In-memory fallback
        # Periodic cleanup of stale IPs every 100 requests
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            stale_ips = [ip for ip, ts in self._requests.items() if not ts or ts[-1] < cutoff]
            for ip in stale_ips:
                del self._requests[ip]

        # Clean old entries for this IP
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > cutoff
        ]

        if len(self._requests[client_ip]) >= effective_rpm:
            retry_after = int(self._requests[client_ip][0] + self.window - now) + 1
            logger.warning(
                "Rate limit exceeded for %s (%d/%d RPM)",
                client_ip,
                len(self._requests[client_ip]),
                effective_rpm,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. Try again in {retry_after}s."},
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


# ─── Request Logging & Tracking ──────────────────────────────────────────────


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique request ID and logs request/response timing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = round(time.perf_counter() - start, 3)
            logger.error(
                "[%s] %s %s → 500 (%.3fs) ERROR: %s",
                request_id,
                request.method,
                request.url.path,
                elapsed,
                exc,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )

        elapsed = round(time.perf_counter() - start, 3)

        # Only log non-trivial routes
        if request.url.path not in {"/health", "/favicon.ico"}:
            logger.info(
                "[%s] %s %s → %d (%.3fs)",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = str(elapsed)
        return response


# ─── Response Caching ────────────────────────────────────────────────────────


import hashlib
import json

class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Caches JSON responses for POST /prompt using Redis.
    """
    def __init__(self, app):
        super().__init__(app)
        self._redis = None
        self._redis_checked = False

    def _get_redis(self):
        """Lazy-init Redis connection; returns None if unavailable."""
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        try:
            import redis as redis_lib
            import os
            redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
            self._redis = redis_lib.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
            self._redis.ping()
            logger.info("Response Cache: using Redis backend (%s)", redis_url)
        except Exception:
            self._redis = None
            logger.info("Response Cache: Redis unavailable, caching disabled")
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only apply to POST /prompt requests
        if request.method != "POST" or request.url.path != "/prompt":
            return await call_next(request)

        r = self._get_redis()
        if r is None:
            return await call_next(request)

        # Extract request body and compute cache key
        body_bytes = await request.body()
        
        # Restore body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        cache_key = hashlib.sha256(body_bytes).hexdigest()
        redis_key = f"cache:response:{cache_key}"

        # Check Redis cache
        try:
            cached_data = r.get(redis_key)
            if cached_data:
                response = Response(content=cached_data, media_type="application/json")
                response.headers["X-Cache"] = "HIT"
                return response
        except Exception as e:
            logger.warning("Redis cache get error: %s", e)

        # Cache miss - call next
        response = await call_next(request)

        # Read response body
        body = b""
        if hasattr(response, "body_iterator"):
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                body += chunk
        
        # Store in Redis
        try:
            if response.status_code == 200:
                r.setex(redis_key, 3600, body.decode("utf-8"))
        except Exception as e:
            logger.warning("Redis cache set error: %s", e)

        # Reconstruct response with consumed content
        new_response = Response(
            content=body, 
            status_code=response.status_code, 
            media_type=response.media_type
        )
        
        # Copy headers
        for k, v in response.headers.items():
            if k.lower() != "content-length":
                new_response.headers[k] = v
                
        new_response.headers["X-Cache"] = "MISS"
        new_response.headers["Content-Length"] = str(len(body))

        return new_response
