"""
AARKAAI – Valuation Scoring Engine

Scores stocks on relative and absolute valuation metrics: P/E vs sector,
P/B, EV/EBITDA, 52-week position, and PEG ratio approximation.
All computations are deterministic.
"""
from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

from modules.screener.schemas import DataQuality, ScoreBreakdown

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)

# ─── Sector median P/E benchmarks ────────────────────────────────────────────
# Approximate trailing P/E medians (NSE + US) as of 2026-Q2.

_SECTOR_PE_MEDIANS: dict[str, float] = {
    "banking_financial": 14.0,
    "it_software": 28.0,
    "pharma_healthcare": 30.0,
    "auto_ancillaries": 22.0,
    "gems_jewellery": 45.0,
    "textiles_apparel": 25.0,
    "defence_aerospace": 35.0,
    "power_energy": 18.0,
    "infrastructure": 20.0,
    "fmcg_consumer": 50.0,
    "chemicals_materials": 30.0,
    "real_estate": 25.0,
    "us_tech": 32.0,
    "us_finance": 12.0,
    "us_healthcare": 22.0,
}

_SECTOR_PB_MEDIANS: dict[str, float] = {
    "banking_financial": 2.0,
    "it_software": 8.0,
    "pharma_healthcare": 4.0,
    "auto_ancillaries": 4.0,
    "gems_jewellery": 6.0,
    "textiles_apparel": 3.0,
    "defence_aerospace": 5.0,
    "power_energy": 2.5,
    "infrastructure": 3.0,
    "fmcg_consumer": 12.0,
    "chemicals_materials": 4.0,
    "real_estate": 2.5,
    "us_tech": 10.0,
    "us_finance": 1.5,
    "us_healthcare": 5.0,
}

_SECTOR_EVEBITDA_MEDIANS: dict[str, float] = {
    "banking_financial": 10.0,
    "it_software": 20.0,
    "pharma_healthcare": 18.0,
    "auto_ancillaries": 12.0,
    "gems_jewellery": 20.0,
    "textiles_apparel": 12.0,
    "defence_aerospace": 18.0,
    "power_energy": 10.0,
    "infrastructure": 12.0,
    "fmcg_consumer": 30.0,
    "chemicals_materials": 15.0,
    "real_estate": 15.0,
    "us_tech": 25.0,
    "us_finance": 8.0,
    "us_healthcare": 15.0,
}


class ValuationEngine:
    """Relative and absolute valuation scoring.

    Evaluates 5 valuation dimensions:
      1. P/E Relative to Sector (deep value, value, fair, expensive)
      2. P/B Ratio (book value coverage)
      3. EV/EBITDA (enterprise value efficiency)
      4. 52-Week Range Position (contrarian value signal)
      5. PEG Approximation (growth-adjusted value)

    Higher scores indicate BETTER value (cheaper stock = higher score).
    """

    def score(self, snapshot: StockSnapshot, sector: str = "") -> ScoreBreakdown:
        """Compute valuation score from StockSnapshot data."""
        evidence: list[str] = []
        raw_score = 0.0
        max_raw = 10.0
        data_points_available = 0
        data_points_total = 5

        pe = snapshot.pe
        pb = snapshot.pb
        ev_ebitda = snapshot.ev_ebitda
        price = snapshot.price
        high_52w = snapshot.high_52w
        low_52w = snapshot.low_52w
        eps = snapshot.eps
        rev_growth = snapshot.revenue_growth

        # ─── 1. P/E Relative to Sector (0-3 pts) ────────────────────
        sector_pe = _SECTOR_PE_MEDIANS.get(sector, 25.0)

        if pe is not None and pe > 0:
            data_points_available += 1
            pe_ratio_to_sector = pe / sector_pe

            if pe_ratio_to_sector < 0.5:
                raw_score += 3.0
                evidence.append(f"Deep value: P/E {pe:.1f}x is {pe_ratio_to_sector:.0%} of sector median ({sector_pe:.0f}x)")
            elif pe_ratio_to_sector < 0.7:
                raw_score += 2.5
                evidence.append(f"Value zone: P/E {pe:.1f}x is {pe_ratio_to_sector:.0%} of sector median ({sector_pe:.0f}x)")
            elif pe_ratio_to_sector < 1.0:
                raw_score += 2.0
                evidence.append(f"Below sector median: P/E {pe:.1f}x vs sector {sector_pe:.0f}x")
            elif pe_ratio_to_sector < 1.3:
                raw_score += 1.0
                evidence.append(f"Near sector median: P/E {pe:.1f}x vs sector {sector_pe:.0f}x")
            elif pe_ratio_to_sector < 1.5:
                raw_score += 0.5
                evidence.append(f"Above sector median: P/E {pe:.1f}x vs sector {sector_pe:.0f}x")
            else:
                evidence.append(f"Premium valuation: P/E {pe:.1f}x is {pe_ratio_to_sector:.0%} of sector median ({sector_pe:.0f}x)")
        elif pe is not None and pe < 0:
            data_points_available += 1
            evidence.append(f"Negative P/E ({pe:.1f}x) — company is loss-making")
        else:
            evidence.append("P/E data unavailable")

        # ─── 2. P/B Ratio (0-2 pts) ─────────────────────────────────
        sector_pb = _SECTOR_PB_MEDIANS.get(sector, 4.0)

        if pb is not None and pb > 0:
            data_points_available += 1
            if pb < 1.0:
                raw_score += 2.0
                evidence.append(f"Trading below book value: P/B {pb:.2f}x — potential deep value")
            elif pb < 2.0:
                raw_score += 1.5
                evidence.append(f"Attractive P/B: {pb:.2f}x")
            elif pb < sector_pb:
                raw_score += 1.0
                evidence.append(f"P/B {pb:.2f}x below sector median ({sector_pb:.1f}x)")
            elif pb < sector_pb * 1.5:
                raw_score += 0.5
                evidence.append(f"P/B {pb:.2f}x near sector median ({sector_pb:.1f}x)")
            else:
                evidence.append(f"Elevated P/B: {pb:.2f}x vs sector median {sector_pb:.1f}x")
        else:
            evidence.append("P/B data unavailable")

        # ─── 3. EV/EBITDA (0-2 pts) ──────────────────────────────────
        sector_ev = _SECTOR_EVEBITDA_MEDIANS.get(sector, 15.0)

        if ev_ebitda is not None and ev_ebitda > 0:
            data_points_available += 1
            if ev_ebitda < sector_ev * 0.6:
                raw_score += 2.0
                evidence.append(f"Deep value EV/EBITDA: {ev_ebitda:.1f}x vs sector {sector_ev:.0f}x")
            elif ev_ebitda < sector_ev:
                raw_score += 1.5
                evidence.append(f"Below-sector EV/EBITDA: {ev_ebitda:.1f}x vs sector {sector_ev:.0f}x")
            elif ev_ebitda < sector_ev * 1.3:
                raw_score += 0.5
                evidence.append(f"Near-sector EV/EBITDA: {ev_ebitda:.1f}x vs sector {sector_ev:.0f}x")
            else:
                evidence.append(f"Premium EV/EBITDA: {ev_ebitda:.1f}x vs sector {sector_ev:.0f}x")
        else:
            evidence.append("EV/EBITDA data unavailable")

        # ─── 4. 52-Week Range Position (0-2 pts) ─────────────────────
        # Contrarian value: stocks closer to 52w low may offer value
        if price and high_52w and low_52w and high_52w > low_52w:
            data_points_available += 1
            range_52w = high_52w - low_52w
            pct_from_low = (price - low_52w) / range_52w

            if pct_from_low < 0.15:
                raw_score += 2.0
                evidence.append(f"Near 52-week low ({pct_from_low:.0%} from bottom) — deep value territory")
            elif pct_from_low < 0.30:
                raw_score += 1.5
                evidence.append(f"Lower quartile of 52-week range ({pct_from_low:.0%}) — value zone")
            elif pct_from_low < 0.50:
                raw_score += 1.0
                evidence.append(f"Mid-range of 52-week range ({pct_from_low:.0%})")
            elif pct_from_low < 0.75:
                raw_score += 0.5
                evidence.append(f"Upper half of 52-week range ({pct_from_low:.0%})")
            else:
                evidence.append(f"Near 52-week high ({pct_from_low:.0%}) — valuation may be stretched")
        else:
            evidence.append("52-week range data unavailable")

        # ─── 5. PEG Ratio Approximation (0-1 pt) ─────────────────────
        if pe is not None and pe > 0 and rev_growth is not None:
            data_points_available += 1
            growth_pct = rev_growth * 100 if abs(rev_growth) < 1 else rev_growth
            if growth_pct > 0:
                peg = pe / growth_pct
                if peg < 0.5:
                    raw_score += 1.0
                    evidence.append(f"Attractive PEG ratio: {peg:.2f} (P/E {pe:.1f}x ÷ Growth {growth_pct:.1f}%)")
                elif peg < 1.0:
                    raw_score += 0.75
                    evidence.append(f"Reasonable PEG: {peg:.2f}")
                elif peg < 2.0:
                    raw_score += 0.5
                    evidence.append(f"Fair PEG: {peg:.2f}")
                else:
                    evidence.append(f"Elevated PEG: {peg:.2f} — growth not justifying valuation")
            else:
                evidence.append("Negative revenue growth — PEG not applicable")
        else:
            evidence.append("PEG data unavailable (missing P/E or growth data)")

        # ─── Normalize to 0-10 ───────────────────────────────────────
        final_score = min(10.0, max(0.0, (raw_score / max_raw) * 10.0))

        # Data quality
        if data_points_available == 0:
            quality = DataQuality.UNAVAILABLE
            final_score = 5.0
            evidence = ["No valuation data available — score set to neutral baseline"]
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
