"""
AARKAAI – Screener Data Models & Schemas

Pydantic v2 models for the multi-dimensional stock screening system.
Defines the 12-score profile, forecast scenarios, backtest results,
request/response contracts, and data quality enums.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─── Enums ───────────────────────────────────────────────────────────────────


class DataQuality(str, Enum):
    """Data completeness classification for each engine score."""
    FULL = "full"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class MarketRegime(str, Enum):
    """Current market regime classification."""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    RANGE_BOUND = "range_bound"
    HIGH_VOLATILITY = "high_volatility"
    CRISIS = "crisis"


class SignalType(str, Enum):
    """Multi-tier signal classification."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    ACCUMULATE = "ACCUMULATE"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class ConvictionLevel(str, Enum):
    """Confidence in the composite signal."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class StrategyCategory(str, Enum):
    """Strategy classification."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    REVERSAL = "reversal"


# ─── Score Models ────────────────────────────────────────────────────────────


class ScoreBreakdown(BaseModel):
    """Individual engine score with evidence chain."""
    score: float = Field(ge=0.0, le=10.0, description="Normalized score 0-10")
    weight: float = Field(ge=0.0, le=1.0, description="Contribution weight in composite")
    confidence: float = Field(ge=0.0, le=1.0, description="Score reliability 0-1")
    data_quality: DataQuality = DataQuality.FULL
    evidence: list[str] = Field(default_factory=list, description="Human-readable evidence points")

    @property
    def weighted_score(self) -> float:
        """Weighted contribution to composite."""
        return self.score * self.weight

    @staticmethod
    def unavailable(weight: float = 0.0) -> ScoreBreakdown:
        """Factory for unavailable engine scores."""
        return ScoreBreakdown(
            score=5.0,
            weight=weight,
            confidence=0.0,
            data_quality=DataQuality.UNAVAILABLE,
            evidence=["Engine data unavailable — score set to neutral baseline"],
        )


class ForecastScenario(BaseModel):
    """Single scenario in Bull/Base/Bear projection."""
    scenario: str = Field(description="bull | base | bear")
    target_price: float = Field(gt=0, description="Projected target price")
    upside_pct: float = Field(default=0.0, description="Projected return percentage")
    confidence: float = Field(ge=0.0, le=1.0, default=0.5, description="Scenario confidence")
    timeframe_days: int = Field(default=30, description="Projection horizon in trading days")
    key_driver: str = Field(default="", description="Primary driver for this scenario")
    support_levels: list[float] = Field(default_factory=list)
    resistance_levels: list[float] = Field(default_factory=list)


class BacktestResult(BaseModel):
    """Historical validation of the applied strategy."""
    strategy_name: str
    lookback_days: int = 90
    total_trades: int = 0
    win_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    avg_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 1.0
    sample_trades: list[dict] = Field(default_factory=list)


# ─── Strategy Result ─────────────────────────────────────────────────────────


class StrategyResult(BaseModel):
    """Output from a single strategy scoring run."""
    strategy_name: str
    category: StrategyCategory
    score: float = Field(ge=0.0, le=10.0, description="Raw strategy score 0-10")
    signal: str = Field(default="NEUTRAL", description="BULLISH | BEARISH | NEUTRAL | REVERSAL_UP | REVERSAL_DOWN")
    evidence: list[str] = Field(default_factory=list)
    triggered: bool = Field(default=False, description="Whether the strategy fully triggered")


# ─── Screen Result ───────────────────────────────────────────────────────────


class ScreenResult(BaseModel):
    """Full 12-score institutional screening result for a single stock."""
    rank: int
    symbol: str
    name: str
    sector: str
    exchange: str
    price: float
    currency: str
    change_pct: float
    market_cap_str: str = "N/A"
    eps: float | None = None
    pe: float | None = None
    pb: float | None = None
    rsi: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    volume: float | None = None

    # ─── 12-Score Profile ─────────────────────────
    strategy_score: ScoreBreakdown
    fundamental_score: ScoreBreakdown
    technical_score: ScoreBreakdown
    momentum_score: ScoreBreakdown
    valuation_score: ScoreBreakdown
    risk_score: ScoreBreakdown
    institutional_score: ScoreBreakdown
    fno_score: ScoreBreakdown | None = None
    smc_score: ScoreBreakdown | None = None
    regime_score: ScoreBreakdown
    forecast_score: ScoreBreakdown
    backtest_score: ScoreBreakdown | None = None
    data_quality_score: ScoreBreakdown

    # ─── Composite ────────────────────────────────
    composite_score: float = Field(ge=0.0, le=10.0)
    signal: SignalType = SignalType.HOLD
    conviction: ConvictionLevel = ConvictionLevel.LOW

    # ─── Forecast ─────────────────────────────────
    forecast: list[ForecastScenario] | None = None
    backtest: BacktestResult | None = None

    # ─── Explanation ──────────────────────────────
    analyst_summary: str = ""
    key_risks: list[str] = Field(default_factory=list)
    key_catalysts: list[str] = Field(default_factory=list)


# ─── Request / Response ──────────────────────────────────────────────────────


class ScreenRequest(BaseModel):
    """Screening request — from REST API or natural language intent detection."""
    strategy: str | None = Field(default=None, description="Single strategy name, e.g. 'golden_cross_momentum'")
    strategies: list[str] | None = Field(default=None, description="Multiple strategy names")
    category: str | None = Field(default=None, description="bullish | bearish | neutral | reversal")
    sector: str | None = Field(default=None, description="Sector key, e.g. 'banking_financial'")
    cap_tier: str | None = Field(default=None, description="small_cap | mid_cap | large_cap")
    exchange: str | None = Field(default=None, description="NSE | BSE | NYSE | NASDAQ")
    top_k: int = Field(default=10, ge=1, le=50)
    sort_by: str = Field(default="composite_score", description="Sort field")
    include_forecast: bool = True
    include_backtest: bool = False
    portfolio_aware: bool = False
    min_composite_score: float = Field(default=0.0, ge=0.0, le=10.0)
    raw_query: str | None = Field(default=None, description="Original natural language query")


class ScreenResponse(BaseModel):
    """Full screening response."""
    request: ScreenRequest
    universe_label: str
    total_universe_size: int
    total_screened: int
    total_passed: int
    results: list[ScreenResult]
    market_regime: MarketRegime = MarketRegime.RANGE_BOUND
    execution_time_ms: float = 0.0
    data_timestamp: str = ""
    disclaimer: str = (
        "This screening output is for educational and informational purposes only. "
        "It is not SEBI-registered investment advice. Past performance does not guarantee "
        "future results. Options trading involves substantial risk of loss. Always conduct "
        "your own due diligence before making investment decisions."
    )


# ─── Stock Metadata ──────────────────────────────────────────────────────────


class StockMeta(BaseModel):
    """Metadata for a stock in the universe."""
    name: str
    symbol: str
    exchange: str = "NSE"
    sector: str = "Diversified"
    industry: str = ""
    cap_tier: str = "mid_cap"
    fno_eligible: bool = False
    catalyst: str = ""
    country: str = "IN"

    @property
    def yf_symbol(self) -> str:
        """Yahoo Finance compatible symbol."""
        if self.exchange in ("NSE", "BSE"):
            suffix = ".NS" if self.exchange == "NSE" else ".BO"
            if not self.symbol.endswith(suffix):
                return f"{self.symbol}{suffix}"
        return self.symbol


# ─── Screener API Request (for main.py endpoint) ─────────────────────────────


class ScreenerAPIRequest(BaseModel):
    """REST API request body for POST /screener."""
    strategy: str | None = None
    strategies: list[str] | None = None
    category: str | None = None
    sector: str | None = None
    cap_tier: str | None = None
    exchange: str | None = None
    top_k: int = Field(default=10, ge=1, le=50)
    sort_by: str = "composite_score"
    include_forecast: bool = True
    include_backtest: bool = False
    min_composite_score: float = Field(default=0.0, ge=0.0, le=10.0)

    def to_screen_request(self, raw_query: str | None = None) -> ScreenRequest:
        """Convert API request to internal ScreenRequest."""
        return ScreenRequest(
            strategy=self.strategy,
            strategies=self.strategies,
            category=self.category,
            sector=self.sector,
            cap_tier=self.cap_tier,
            exchange=self.exchange,
            top_k=self.top_k,
            sort_by=self.sort_by,
            include_forecast=self.include_forecast,
            include_backtest=self.include_backtest,
            min_composite_score=self.min_composite_score,
            raw_query=raw_query,
        )
