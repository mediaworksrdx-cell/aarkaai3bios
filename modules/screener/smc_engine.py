"""
AARKAAI – Smart Money Concepts (SMC) / Market Structure Engine

Scores stocks based on market structure analysis: Break of Structure (BOS),
Change of Character (CHoCH), order block alignment, fair value gaps,
and liquidity sweep detection. All computations are deterministic
from OHLCV and indicator data.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)


class SMCEngine:
    """Smart Money Concepts and market structure scoring.

    Evaluates 4 SMC dimensions:
      1. Market Structure (higher highs/lows vs lower highs/lows)
      2. Order Block Alignment (price near key institutional levels)
      3. Fair Value Gap (FVG) Detection (unfilled gaps as magnets)
      4. Liquidity Sweep Signals (stop hunts followed by reversal)
    """

    def score(self, snapshot: StockSnapshot) -> ScoreBreakdown:
        """Compute SMC market structure score."""
        indicators = snapshot.indicators or {}
        price = snapshot.price

        if not price or not indicators:
            return ScoreBreakdown.unavailable(weight=0.05)

        evidence: list[str] = []
        raw_score = 5.0
        data_points = 0

        ema20 = indicators.get("ema20")
        ema50 = indicators.get("ema50")
        ema200 = indicators.get("ema200")
        high_52w = snapshot.high_52w
        low_52w = snapshot.low_52w
        bb_upper = indicators.get("bb_upper")
        bb_lower = indicators.get("bb_lower")
        bb_middle = indicators.get("bb_middle")
        vwap = indicators.get("vwap")
        atr = indicators.get("atr")
        rsi = indicators.get("rsi")
        volume_ratio = indicators.get("volume_ratio")
        supertrend_dir = indicators.get("supertrend_direction")
        patterns = indicators.get("patterns") or []

        # ─── 1. Market Structure (Higher Highs / Lower Lows) ─────────
        if ema20 and ema50 and ema200:
            data_points += 1
            if price > ema20 > ema50 > ema200:
                raw_score += 2.0
                evidence.append("Bullish market structure: Price > EMA20 > EMA50 > EMA200 (Higher Highs)")
            elif price > ema50 > ema200:
                raw_score += 1.0
                evidence.append("Constructive structure: Price > EMA50 > EMA200")
            elif price < ema20 < ema50 < ema200:
                raw_score -= 1.5
                evidence.append("Bearish market structure: Price < EMA20 < EMA50 < EMA200 (Lower Lows)")
            elif price < ema50 < ema200:
                raw_score -= 1.0
                evidence.append("Deteriorating structure: Price < EMA50 < EMA200")
            else:
                evidence.append("Mixed market structure — no clear directional bias")

            # BOS/CHoCH detection via supertrend
            if supertrend_dir == 1 and price > ema50:
                raw_score += 0.5
                evidence.append("Supertrend bullish — potential Break of Structure (BOS) to upside")
            elif supertrend_dir == -1 and price < ema50:
                raw_score -= 0.5
                evidence.append("Supertrend bearish — potential BOS to downside")

        # ─── 2. Order Block Alignment ────────────────────────────────
        if vwap and price:
            data_points += 1
            vwap_deviation = ((price - vwap) / vwap) * 100 if vwap > 0 else 0
            if abs(vwap_deviation) < 1.0:
                raw_score += 1.5
                evidence.append(f"Price at VWAP ({vwap_deviation:+.1f}%) — institutional order block zone")
            elif 0 < vwap_deviation < 2.5:
                raw_score += 0.5
                evidence.append(f"Price slightly above VWAP ({vwap_deviation:+.1f}%)")
            elif vwap_deviation < -2.5:
                raw_score -= 0.5
                evidence.append(f"Price below VWAP ({vwap_deviation:+.1f}%) — below institutional value")
            elif vwap_deviation > 3.0:
                evidence.append(f"Price extended above VWAP ({vwap_deviation:+.1f}%) — overextended from order block")

        # ─── 3. Fair Value Gap Detection ─────────────────────────────
        if bb_upper and bb_lower and bb_middle and atr and price:
            data_points += 1
            bb_width = bb_upper - bb_lower
            # FVG proxy: when price gaps beyond normal BB range
            if price > bb_upper:
                if volume_ratio and volume_ratio > 1.5:
                    raw_score += 1.0
                    evidence.append("Price above upper BB with volume — FVG breakout (bullish)")
                else:
                    raw_score -= 0.5
                    evidence.append("Price above upper BB without volume — potential false breakout")
            elif price < bb_lower:
                if volume_ratio and volume_ratio > 1.5:
                    raw_score -= 1.0
                    evidence.append("Price below lower BB with volume — FVG breakdown (bearish)")
                else:
                    raw_score += 0.5
                    evidence.append("Price below lower BB without volume — potential mean reversion FVG fill")
            else:
                # Price within BBs — check for narrow FVG zones
                if bb_width and atr and bb_width < atr * 1.5:
                    raw_score += 0.5
                    evidence.append("Tight BB squeeze — FVG expansion likely")

        # ─── 4. Liquidity Sweep Detection ────────────────────────────
        if high_52w and low_52w and price and atr:
            data_points += 1
            # Sweep detection: price very close to 52w extreme then reversing
            dist_from_high = (high_52w - price) / high_52w * 100 if high_52w > 0 else 0
            dist_from_low = (price - low_52w) / low_52w * 100 if low_52w > 0 else 0

            if dist_from_high < 2.0 and rsi and rsi > 70:
                raw_score -= 0.5
                evidence.append(f"Near 52w high with overbought RSI — potential liquidity grab at highs")
            elif dist_from_low < 5.0 and rsi and rsi < 35:
                raw_score += 1.0
                evidence.append(f"Near 52w low with oversold RSI — potential liquidity sweep at lows (reversal)")

            # Candlestick pattern confirmation
            if patterns:
                for p in patterns:
                    if p in ("hammer", "bullish_engulfing"):
                        raw_score += 0.5
                        evidence.append(f"Bullish candlestick pattern ({p}) — smart money absorption")
                        break
                    elif p in ("bearish_engulfing",):
                        raw_score -= 0.5
                        evidence.append(f"Bearish candlestick pattern ({p}) — distribution")
                        break

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
