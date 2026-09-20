"""
AARKAAI Zero-Dependency Production Observability & Prometheus Metrics Engine.

Provides high-performance, thread-safe Prometheus metrics collection and exposition
(format: text/plain; version=0.0.4) without external dependencies.
"""
import time
import threading
from typing import Dict, List, Tuple, Optional, Any


class Metric:
    """Base class for thread-safe Prometheus metrics."""
    def __init__(self, name: str, docstring: str, labelnames: Optional[List[str]] = None):
        self.name = name
        self.docstring = docstring
        self.labelnames = labelnames or []
        self._lock = threading.Lock()

    def _format_labels(self, label_values: Tuple[str, ...]) -> str:
        if not self.labelnames or not label_values:
            return ""
        pairs = [f'{k}="{v}"' for k, v in zip(self.labelnames, label_values)]
        return "{" + ",".join(pairs) + "}"


class Counter(Metric):
    """Cumulative metric that monotonically increases."""
    def __init__(self, name: str, docstring: str, labelnames: Optional[List[str]] = None):
        super().__init__(name, docstring, labelnames)
        self._values: Dict[Tuple[str, ...], float] = {}

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        if amount < 0:
            raise ValueError("Counter increments must be non-negative.")
        label_tuple = tuple(str(labels.get(k, "")) for k in self.labelnames)
        with self._lock:
            self._values[label_tuple] = self._values.get(label_tuple, 0.0) + amount

    def collect(self) -> List[str]:
        lines = [f"# HELP {self.name} {self.docstring}", f"# TYPE {self.name} counter"]
        with self._lock:
            if not self._values and not self.labelnames:
                lines.append(f"{self.name} 0.0")
            for label_tuple, val in sorted(self._values.items()):
                lbl_str = self._format_labels(label_tuple)
                lines.append(f"{self.name}{lbl_str} {val}")
        return lines


class Gauge(Metric):
    """Metric that represents a single numerical value that can arbitrarily go up and down."""
    def __init__(self, name: str, docstring: str, labelnames: Optional[List[str]] = None):
        super().__init__(name, docstring, labelnames)
        self._values: Dict[Tuple[str, ...], float] = {}

    def set(self, value: float, **labels: str) -> None:
        label_tuple = tuple(str(labels.get(k, "")) for k in self.labelnames)
        with self._lock:
            self._values[label_tuple] = float(value)

    def inc(self, amount: float = 1.0, **labels: str) -> None:
        label_tuple = tuple(str(labels.get(k, "")) for k in self.labelnames)
        with self._lock:
            self._values[label_tuple] = self._values.get(label_tuple, 0.0) + amount

    def dec(self, amount: float = 1.0, **labels: str) -> None:
        label_tuple = tuple(str(labels.get(k, "")) for k in self.labelnames)
        with self._lock:
            self._values[label_tuple] = self._values.get(label_tuple, 0.0) - amount

    def collect(self) -> List[str]:
        lines = [f"# HELP {self.name} {self.docstring}", f"# TYPE {self.name} gauge"]
        with self._lock:
            if not self._values and not self.labelnames:
                lines.append(f"{self.name} 0.0")
            for label_tuple, val in sorted(self._values.items()):
                lbl_str = self._format_labels(label_tuple)
                lines.append(f"{self.name}{lbl_str} {val}")
        return lines


class Histogram(Metric):
    """Tracks the size and count of events in configured buckets."""
    DEFAULT_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)

    def __init__(
        self,
        name: str,
        docstring: str,
        labelnames: Optional[List[str]] = None,
        buckets: Optional[Tuple[float, ...]] = None,
    ):
        super().__init__(name, docstring, labelnames)
        self.buckets = sorted(buckets or self.DEFAULT_BUCKETS)
        self._counts: Dict[Tuple[str, ...], Dict[float, int]] = {}
        self._sums: Dict[Tuple[str, ...], float] = {}
        self._totals: Dict[Tuple[str, ...], int] = {}

    def observe(self, value: float, **labels: str) -> None:
        label_tuple = tuple(str(labels.get(k, "")) for k in self.labelnames)
        val = float(value)
        with self._lock:
            if label_tuple not in self._counts:
                self._counts[label_tuple] = {b: 0 for b in self.buckets}
                self._sums[label_tuple] = 0.0
                self._totals[label_tuple] = 0

            self._sums[label_tuple] += val
            self._totals[label_tuple] += 1
            for b in self.buckets:
                if val <= b:
                    self._counts[label_tuple][b] += 1

    def collect(self) -> List[str]:
        lines = [f"# HELP {self.name} {self.docstring}", f"# TYPE {self.name} histogram"]
        with self._lock:
            for label_tuple, bucket_counts in sorted(self._counts.items()):
                lbl_pairs = [f'{k}="{v}"' for k, v in zip(self.labelnames, label_tuple)] if self.labelnames else []
                cumulative = 0
                for b in self.buckets:
                    cumulative = bucket_counts[b]
                    b_lbls = lbl_pairs + [f'le="{b}"']
                    lines.append(f"{self.name}_bucket{{{','.join(b_lbls)}}} {cumulative}")
                inf_lbls = lbl_pairs + ['le="+Inf"']
                lines.append(f"{self.name}_bucket{{{','.join(inf_lbls)}}} {self._totals[label_tuple]}")
                lbl_str = f"{{{','.join(lbl_pairs)}}}" if lbl_pairs else ""
                lines.append(f"{self.name}_sum{lbl_str} {self._sums[label_tuple]}")
                lines.append(f"{self.name}_count{lbl_str} {self._totals[label_tuple]}")
        return lines


class MetricsRegistry:
    """Registry coordinating all Prometheus metrics collectors."""
    def __init__(self):
        self._metrics: List[Metric] = []
        self._lock = threading.Lock()

    def register(self, metric: Metric) -> Metric:
        with self._lock:
            self._metrics.append(metric)
        return metric

    def generate_latest(self) -> str:
        """Render all metrics into standard Prometheus exposition format."""
        all_lines = []
        with self._lock:
            for m in self._metrics:
                all_lines.extend(m.collect())
        return "\n".join(all_lines) + "\n"


# Global Registry Instance
REGISTRY = MetricsRegistry()

# ── Standard Platform Metrics ──────────────────────────────────────────────────

GATEWAY_REQUESTS = REGISTRY.register(
    Counter(
        "aarkaai_gateway_requests_total",
        "Total tool execution requests received by ToolGateway",
        ["tool", "classification", "status"],
    )
)

GATEWAY_DENIALS = REGISTRY.register(
    Counter(
        "aarkaai_gateway_denials_total",
        "Total tool authorization, permission, and path traversal denials",
        ["tool", "reason"],
    )
)

APPROVALS_PROCESSED = REGISTRY.register(
    Counter(
        "aarkaai_approvals_total",
        "Total operator and CI approval decisions processed",
        ["tool", "outcome"],
    )
)

SANDBOX_DURATION = REGISTRY.register(
    Histogram(
        "aarkaai_sandbox_duration_seconds",
        "Execution latency of secondary container and fallback sandboxes in seconds",
        ["tool"],
    )
)

HTTP_REQUESTS = REGISTRY.register(
    Counter(
        "aarkaai_http_requests_total",
        "Total HTTP requests handled by the API",
        ["method", "endpoint", "status_code"],
    )
)

AUDIT_SPOOL_LAG = REGISTRY.register(
    Gauge(
        "aarkaai_audit_spool_lag_seconds",
        "Age of oldest unanchored security audit record in seconds",
    )
)
