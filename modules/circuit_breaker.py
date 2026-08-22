"""
AARKAAI Backend – Circuit Breaker Pattern

Protects the system from cascading failures when external services
(web search, finance APIs, Google CSE, etc.) become unavailable.

Usage:
    breaker = CircuitBreaker(name="web_search", failure_threshold=5, recovery_timeout=120.0)
    
    if breaker.is_open:
        return fallback_response()
    
    try:
        result = call_external_service()
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        return fallback_response()
"""
from __future__ import annotations

import logging
import time
import threading
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation, requests pass through
    OPEN = "open"            # Failures exceeded threshold, requests blocked
    HALF_OPEN = "half_open"  # Recovery period, testing with single request


class CircuitBreaker:
    """Thread-safe circuit breaker for external service calls.
    
    Args:
        name: Identifier for this circuit (used in logs).
        failure_threshold: Number of consecutive failures before opening.
        recovery_timeout: Seconds to wait before transitioning to half-open.
        success_threshold: Successes in half-open state to close the circuit.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 120.0,
        success_threshold: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Current circuit state, with automatic half-open transition."""
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and self._last_failure_time is not None
                and (time.time() - self._last_failure_time) >= self.recovery_timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info(
                    "CircuitBreaker[%s]: OPEN -> HALF_OPEN (recovery timeout elapsed)",
                    self.name,
                )
            return self._state
    
    @property
    def is_open(self) -> bool:
        """True if requests should be blocked (circuit is open)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """True if requests should pass through normally."""
        return self.state == CircuitState.CLOSED
    
    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(
                        "CircuitBreaker[%s]: HALF_OPEN -> CLOSED (recovery confirmed)",
                        self.name,
                    )
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0  # Reset consecutive failure count
    
    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens immediately
                self._state = CircuitState.OPEN
                logger.warning(
                    "CircuitBreaker[%s]: HALF_OPEN -> OPEN (failure during recovery)",
                    self.name,
                )
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self.failure_threshold
            ):
                self._state = CircuitState.OPEN
                logger.warning(
                    "CircuitBreaker[%s]: CLOSED -> OPEN (%d consecutive failures)",
                    self.name,
                    self._failure_count,
                )
    
    def reset(self) -> None:
        """Manually reset the circuit to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info("CircuitBreaker[%s]: Manually reset to CLOSED", self.name)
    
    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, state={self._state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )


# ─── Pre-configured breakers for known external services ──────────────────

_breakers: dict[str, CircuitBreaker] = {}
_breakers_lock = threading.Lock()


def get_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 120.0,
) -> CircuitBreaker:
    """Get or create a named circuit breaker singleton."""
    with _breakers_lock:
        if name not in _breakers:
            _breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        return _breakers[name]
