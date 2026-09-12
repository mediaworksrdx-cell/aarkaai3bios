"""
AARKAAI – Sector Rotation Engine

Scores stocks based on their sector's position in the economic cycle,
relative sector momentum, and sector-specific risk factors.
Implements a simplified sector rotation model.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

from modules.screener.schemas import DataQuality, ScoreBreakdown
from modules.screener.universe import UniverseManager

if TYPE_CHECKING:
    from modules.screener.data_fetcher import StockSnapshot

logger = logging.getLogger(__name__)

# ─── Sector Cycle Positioning ────────────────────────────────────────────────
# Where each sector typically performs best in the economic cycle.
# Phase: EARLY_RECOVERY → MID_EXPANSION → LATE_EXPANSION → CONTRACTION
# Score reflects a static "neutral cycle" baseline. Dynamic regime adjustment
# in Phase 3 will shift these weights based on detected macro regime.

_SECTOR_CYCLE_SCORE: dict[str, float] = {
    # Defensive sectors — perform in all regimes
    "fmcg_consumer": 7.0,
    "pharma_healthcare": 7.0,
    "power_energy": 6.5,
    # Cyclical — best in expansion
    "banking_financial": 6.0,
    "auto_ancillaries": 5.5,
    "infrastructure": 5.5,
    "real_estate": 5.0,
    "chemicals_materials": 5.5,
    # Growth — best in bull markets
    "it_software": 6.0,
    "defence_aerospace": 6.5,
    # Niche / high-beta
    "gems_jewellery": 5.0,
    "textiles_apparel": 5.0,
    # US sectors
    "us_tech": 6.0,
    "us_finance": 5.5,
    "us_healthcare": 7.0,
}

# Sector-specific risk factors (higher = riskier sector)
_SECTOR_RISK: dict[str, float] = {
    "banking_financial": 0.6,
    "it_software": 0.4,
    "pharma_healthcare": 0.3,
    "auto_ancillaries": 0.5,
    "gems_jewellery": 0.7,
    "textiles_apparel": 0.6,
    "defence_aerospace": 0.4,
    "power_energy": 0.4,
    "infrastructure": 0.6,
    "fmcg_consumer": 0.2,
    "chemicals_materials": 0.5,
    "real_estate": 0.8,
    "us_tech": 0.5,
    "us_finance": 0.5,
    "us_healthcare": 0.3,
}

_SECTOR_CATALYSTS: dict[str, str] = {
    "banking_financial": "Credit growth acceleration, robust asset quality (low NPAs), and capital adequacy supporting earnings momentum.",
    "it_software": "Cost optimization transformations, enterprise generative AI workloads, and cross-border tech discretionary spend recovery.",
    "pharma_healthcare": "Domestic acute/chronic formulation demand, US specialty pipeline monetization, and sustained hospital ARPOB expansion.",
    "auto_ancillaries": "Premiumization across passenger vehicles, commercial fleet renewal cycle, and EV components localization.",
    "fmcg_consumer": "Rural volume demand recovery, favorable commodity input pricing, and non-cyclical staple pricing power.",
    "chemicals_materials": "Infrastructure capex demand, supply realignment, and domestic steel/cement consumption.",
    "power_energy": "Peak power demand surges, aggressive renewable energy transition capex, and transmission network expansion.",
    "real_estate": "Multi-year residential housing demand upcycle, luxury inventory presales velocity, and balance sheet deleveraging.",
    "infrastructure": "Government budgetary capital outlays, national highway/railway corridor execution, and commercial order book visibility.",
    "defence_aerospace": "Indigenization defense mandates (Make in India), export defense corridor agreements, and expanding order backlogs.",
    "us_tech": "Hyperscale cloud capex, AI hardware infrastructure buildout, and enterprise software margin discipline.",
    "us_finance": "Net interest income stabilization, investment banking deal pipeline revival, and solid balance sheet capitalization.",
    "us_healthcare": "GLP-1 metabolic drug demand, medical device innovation, and defensive secular healthcare demographic tailwinds.",
}


@dataclass
class SectorMetric:
    """Individual sector quantitative performance and breadth metrics."""
    sector_key: str
    display_name: str
    index_name: str
    index_symbol: str
    current_level: float
    change_1d_pct: float
    change_1m_pct: float
    change_3m_pct: float
    rsi: float
    trend: str                         # "BULLISH" | "BEARISH" | "NEUTRAL"
    breadth_pct: float                 # % of checked constituents > 50-day EMA
    top_drivers: list[dict]            # [{'symbol': 'DLF', 'name': 'DLF Limited', 'price': 850.0, 'change_1d': 2.4}]
    composite_score: float             # 0.0 to 10.0
    conviction: str                    # "HIGH" | "MEDIUM" | "LOW"
    signal: str                        # "OVERWEIGHT" | "ACCUMULATE" | "NEUTRAL" | "UNDERWEIGHT"
    catalyst: str = ""


@dataclass
class SectorScreenResponse:
    """Consolidated response object for sector-level screening."""
    exchange: str
    as_of: str
    timeframe: str
    results: list[SectorMetric] = field(default_factory=list)
    execution_time_ms: float = 0.0
    market_regime: str = "Range Bound"
    total_sectors: int = 0


def _rsi_wilder(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's exponential smoothing RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


class SectorEngine:
    """Sector rotation, relative positioning, and sectoral performance screening engine.

    Evaluates:
      1. Single-stock relative sector scoring (used in stock screener).
      2. Comprehensive sector index screening & rotation ranking (used for sector queries).
    """

    def __init__(self, cache_ttl: int = 60) -> None:
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[SectorScreenResponse, float]] = {}

    def score(self, snapshot: StockSnapshot, sector: str = "") -> ScoreBreakdown:
        """Compute sector rotation score."""
        if not sector:
            return ScoreBreakdown.unavailable(weight=0.0)

        evidence: list[str] = []
        data_points = 0

        # ─── 1. Sector Cycle Position ────────────────────────────────
        cycle_score = _SECTOR_CYCLE_SCORE.get(sector, 5.0)
        data_points += 1

        sector_display = sector.replace("_", " ").title()
        if cycle_score >= 7.0:
            evidence.append(f"{sector_display} is a defensive sector — resilient across cycles (base: {cycle_score:.0f})")
        elif cycle_score >= 6.0:
            evidence.append(f"{sector_display} has strong cycle positioning (base: {cycle_score:.0f})")
        elif cycle_score >= 5.5:
            evidence.append(f"{sector_display} is a mid-cycle sector (base: {cycle_score:.0f})")
        else:
            evidence.append(f"{sector_display} is a cyclical/niche sector (base: {cycle_score:.0f})")

        raw_score = cycle_score

        # ─── 2. Stock-vs-Sector Relative Strength ────────────────────
        indicators = snapshot.indicators or {}
        price = snapshot.price
        ema50 = indicators.get("ema50")
        ema200 = indicators.get("ema200")
        rsi = indicators.get("rsi")
        change_pct = snapshot.change_pct or 0.0

        if price and ema50 and ema200:
            data_points += 1
            if price > ema50 > ema200:
                raw_score += 1.5
                evidence.append("Stock in strong uptrend — likely outperforming sector")
            elif price > ema200:
                raw_score += 0.5
                evidence.append("Stock above EMA200 — holding relative to sector")
            elif price < ema50 < ema200:
                raw_score -= 1.5
                evidence.append("Stock in downtrend — likely underperforming sector")

        if rsi is not None:
            if rsi > 55:
                raw_score += 0.5
                evidence.append(f"RSI {rsi:.0f} shows relative momentum vs sector")
            elif rsi < 40:
                raw_score -= 0.5
                evidence.append(f"RSI {rsi:.0f} — weak relative momentum")

        # ─── 3. Sector Risk Factor ───────────────────────────────────
        sector_risk = _SECTOR_RISK.get(sector, 0.5)
        data_points += 1

        risk_adjustment = (0.5 - sector_risk) * 2  # -0.6 to +0.6 range
        raw_score += risk_adjustment
        if sector_risk <= 0.3:
            evidence.append(f"Low sector risk ({sector_risk:.1f}) — defensive positioning")
        elif sector_risk >= 0.7:
            evidence.append(f"High sector risk ({sector_risk:.1f}) — elevated sector volatility")

        final_score = min(10.0, max(0.0, raw_score))
        quality = DataQuality.FULL if data_points >= 2 else DataQuality.PARTIAL
        confidence = min(1.0, data_points / 3)

        return ScoreBreakdown(
            score=round(final_score, 2),
            weight=0.0,  # Sector score is informational, not in composite
            confidence=round(confidence, 2),
            data_quality=quality,
            evidence=evidence,
        )

    # ─── Multi-Sector Quantitative Screening & Ranking ───────────────────────

    def screen_sectors(
        self,
        exchange: str = "NSE",
        top_k: int = 5,
        timeframe: str = "1mo",
    ) -> SectorScreenResponse:
        """Screen and rank sectors using real-time benchmark indices and constituents.

        Calculates:
          - 1D, 1M, and 3M index returns
          - Wilder RSI(14)
          - EMA20 & EMA50 trend structure
          - Market breadth (% of constituents above 50-day EMA)
          - Top constituent driver stocks strictly mapped from UniverseManager
          - Composite Sector Bullish Score (0.0 - 10.0)
        """
        start_t = time.monotonic()
        cache_key = f"{exchange}_{top_k}_{timeframe}"
        now_ts = time.time()

        # Cache lookup
        if cache_key in self._cache:
            cached_res, cached_time = self._cache[cache_key]
            if now_ts - cached_time < self.cache_ttl:
                logger.info("Serving sector screen results from cache (%s)", cache_key)
                return cached_res

        sector_indices = UniverseManager.get_sector_indices(exchange)
        if not sector_indices:
            logger.warning("No sector indices found for exchange %s", exchange)
            return SectorScreenResponse(
                exchange=exchange,
                as_of=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                timeframe=timeframe,
            )

        # Collect symbols to download concurrently
        all_symbols = [info["symbol"] for info in sector_indices.values()]
        candidate_map: dict[str, list[str]] = {}

        for sec_k in sector_indices.keys():
            constituents = UniverseManager.get_sector_constituents(sec_k)
            # Prioritize large caps, then mid caps
            sorted_stocks = sorted(
                constituents.items(),
                key=lambda item: 0 if item[1].cap_tier == "large_cap" else (1 if item[1].cap_tier == "mid_cap" else 2)
            )
            sample_syms = [sym for sym, _ in sorted_stocks[:6]]
            candidate_map[sec_k] = sample_syms
            all_symbols.extend(sample_syms)

        unique_symbols = list(set(all_symbols))
        logger.info("Batch downloading %d symbols for sector analysis...", len(unique_symbols))

        try:
            download_df = yf.download(
                unique_symbols,
                period="3mo",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            close_df = download_df["Close"] if "Close" in download_df else download_df
        except Exception as exc:
            logger.error("Error downloading batch sector data: %s", exc)
            close_df = pd.DataFrame()

        results: list[SectorMetric] = []

        for sec_k, sec_info in sector_indices.items():
            sym = sec_info["symbol"]
            display_name = sec_info["display_name"]
            index_name = sec_info["name"]

            curr_level = 0.0
            chg_1d = 0.0
            chg_1m = 0.0
            chg_3m = 0.0
            rsi_val = 50.0
            trend = "NEUTRAL"

            # Check if index data is present
            if sym in close_df.columns:
                idx_series = close_df[sym].dropna()
                if len(idx_series) >= 15:
                    curr_level = float(idx_series.iloc[-1])
                    prev_close = float(idx_series.iloc[-2]) if len(idx_series) > 1 else curr_level
                    chg_1d = ((curr_level - prev_close) / prev_close) * 100

                    p_1m = float(idx_series.iloc[-21]) if len(idx_series) >= 21 else float(idx_series.iloc[0])
                    chg_1m = ((curr_level - p_1m) / p_1m) * 100

                    p_3m = float(idx_series.iloc[0])
                    chg_3m = ((curr_level - p_3m) / p_3m) * 100

                    rsi_series = _rsi_wilder(idx_series, 14)
                    if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]):
                        rsi_val = float(rsi_series.iloc[-1])

                    ema20 = float(idx_series.ewm(span=20, adjust=False).mean().iloc[-1])
                    ema50 = float(idx_series.ewm(span=50, adjust=False).mean().iloc[-1])

                    if curr_level > ema20 > ema50:
                        trend = "BULLISH"
                    elif curr_level < ema20 < ema50:
                        trend = "BEARISH"
                    else:
                        trend = "NEUTRAL"

            # Compute breadth and top driver constituents
            sample_syms = candidate_map.get(sec_k, [])
            valid_stocks = 0
            above_ema50_count = 0
            driver_candidates: list[dict] = []

            for st_sym in sample_syms:
                if st_sym in close_df.columns:
                    st_series = close_df[st_sym].dropna()
                    if len(st_series) >= 15:
                        s_curr = float(st_series.iloc[-1])
                        s_prev = float(st_series.iloc[-2]) if len(st_series) > 1 else s_curr
                        s_chg1d = ((s_curr - s_prev) / s_prev) * 100
                        s_ema50 = float(st_series.ewm(span=min(50, len(st_series)), adjust=False).mean().iloc[-1])

                        valid_stocks += 1
                        if s_curr >= s_ema50:
                            above_ema50_count += 1

                        meta = UniverseManager.get_stock_meta(st_sym)
                        clean_sym = st_sym.replace(".NS", "")
                        comp_name = meta.name if meta else clean_sym

                        driver_candidates.append({
                            "symbol": clean_sym,
                            "name": comp_name,
                            "price": s_curr,
                            "change_1d": s_chg1d,
                        })

            breadth_pct = (above_ema50_count / valid_stocks * 100.0) if valid_stocks > 0 else 50.0
            driver_candidates.sort(key=lambda x: x["change_1d"], reverse=True)
            top_drivers = driver_candidates[:3]

            # ─── Composite Sector Bullish Scoring Formula [0.0 - 10.0] ────────
            # 1. Momentum Component (35%): 1M Return + 3M Return + RSI positioning
            mom_component = float(np.clip(chg_1m * 0.25, -2.5, 2.5) + np.clip(chg_3m * 0.10, -1.5, 1.5))
            rsi_adj = 0.5 if (50.0 <= rsi_val <= 68.0) else (-0.6 if rsi_val < 42.0 else 0.0)

            # 2. Market Breadth Component (25%): Percentage of stocks > 50-day EMA
            breadth_component = (breadth_pct / 100.0) * 2.5

            # 3. Trend Alignment Component (25%): EMA20/EMA50 alignment
            trend_component = 2.5 if trend == "BULLISH" else (1.2 if trend == "NEUTRAL" else 0.0)

            # 4. Cycle & Defensive Baseline Component (15%)
            cycle_component = (_SECTOR_CYCLE_SCORE.get(sec_k, 5.0) / 10.0) * 1.5

            raw_score = 2.5 + mom_component + rsi_adj + breadth_component + trend_component + cycle_component
            composite_score = round(float(np.clip(raw_score, 1.0, 9.6)), 2)

            # Assign Signal & Conviction
            if composite_score >= 7.2:
                signal = "OVERWEIGHT"
                conviction = "HIGH"
            elif composite_score >= 5.8:
                signal = "ACCUMULATE"
                conviction = "MEDIUM"
            elif composite_score >= 4.5:
                signal = "NEUTRAL"
                conviction = "LOW"
            else:
                signal = "UNDERWEIGHT"
                conviction = "LOW"

            catalyst = _SECTOR_CATALYSTS.get(sec_k, "Sector fundamentals aligned with macro market regime.")

            results.append(SectorMetric(
                sector_key=sec_k,
                display_name=display_name,
                index_name=index_name,
                index_symbol=sym,
                current_level=round(curr_level, 2),
                change_1d_pct=round(chg_1d, 2),
                change_1m_pct=round(chg_1m, 2),
                change_3m_pct=round(chg_3m, 2),
                rsi=round(rsi_val, 1),
                trend=trend,
                breadth_pct=round(breadth_pct, 1),
                top_drivers=top_drivers,
                composite_score=composite_score,
                conviction=conviction,
                signal=signal,
                catalyst=catalyst,
            ))

        # Sort results by composite_score descending
        results.sort(key=lambda item: item.composite_score, reverse=True)

        exec_ms = round((time.monotonic() - start_t) * 1000, 2)
        response = SectorScreenResponse(
            exchange=exchange,
            as_of=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            timeframe=timeframe,
            results=results[:top_k] if top_k else results,
            execution_time_ms=exec_ms,
            market_regime="Range Bound",
            total_sectors=len(results),
        )

        # Cache response
        self._cache[cache_key] = (response, now_ts)
        logger.info(
            "Sector screening completed in %.1fms for exchange %s (%d sectors analyzed)",
            exec_ms, exchange, len(results)
        )
        return response
