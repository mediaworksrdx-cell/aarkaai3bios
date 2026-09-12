"""
AARKAAI – F&O / Options Analytics Engine

Scores stocks based on derivatives data: Put-Call Ratio, Open Interest
trends, IV percentile, and max pain alignment. Uses existing
modules/fno_analytics.py infrastructure.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)


class FnOEngine:
    """F&O derivatives intelligence scoring.

    Evaluates 4 dimensions:
      1. Put-Call Ratio (sentiment from options flow)
      2. Open Interest Trend (accumulation vs unwinding)
      3. IV Percentile (implied volatility regime)
      4. Max Pain Alignment (price vs max pain level)

    Only applicable to F&O-eligible stocks.
    """

    def score(self, snapshot: StockSnapshot, fno_eligible: bool = False) -> ScoreBreakdown:
        """Compute F&O score from options data in snapshot."""
        if not fno_eligible:
            return ScoreBreakdown(
                score=5.0, weight=0.05, confidence=0.0,
                data_quality=DataQuality.UNAVAILABLE,
                evidence=["Stock not F&O eligible — score neutral"],
            )

        options = snapshot.options_data or {}
        if not options:
            return ScoreBreakdown.unavailable(weight=0.05)

        evidence: list[str] = []
        raw_score = 5.0
        data_points = 0

        # ─── 1. Put-Call Ratio ───────────────────────────────────────
        pcr = options.get("pcr") or options.get("put_call_ratio")
        if pcr is not None:
            data_points += 1
            if pcr > 1.5:
                raw_score += 2.0
                evidence.append(f"High PCR: {pcr:.2f} — heavy put writing, bullish undertone")
            elif pcr > 1.0:
                raw_score += 1.0
                evidence.append(f"Moderately bullish PCR: {pcr:.2f}")
            elif pcr > 0.7:
                raw_score += 0.0
                evidence.append(f"Neutral PCR: {pcr:.2f}")
            elif pcr > 0.5:
                raw_score -= 0.5
                evidence.append(f"Low PCR: {pcr:.2f} — more call buying, potentially bearish")
            else:
                raw_score -= 1.0
                evidence.append(f"Very low PCR: {pcr:.2f} — excessive call buying, bearish signal")

        # ─── 2. Open Interest Trend ──────────────────────────────────
        oi_change = options.get("oi_change_pct") or options.get("oi_change")
        if oi_change is not None:
            data_points += 1
            change_pct = snapshot.change_pct or 0.0
            if oi_change > 0 and change_pct > 0:
                raw_score += 1.5
                evidence.append(f"Long buildup: OI +{oi_change:.1f}% with price up — bullish")
            elif oi_change > 0 and change_pct < 0:
                raw_score -= 1.0
                evidence.append(f"Short buildup: OI +{oi_change:.1f}% with price down — bearish")
            elif oi_change < 0 and change_pct > 0:
                raw_score += 0.5
                evidence.append(f"Short covering: OI {oi_change:.1f}% with price up")
            elif oi_change < 0 and change_pct < 0:
                raw_score -= 0.5
                evidence.append(f"Long unwinding: OI {oi_change:.1f}% with price down")

        # ─── 3. IV Percentile ────────────────────────────────────────
        iv_pct = options.get("iv_percentile") or options.get("iv")
        if iv_pct is not None:
            data_points += 1
            if iv_pct < 20:
                raw_score += 1.0
                evidence.append(f"Low IV percentile: {iv_pct:.0f}% — cheap options, potential move ahead")
            elif iv_pct < 50:
                raw_score += 0.5
                evidence.append(f"Normal IV: {iv_pct:.0f}%")
            elif iv_pct < 80:
                raw_score += 0.0
                evidence.append(f"Elevated IV: {iv_pct:.0f}% — options expensive")
            else:
                raw_score -= 0.5
                evidence.append(f"Extreme IV: {iv_pct:.0f}% — high fear/uncertainty")

        # ─── 4. Max Pain Alignment ───────────────────────────────────
        max_pain = options.get("max_pain")
        price = snapshot.price
        if max_pain and price and max_pain > 0:
            data_points += 1
            deviation = ((price - max_pain) / max_pain) * 100
            if abs(deviation) < 2:
                raw_score += 1.0
                evidence.append(f"Price near max pain ({max_pain:.0f}) — likely to stay pinned")
            elif deviation > 5:
                raw_score += 0.5
                evidence.append(f"Price {deviation:.1f}% above max pain — may pull back toward {max_pain:.0f}")
            elif deviation < -5:
                raw_score += 0.5
                evidence.append(f"Price {abs(deviation):.1f}% below max pain — may gravitate up toward {max_pain:.0f}")

        final_score = min(10.0, max(0.0, raw_score))

        if data_points == 0:
            return ScoreBreakdown.unavailable(weight=0.05)

        quality = DataQuality.FULL if data_points >= 3 else DataQuality.PARTIAL
        confidence = min(1.0, data_points / 4)

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.05,
            confidence=round(confidence, 2),
            data_quality=quality,
            evidence=evidence,
        )
