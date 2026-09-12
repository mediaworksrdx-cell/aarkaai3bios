"""
AARKAAI – Forecast Engine

Generates deterministic price forecasts using multi-timeframe technical
projections, trend extrapolation, and support/resistance analysis.
Produces bull/base/bear scenarios with confidence levels.

NOT an LLM prediction — purely mathematical projections from current
indicator state and historical price structure.
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from modules.screener.schemas import (
    DataQuality,
    ForecastScenario,
    ScoreBreakdown,
)

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)


class ForecastEngine:
    """Deterministic price forecasting engine.

    Generates 3-scenario forecasts (bull/base/bear) using:
      1. Trend Extrapolation (EMA slope projection)
      2. ATR-Based Range (volatility envelopes)
      3. Support/Resistance Levels (BB, 52w high/low)
      4. Momentum Persistence (RSI mean-reversion tendency)

    Also produces a forecast confidence score for the composite scorer.
    """

    def forecast(self, snapshot: StockSnapshot) -> list[ForecastScenario] | None:
        """Generate bull/base/bear price scenarios.

        Returns list of 3 ForecastScenario objects or None if insufficient data.
        """
        indicators = snapshot.indicators or {}
        price = snapshot.price

        if not price or price <= 0:
            return None

        ema20 = indicators.get("ema20")
        ema50 = indicators.get("ema50")
        ema200 = indicators.get("ema200")
        atr = indicators.get("atr")
        rsi = indicators.get("rsi")
        bb_upper = indicators.get("bb_upper")
        bb_lower = indicators.get("bb_lower")
        high_52w = snapshot.high_52w
        low_52w = snapshot.low_52w

        if not atr or atr <= 0:
            # Estimate ATR as 2% of price if unavailable
            atr = price * 0.02

        # ─── Trend Direction & Magnitude ─────────────────────────────
        trend_bias = 0.0  # Positive = bullish, negative = bearish
        trend_evidence: list[str] = []

        if ema20 and ema50:
            if ema20 > ema50:
                trend_bias += 0.3
                trend_evidence.append("EMA20 > EMA50 (short-term bullish)")
            else:
                trend_bias -= 0.3
                trend_evidence.append("EMA20 < EMA50 (short-term bearish)")

        if ema50 and ema200:
            if ema50 > ema200:
                trend_bias += 0.4
                trend_evidence.append("EMA50 > EMA200 (long-term bullish)")
            else:
                trend_bias -= 0.4
                trend_evidence.append("EMA50 < EMA200 (long-term bearish)")

        if price and ema200:
            if price > ema200:
                trend_bias += 0.2
            else:
                trend_bias -= 0.2

        # RSI mean-reversion adjustment
        if rsi is not None:
            if rsi > 70:
                trend_bias -= 0.2
                trend_evidence.append(f"RSI {rsi:.0f} overbought — mean reversion pressure")
            elif rsi < 30:
                trend_bias += 0.2
                trend_evidence.append(f"RSI {rsi:.0f} oversold — bounce potential")

        # ─── Scenario Construction ───────────────────────────────────
        # 30-day projection using ATR-based ranges
        days = 30
        daily_move = atr  # 1 ATR per day is extreme; use fraction
        projected_range = daily_move * math.sqrt(days) * 0.5  # Square root of time scaling

        # Base case: trend continuation at reduced magnitude
        base_move = price * trend_bias * 0.05  # 5% scaled by trend bias
        base_target = price + base_move

        # Bull case: trend + ATR expansion
        bull_target = price + abs(base_move) + projected_range
        if bb_upper and bull_target < bb_upper:
            bull_target = max(bull_target, bb_upper)
        if high_52w and bull_target > high_52w * 1.1:
            bull_target = high_52w * 1.05  # Cap at 5% above 52w high

        # Bear case: counter-trend + ATR contraction
        bear_target = price - abs(base_move) - projected_range
        if bb_lower and bear_target > bb_lower:
            bear_target = min(bear_target, bb_lower)
        if low_52w and bear_target < low_52w * 0.9:
            bear_target = low_52w * 0.95  # Floor at 5% below 52w low
        bear_target = max(bear_target, price * 0.5)  # Never forecast > 50% decline

        # ─── Confidence Calculation ──────────────────────────────────
        data_points = sum(1 for v in [ema20, ema50, ema200, rsi, bb_upper, bb_lower, high_52w] if v is not None)
        base_confidence = min(0.75, data_points / 7 * 0.75)

        # Higher confidence when trend is clear
        if abs(trend_bias) > 0.5:
            base_confidence += 0.1

        bull_confidence = base_confidence * (0.6 if trend_bias > 0 else 0.3)
        bear_confidence = base_confidence * (0.6 if trend_bias < 0 else 0.3)
        base_confidence_final = base_confidence * 0.7

        # ─── Support / Resistance Levels ─────────────────────────────
        support_levels: list[float] = []
        resistance_levels: list[float] = []

        if ema50:
            if price > ema50:
                support_levels.append(round(ema50, 2))
            else:
                resistance_levels.append(round(ema50, 2))
        if ema200:
            if price > ema200:
                support_levels.append(round(ema200, 2))
            else:
                resistance_levels.append(round(ema200, 2))
        if bb_lower:
            support_levels.append(round(bb_lower, 2))
        if bb_upper:
            resistance_levels.append(round(bb_upper, 2))
        if high_52w:
            resistance_levels.append(round(high_52w, 2))
        if low_52w:
            support_levels.append(round(low_52w, 2))

        scenarios = [
            ForecastScenario(
                scenario="bull",
                target_price=round(bull_target, 2),
                upside_pct=round(((bull_target - price) / price) * 100, 2),
                confidence=round(bull_confidence, 2),
                timeframe_days=days,
                key_driver="Trend continuation with momentum expansion",
                support_levels=sorted(set(support_levels))[:3],
                resistance_levels=sorted(set(resistance_levels))[:3],
            ),
            ForecastScenario(
                scenario="base",
                target_price=round(base_target, 2),
                upside_pct=round(((base_target - price) / price) * 100, 2),
                confidence=round(base_confidence_final, 2),
                timeframe_days=days,
                key_driver="Current trend persists at moderated pace",
                support_levels=sorted(set(support_levels))[:3],
                resistance_levels=sorted(set(resistance_levels))[:3],
            ),
            ForecastScenario(
                scenario="bear",
                target_price=round(bear_target, 2),
                upside_pct=round(((bear_target - price) / price) * 100, 2),
                confidence=round(bear_confidence, 2),
                timeframe_days=days,
                key_driver="Trend reversal or macro deterioration",
                support_levels=sorted(set(support_levels))[:3],
                resistance_levels=sorted(set(resistance_levels))[:3],
            ),
        ]

        return scenarios

    def score(self, snapshot: StockSnapshot) -> ScoreBreakdown:
        """Compute forecast score based on projected upside/downside ratio.

        Higher score = more favorable risk/reward based on forecast scenarios.
        """
        scenarios = self.forecast(snapshot)

        if not scenarios:
            return ScoreBreakdown.unavailable(weight=0.04)

        bull = next((s for s in scenarios if s.scenario == "bull"), None)
        bear = next((s for s in scenarios if s.scenario == "bear"), None)
        base = next((s for s in scenarios if s.scenario == "base"), None)

        evidence: list[str] = []
        raw_score = 5.0

        if bull and bear:
            upside = abs(bull.upside_pct)
            downside = abs(bear.upside_pct)

            if downside > 0:
                rr_ratio = upside / downside
            else:
                rr_ratio = upside if upside > 0 else 1.0

            if rr_ratio > 3.0:
                raw_score += 3.0
                evidence.append(f"Excellent risk/reward: {rr_ratio:.1f}:1 (upside {upside:.1f}% vs downside {downside:.1f}%)")
            elif rr_ratio > 2.0:
                raw_score += 2.0
                evidence.append(f"Favorable risk/reward: {rr_ratio:.1f}:1")
            elif rr_ratio > 1.5:
                raw_score += 1.0
                evidence.append(f"Moderate risk/reward: {rr_ratio:.1f}:1")
            elif rr_ratio > 1.0:
                raw_score += 0.5
                evidence.append(f"Slightly positive risk/reward: {rr_ratio:.1f}:1")
            elif rr_ratio > 0.5:
                raw_score -= 0.5
                evidence.append(f"Unfavorable risk/reward: {rr_ratio:.1f}:1")
            else:
                raw_score -= 1.5
                evidence.append(f"Poor risk/reward: {rr_ratio:.1f}:1 — downside dominates")

            evidence.append(f"30-day bull target: {bull.target_price} (+{bull.upside_pct}%)")
            evidence.append(f"30-day bear target: {bear.target_price} ({bear.upside_pct}%)")

        if base:
            if base.upside_pct > 3:
                raw_score += 1.0
                evidence.append(f"Base case projects +{base.upside_pct}% upside")
            elif base.upside_pct < -3:
                raw_score -= 1.0
                evidence.append(f"Base case projects {base.upside_pct}% downside")
        # Cap heuristic forecast proxy score at 8.5/10 to reflect scenario proxy nature without artificial precision
        final_score = min(8.5, max(1.5, raw_score))
        avg_confidence = sum(s.confidence for s in scenarios) / len(scenarios) if scenarios else 0.3

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.04,
            confidence=round(avg_confidence, 2),
            data_quality=DataQuality.FULL,
            evidence=evidence,
        )
