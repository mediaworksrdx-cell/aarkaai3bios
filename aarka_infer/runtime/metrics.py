"""
AARKA Infer Performance & Observability Metrics Engine
Tracks precise Time to First Token (TTFT), Inter-Token Latency (ITL),
Tokens Per Second (TPS), Queue Time, and Memory Utilization.
"""
from __future__ import annotations

import logging
import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger("aarka_infer.metrics")


@dataclass
class RequestTrace:
    """Detailed timing and token profile for an individual inference request."""
    request_id: str
    queue_enter_time: float
    start_time: float = 0.0
    first_token_time: float = 0.0
    end_time: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    token_timestamps: List[float] = field(default_factory=list)

    @property
    def queue_latency_ms(self) -> float:
        if self.start_time > 0:
            return max(0.0, (self.start_time - self.queue_enter_time) * 1000.0)
        return 0.0

    @property
    def ttft_ms(self) -> float:
        """Time to First Token (prefill + scheduling latency)."""
        if self.first_token_time > 0 and self.start_time > 0:
            return max(0.0, (self.first_token_time - self.start_time) * 1000.0)
        return 0.0

    @property
    def total_latency_ms(self) -> float:
        if self.end_time > 0 and self.start_time > 0:
            return max(0.0, (self.end_time - self.start_time) * 1000.0)
        return 0.0

    @property
    def tokens_per_second(self) -> float:
        duration_sec = self.total_latency_ms / 1000.0
        if duration_sec > 0 and self.completion_tokens > 0:
            return round(self.completion_tokens / duration_sec, 2)
        return 0.0

    @property
    def avg_inter_token_latency_ms(self) -> float:
        if len(self.token_timestamps) > 1:
            diffs = [
                (self.token_timestamps[i] - self.token_timestamps[i - 1]) * 1000.0
                for i in range(1, len(self.token_timestamps))
            ]
            return round(statistics.mean(diffs), 2)
        return 0.0


class InferenceMetricsTracker:
    """Aggregates latency and throughput metrics with rolling window percentile tracking."""

    def __init__(self, history_size: int = 500):
        self.history_size = history_size
        self._history: deque[RequestTrace] = deque(maxlen=history_size)
        self.active_requests: int = 0
        self.total_completed: int = 0
        self.total_failed: int = 0
        self.total_tokens_generated: int = 0
        self.peak_concurrent: int = 0
        self.server_start_time: float = time.time()

    def start_request(self, request_id: str, prompt_tokens: int) -> RequestTrace:
        """Called when request enters the queue."""
        now = time.time()
        trace = RequestTrace(
            request_id=request_id,
            queue_enter_time=now,
            prompt_tokens=prompt_tokens,
        )
        self.active_requests += 1
        if self.active_requests > self.peak_concurrent:
            self.peak_concurrent = self.active_requests
        return trace

    def mark_execution_start(self, trace: RequestTrace) -> None:
        """Called when request dequeues and begins model execution."""
        trace.start_time = time.time()

    def mark_first_token(self, trace: RequestTrace) -> None:
        """Called when first output token is generated."""
        now = time.time()
        trace.first_token_time = now
        trace.token_timestamps.append(now)

    def mark_token(self, trace: RequestTrace) -> None:
        """Called on subsequent tokens."""
        trace.token_timestamps.append(time.time())

    def complete_request(self, trace: RequestTrace, completion_tokens: int) -> None:
        """Called when request completes successfully."""
        trace.end_time = time.time()
        trace.completion_tokens = completion_tokens
        self.active_requests = max(0, self.active_requests - 1)
        self.total_completed += 1
        self.total_tokens_generated += completion_tokens
        self._history.append(trace)

    def fail_request(self, trace: RequestTrace) -> None:
        """Called when request aborts or errors."""
        trace.end_time = time.time()
        self.active_requests = max(0, self.active_requests - 1)
        self.total_failed += 1
        self._history.append(trace)

    def get_summary(self) -> Dict[str, Any]:
        """Calculates p50, p95, p99 TTFT, throughput, and system health metrics."""
        traces = list(self._history)
        ttfts = [t.ttft_ms for t in traces if t.ttft_ms > 0]
        latencies = [t.total_latency_ms for t in traces if t.total_latency_ms > 0]
        tps_list = [t.tokens_per_second for t in traces if t.tokens_per_second > 0]
        queue_times = [t.queue_latency_ms for t in traces]

        # Host RAM metrics
        mem = psutil.virtual_memory()
        ram_used_gb = round(mem.used / (1024**3), 2)
        ram_total_gb = round(mem.total / (1024**3), 2)

        # GPU metrics if torch + cuda available
        gpu_info = None
        try:
            import torch
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / (1024**3)
                reserved = torch.cuda.memory_reserved() / (1024**3)
                device_name = torch.cuda.get_device_name(0)
                gpu_info = {
                    "device": device_name,
                    "vram_allocated_gb": round(allocated, 2),
                    "vram_reserved_gb": round(reserved, 2),
                }
        except Exception:
            pass

        def percentile(data: List[float], p: float) -> float:
            if not data:
                return 0.0
            data_sorted = sorted(data)
            k = (len(data_sorted) - 1) * (p / 100.0)
            f = int(k)
            c = math_ceil(k)
            if f == c:
                return round(data_sorted[int(k)], 2)
            d0 = data_sorted[f] * (c - k)
            d1 = data_sorted[c] * (k - f)
            return round(d0 + d1, 2)

        def math_ceil(val: float) -> int:
            return int(val) + (1 if val > int(val) else 0)

        uptime_sec = round(time.time() - self.server_start_time, 1)

        return {
            "uptime_seconds": uptime_sec,
            "requests": {
                "active": self.active_requests,
                "completed": self.total_completed,
                "failed": self.total_failed,
                "peak_concurrent": self.peak_concurrent,
            },
            "tokens": {
                "total_generated": self.total_tokens_generated,
                "avg_tps": round(statistics.mean(tps_list), 2) if tps_list else 0.0,
                "p95_tps": percentile(tps_list, 95),
            },
            "ttft_ms": {
                "p50": percentile(ttfts, 50),
                "p90": percentile(ttfts, 90),
                "p95": percentile(ttfts, 95),
                "p99": percentile(ttfts, 99),
                "avg": round(statistics.mean(ttfts), 2) if ttfts else 0.0,
            },
            "total_latency_ms": {
                "p50": percentile(latencies, 50),
                "p90": percentile(latencies, 90),
                "p95": percentile(latencies, 95),
                "avg": round(statistics.mean(latencies), 2) if latencies else 0.0,
            },
            "queue_latency_ms": {
                "avg": round(statistics.mean(queue_times), 2) if queue_times else 0.0,
                "p95": percentile(queue_times, 95),
            },
            "memory": {
                "ram_used_gb": ram_used_gb,
                "ram_total_gb": ram_total_gb,
                "ram_percent": mem.percent,
                "gpu": gpu_info,
            },
        }
