"""
AARKAAI – Fundamental Quality Engine

Scores stocks on earnings quality, profitability, balance-sheet health,
and revenue trajectory. All computations are deterministic from yfinance
fundamental data — no LLM involvement.
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)

# ─── Sector median benchmarks (approximate trailing values) ──────────────────
# Used for relative valuation within FundamentalEngine.
# Source: Screener.in / NSE industry medians as of 2026-Q2.

_SECTOR_ROE_MEDIANS: dict[str, float] = {
    "banking_financial": 14.0,
    "it_software": 22.0,
    "pharma_healthcare": 15.0,
    "auto_ancillaries": 14.0,
    "gems_jewellery": 18.0,
    "textiles_apparel": 12.0,
    "defence_aerospace": 16.0,
    "power_energy": 12.0,
    "infrastructure": 10.0,
    "fmcg_consumer": 25.0,
    "chemicals_materials": 14.0,
    "real_estate": 10.0,
    "us_tech": 25.0,
    "us_finance": 12.0,
    "us_healthcare": 18.0,
}

_SECTOR_MARGIN_MEDIANS: dict[str, float] = {
    "banking_financial": 20.0,
    "it_software": 18.0,
    "pharma_healthcare": 15.0,
    "auto_ancillaries": 8.0,
    "gems_jewellery": 7.0,
    "textiles_apparel": 6.0,
    "defence_aerospace": 12.0,
    "power_energy": 15.0,
    "infrastructure": 8.0,
    "fmcg_consumer": 15.0,
    "chemicals_materials": 12.0,
    "real_estate": 18.0,
    "us_tech": 22.0,
    "us_finance": 25.0,
    "us_healthcare": 18.0,
}


class FundamentalEngine:
    """Earnings quality, profitability, and financial health scoring.

    Evaluates 5 fundamental dimensions:
      1. Earnings Quality (EPS positivity and growth)
      2. Profitability (ROE, ROA, profit margins)
      3. Balance Sheet Health (Debt/Equity, current ratio)
      4. Revenue Trajectory (revenue growth rate)
      5. Dividend & Shareholder Returns (yield, if applicable)

    Each dimension contributes 0-2 raw points, normalized to 0-10 final score.
    """

    def score(self, snapshot: StockSnapshot, sector: str = "") -> ScoreBreakdown:
        """Compute fundamental quality score from StockSnapshot data."""
        evidence: list[str] = []
        raw_score = 0.0
        max_raw = 10.0
        data_points_available = 0
        data_points_total = 5

        # Extract fundamentals from snapshot
        eps = snapshot.eps
        pe = snapshot.pe
        roe = snapshot.roe
        roa = snapshot.roa
        debt_eq = snapshot.debt_equity
        div_yield = snapshot.dividend_yield
        rev_growth = snapshot.revenue_growth
        margin = snapshot.profit_margin

        # ─── 1. Earnings Quality (0-2 pts) ───────────────────────────
        if eps is not None:
            data_points_available += 1
            if eps > 0:
                raw_score += 1.0
                evidence.append(f"Positive trailing EPS: {eps:.2f}")
                # Bonus for strong EPS
                if eps > 5.0:
                    raw_score += 0.5
                    evidence.append(f"Strong EPS > 5.0")
                elif eps > 2.0:
                    raw_score += 0.25
            else:
                evidence.append(f"Negative trailing EPS: {eps:.2f} — earnings quality concern")
        else:
            evidence.append("EPS data unavailable")

        # Additional EPS quality from P/E rationality
        if pe is not None:
            if 0 < pe <= 25:
                raw_score += 0.5
                evidence.append(f"Reasonable P/E ratio: {pe:.1f}x")
            elif pe > 50:
                raw_score -= 0.25
                evidence.append(f"Elevated P/E ratio: {pe:.1f}x — potential overvaluation")

        # ─── 2. Profitability (0-2 pts) ──────────────────────────────
        sector_roe_median = _SECTOR_ROE_MEDIANS.get(sector, 15.0)
        sector_margin_median = _SECTOR_MARGIN_MEDIANS.get(sector, 12.0)

        if roe is not None:
            data_points_available += 1
            roe_pct = roe * 100 if roe < 1 else roe  # Handle both 0.15 and 15.0 formats
            if roe_pct > 25:
                raw_score += 2.0
                evidence.append(f"Excellent ROE: {roe_pct:.1f}% (sector median: {sector_roe_median:.0f}%)")
            elif roe_pct > 15:
                raw_score += 1.5
                evidence.append(f"Strong ROE: {roe_pct:.1f}% (above sector median)")
            elif roe_pct > 10:
                raw_score += 1.0
                evidence.append(f"Adequate ROE: {roe_pct:.1f}%")
            elif roe_pct > 0:
                raw_score += 0.5
                evidence.append(f"Below-average ROE: {roe_pct:.1f}%")
            else:
                evidence.append(f"Negative ROE: {roe_pct:.1f}% — profitability issue")
        else:
            evidence.append("ROE data unavailable")

        if margin is not None:
            margin_pct = margin * 100 if abs(margin) < 1 else margin
            if margin_pct > sector_margin_median * 1.2:
                raw_score += 0.5
                evidence.append(f"Profit margin {margin_pct:.1f}% exceeds sector median")
            elif margin_pct > 0:
                raw_score += 0.25
            else:
                evidence.append(f"Negative profit margin: {margin_pct:.1f}%")

        # ─── 3. Balance Sheet Health (0-2 pts) ───────────────────────
        if debt_eq is not None:
            data_points_available += 1
            if debt_eq < 0.3:
                raw_score += 2.0
                evidence.append(f"Very low Debt/Equity: {debt_eq:.2f} — strong balance sheet")
            elif debt_eq < 0.5:
                raw_score += 1.5
                evidence.append(f"Low Debt/Equity: {debt_eq:.2f} — healthy leverage")
            elif debt_eq < 1.0:
                raw_score += 1.0
                evidence.append(f"Moderate Debt/Equity: {debt_eq:.2f}")
            elif debt_eq < 2.0:
                raw_score += 0.5
                evidence.append(f"Elevated Debt/Equity: {debt_eq:.2f} — monitor leverage")
            else:
                evidence.append(f"High Debt/Equity: {debt_eq:.2f} — leverage risk")
        else:
            evidence.append("Debt/Equity data unavailable")

        # ─── 4. Revenue Trajectory (0-2 pts) ─────────────────────────
        if rev_growth is not None:
            data_points_available += 1
            growth_pct = rev_growth * 100 if abs(rev_growth) < 1 else rev_growth
            if growth_pct > 25:
                raw_score += 2.0
                evidence.append(f"Exceptional revenue growth: {growth_pct:.1f}%")
            elif growth_pct > 15:
                raw_score += 1.5
                evidence.append(f"Strong revenue growth: {growth_pct:.1f}%")
            elif growth_pct > 5:
                raw_score += 1.0
                evidence.append(f"Moderate revenue growth: {growth_pct:.1f}%")
            elif growth_pct > 0:
                raw_score += 0.5
                evidence.append(f"Modest revenue growth: {growth_pct:.1f}%")
            else:
                evidence.append(f"Revenue decline: {growth_pct:.1f}%")
        else:
            evidence.append("Revenue growth data unavailable")

        # ─── 5. Dividend & Shareholder Returns (0-2 pts) ─────────────
        if div_yield is not None:
            data_points_available += 1
            yield_pct = div_yield * 100 if div_yield < 1 else div_yield
            if yield_pct > 3.0:
                raw_score += 1.5
                evidence.append(f"Attractive dividend yield: {yield_pct:.2f}%")
            elif yield_pct > 1.5:
                raw_score += 1.0
                evidence.append(f"Moderate dividend yield: {yield_pct:.2f}%")
            elif yield_pct > 0.5:
                raw_score += 0.5
                evidence.append(f"Nominal dividend yield: {yield_pct:.2f}%")
            else:
                raw_score += 0.25
                evidence.append(f"Minimal dividend yield: {yield_pct:.2f}%")
        else:
            # No dividend is fine for growth stocks
            evidence.append("No dividend data (growth stock or data unavailable)")
            # Still count as available since absence is informative
            data_points_available += 1
            raw_score += 0.25

        # ─── ROA bonus ───────────────────────────────────────────────
        if roa is not None:
            roa_pct = roa * 100 if abs(roa) < 1 else roa
            if roa_pct > 10:
                raw_score += 0.5
                evidence.append(f"Strong ROA: {roa_pct:.1f}%")

        # ─── Normalize to 0-10 ───────────────────────────────────────
        final_score = min(10.0, max(0.0, (raw_score / max_raw) * 10.0))

        # Determine data quality
        if data_points_available == 0:
            quality = DataQuality.UNAVAILABLE
            final_score = 5.0  # Neutral baseline when no data
            evidence = ["No fundamental data available — score set to neutral baseline"]
        elif data_points_available < 3:
            quality = DataQuality.PARTIAL
        else:
            quality = DataQuality.FULL

        # Confidence based on data availability
        confidence = min(1.0, data_points_available / data_points_total)

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.15,
            confidence=round(confidence, 2),
            data_quality=quality,
            evidence=evidence,
        )
