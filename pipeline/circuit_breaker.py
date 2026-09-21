"""
AARKAAI Pipeline – Circuit Breaker & Screener Singleton

Extracted from pipeline.py lines 36-84.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


# ─── Screener Agent Singleton ────────────────────────────────────────────────
try:
    from modules.screener.agent import ScreenerAgent as _ScreenerAgentClass
    _screener_agent = _ScreenerAgentClass()
    _SCREENER_AVAILABLE = True
    logger.info("ScreenerAgent loaded successfully")
except Exception as _screener_err:
    _screener_agent = None
    _SCREENER_AVAILABLE = False
    logger.warning("ScreenerAgent unavailable: %s", _screener_err)


# ─── Circuit Breaker ─────────────────────────────────────────────────────────

class _CircuitBreaker:
    """Simple circuit breaker: disables a module after N consecutive failures."""

    def __init__(self, name: str, threshold: int = 3, cooldown: float = 300.0):
        self.name = name
        self.threshold = threshold
        self.cooldown = cooldown  # seconds before retry
        self._failures = 0
        self._last_failure = 0.0

    @property
    def is_open(self) -> bool:
        if self._failures < self.threshold:
            return False
        # Check if cooldown elapsed
        if time.time() - self._last_failure > self.cooldown:
            self._failures = 0  # Reset — allow retry
            return False
        return True

    def record_success(self):
        self._failures = 0

    def record_failure(self):
        self._failures += 1
        self._last_failure = time.time()
        if self._failures >= self.threshold:
            logger.warning(
                "Circuit breaker OPEN for '%s' after %d failures (cooldown=%ds)",
                self.name, self._failures, int(self.cooldown),
            )


_web_breaker = _CircuitBreaker("web_search", threshold=3, cooldown=300)
_finance_breaker = _CircuitBreaker("finance", threshold=3, cooldown=120)
