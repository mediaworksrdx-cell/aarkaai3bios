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
        if request.url.path in PUBLIC_ROUTES:
            return await call_next(request)

        # Skip OPTIONS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Validate key
        provided_key = request.headers.get(API_KEY_HEADER, "")
        if provided_key != API_KEY:
            logger.warning(
                "Unauthorized request to %s from %s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)


# ─── Rate Limiting ───────────────────────────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter per client IP.
    Limits requests to RATE_LIMIT_RPM per 60-second window.
    """

    def __init__(self, app, rpm: int = RATE_LIMIT_RPM):
        super().__init__(app)
        self.rpm = rpm
        self.window = 60.0  # seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)

        # Skip health checks from rate limiting
        if request.url.path in {"/health", "/"}:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - self.window

        # Clean old entries
        self._requests[client_ip] = [
            t for t in self._requests[client_ip] if t > cutoff
        ]

        if len(self._requests[client_ip]) >= self.rpm:
            retry_after = int(self._requests[client_ip][0] + self.window - now) + 1
            logger.warning(
                "Rate limit exceeded for %s (%d/%d RPM)",
                client_ip,
                len(self._requests[client_ip]),
                self.rpm,
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
