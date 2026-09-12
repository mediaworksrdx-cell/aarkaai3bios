"""
AARKAAI – Market Regime Detection Engine

Classifies the current market environment into one of 5 regimes:
  BULL_TREND, BEAR_TREND, RANGE_BOUND, HIGH_VOLATILITY, CRISIS

Uses breadth indicators (index-level EMA alignment, VIX proxy via ATR,
advance/decline ratios) and technical structure to determine regime.
All computations are deterministic.
"""
from __future__ import annotations

import logging
import math
from typing import Optional

from modules.screener.schemas import DataQuality, MarketRegime, ScoreBreakdown

logger = logging.getLogger(__name__)


class RegimeEngine:
    """Market regime classification and scoring.

    Evaluates 4 regime dimensions:
      1. Trend Structure (index-level EMA alignment proxy)
      2. Volatility Regime (ATR-based, BB width)
      3. Momentum Breadth (RSI distribution, MACD histogram sign)
      4. Risk Appetite (volume patterns, price distance from key MAs)

    The engine also determines the MarketRegime enum for adaptive weighting.
    """

    def detect_regime(self, index_indicators: dict | None = None) -> MarketRegime:
        """Classify market regime from broad market indicators.

        Args:
            index_indicators: Technical indicators for a broad index
                (e.g., NIFTY50, S&P500). If None, defaults to RANGE_BOUND.

        Returns:
            MarketRegime enum value.
        """
        if not index_indicators:
            return MarketRegime.RANGE_BOUND

        bull_signals = 0
        bear_signals = 0
        vol_signals = 0

        # EMA alignment
        price = index_indicators.get("price")
        ema50 = index_indicators.get("ema50")
        ema200 = index_indicators.get("ema200")
        ema20 = index_indicators.get("ema20")

        if price and ema50 and ema200:
            if price > ema50 > ema200:
                bull_signals += 2
            elif price < ema50 < ema200:
                bear_signals += 2
            elif price > ema200:
                bull_signals += 1
            else:
                bear_signals += 1

        # RSI regime
        rsi = index_indicators.get("rsi")
        if rsi is not None:
            if rsi > 65:
                bull_signals += 1
            elif rsi < 35:
                bear_signals += 1
            if rsi > 80 or rsi < 20:
                vol_signals += 1

        # ADX for trend strength
        adx = index_indicators.get("adx")
        if adx is not None:
            if adx > 30:
                # Strong trend — direction determined by other signals
                if bull_signals > bear_signals:
                    bull_signals += 1
                elif bear_signals > bull_signals:
                    bear_signals += 1
            elif adx < 15:
                # No trend
                vol_signals -= 1  # Reduce vol concern in quiet markets

        # Bollinger Band width as volatility proxy
        bb_upper = index_indicators.get("bb_upper")
        bb_lower = index_indicators.get("bb_lower")
        bb_middle = index_indicators.get("bb_middle")
        if bb_upper and bb_lower and bb_middle and bb_middle > 0:
            bb_width = (bb_upper - bb_lower) / bb_middle
            if bb_width > 0.08:
                vol_signals += 2
            elif bb_width > 0.05:
                vol_signals += 1

        # ATR as volatility proxy
        atr = index_indicators.get("atr")
        if atr and price and price > 0:
            atr_pct = (atr / price) * 100
            if atr_pct > 3.0:
                vol_signals += 2
            elif atr_pct > 2.0:
                vol_signals += 1

        # Classification
        if vol_signals >= 3 and bear_signals >= 2:
            return MarketRegime.CRISIS
        elif vol_signals >= 3:
            return MarketRegime.HIGH_VOLATILITY
        elif bull_signals >= 3 and bear_signals <= 1:
            return MarketRegime.BULL_TREND
        elif bear_signals >= 3 and bull_signals <= 1:
            return MarketRegime.BEAR_TREND
        else:
            return MarketRegime.RANGE_BOUND

    def score(self, snapshot_indicators: dict | None = None,
              market_regime: MarketRegime = MarketRegime.RANGE_BOUND) -> ScoreBreakdown:
        """Score how well a stock aligns with the current regime.

        Stocks that align with the prevailing regime get higher scores.
        Counter-trend stocks get lower scores (but not zero — contrarian value).
        """
        if not snapshot_indicators:
            return ScoreBreakdown.unavailable(weight=0.04)

        evidence: list[str] = []
        raw_score = 5.0  # Start neutral

        price = snapshot_indicators.get("price")
        ema50 = snapshot_indicators.get("ema50")
        ema200 = snapshot_indicators.get("ema200")
        rsi = snapshot_indicators.get("rsi")
        adx = snapshot_indicators.get("adx")
        volume_ratio = snapshot_indicators.get("volume_ratio")

        if market_regime == MarketRegime.BULL_TREND:
            evidence.append("Market regime: BULL TREND")
            # Reward stocks in uptrend alignment
            if price and ema50 and price > ema50:
                raw_score += 1.5
                evidence.append("Stock above EMA50 — aligned with bull regime")
            if rsi and 45 <= rsi <= 70:
                raw_score += 1.0
                evidence.append(f"RSI {rsi:.0f} in healthy bull zone")
            elif rsi and rsi > 75:
                raw_score -= 0.5
                evidence.append(f"RSI {rsi:.0f} overbought — caution in bull regime")
            if adx and adx > 25:
                raw_score += 0.5
                evidence.append(f"ADX {adx:.0f} confirms trend strength")

        elif market_regime == MarketRegime.BEAR_TREND:
            evidence.append("Market regime: BEAR TREND")
            # Reward defensive characteristics
            if price and ema200 and price > ema200:
                raw_score += 1.0
                evidence.append("Stock holding above EMA200 despite bear regime — relative strength")
            elif price and ema200 and price < ema200:
                raw_score -= 1.5
                evidence.append("Stock below EMA200 in bear regime — vulnerable")
            if rsi and rsi < 30:
                raw_score += 0.5
                evidence.append(f"RSI {rsi:.0f} deeply oversold — potential bounce")

        elif market_regime == MarketRegime.HIGH_VOLATILITY:
            evidence.append("Market regime: HIGH VOLATILITY")
            if volume_ratio and volume_ratio < 1.5:
                raw_score += 1.0
                evidence.append("Low relative volume — less exposed to volatility")
            if adx and adx < 20:
                raw_score += 0.5
                evidence.append("Low ADX — stock in consolidation, may weather volatility")

        elif market_regime == MarketRegime.CRISIS:
            evidence.append("Market regime: CRISIS")
            # In crisis, reward anything holding above key support
            if price and ema200 and price > ema200:
                raw_score += 2.0
                evidence.append("Holding above EMA200 during crisis — exceptional strength")
            else:
                raw_score -= 2.0
                evidence.append("Below EMA200 during crisis — high risk")

        else:
            evidence.append("Market regime: RANGE BOUND")
            # Range-bound rewards mean-reversion characteristics
            bb_pos = snapshot_indicators.get("bb_position")
            if bb_pos is not None:
                if 0.2 <= bb_pos <= 0.8:
                    raw_score += 1.0
                    evidence.append(f"BB position {bb_pos:.0%} — within trading range")
                elif bb_pos < 0.1:
                    raw_score += 0.5
                    evidence.append("Near lower BB — potential mean reversion")

        final_score = min(10.0, max(0.0, raw_score))

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.04,
            confidence=0.70,
            data_quality=DataQuality.FULL if snapshot_indicators else DataQuality.UNAVAILABLE,
            evidence=evidence,
        )
