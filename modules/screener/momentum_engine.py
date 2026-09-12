"""
AARKAAI – Momentum Scoring Engine

Scores stocks on price momentum, relative strength, trend persistence,
and volume-confirmed directional movement. All computations are
deterministic from technical indicator data.
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)


class MomentumEngine:
    """Price momentum, relative strength, and trend persistence scoring.

    Evaluates 5 momentum dimensions:
      1. Price Position (52-week range, EMA alignment)
      2. RSI Momentum (directional strength)
      3. MACD Momentum (histogram and crossover)
      4. Volume Confirmation (volume-price alignment)
      5. ADX Trend Strength (directional movement index)

    Each dimension contributes 0-2 raw points, normalized to 0-10 final score.
    """

    def score(self, snapshot: StockSnapshot) -> ScoreBreakdown:
        """Compute momentum score from StockSnapshot indicator data."""
        evidence: list[str] = []
        raw_score = 0.0
        max_raw = 10.0
        data_points_available = 0
        data_points_total = 5

        ind = snapshot.indicators or {}
        price = snapshot.price
        high_52w = snapshot.high_52w
        low_52w = snapshot.low_52w

        # ─── 1. Price Position (0-3 pts) ─────────────────────────────
        # Distance from 52-week high/low and EMA alignment
        if price and high_52w and low_52w and high_52w > low_52w:
            data_points_available += 1
            range_52w = high_52w - low_52w
            position_in_range = (price - low_52w) / range_52w  # 0 = at low, 1 = at high

            if position_in_range > 0.85:
                raw_score += 2.5
                evidence.append(f"Near 52-week high ({position_in_range:.0%} of range) — strong momentum")
            elif position_in_range > 0.65:
                raw_score += 2.0
                evidence.append(f"Upper half of 52-week range ({position_in_range:.0%})")
            elif position_in_range > 0.45:
                raw_score += 1.0
                evidence.append(f"Mid-range of 52-week range ({position_in_range:.0%})")
            elif position_in_range > 0.25:
                raw_score += 0.5
                evidence.append(f"Lower half of 52-week range ({position_in_range:.0%})")
            else:
                evidence.append(f"Near 52-week low ({position_in_range:.0%}) — weak momentum")

        # EMA alignment bonus
        ema20 = ind.get("ema20")
        ema50 = ind.get("ema50")
        ema200 = ind.get("ema200")

        if price and ema20 and ema50 and ema200:
            if price > ema20 > ema50 > ema200:
                raw_score += 0.5
                evidence.append("Perfect EMA stack: Price > EMA20 > EMA50 > EMA200")
            elif price > ema50 > ema200:
                raw_score += 0.3
                evidence.append("Bullish EMA alignment: Price > EMA50 > EMA200")
            elif price > ema200:
                raw_score += 0.15
                evidence.append("Price above EMA200 (long-term uptrend intact)")
            elif price < ema20 < ema50 < ema200:
                evidence.append("Inverse EMA stack — bearish momentum")
        elif price and ema50:
            data_points_available += 1
            if price > ema50:
                raw_score += 0.25
                evidence.append("Price above EMA50")

        # ─── 2. RSI Momentum (0-2 pts) ───────────────────────────────
        rsi = ind.get("rsi")
        if rsi is not None:
            data_points_available += 1
            if 50 <= rsi <= 65:
                raw_score += 2.0
                evidence.append(f"RSI {rsi:.1f} — strong building momentum zone")
            elif 40 <= rsi < 50:
                raw_score += 1.0
                evidence.append(f"RSI {rsi:.1f} — early momentum phase")
            elif 65 < rsi <= 75:
                raw_score += 1.5
                evidence.append(f"RSI {rsi:.1f} — elevated momentum (watch for overbought)")
            elif rsi > 75:
                raw_score += 0.5
                evidence.append(f"RSI {rsi:.1f} — overbought territory, momentum may exhaust")
            elif 30 <= rsi < 40:
                raw_score += 0.5
                evidence.append(f"RSI {rsi:.1f} — weak momentum, oversold bounce possible")
            else:
                evidence.append(f"RSI {rsi:.1f} — deeply oversold, momentum absent")
        else:
            evidence.append("RSI data unavailable")

        # ─── 3. MACD Momentum (0-2 pts) ──────────────────────────────
        macd_hist = ind.get("macd_histogram")
        macd_crossover = ind.get("macd_crossover")

        if macd_hist is not None:
            data_points_available += 1
            if macd_hist > 0:
                raw_score += 1.0
                evidence.append(f"MACD histogram positive ({macd_hist:.3f}) — bullish momentum")
                # Check if histogram is expanding (compare with previous if available)
                if macd_crossover == "bullish":
                    raw_score += 1.0
                    evidence.append("Recent bullish MACD crossover — momentum accelerating")
                else:
                    raw_score += 0.5
            elif macd_hist < 0:
                if macd_crossover == "bearish":
                    evidence.append("MACD histogram negative with bearish crossover")
                else:
                    raw_score += 0.25
                    evidence.append(f"MACD histogram negative ({macd_hist:.3f}) but no bearish crossover")
        else:
            evidence.append("MACD data unavailable")

        # ─── 4. Volume Confirmation (0-2 pts) ────────────────────────
        volume_ratio = ind.get("volume_ratio")
        if volume_ratio is not None:
            data_points_available += 1
            change_pct = snapshot.change_pct or 0.0

            if volume_ratio > 2.0 and change_pct > 0:
                raw_score += 2.0
                evidence.append(f"Volume surge ({volume_ratio:.1f}x average) with positive price action — strong confirmation")
            elif volume_ratio > 1.5 and change_pct > 0:
                raw_score += 1.5
                evidence.append(f"Elevated volume ({volume_ratio:.1f}x) confirming upward move")
            elif volume_ratio > 1.0:
                raw_score += 0.5
                evidence.append(f"Normal volume ({volume_ratio:.1f}x average)")
            elif volume_ratio > 2.0 and change_pct < 0:
                evidence.append(f"Volume surge ({volume_ratio:.1f}x) on down day — potential distribution")
            else:
                evidence.append(f"Below-average volume ({volume_ratio:.1f}x) — weak conviction")
        else:
            evidence.append("Volume data unavailable")

        # ─── 5. ADX Trend Strength (0-2 pts) ─────────────────────────
        adx = ind.get("adx")
        if adx is not None:
            data_points_available += 1
            if adx > 40:
                raw_score += 2.0
                evidence.append(f"ADX {adx:.1f} — very strong trend")
            elif adx > 25:
                raw_score += 1.5
                evidence.append(f"ADX {adx:.1f} — strong trend in progress")
            elif adx > 20:
                raw_score += 1.0
                evidence.append(f"ADX {adx:.1f} — emerging trend")
            elif adx > 15:
                raw_score += 0.5
                evidence.append(f"ADX {adx:.1f} — weak trend / transitioning")
            else:
                evidence.append(f"ADX {adx:.1f} — no trend (range-bound)")
        else:
            evidence.append("ADX data unavailable")

        # ─── Supertrend bonus ────────────────────────────────────────
        st_dir = ind.get("supertrend_direction")
        if st_dir is not None:
            if st_dir == 1:
                raw_score += 0.25
                evidence.append("Supertrend bullish (+1)")
            elif st_dir == -1:
                evidence.append("Supertrend bearish (-1)")

        # ─── Normalize to 0-10 ───────────────────────────────────────
        final_score = min(10.0, max(0.0, (raw_score / max_raw) * 10.0))

        # Data quality
        if data_points_available == 0:
            quality = DataQuality.UNAVAILABLE
            final_score = 5.0
            evidence = ["No momentum data available — score set to neutral baseline"]
        elif data_points_available < 3:
            quality = DataQuality.PARTIAL
        else:
            quality = DataQuality.FULL

        confidence = min(1.0, data_points_available / data_points_total)

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.12,
            confidence=round(confidence, 2),
            data_quality=quality,
            evidence=evidence,
        )
