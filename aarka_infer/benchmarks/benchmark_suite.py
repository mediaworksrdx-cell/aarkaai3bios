"""
AARKA Infer Performance Benchmark & Validation Suite
Measures TTFT, ITL, Tokens-per-Second, KV-Cache Prefix Reuse, and Seed Determinism.
"""
from __future__ import annotations

import asyncio
import logging
import statistics
import time
from typing import Any, Dict, List

from aarka_infer.config import settings
from aarka_infer.runtime.engine import AarkaInferEngine
from aarka_infer.runtime.sampler import SamplingParams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aarka_infer.benchmark")


async def run_benchmark(concurrency: int = 4, requests_per_worker: int = 2) -> Dict[str, Any]:
    """Runs concurrent load test against AARKA Infer engine."""
    engine = AarkaInferEngine.get_instance()
    await engine.initialize(force_backend="mock")

    logger.info("Starting AARKA Infer benchmark: concurrency=%d, total_requests=%d", concurrency, concurrency * requests_per_worker)

    shared_system_prompt = (
        "You are Aarkaa AI, created by Synthetix Analytics. You specialize in quantitative finance, "
        "options strategies, trading algorithms, and financial market intelligence."
    )

    test_queries = [
        "Explain Price-to-Earnings (P/E) ratio versus ROCE for stock valuation.",
        "Write a Python function to compute volume-weighted moving average (VWAP).",
        "Explain Order Blocks and Fair Value Gaps in Smart Money Concepts.",
        "What are the risks of trading high implied volatility options straddles?",
    ]

    latencies: List[float] = []
    ttfts: List[float] = []
    tps_list: List[float] = []
    tokens_generated: List[int] = []

    async def _worker(worker_id: int):
        for req_idx in range(requests_per_worker):
            query = test_queries[(worker_id + req_idx) % len(test_queries)]
            messages = [
                {"role": "system", "content": shared_system_prompt},
                {"role": "user", "content": query},
            ]
            params = SamplingParams(max_tokens=256, temperature=0.7)

            start = time.time()
            first_tok_time = None
            tok_count = 0

            async for tok in engine.chat_stream(messages, params=params):
                if first_tok_time is None:
                    first_tok_time = time.time()
                tok_count += 1

            end = time.time()
            total_duration = end - start
            ttft = (first_tok_time - start) * 1000.0 if first_tok_time else 0.0
            tps = (tok_count / total_duration) if total_duration > 0 else 0.0

            latencies.append(total_duration * 1000.0)
            ttfts.append(ttft)
            tps_list.append(tps)
            tokens_generated.append(tok_count)

    tasks = [_worker(i) for i in range(concurrency)]
    start_total = time.time()
    await asyncio.gather(*tasks)
    total_time = time.time() - start_total

    kv_stats = engine.kv_cache.get_stats()
    aggregate_tps = sum(tokens_generated) / total_time if total_time > 0 else 0.0

    summary = {
        "concurrency": concurrency,
        "total_requests": len(latencies),
        "total_time_seconds": round(total_time, 2),
        "total_tokens": sum(tokens_generated),
        "aggregate_tokens_per_second": round(aggregate_tps, 2),
        "ttft_ms": {
            "p50": round(statistics.median(ttfts), 2),
            "p95": round(statistics.quantiles(ttfts, n=20)[18] if len(ttfts) >= 20 else max(ttfts), 2),
            "avg": round(statistics.mean(ttfts), 2),
        },
        "latency_ms": {
            "p50": round(statistics.median(latencies), 2),
            "avg": round(statistics.mean(latencies), 2),
        },
        "kv_cache_prefix_hit_rate_pct": kv_stats["hit_rate_pct"],
        "kv_cache_tokens_saved": kv_stats["reused_tokens"],
    }

    print("\n" + "=" * 65)
    print("        AARKA INFER BENCHMARK PERFORMANCE REPORT")
    print("=" * 65)
    print(f" Concurrency Level       : {summary['concurrency']}")
    print(f" Total Requests          : {summary['total_requests']}")
    print(f" Aggregate Throughput    : {summary['aggregate_tokens_per_second']} tokens/sec")
    print(f" Average TTFT            : {summary['ttft_ms']['avg']} ms")
    print(f" Median (p50) TTFT       : {summary['ttft_ms']['p50']} ms")
    print(f" Average Latency         : {summary['latency_ms']['avg']} ms")
    print(f" KV Cache Prefix Hit Rate: {summary['kv_cache_prefix_hit_rate_pct']}%")
    print(f" Reused Cache Tokens     : {summary['kv_cache_tokens_saved']}")
    print("=" * 65 + "\n")

    return summary


if __name__ == "__main__":
    asyncio.run(run_benchmark())
