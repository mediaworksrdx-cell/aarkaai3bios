"""
AARKAAI – Screener Package

Exposes the public API for the Aarka AI Global Advanced Screener Agent.
"""
from modules.screener.agent import ScreenerAgent
from modules.screener.schemas import (
    BacktestResult,
    ConvictionLevel,
    DataQuality,
    ForecastScenario,
    MarketRegime,
    ScoreBreakdown,
    ScreenerAPIRequest,
    ScreenRequest,
    ScreenResponse,
    ScreenResult,
    SignalType,
    StockMeta,
    StrategyCategory,
    StrategyResult,
)
from modules.screener.registry import StrategyRegistry  # noqa: F401  (re-export)
from modules.screener.universe import UniverseManager  # noqa: F401  (re-export)

__all__ = [
    "ScreenerAgent",
    "ScreenRequest",
    "ScreenResponse",
    "ScreenResult",
    "ScoreBreakdown",
    "ForecastScenario",
    "BacktestResult",
    "DataQuality",
    "MarketRegime",
    "SignalType",
    "ConvictionLevel",
    "StrategyCategory",
    "StrategyResult",
    "StockMeta",
    "ScreenerAPIRequest",
    "StrategyRegistry",
    "UniverseManager",
]
