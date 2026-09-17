"""
tests/unit/test_canary_router.py
Unit tests for the CanaryRouter and staged rollout controller.
"""

import pytest
from modules.canary_router import CanaryRouter, CanaryStage, StageTelemetry


def test_canary_initial_state():
    router = CanaryRouter()
    assert router.stage == CanaryStage.STAGE_0_DISABLED
    assert router.circuit_broken is False
    assert router.rollback_reason is None
    # Routing should be False when stage is 0
    assert router.should_route_to_canary("user1", "sess1") is False


def test_deterministic_hashing():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_2_CANARY_5PCT)
    # The same user and session ID must consistently yield the exact same decision
    decision1 = router.should_route_to_canary("alice_user", "session_abc")
    decision2 = router.should_route_to_canary("alice_user", "session_abc")
    assert decision1 == decision2


def test_traffic_distribution_proportions():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_3_CANARY_25PCT)
    routed_count = 0
    total = 1000

    for i in range(total):
        if router.should_route_to_canary(f"user_{i}", f"session_{i}"):
            routed_count += 1

    # At 25%, routed count should be reasonably close to 250 (e.g. 200 - 300)
    assert 200 <= routed_count <= 300


def test_100_percent_production_cutover():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_4_PRODUCTION_100PCT)
    for i in range(50):
        assert router.should_route_to_canary(f"user_{i}", f"session_{i}") is True


def test_stage_advancement_and_health():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_1_CANARY_1PCT)
    # Record 10 healthy requests
    for _ in range(10):
        router.record_request("u1", "s1", routed_to_canary=True, success=True, duration_s=0.5)

    healthy, reason = router.check_health()
    assert healthy is True
    assert reason is None

    # Advance to Stage 2 (5%)
    advanced, msg = router.advance_stage(CanaryStage.STAGE_2_CANARY_5PCT)
    assert advanced is True
    assert router.stage == CanaryStage.STAGE_2_CANARY_5PCT


def test_circuit_breaker_on_error_rate_spike():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_2_CANARY_5PCT)
    # Inject healthy baseline
    for _ in range(5):
        router.record_request("u", "s", routed_to_canary=True, success=True, duration_s=0.5)

    # Inject error spike (2 errors out of 7 requests = 28.5% error rate > 1% threshold)
    router.record_request("u", "s", routed_to_canary=True, success=False, duration_s=0.5)
    router.record_request("u", "s", routed_to_canary=True, success=False, duration_s=0.5)

    # Circuit breaker must be tripped
    assert router.circuit_broken is True
    assert router.stage == CanaryStage.STAGE_0_DISABLED
    assert "Error rate breach" in router.rollback_reason
    # Subsequent requests must route to baseline (False)
    assert router.should_route_to_canary("u", "s") is False


def test_circuit_breaker_on_security_violation():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_3_CANARY_25PCT)
    for _ in range(5):
        router.record_request("u", "s", routed_to_canary=True, success=True, duration_s=0.5)

    # Inject security violation
    router.record_request(
        "attacker", "sess_x",
        routed_to_canary=True,
        success=False,
        duration_s=0.1,
        security_violation=True
    )

    assert router.circuit_broken is True
    assert router.stage == CanaryStage.STAGE_0_DISABLED
    assert "Security policy anomaly" in router.rollback_reason


def test_rearm_after_trip():
    router = CanaryRouter(initial_stage=CanaryStage.STAGE_1_CANARY_1PCT)
    router.trigger_canary_rollback("Manual drill test")
    assert router.circuit_broken is True

    # Rearm
    router.rearm_canary(target_stage=CanaryStage.STAGE_1_CANARY_1PCT)
    assert router.circuit_broken is False
    assert router.stage == CanaryStage.STAGE_1_CANARY_1PCT
    assert router.rollback_reason is None
