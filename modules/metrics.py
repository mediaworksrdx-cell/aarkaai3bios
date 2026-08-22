"""
AARKAAI Backend – Prometheus Metrics Instrumentation

Provides application-level metrics for monitoring and alerting.
Requires `prometheus-fastapi-instrumentator` for automatic HTTP metrics.
Custom metrics track LLM inference, agent routing, and tool execution.

Usage:
    from modules.metrics import setup_metrics, INFERENCE_DURATION, AGENT_ROUTING
    
    # In main.py startup:
    setup_metrics(app)
    
    # In inference code:
    with INFERENCE_DURATION.labels(model="aarkaa-3b").time():
        result = generate(...)
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Try to import Prometheus client; provide no-op fallbacks ────────────

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Info,
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.info("prometheus_client not installed; metrics will be no-ops")


if PROMETHEUS_AVAILABLE:
    # ─── LLM Inference Metrics ─────────────────────────────────────────
    INFERENCE_DURATION = Histogram(
        "aarkaai_inference_duration_seconds",
        "Time spent on LLM inference",
        labelnames=["model", "temperature"],
        buckets=[0.5, 1, 2, 5, 10, 20, 30, 60],
    )
    INFERENCE_TOKENS = Counter(
        "aarkaai_inference_tokens_total",
        "Total tokens generated",
        labelnames=["model", "direction"],  # direction: input/output
    )
    
    # ─── Agent Routing Metrics ─────────────────────────────────────────
    AGENT_ROUTING = Counter(
        "aarkaai_agent_routing_total",
        "Agent routing decisions",
        labelnames=["agent", "strategy"],
    )
    AGENT_ROUTING_DURATION = Histogram(
        "aarkaai_agent_routing_duration_seconds",
        "Time spent on agent routing decisions",
        labelnames=["strategy"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
    )
    
    # ─── Tool Execution Metrics ────────────────────────────────────────
    TOOL_EXECUTION = Counter(
        "aarkaai_tool_execution_total",
        "Tool execution attempts",
        labelnames=["tool", "status"],  # status: success/failure/blocked
    )
    TOOL_DURATION = Histogram(
        "aarkaai_tool_duration_seconds",
        "Time spent on tool execution",
        labelnames=["tool"],
        buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
    )
    
    # ─── External Service Metrics ─────────────────────────────────────
    EXTERNAL_API_CALLS = Counter(
        "aarkaai_external_api_calls_total",
        "External API calls (web search, finance, etc.)",
        labelnames=["service", "status"],
    )
    CIRCUIT_BREAKER_STATE = Gauge(
        "aarkaai_circuit_breaker_state",
        "Circuit breaker state (0=closed, 1=half_open, 2=open)",
        labelnames=["service"],
    )
    
    # ─── System Metrics ──────────────────────────────────────────────
    ACTIVE_CONNECTIONS = Gauge(
        "aarkaai_active_connections",
        "Number of active client connections",
    )
    BUILD_INFO = Info(
        "aarkaai_build",
        "Build and version information",
    )

else:
    # No-op stubs when prometheus_client is not installed
    class _NoOpMetric:
        """Silent no-op metric that accepts any method call."""
        def __getattr__(self, _):
            return lambda *a, **kw: self
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
    
    INFERENCE_DURATION = _NoOpMetric()
    INFERENCE_TOKENS = _NoOpMetric()
    AGENT_ROUTING = _NoOpMetric()
    AGENT_ROUTING_DURATION = _NoOpMetric()
    TOOL_EXECUTION = _NoOpMetric()
    TOOL_DURATION = _NoOpMetric()
    EXTERNAL_API_CALLS = _NoOpMetric()
    CIRCUIT_BREAKER_STATE = _NoOpMetric()
    ACTIVE_CONNECTIONS = _NoOpMetric()
    BUILD_INFO = _NoOpMetric()


def setup_metrics(app) -> None:
    """Attach Prometheus metrics endpoint to FastAPI app.
    
    Adds automatic HTTP request instrumentation and exposes /metrics endpoint.
    """
    if not PROMETHEUS_AVAILABLE:
        logger.info("Prometheus metrics disabled (prometheus_client not installed)")
        return
    
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            excluded_handlers=["/health", "/health/live", "/health/ready", "/metrics"],
        )
        instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
        
        # Set build info
        BUILD_INFO.info({
            "version": "3.0.0",
            "model": "aarkaa-3b",
        })
        
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError:
        logger.info(
            "prometheus-fastapi-instrumentator not installed; "
            "HTTP metrics disabled (custom metrics still active)"
        )
    except Exception as e:
        logger.warning("Failed to setup Prometheus instrumentation: %s", e)


@contextmanager
def track_duration(histogram, **labels):
    """Context manager to track operation duration.
    
    Usage:
        with track_duration(INFERENCE_DURATION, model="aarkaa-3b"):
            result = generate(...)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        try:
            histogram.labels(**labels).observe(duration)
        except Exception:
            pass
