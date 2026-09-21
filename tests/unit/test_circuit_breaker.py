"""
Unit tests for the CircuitBreaker class.
"""
import time
import pytest


class TestCircuitBreaker:
    def _make(self, threshold=3, cooldown=300.0):
        from pipeline.circuit_breaker import _CircuitBreaker
        return _CircuitBreaker("test", threshold=threshold, cooldown=cooldown)

    def test_starts_closed(self):
        cb = self._make()
        assert not cb.is_open

    def test_opens_after_threshold_failures(self):
        cb = self._make(threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert not cb.is_open  # 2 failures — not yet open
        cb.record_failure()
        assert cb.is_open  # 3 failures — now open

    def test_success_resets_failure_count(self):
        cb = self._make(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()
        assert not cb.is_open  # Only 2 failures since last success

    def test_closes_after_cooldown(self):
        cb = self._make(threshold=1, cooldown=0.05)
        cb.record_failure()
        assert cb.is_open
        time.sleep(0.1)
        assert not cb.is_open  # Cooldown elapsed — auto-reset

    def test_resets_failure_count_on_cooldown_check(self):
        cb = self._make(threshold=1, cooldown=0.05)
        cb.record_failure()
        time.sleep(0.1)
        _ = cb.is_open  # Triggers reset
        assert cb._failures == 0
