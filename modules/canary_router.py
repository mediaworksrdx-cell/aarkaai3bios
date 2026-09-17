"""
modules/canary_router.py
Production Canary Traffic Router and Multi-Stage Rollout Controller.

Manages deterministic, hash-partitioned traffic routing across the 4 canary stages:
  - Stage 1: 1% Canary Phase
  - Stage 2: 5% Canary Phase
  - Stage 3: 25% Canary Phase
  - Stage 4: 100% General Production Cutover

Integrates real-time SLA tracking, automated health verification, and instant
fail-closed circuit-breaker rollback upon SLA breach or security anomaly.
"""

import enum
import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from modules.alerting import AlertManager
from modules.metrics import (
    CODE_MODE_EXECUTIONS,
    CODE_MODE_DURATION,
    SECURITY_VIOLATIONS,
)
from modules.rollback_automation import rollback_controller

logger = logging.getLogger(__name__)


class CanaryStage(enum.IntEnum):
    """Canary progression stages with percentage allocation."""
    STAGE_0_DISABLED = 0
    STAGE_1_CANARY_1PCT = 1
    STAGE_2_CANARY_5PCT = 5
    STAGE_3_CANARY_25PCT = 25
    STAGE_4_PRODUCTION_100PCT = 100


@dataclass
class StageTelemetry:
    """Telemetry counters for a specific canary stage."""
    total_requests: int = 0
    canary_routed: int = 0
    baseline_routed: int = 0
    success_count: int = 0
    error_count: int = 0
    security_violations: int = 0
    latencies: list[float] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        if self.canary_routed == 0:
            return 0.0
        return self.error_count / self.canary_routed

    @property
    def p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(0.95 * len(sorted_latencies))
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]


class CanaryRouter:
    """
    Manages deterministic user/session routing, progressive canary stages,
    and automatic circuit breaker rollback.
    """

    def __init__(self, initial_stage: CanaryStage = CanaryStage.STAGE_0_DISABLED):
        self.stage = initial_stage
        self.telemetry: dict[CanaryStage, StageTelemetry] = {
            s: StageTelemetry() for s in CanaryStage
        }
        self.circuit_broken = False
        self.rollback_reason: Optional[str] = None
        self._salt = "aarkaa_canary_v1_deterministic_salt"

    def should_route_to_canary(self, user_id: str, session_id: str) -> bool:
        """
        Deterministically decide if a request is routed to the hardened canary runtime.
        Uses SHA-256 hash partitioning to ensure sticky session behavior.
        """
        if self.circuit_broken or self.stage == CanaryStage.STAGE_0_DISABLED:
            return False

        if self.stage == CanaryStage.STAGE_4_PRODUCTION_100PCT:
            return True

        # Consistent hash partition between 0 and 99
        hash_input = f"{self._salt}:{user_id}:{session_id}".encode("utf-8")
        hash_val = int(hashlib.sha256(hash_input).hexdigest()[:8], 16)
        partition = hash_val % 100

        return partition < int(self.stage)

    def record_request(
        self,
        user_id: str,
        session_id: str,
        routed_to_canary: bool,
        success: bool,
        duration_s: float,
        security_violation: bool = False,
    ):
        """Record traffic and health metrics for the current active stage."""
        tel = self.telemetry[self.stage]
        tel.total_requests += 1

        if routed_to_canary:
            tel.canary_routed += 1
            if success:
                tel.success_count += 1
            else:
                tel.error_count += 1
            tel.latencies.append(duration_s)

            if security_violation:
                tel.security_violations += 1

            # Check health thresholds immediately
            healthy, reason = self.check_health()
            if not healthy:
                logger.error("Canary health check failed: %s. Initiating circuit breaker.", reason)
                self.trigger_canary_rollback(reason)
        else:
            tel.baseline_routed += 1

    def check_health(self) -> tuple[bool, Optional[str]]:
        """
        Evaluate health criteria:
        1. Error rate must be <= 1.0%
        2. P95 latency must be <= 5.0s
        3. Security violations must be 0
        """
        tel = self.telemetry[self.stage]
        if tel.canary_routed < 5:
            # Need minimal sample size before statistical evaluation
            return True, None

        if tel.security_violations > 0:
            return False, f"Security policy anomaly: {tel.security_violations} violation(s)"

        if tel.error_rate > 0.01:
            return False, f"Error rate breach: {tel.error_rate * 100:.2f}% (SLO threshold: 1.0%)"

        if tel.p95_latency > 5.0:
            return False, f"Latency SLA breach: P95 {tel.p95_latency:.2f}s (SLA threshold: 5.0s)"

        return True, None

    def advance_stage(self, target_stage: CanaryStage) -> tuple[bool, str]:
        """
        Promote rollout to next canary stage if health criteria are met.
        """
        if self.circuit_broken:
            return False, "Cannot advance stage while circuit breaker is tripped."

        if target_stage <= self.stage:
            return False, f"Target stage ({target_stage.name}) must be greater than current ({self.stage.name})."

        # Check health of current stage before promoting
        healthy, reason = self.check_health()
        if not healthy:
            return False, f"Cannot promote stage: current stage unhealthy ({reason})."

        old_stage = self.stage
        self.stage = target_stage
        logger.info(
            "Canary advanced from %s to %s (%d%% traffic allocation)",
            old_stage.name,
            target_stage.name,
            int(target_stage),
        )
        return True, f"Advanced to {target_stage.name}"

    def trigger_canary_rollback(self, reason: str):
        """Instantly trip circuit breaker and roll back canary allocation to 0%."""
        self.circuit_broken = True
        self.rollback_reason = reason
        self.stage = CanaryStage.STAGE_0_DISABLED

        # Cascade to system-level rollback controller
        rollback_controller.trigger_rollback(
            reason=f"Canary Circuit Breaker Trip: {reason}",
            operator="canary_router_watchdog",
        )
        logger.warning("Canary circuit breaker tripped: %s. Traffic reverted to 0%%.", reason)

    def rearm_canary(self, target_stage: CanaryStage = CanaryStage.STAGE_1_CANARY_1PCT):
        """Safely rearm canary after investigating and clearing a trip."""
        self.circuit_broken = False
        self.rollback_reason = None
        self.stage = target_stage
        logger.info("Canary rearmed at %s.", target_stage.name)

    def get_summary(self) -> dict:
        """Return comprehensive status of all canary stages."""
        summary = {
            "current_stage": self.stage.name,
            "traffic_percentage": int(self.stage),
            "circuit_broken": self.circuit_broken,
            "rollback_reason": self.rollback_reason,
            "stages": {},
        }
        for s, tel in self.telemetry.items():
            summary["stages"][s.name] = {
                "total_requests": tel.total_requests,
                "canary_routed": tel.canary_routed,
                "baseline_routed": tel.baseline_routed,
                "success_count": tel.success_count,
                "error_count": tel.error_count,
                "security_violations": tel.security_violations,
                "error_rate": f"{tel.error_rate * 100:.2f}%",
                "p95_latency_s": round(tel.p95_latency, 3),
            }
        return summary


# Global singleton instance
canary_router = CanaryRouter()
