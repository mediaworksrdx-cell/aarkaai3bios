"""
AARKAAI Production Operational Tooling – SLA & SLO Compliance Tracker (Gate 3).

Service Level Objectives:
- Availability: >= 99.9%
- Latency: P50 <= 1.5s, P95 <= 5.0s, P99 <= 10.0s
- Error Budget: Tracks allowed vs consumed error budget
"""
from __future__ import annotations

import time
import math
import statistics
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("aarkaai.sla_tracker")


@dataclass
class RequestMetric:
    timestamp: float
    latency_sec: float
    success: bool
    endpoint: str = "general"


@dataclass
class SLOTargets:
    availability_min_pct: float = 99.9
    p50_latency_max_sec: float = 1.5
    p95_latency_max_sec: float = 5.0
    p99_latency_max_sec: float = 10.0


class SLATracker:
    _instance: Optional[SLATracker] = None

    def __init__(self, targets: Optional[SLOTargets] = None):
        self.targets = targets or SLOTargets()
        self.history: List[RequestMetric] = []
        self._max_history = 10000

    @classmethod
    def get_instance(cls) -> SLATracker:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_request(self, latency_sec: float, success: bool, endpoint: str = "general") -> None:
        metric = RequestMetric(
            timestamp=time.time(),
            latency_sec=latency_sec,
            success=success,
            endpoint=endpoint
        )
        self.history.append(metric)
        if len(self.history) > self._max_history:
            self.history = self.history[-self._max_history:]

    def get_metrics(self, window_sec: float = 3600.0) -> Dict[str, Any]:
        now = time.time()
        cutoff = now - window_sec
        recent = [m for m in self.history if m.timestamp >= cutoff]

        total = len(recent)
        if total == 0:
            return {
                "total_requests": 0,
                "availability_pct": 100.0,
                "error_rate_pct": 0.0,
                "p50_sec": 0.0,
                "p95_sec": 0.0,
                "p99_sec": 0.0,
                "error_budget_consumed_pct": 0.0,
                "status": "COMPLIANT"
            }

        success_count = sum(1 for m in recent if m.success)
        fail_count = total - success_count
        avail_pct = (success_count / total) * 100.0
        err_pct = (fail_count / total) * 100.0

        latencies = sorted(m.latency_sec for m in recent)
        p50 = latencies[int(math.ceil(0.50 * total)) - 1]
        p95 = latencies[int(math.ceil(0.95 * total)) - 1]
        p99 = latencies[int(math.ceil(0.99 * total)) - 1]

        # Error budget: Allowed failure budget = (100 - availability_min_pct)% * total
        allowed_failures = max(1.0, total * ((100.0 - self.targets.availability_min_pct) / 100.0))
        budget_consumed_pct = min(100.0, (fail_count / allowed_failures) * 100.0)

        # Status determination
        is_breached = (
            avail_pct < self.targets.availability_min_pct
            or p95 > self.targets.p95_latency_max_sec
            or p99 > self.targets.p99_latency_max_sec
        )
        is_at_risk = budget_consumed_pct > 80.0 or p95 > (self.targets.p95_latency_max_sec * 0.85)

        status = "BREACHED" if is_breached else ("AT_RISK" if is_at_risk else "COMPLIANT")

        return {
            "total_requests": total,
            "success_count": success_count,
            "failure_count": fail_count,
            "availability_pct": round(avail_pct, 3),
            "error_rate_pct": round(err_pct, 3),
            "p50_sec": round(p50, 3),
            "p95_sec": round(p95, 3),
            "p99_sec": round(p99, 3),
            "error_budget_consumed_pct": round(budget_consumed_pct, 2),
            "status": status
        }


# Global singleton
sla_tracker = SLATracker()
