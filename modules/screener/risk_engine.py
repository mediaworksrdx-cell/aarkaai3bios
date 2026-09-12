"""
AARKAAI – Risk Scoring Engine

Evaluates downside risk, drawdown exposure, leverage risk, volatility
risk, and liquidity risk for each stock. Higher risk scores indicate
LOWER risk (i.e., safer stock = higher score, riskier stock = lower score).
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)


class RiskEngine:
    """Multi-factor risk assessment scoring.

    Evaluates 5 risk dimensions (inverse-scored: high score = low risk):
      1. Beta Risk (market sensitivity)
      2. Drawdown Exposure (distance from 52-week high)
      3. Leverage Risk (debt/equity ratio)
      4. Volatility Risk (ATR as % of price, BB width)
      5. Liquidity Risk (volume adequacy)
    """

    def score(self, snapshot: StockSnapshot) -> ScoreBreakdown:
        """Compute risk score (higher = safer)."""
        evidence: list[str] = []
        raw_score = 5.0  # Start neutral
        data_points_available = 0
        data_points_total = 5

        indicators = snapshot.indicators or {}
        price = snapshot.price

        # ─── 1. Beta Risk (0-2 pts) ──────────────────────────────────
        beta = snapshot.beta
        if beta is not None:
            data_points_available += 1
            if beta < 0.5:
                raw_score += 2.0
                evidence.append(f"Very low beta: {beta:.2f} — defensive stock")
            elif beta < 0.8:
                raw_score += 1.5
                evidence.append(f"Low beta: {beta:.2f} — below-market volatility")
            elif beta < 1.2:
                raw_score += 1.0
                evidence.append(f"Market-neutral beta: {beta:.2f}")
            elif beta < 1.5:
                raw_score += 0.25
                evidence.append(f"Elevated beta: {beta:.2f} — above-market volatility")
            else:
                raw_score -= 0.5
                evidence.append(f"High beta: {beta:.2f} — significant market sensitivity")
        else:
            evidence.append("Beta data unavailable")

        # ─── 2. Drawdown Exposure (0-2 pts) ──────────────────────────
        high_52w = snapshot.high_52w
        if price and high_52w and high_52w > 0:
            data_points_available += 1
            drawdown = (high_52w - price) / high_52w * 100
            if drawdown < 5:
                raw_score += 2.0
                evidence.append(f"Minimal drawdown: {drawdown:.1f}% from 52w high")
            elif drawdown < 15:
                raw_score += 1.5
                evidence.append(f"Moderate drawdown: {drawdown:.1f}% from 52w high")
            elif drawdown < 30:
                raw_score += 0.5
                evidence.append(f"Significant drawdown: {drawdown:.1f}% from 52w high")
            elif drawdown < 50:
                raw_score -= 0.5
                evidence.append(f"Large drawdown: {drawdown:.1f}% from 52w high — recovery risk")
            else:
                raw_score -= 1.5
                evidence.append(f"Severe drawdown: {drawdown:.1f}% from 52w high — capital destruction risk")
        else:
            evidence.append("52-week high data unavailable")

        # ─── 3. Leverage Risk (0-2 pts) ──────────────────────────────
        debt_eq = snapshot.debt_equity
        if debt_eq is not None:
            data_points_available += 1
            if debt_eq < 0.2:
                raw_score += 2.0
                evidence.append(f"Near-zero leverage: D/E {debt_eq:.2f}")
            elif debt_eq < 0.5:
                raw_score += 1.5
                evidence.append(f"Conservative leverage: D/E {debt_eq:.2f}")
            elif debt_eq < 1.0:
                raw_score += 0.5
                evidence.append(f"Moderate leverage: D/E {debt_eq:.2f}")
            elif debt_eq < 2.0:
                raw_score -= 0.5
                evidence.append(f"Elevated leverage: D/E {debt_eq:.2f} — financial risk")
            else:
                raw_score -= 1.5
                evidence.append(f"Dangerous leverage: D/E {debt_eq:.2f} — solvency concern")
        else:
            evidence.append("Debt/Equity data unavailable")

        # ─── 4. Volatility Risk (0-2 pts) ────────────────────────────
        atr = indicators.get("atr")
        if atr and price and price > 0:
            data_points_available += 1
            atr_pct = (atr / price) * 100
            if atr_pct < 1.5:
                raw_score += 2.0
                evidence.append(f"Low volatility: ATR {atr_pct:.1f}% of price")
            elif atr_pct < 2.5:
                raw_score += 1.0
                evidence.append(f"Normal volatility: ATR {atr_pct:.1f}% of price")
            elif atr_pct < 4.0:
                raw_score += 0.0
                evidence.append(f"Elevated volatility: ATR {atr_pct:.1f}% of price")
            else:
                raw_score -= 1.0
                evidence.append(f"High volatility: ATR {atr_pct:.1f}% of price — large daily swings")
        else:
            # Use BB width as fallback
            bb_upper = indicators.get("bb_upper")
            bb_lower = indicators.get("bb_lower")
            if bb_upper and bb_lower and price and price > 0:
                data_points_available += 1
                bb_width_pct = ((bb_upper - bb_lower) / price) * 100
                if bb_width_pct < 5:
                    raw_score += 1.5
                    evidence.append(f"Tight Bollinger Bands ({bb_width_pct:.1f}%) — low volatility")
                elif bb_width_pct < 10:
                    raw_score += 0.5
                    evidence.append(f"Normal BB width ({bb_width_pct:.1f}%)")
                else:
                    raw_score -= 0.5
                    evidence.append(f"Wide Bollinger Bands ({bb_width_pct:.1f}%) — elevated volatility")
            else:
                evidence.append("Volatility data unavailable")

        # ─── 5. Liquidity Risk (0-2 pts) ─────────────────────────────
        volume_ratio = indicators.get("volume_ratio")
        volume_sma = indicators.get("volume_sma")
        market_cap = snapshot.market_cap

        if volume_sma is not None:
            data_points_available += 1
            if volume_sma > 5_000_000:
                raw_score += 2.0
                evidence.append(f"High liquidity: avg volume {volume_sma:,.0f}")
            elif volume_sma > 1_000_000:
                raw_score += 1.5
                evidence.append(f"Good liquidity: avg volume {volume_sma:,.0f}")
            elif volume_sma > 200_000:
                raw_score += 0.5
                evidence.append(f"Moderate liquidity: avg volume {volume_sma:,.0f}")
            else:
                raw_score -= 0.5
                evidence.append(f"Low liquidity: avg volume {volume_sma:,.0f} — execution risk")
        elif market_cap:
            data_points_available += 1
            if market_cap > 100e9:
                raw_score += 1.5
                evidence.append("Large market cap — likely liquid")
            elif market_cap > 10e9:
                raw_score += 0.5
            else:
                evidence.append("Small market cap — potential liquidity risk")
        else:
            evidence.append("Liquidity data unavailable")

        # ─── Normalize ───────────────────────────────────────────────
        final_score = min(10.0, max(0.0, raw_score))

        if data_points_available == 0:
            return ScoreBreakdown.unavailable(weight=0.10)
        elif data_points_available < 3:
            quality = DataQuality.PARTIAL
        else:
            quality = DataQuality.FULL

        confidence = min(1.0, data_points_available / data_points_total)

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.10,
            confidence=round(confidence, 2),
            data_quality=quality,
            evidence=evidence,
        )
