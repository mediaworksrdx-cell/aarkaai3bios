"""
AARKAAI Production – Progressive Synthetic Load Testing

Benchmarks three distinct capacity layers independently:
  Layer 1: FastAPI HTTP throughput (health endpoint, no DB/GPU)
  Layer 2: Redis + Auth pipeline (login endpoint, DB roundtrip)
  Layer 3: GPU inference throughput (prompt endpoint, full AI pipeline)

Usage:
  python load_test.py --target http://localhost:5000 --phases 100,1000,5000
  python load_test.py --target https://staging.aarkaai.com --phases 100,500 --duration 30
  python load_test.py --target http://localhost:5000 --phases 100 --layer fastapi

Outputs P50/P95/P99 latency, RPS, error rate, and cache hit ratio per layer per phase.

IMPORTANT: Results from synthetic load testing do NOT constitute production readiness
certification. Each layer (FastAPI, Redis, GPU) must be evaluated independently.
GPU inference capacity is fundamentally bounded by VRAM and cannot be extrapolated
linearly from FastAPI throughput numbers.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("load_test")

# ─── Test Configuration ──────────────────────────────────────────────────────

DEFAULT_PHASES = [100, 1000, 5000]
DEFAULT_DURATION = 20  # seconds per phase
DEFAULT_TARGET = "http://localhost:5000"

# Synthetic test payloads
TEST_PROMPTS = [
    "What is the current price of Bitcoin?",
    "Explain the concept of portfolio diversification.",
    "Write a Python function to calculate compound interest.",
    "What are the key financial ratios for evaluating a company?",
    "Summarize the latest trends in artificial intelligence.",
    "How does a transformer neural network architecture work?",
    "Calculate the Sharpe ratio for a portfolio with 12% return and 8% volatility.",
    "What is the difference between TCP and UDP protocols?",
    "Explain the Black-Scholes option pricing model.",
    "Write a SQL query to find the top 10 customers by revenue.",
]

TEST_EMAIL = "loadtest@aarkaai-benchmark.internal"
TEST_PASSWORD = "LoadTest_Secure_2026!"


# ─── Data Structures ─────────────────────────────────────────────────────────


@dataclass
class RequestResult:
    """Single request outcome."""
    latency_ms: float
    status_code: int
    success: bool
    cache_hit: Optional[bool] = None
    error: Optional[str] = None


@dataclass
class LayerResult:
    """Aggregated results for a single layer in a single phase."""
    layer_name: str
    phase_users: int
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    errors_4xx: int = 0
    errors_5xx: int = 0
    timeouts: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    latencies: list[float] = field(default_factory=list)
    duration_sec: float = 0.0

    @property
    def error_rate(self) -> float:
        return (self.failed / self.total_requests * 100) if self.total_requests else 0.0

    @property
    def rps(self) -> float:
        return self.total_requests / self.duration_sec if self.duration_sec else 0.0

    @property
    def cache_hit_ratio(self) -> float:
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total else 0.0

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]

    @property
    def p50(self) -> float:
        return self.percentile(50)

    @property
    def p95(self) -> float:
        return self.percentile(95)

    @property
    def p99(self) -> float:
        return self.percentile(99)

    @property
    def mean(self) -> float:
        return statistics.mean(self.latencies) if self.latencies else 0.0

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.latencies) if len(self.latencies) > 1 else 0.0


# ─── Request Generators ─────────────────────────────────────────────────────


async def _request_health(client: httpx.AsyncClient, base_url: str) -> RequestResult:
    """Layer 1: Pure FastAPI throughput — no DB, no GPU."""
    start = time.perf_counter()
    try:
        resp = await client.get(f"{base_url}/health")
        latency = (time.perf_counter() - start) * 1000
        return RequestResult(
            latency_ms=latency,
            status_code=resp.status_code,
            success=resp.status_code == 200,
        )
    except httpx.TimeoutException:
        return RequestResult(latency_ms=(time.perf_counter() - start) * 1000, status_code=0, success=False, error="timeout")
    except Exception as exc:
        return RequestResult(latency_ms=(time.perf_counter() - start) * 1000, status_code=0, success=False, error=str(exc))


async def _request_auth(client: httpx.AsyncClient, base_url: str) -> RequestResult:
    """Layer 2: Auth pipeline — FastAPI + DB roundtrip + Redis rate limiting."""
    start = time.perf_counter()
    try:
        resp = await client.post(
            f"{base_url}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        latency = (time.perf_counter() - start) * 1000
        # 401 is expected (test user may not exist) — still measures pipeline latency
        return RequestResult(
            latency_ms=latency,
            status_code=resp.status_code,
            success=resp.status_code in (200, 401),
        )
    except httpx.TimeoutException:
        return RequestResult(latency_ms=(time.perf_counter() - start) * 1000, status_code=0, success=False, error="timeout")
    except Exception as exc:
        return RequestResult(latency_ms=(time.perf_counter() - start) * 1000, status_code=0, success=False, error=str(exc))


async def _request_prompt(
    client: httpx.AsyncClient, base_url: str, token: str, prompt_idx: int
) -> RequestResult:
    """Layer 3: Full GPU inference pipeline — FastAPI + Redis cache + AI Router + vLLM."""
    prompt = TEST_PROMPTS[prompt_idx % len(TEST_PROMPTS)]
    start = time.perf_counter()
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = await client.post(
            f"{base_url}/prompt",
            json={"query": prompt, "session_id": f"loadtest-{prompt_idx}"},
            headers=headers,
        )
        latency = (time.perf_counter() - start) * 1000
        cache_hit = resp.headers.get("X-Cache", "").upper() == "HIT"
        cache_miss = resp.headers.get("X-Cache", "").upper() == "MISS"
        return RequestResult(
            latency_ms=latency,
            status_code=resp.status_code,
            success=resp.status_code == 200,
            cache_hit=cache_hit if (cache_hit or cache_miss) else None,
        )
    except httpx.TimeoutException:
        return RequestResult(latency_ms=(time.perf_counter() - start) * 1000, status_code=0, success=False, error="timeout")
    except Exception as exc:
        return RequestResult(latency_ms=(time.perf_counter() - start) * 1000, status_code=0, success=False, error=str(exc))


# ─── Phase Runner ────────────────────────────────────────────────────────────


async def _run_layer(
    layer_name: str,
    request_fn,
    concurrent_users: int,
    duration_sec: float,
    base_url: str,
    token: str = "",
) -> LayerResult:
    """Run a single layer benchmark for the specified duration."""
    result = LayerResult(layer_name=layer_name, phase_users=concurrent_users)
    stop_event = asyncio.Event()
    request_counter = 0

    async def worker(worker_id: int):
        nonlocal request_counter
        limits = httpx.Limits(max_connections=concurrent_users, max_keepalive_connections=concurrent_users // 2)
        timeout = httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=30.0)
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            while not stop_event.is_set():
                request_counter += 1
                idx = request_counter
                if layer_name == "gpu_inference":
                    req_result = await request_fn(client, base_url, token, idx)
                else:
                    req_result = await request_fn(client, base_url)

                result.total_requests += 1
                result.latencies.append(req_result.latency_ms)

                if req_result.success:
                    result.successful += 1
                else:
                    result.failed += 1
                    if req_result.error == "timeout":
                        result.timeouts += 1
                    elif req_result.status_code >= 500:
                        result.errors_5xx += 1
                    elif req_result.status_code >= 400:
                        result.errors_4xx += 1

                if req_result.cache_hit is True:
                    result.cache_hits += 1
                elif req_result.cache_hit is False:
                    result.cache_misses += 1

    # Launch concurrent workers
    workers = [asyncio.create_task(worker(i)) for i in range(concurrent_users)]

    # Let them run for the specified duration
    start_time = time.perf_counter()
    await asyncio.sleep(duration_sec)
    stop_event.set()

    # Wait for all workers to finish their current request
    await asyncio.gather(*workers, return_exceptions=True)
    result.duration_sec = time.perf_counter() - start_time

    return result


async def _obtain_visitor_token(base_url: str) -> str:
    """Get a visitor token for authenticated endpoint testing."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.post(f"{base_url}/auth/visitor-token")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("access_token", "")
    except Exception as exc:
        logger.warning("Could not obtain visitor token: %s", exc)
    return ""


async def run_phase(
    phase_users: int,
    duration_sec: float,
    base_url: str,
    layers: list[str],
) -> list[LayerResult]:
    """Run all requested layers for a single concurrency phase."""
    logger.info("=" * 72)
    logger.info(
        "PHASE: %d concurrent users | Duration: %ds | Target: %s",
        phase_users, duration_sec, base_url,
    )
    logger.info("=" * 72)

    results = []

    # Layer 1: FastAPI throughput
    if "fastapi" in layers or "all" in layers:
        logger.info("[Layer 1/3] FastAPI HTTP throughput (/health)...")
        r = await _run_layer("fastapi_http", _request_health, phase_users, duration_sec, base_url)
        results.append(r)
        _print_layer_result(r)

    # Layer 2: Redis + Auth pipeline
    if "redis" in layers or "all" in layers:
        logger.info("[Layer 2/3] Redis + Auth pipeline (/auth/login)...")
        r = await _run_layer("redis_auth", _request_auth, phase_users, duration_sec, base_url)
        results.append(r)
        _print_layer_result(r)

    # Layer 3: GPU inference
    if "gpu" in layers or "all" in layers:
        logger.info("[Layer 3/3] GPU inference pipeline (/prompt)...")
        token = await _obtain_visitor_token(base_url)
        if not token:
            logger.warning("No auth token available — GPU layer will use unauthenticated requests")
        # Use lower concurrency for GPU to avoid OOM — scale is the phase_users but capped
        gpu_users = min(phase_users, int(os.getenv("AARKAAI_LOADTEST_GPU_CONCURRENCY", str(min(phase_users, 50)))))
        if gpu_users < phase_users:
            logger.info("  GPU concurrency capped at %d (vs %d phase users) to avoid OOM", gpu_users, phase_users)
        r = await _run_layer("gpu_inference", _request_prompt, gpu_users, duration_sec, base_url, token)
        results.append(r)
        _print_layer_result(r)

    return results


# ─── Output Formatting ──────────────────────────────────────────────────────


def _print_layer_result(r: LayerResult):
    """Print a single layer's results."""
    logger.info("  ┌─────────────────────────────────────────────────────┐")
    logger.info("  │ Layer: %-44s │", r.layer_name)
    logger.info("  ├─────────────────────────────────────────────────────┤")
    logger.info("  │ Concurrent Users:  %-32d │", r.phase_users)
    logger.info("  │ Total Requests:    %-32d │", r.total_requests)
    logger.info("  │ Successful:        %-32d │", r.successful)
    logger.info("  │ Failed:            %-32d │", r.failed)
    logger.info("  │   ├─ 4xx Errors:   %-32d │", r.errors_4xx)
    logger.info("  │   ├─ 5xx Errors:   %-32d │", r.errors_5xx)
    logger.info("  │   └─ Timeouts:     %-32d │", r.timeouts)
    logger.info("  │ Error Rate:        %-31.2f%% │", r.error_rate)
    logger.info("  │ Throughput (RPS):   %-31.1f │", r.rps)
    logger.info("  ├─────────────────────────────────────────────────────┤")
    logger.info("  │ Latency (ms):                                      │")
    logger.info("  │   P50:  %-43.2f │", r.p50)
    logger.info("  │   P95:  %-43.2f │", r.p95)
    logger.info("  │   P99:  %-43.2f │", r.p99)
    logger.info("  │   Mean: %-43.2f │", r.mean)
    logger.info("  │   Std:  %-43.2f │", r.stdev)
    if r.cache_hits + r.cache_misses > 0:
        logger.info("  ├─────────────────────────────────────────────────────┤")
        logger.info("  │ Cache Hit Ratio:   %-31.1f%% │", r.cache_hit_ratio)
        logger.info("  │   Hits:  %-42d │", r.cache_hits)
        logger.info("  │   Misses: %-41d │", r.cache_misses)
    logger.info("  └─────────────────────────────────────────────────────┘")
    logger.info("")


def _print_summary(all_results: dict[int, list[LayerResult]]):
    """Print cross-phase comparison table."""
    logger.info("")
    logger.info("=" * 92)
    logger.info("CAPACITY DECOMPOSITION SUMMARY")
    logger.info("=" * 92)
    logger.info(
        "%-18s │ %8s │ %8s │ %8s │ %8s │ %8s │ %7s",
        "Layer / Phase", "RPS", "P50 ms", "P95 ms", "P99 ms", "Errors", "Cache%"
    )
    logger.info("─" * 92)

    for phase, results in sorted(all_results.items()):
        for r in results:
            cache_str = f"{r.cache_hit_ratio:.1f}%" if (r.cache_hits + r.cache_misses) > 0 else "N/A"
            logger.info(
                "%-18s │ %8.1f │ %8.2f │ %8.2f │ %8.2f │ %7.2f%% │ %7s",
                f"{r.layer_name[:14]}@{phase}",
                r.rps, r.p50, r.p95, r.p99, r.error_rate, cache_str,
            )
        if len(all_results) > 1:
            logger.info("─" * 92)

    logger.info("")
    logger.info("⚠  IMPORTANT DISCLAIMER:")
    logger.info("   These synthetic benchmarks measure ISOLATED layer capacity.")
    logger.info("   FastAPI RPS ≠ GPU inference RPS. GPU throughput is bounded by VRAM")
    logger.info("   and model size, not HTTP connection handling. Do not extrapolate")
    logger.info("   FastAPI/Redis numbers to claim GPU inference capacity at the same scale.")
    logger.info("")


def _export_json(all_results: dict[int, list[LayerResult]], output_path: str):
    """Export results as machine-readable JSON."""
    export = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "disclaimer": (
            "Synthetic benchmark only. FastAPI/Redis capacity does NOT equal GPU inference capacity. "
            "Each layer must be evaluated independently for production readiness."
        ),
        "phases": {},
    }
    for phase, results in sorted(all_results.items()):
        export["phases"][str(phase)] = []
        for r in results:
            export["phases"][str(phase)].append({
                "layer": r.layer_name,
                "concurrent_users": r.phase_users,
                "total_requests": r.total_requests,
                "successful": r.successful,
                "failed": r.failed,
                "errors_4xx": r.errors_4xx,
                "errors_5xx": r.errors_5xx,
                "timeouts": r.timeouts,
                "error_rate_pct": round(r.error_rate, 3),
                "rps": round(r.rps, 2),
                "latency_ms": {
                    "p50": round(r.p50, 3),
                    "p95": round(r.p95, 3),
                    "p99": round(r.p99, 3),
                    "mean": round(r.mean, 3),
                    "stdev": round(r.stdev, 3),
                },
                "cache": {
                    "hits": r.cache_hits,
                    "misses": r.cache_misses,
                    "hit_ratio_pct": round(r.cache_hit_ratio, 2),
                } if (r.cache_hits + r.cache_misses) > 0 else None,
            })

    with open(output_path, "w") as f:
        json.dump(export, f, indent=2)
    logger.info("Results exported to %s", output_path)


# ─── Main ────────────────────────────────────────────────────────────────────


async def main():
    parser = argparse.ArgumentParser(
        description="AARKAAI Progressive Load Testing — 3-Layer Capacity Decomposition",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_test.py --target http://localhost:5000 --phases 100,1000,5000
  python load_test.py --target http://localhost:5000 --phases 100 --layer fastapi --duration 10
  python load_test.py --target https://staging.aarkaai.com --phases 100,500 --output results.json
        """,
    )
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Base URL of the AARKAAI server")
    parser.add_argument("--phases", default=",".join(str(p) for p in DEFAULT_PHASES),
                        help="Comma-separated concurrent user counts (default: 100,1000,5000)")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                        help="Duration per phase in seconds (default: 20)")
    parser.add_argument("--layer", default="all", choices=["all", "fastapi", "redis", "gpu"],
                        help="Which capacity layer to test (default: all)")
    parser.add_argument("--output", default="load_test_results.json",
                        help="Output JSON file path (default: load_test_results.json)")
    args = parser.parse_args()

    phases = [int(p.strip()) for p in args.phases.split(",")]
    layers = [args.layer]

    # Pre-flight: verify target is reachable
    logger.info("Pre-flight check: %s", args.target)
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(f"{args.target}/health")
            if resp.status_code != 200:
                logger.error("Target returned %d on /health — aborting", resp.status_code)
                sys.exit(1)
            logger.info("Target is healthy: %s", resp.json())
    except Exception as exc:
        logger.error("Cannot reach target %s: %s", args.target, exc)
        sys.exit(1)

    # Run phases
    all_results: dict[int, list[LayerResult]] = {}
    for phase_users in phases:
        results = await run_phase(phase_users, args.duration, args.target, layers)
        all_results[phase_users] = results

    # Summary and export
    _print_summary(all_results)
    _export_json(all_results, args.output)


if __name__ == "__main__":
    asyncio.run(main())
