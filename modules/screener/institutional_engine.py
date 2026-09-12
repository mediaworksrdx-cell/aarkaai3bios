"""
AARKAAI – Institutional Intelligence Engine

Scores stocks based on institutional ownership signals: promoter holding
stability, FII/DII activity patterns, bulk/block deal detection, and
market cap tier as institutional interest proxy.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)


class InstitutionalEngine:
    """Institutional ownership and activity scoring.

    Evaluates 4 dimensions:
      1. Market Cap Tier (institutional investability)
      2. Volume Anomaly Detection (block deal proxy)
      3. Promoter Holding Proxy (insider confidence via fundamentals)
      4. Institutional Flow Proxy (sustained volume + price trends)
    """

    def score(self, snapshot: StockSnapshot, cap_tier: str = "") -> ScoreBreakdown:
        """Compute institutional intelligence score."""
        evidence: list[str] = []
        raw_score = 5.0
        data_points = 0
        data_points_total = 4

        indicators = snapshot.indicators or {}
        price = snapshot.price
        market_cap = snapshot.market_cap

        # ─── 1. Market Cap Tier — Institutional Investability ────────
        if market_cap:
            data_points += 1
            if market_cap > 500e9:  # > 500B (INR) or ~60B USD
                raw_score += 2.0
                evidence.append("Mega-cap tier — top institutional coverage proxy")
            elif market_cap > 100e9:
                raw_score += 1.5
                evidence.append("Large-cap tier — institutional coverage proxy")
            elif market_cap > 20e9:
                raw_score += 1.0
                evidence.append("Mid-cap tier — moderate institutional coverage proxy")
            elif market_cap > 5e9:
                raw_score += 0.5
                evidence.append("Small-cap tier — limited institutional coverage proxy")
            else:
                raw_score -= 0.5
                evidence.append("Micro-cap tier — minimal institutional coverage proxy")
        elif cap_tier:
            data_points += 1
            tier_scores = {"large_cap": 1.5, "mid_cap": 1.0, "small_cap": 0.5}
            raw_score += tier_scores.get(cap_tier, 0.0)
            evidence.append(f"Cap tier: {cap_tier.replace('_', ' ').title()} proxy")

        # ─── 2. Volume Anomaly — Block/Bulk Deal Proxy ───────────────
        volume_ratio = indicators.get("volume_ratio")
        volume_sma = indicators.get("volume_sma")
        change_pct = snapshot.change_pct or 0.0

        if volume_ratio is not None:
            data_points += 1
            if volume_ratio > 3.0:
                if change_pct > 0:
                    raw_score += 2.0
                    evidence.append(f"Extreme volume surge ({volume_ratio:.1f}x avg) + positive price — institutional accumulation proxy")
                else:
                    raw_score -= 0.5
                    evidence.append(f"Extreme volume ({volume_ratio:.1f}x) on negative day — potential institutional distribution proxy")
            elif volume_ratio > 2.0:
                if change_pct > 0:
                    raw_score += 1.0
                    evidence.append(f"High volume ({volume_ratio:.1f}x) with positive move — institutional accumulation proxy")
                else:
                    evidence.append(f"High volume ({volume_ratio:.1f}x) on down day — monitor for distribution proxy")
            elif volume_ratio > 1.3:
                raw_score += 0.25
                evidence.append(f"Above-average volume ({volume_ratio:.1f}x) proxy")
            elif volume_ratio < 0.5:
                raw_score -= 0.5
                evidence.append(f"Very low volume ({volume_ratio:.1f}x) — institutional disinterest proxy")

        # ─── 3. Promoter Confidence Proxy ────────────────────────────
        # Use fundamental metrics as proxy for insider confidence
        roe = snapshot.roe
        debt_eq = snapshot.debt_equity
        div_yield = snapshot.dividend_yield

        proxy_signals = 0
        if roe is not None:
            roe_pct = roe * 100 if abs(roe) < 1 else roe
            if roe_pct > 15:
                proxy_signals += 1
        if debt_eq is not None and debt_eq < 0.5:
            proxy_signals += 1
        if div_yield is not None:
            yield_pct = div_yield * 100 if div_yield < 1 else div_yield
            if yield_pct > 1.0:
                proxy_signals += 1

        if proxy_signals > 0:
            data_points += 1
            if proxy_signals >= 3:
                raw_score += 1.5
                evidence.append("Promoter confidence proxy: high ROE + low debt + dividend paying")
            elif proxy_signals >= 2:
                raw_score += 1.0
                evidence.append("Moderate promoter confidence proxy")
            else:
                raw_score += 0.5
                evidence.append("Some promoter confidence proxy indicators present")

        # ─── 4. Sustained Institutional Flow Proxy ───────────────────
        # Stocks trending up on consistent above-avg volume = institutional accumulation
        ema50 = indicators.get("ema50")
        ema200 = indicators.get("ema200")
        adx = indicators.get("adx")

        if price and ema50 and ema200 and volume_ratio:
            data_points += 1
            if price > ema50 > ema200 and volume_ratio > 1.0 and adx and adx > 20:
                raw_score += 1.5
                evidence.append("Sustained uptrend with above-avg volume — institutional accumulation proxy pattern")
            elif price > ema200 and volume_ratio > 1.2:
                raw_score += 0.5
                evidence.append("Price above EMA200 with decent volume — institutional support proxy")
            elif price < ema200 and volume_ratio > 1.5:
                raw_score -= 0.5
                evidence.append("Below EMA200 with high volume — institutional distribution proxy")

        # Bound institutional score to 8.5/10 max as it is an algorithmic proxy, not confirmed filings
        final_score = min(8.5, max(1.5, raw_score))

        if data_points == 0:
            return ScoreBreakdown.unavailable(weight=0.08)

        quality = DataQuality.FULL if data_points >= 3 else DataQuality.PARTIAL
        confidence = min(1.0, data_points / data_points_total)

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.08,
            confidence=round(confidence, 2),
            data_quality=quality,
            evidence=evidence,
        )
