"""
AARKA Infer Verified Deterministic Mock Backend
Used for verification, unit testing, and development when raw weights are unmounted.
Enforces AARKAA persona, financial reasoning, and timing fidelity.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from aarka_infer.backends.base import BaseBackend
from aarka_infer.runtime.sampler import DeterministicSampler, SamplingParams

logger = logging.getLogger("aarka_infer.backend.mock")


class MockBackend(BaseBackend):
    """
    Deterministic mock backend ensuring end-to-end functionality,
    streaming verification, and pipeline testing without GPU weights.
    """

    def __init__(self, simulate_latency_ms: float = 8.0):
        self.simulate_latency_ms = simulate_latency_ms
        self._is_ready = True

    @property
    def name(self) -> str:
        return "mock"

    async def initialize(self) -> bool:
        self._is_ready = True
        return True

    async def generate_stream(
        self,
        prompt: str,
        prompt_tokens: List[int],
        params: SamplingParams,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        """Generates realistic structured responses with timing fidelity."""
        sampler = DeterministicSampler(params)

        # Generate contextual response based on prompt keywords
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["pe", "roce", "ratio", "screener", "finance", "stock", "reliance", "tcs"]):
            response_text = (
                "### AARKAA Quantitative Financial Analysis\n\n"
                "**1. Core Fundamentals & Valuation Metrics:**\n"
                "- **P/E (Price-to-Earnings):** Evaluated against 5-year historical median.\n"
                "- **ROCE (Return on Capital Employed):** Demonstrates sustained capital efficiency > 18%.\n"
                "- **Debt-to-Equity:** Conservative balance sheet leverage < 0.5x.\n\n"
                "**2. Institutional Order Flow & Price Action:**\n"
                "- Confirmed bullish market structure with liquidity sweep recovery.\n"
                "- Fair Value Gap (FVG) mitigation observed near key demand block.\n\n"
                "*Disclaimer: Synthetix Analytics quantitative intelligence generated for informational purposes.*"
            )
        elif any(w in p_lower for w in ["code", "function", "python", "typescript", "bug", "algorithm"]):
            response_text = (
                "```python\n"
                "# AARKAA-3B High-Performance Stream Processor\n"
                "def process_market_ticks(ticks: list[dict]) -> dict:\n"
                "    volume_weighted_price = sum(t['price'] * t['vol'] for t in ticks) / max(1, sum(t['vol'] for t in ticks))\n"
                "    return {'vwap': round(volume_weighted_price, 2), 'count': len(ticks)}\n"
                "```\n"
                "The function computes volume-weighted average price across batch ticks with zero division safeguards."
            )
        else:
            response_text = (
                "I am Aarkaa AI, developed by Synthetix Analytics. I am an advanced reasoning and intelligence model "
                "designed for financial analysis, quantitative market strategy, coding, and mathematical reasoning. "
                "How may I assist your analysis today?"
            )

        # Split into realistic token-sized words/chunks
        chunks = re.findall(r"\S+|\s+", response_text)
        max_chunks = min(len(chunks), params.max_tokens)

        # Prefill delay (simulating TTFT: ~25-45ms)
        await asyncio.sleep(0.035)

        for i in range(max_chunks):
            if cancel_event.is_set():
                break

            chunk = chunks[i]
            # Inter-token latency simulation
            if self.simulate_latency_ms > 0:
                await asyncio.sleep(self.simulate_latency_ms / 1000.0)

            # Check stop condition
            if sampler.check_stop_condition(chunk):
                break

            yield chunk

    def is_healthy(self) -> bool:
        return self._is_ready

    def get_memory_usage(self) -> Dict[str, Any]:
        return {
            "mode": "verified_deterministic_mock",
            "is_real_weights": False,
        }
