"""
AARKAAI Production Operational Tooling – Alerting Manager (Gate 3).

Features:
- Configurable threshold rules with windowed evaluation.
- Severity levels (INFO, WARNING, HIGH, CRITICAL).
- Alert deduplication and cooldown management.
- Dispatches notifications and triggers automated emergency rollback hooks.
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("aarkaai.alerting")


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    name: str
    severity: AlertSeverity
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    message_fn: Callable[[Dict[str, Any]], str]
    cooldown_seconds: float = 60.0


class AlertManager:
    _instance: Optional[AlertManager] = None

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.last_fired: Dict[str, float] = {}
        self.alert_history: List[Alert] = []
        self.handlers: List[Callable[[Alert], None]] = []
        self._register_default_rules()

    @classmethod
    def get_instance(cls) -> AlertManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_rule(self, rule: AlertRule) -> None:
        self.rules[rule.name] = rule

    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        self.handlers.append(handler)

    def _register_default_rules(self) -> None:
        # 1. High Error Rate (> 1.0% errors)
        self.register_rule(AlertRule(
            name="HighErrorRate",
            severity=AlertSeverity.CRITICAL,
            description="Error rate exceeded 1.0% threshold",
            condition=lambda m: m.get("error_rate", 0.0) > 0.01,
            message_fn=lambda m: f"Critical Error Rate: {m.get('error_rate', 0.0)*100:.2f}% (threshold: 1.00%)",
            cooldown_seconds=60.0
        ))

        # 2. Latency SLA Breach (P95 > 5.0s)
        self.register_rule(AlertRule(
            name="LatencySLABreach",
            severity=AlertSeverity.HIGH,
            description="P95 latency exceeded 5.0s SLA target",
            condition=lambda m: m.get("p95_latency_sec", 0.0) > 5.0,
            message_fn=lambda m: f"P95 Latency SLA Breached: {m.get('p95_latency_sec', 0.0):.2f}s (SLA: 5.00s)",
            cooldown_seconds=60.0
        ))

        # 3. Security Anomaly (> 3 violations in window)
        self.register_rule(AlertRule(
            name="SecurityAnomalyDetected",
            severity=AlertSeverity.CRITICAL,
            description="Security boundary violation rate exceeded safe threshold",
            condition=lambda m: m.get("security_violations_5m", 0) > 3,
            message_fn=lambda m: f"Security Anomaly: {m.get('security_violations_5m', 0)} violations in 5m window",
            cooldown_seconds=30.0
        ))

        # 4. Storage Quota High (> 80 MB of 100 MB)
        self.register_rule(AlertRule(
            name="StorageQuotaHigh",
            severity=AlertSeverity.WARNING,
            description="Sandbox workspace storage usage exceeded 80% capacity",
            condition=lambda m: m.get("workspace_bytes", 0) > 80 * 1024 * 1024,
            message_fn=lambda m: f"Storage Warning: {m.get('workspace_bytes', 0)/(1024*1024):.1f} MB used (threshold: 80 MB)",
            cooldown_seconds=120.0
        ))

        # 5. Audit Log Flood (> 100 records/min)
        self.register_rule(AlertRule(
            name="AuditRateFlood",
            severity=AlertSeverity.WARNING,
            description="Security audit log throughput exceeded standard operational rate",
            condition=lambda m: m.get("audit_records_min", 0) > 100,
            message_fn=lambda m: f"Audit Flood Warning: {m.get('audit_records_min', 0)} records/min (standard: 100)",
            cooldown_seconds=60.0
        ))

    def evaluate_metrics(self, snapshot: Dict[str, Any]) -> List[Alert]:
        now = time.time()
        fired_alerts = []

        for name, rule in self.rules.items():
            last_time = self.last_fired.get(name, 0.0)
            if now - last_time < rule.cooldown_seconds:
                continue

            try:
                if rule.condition(snapshot):
                    alert = Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=rule.message_fn(snapshot),
                        timestamp=now,
                        details=dict(snapshot)
                    )
                    self.last_fired[name] = now
                    self.alert_history.append(alert)
                    fired_alerts.append(alert)
                    self.dispatch(alert)
            except Exception as e:
                logger.error("Error evaluating alert rule %s: %s", name, e)

        return fired_alerts

    def dispatch(self, alert: Alert) -> None:
        log_method = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.HIGH: logger.error,
            AlertSeverity.CRITICAL: logger.critical
        }.get(alert.severity, logger.warning)

        log_method("ALERT [%s] %s: %s", alert.severity.value, alert.rule_name, alert.message)

        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error("Alert handler error: %s", e)
