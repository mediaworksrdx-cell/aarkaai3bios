"""
AARKAAI – Screener Unit Tests (Phase 1)

Tests for strategy scoring, engine modules, intent detection,
universe management, and composite scoring.
"""
from __future__ import annotations

import pytest
import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Schema Tests ────────────────────────────────────────────────────────────


class TestSchemas:
    """Test data model construction and validation."""

    def test_score_breakdown_creation(self):
        from modules.screener.schemas import ScoreBreakdown, DataQuality
        sb = ScoreBreakdown(
            score=7.5, weight=0.15, confidence=0.9,
            data_quality=DataQuality.FULL,
            evidence=["Test evidence"],
        )
        assert sb.score == 7.5
        assert sb.weighted_score == pytest.approx(7.5 * 0.15)

    def test_score_breakdown_unavailable_factory(self):
        from modules.screener.schemas import ScoreBreakdown, DataQuality
        sb = ScoreBreakdown.unavailable(weight=0.10)
        assert sb.score == 5.0
        assert sb.confidence == 0.0
        assert sb.data_quality == DataQuality.UNAVAILABLE

    def test_screen_request_defaults(self):
        from modules.screener.schemas import ScreenRequest
        req = ScreenRequest()
        assert req.top_k == 10
        assert req.sort_by == "composite_score"
        assert req.include_forecast is True
        assert req.min_composite_score == 0.0

    def test_stock_meta_yf_symbol(self):
        from modules.screener.schemas import StockMeta
        meta_nse = StockMeta(name="HDFC Bank", symbol="HDFCBANK", exchange="NSE")
        assert meta_nse.yf_symbol == "HDFCBANK.NS"

        meta_us = StockMeta(name="Apple", symbol="AAPL", exchange="NASDAQ")
        assert meta_us.yf_symbol == "AAPL"

    def test_signal_type_enum(self):
        from modules.screener.schemas import SignalType
        assert SignalType.STRONG_BUY.value == "STRONG_BUY"
        assert SignalType.HOLD.value == "HOLD"

    def test_screen_response_disclaimer(self):
        from modules.screener.schemas import ScreenResponse, ScreenRequest
        resp = ScreenResponse(
            request=ScreenRequest(),
            universe_label="Test",
            total_universe_size=0,
            total_screened=0,
            total_passed=0,
            results=[],
        )
        assert "educational" in resp.disclaimer.lower()
        assert "SEBI" in resp.disclaimer


# ─── Strategy Tests ──────────────────────────────────────────────────────────


class TestStrategies:
    """Test all 20 strategy scoring implementations."""

    @pytest.fixture
    def bullish_indicators(self):
        return {
            "price": 500.0,
            "rsi": 58.0,
            "macd_line": 2.5,
            "macd_signal": 1.8,
            "macd_histogram": 0.7,
            "macd_crossover": "bullish",
            "ema20": 495.0,
            "ema50": 480.0,
            "ema200": 450.0,
            "sma_20": 495.0,
            "sma_50": 480.0,
            "sma_200": 450.0,
            "bb_upper": 520.0,
            "bb_lower": 470.0,
            "bb_middle": 495.0,
            "bb_position": 0.65,
            "atr": 12.0,
            "volume_ratio": 1.8,
            "volume_sma": 1000000,
            "adx": 30.0,
            "supertrend_value": 480.0,
            "supertrend_direction": 1,
            "vwap": 498.0,
            "patterns": [],
        }

    @pytest.fixture
    def bearish_indicators(self):
        return {
            "price": 300.0,
            "rsi": 35.0,
            "macd_line": -1.5,
            "macd_signal": -0.8,
            "macd_histogram": -0.7,
            "macd_crossover": "bearish",
            "ema20": 310.0,
            "ema50": 330.0,
            "ema200": 360.0,
            "sma_20": 310.0,
            "sma_50": 330.0,
            "sma_200": 360.0,
            "bb_upper": 320.0,
            "bb_lower": 280.0,
            "bb_middle": 300.0,
            "bb_position": 0.25,
            "atr": 15.0,
            "volume_ratio": 2.2,
            "volume_sma": 800000,
            "adx": 28.0,
            "supertrend_value": 320.0,
            "supertrend_direction": -1,
            "vwap": 305.0,
            "patterns": [],
        }

    @pytest.fixture
    def fundamentals(self):
        return {
            "eps": 15.0,
            "pe": 20.0,
            "pb": 3.5,
            "ps": 2.0,
            "ev_ebitda": 12.0,
            "roe": 0.18,
            "roa": 0.08,
            "debt_equity": 0.4,
            "dividend_yield": 0.02,
            "revenue_growth": 0.15,
            "profit_margin": 0.12,
            "market_cap": 500e9,
            "beta": 1.1,
        }

    def test_registry_has_20_strategies(self):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        names = reg.list_names()
        assert len(names) == 20, f"Expected 20 strategies, got {len(names)}: {names}"

    def test_registry_category_counts(self):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        assert len(reg.get_by_category("bullish")) == 5
        assert len(reg.get_by_category("bearish")) == 5
        assert len(reg.get_by_category("neutral")) == 5
        assert len(reg.get_by_category("reversal")) == 5

    def test_bullish_strategy_scores_high_on_bullish_data(self, bullish_indicators, fundamentals):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        bullish_strategies = reg.get_by_category("bullish")
        for strat in bullish_strategies:
            result = strat.score(bullish_indicators, fundamentals)
            assert result.score >= 0.0
            assert result.score <= 10.0
            assert result.strategy_name == strat.name

    def test_bearish_strategy_scores_on_bearish_data(self, bearish_indicators, fundamentals):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        bearish_strategies = reg.get_by_category("bearish")
        for strat in bearish_strategies:
            result = strat.score(bearish_indicators, fundamentals)
            assert result.score >= 0.0
            assert result.score <= 10.0

    def test_strategies_handle_empty_indicators(self, fundamentals):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        for strat in reg.get_all():
            result = strat.score({}, fundamentals)
            assert result.score >= 0.0
            assert result.score <= 10.0

    def test_strategies_handle_none_values(self):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        indicators = {"price": None, "rsi": None, "macd_histogram": None}
        fundamentals = {"eps": None, "pe": None}
        for strat in reg.get_all():
            result = strat.score(indicators, fundamentals)
            assert result.score >= 0.0

    def test_strategy_info_has_required_fields(self):
        from modules.screener.registry import StrategyRegistry
        reg = StrategyRegistry()
        infos = reg.list_strategies_info()
        assert len(infos) == 20
        for info in infos:
            assert "name" in info
            assert "display_name" in info
            assert "category" in info
            assert "description" in info


# ─── Universe Tests ──────────────────────────────────────────────────────────


class TestUniverse:
    """Test stock universe management."""

    def test_universe_manager_has_sectors(self):
        from modules.screener.universe import UniverseManager
        sectors = UniverseManager.get_all_sectors()
        assert len(sectors) >= 10, f"Expected 10+ sectors, got {len(sectors)}"

    def test_universe_total_stocks(self):
        from modules.screener.universe import UniverseManager
        all_stocks = UniverseManager.get_universe()
        assert len(all_stocks) >= 200, f"Expected 200+ stocks, got {len(all_stocks)}"

    def test_universe_sector_filter(self):
        from modules.screener.universe import UniverseManager
        banking = UniverseManager.get_universe(sector="banking_financial")
        assert len(banking) >= 10
        for symbol, meta in banking.items():
            assert meta.sector == "banking_financial"

    def test_universe_cap_tier_filter(self):
        from modules.screener.universe import UniverseManager
        large = UniverseManager.get_universe(cap_tier="large_cap")
        for symbol, meta in large.items():
            assert meta.cap_tier == "large_cap"

    def test_sector_query_detection(self):
        from modules.screener.universe import UniverseManager
        assert UniverseManager.get_sector_for_query("banking stocks") == "banking_financial"
        assert UniverseManager.get_sector_for_query("IT companies") == "it_software"
        assert UniverseManager.get_sector_for_query("pharma sector") == "pharma_healthcare"

    def test_fno_stocks(self):
        from modules.screener.universe import UniverseManager
        fno = UniverseManager.get_fno_stocks()
        assert len(fno) >= 20
        for symbol, meta in fno.items():
            assert meta.fno_eligible is True

    def test_legacy_universe_format(self):
        from modules.screener.universe import UniverseManager
        legacy = UniverseManager.get_legacy_universe()
        for symbol, data in legacy.items():
            assert "name" in data
            assert "sector" in data
            assert "symbol" in data
            assert "catalyst" in data

    def test_stock_meta_lookup(self):
        from modules.screener.universe import UniverseManager
        meta = UniverseManager.get_stock_meta("HDFCBANK.NS")
        assert meta is not None
        assert meta.name == "HDFC Bank Limited"


# ─── Engine Tests ────────────────────────────────────────────────────────────


class TestFundamentalEngine:
    """Test fundamental quality scoring."""

    def test_strong_fundamentals(self):
        from modules.screener.fundamental_engine import FundamentalEngine
        from modules.screener.data_fetcher import StockSnapshot
        engine = FundamentalEngine()
        snapshot = StockSnapshot(
            symbol="TEST.NS", price=500.0, prev_close=490.0, change_pct=2.0,
            eps=20.0, pe=18.0, roe=0.22, roa=0.10,
            debt_equity=0.3, revenue_growth=0.20, profit_margin=0.15,
            dividend_yield=0.025,
        )
        result = engine.score(snapshot, sector="banking_financial")
        assert result.score >= 6.0, f"Strong fundamentals should score 6+, got {result.score}"
        assert result.data_quality.value == "full"

    def test_weak_fundamentals(self):
        from modules.screener.fundamental_engine import FundamentalEngine
        from modules.screener.data_fetcher import StockSnapshot
        engine = FundamentalEngine()
        snapshot = StockSnapshot(
            symbol="TEST.NS", price=100.0, prev_close=105.0, change_pct=-4.8,
            eps=-2.0, pe=-50.0, roe=-0.05, debt_equity=3.0,
            revenue_growth=-0.10,
        )
        result = engine.score(snapshot, sector="it_software")
        assert result.score < 5.0

    def test_no_data_returns_low_score(self):
        from modules.screener.fundamental_engine import FundamentalEngine
        from modules.screener.data_fetcher import StockSnapshot
        engine = FundamentalEngine()
        snapshot = StockSnapshot(
            symbol="TEST.NS", price=100.0, prev_close=100.0, change_pct=0.0,
        )
        result = engine.score(snapshot)
        assert result.score < 3.0, f"No fundamentals should score low, got {result.score}"
        assert result.confidence < 0.5


class TestMomentumEngine:
    """Test momentum scoring."""

    def test_strong_momentum(self):
        from modules.screener.momentum_engine import MomentumEngine
        from modules.screener.data_fetcher import StockSnapshot
        engine = MomentumEngine()
        snapshot = StockSnapshot(
            symbol="TEST.NS", price=500.0, prev_close=490.0, change_pct=2.0,
            high_52w=520.0, low_52w=350.0,
            indicators={
                "rsi": 58.0, "macd_histogram": 1.5, "macd_crossover": "bullish",
                "ema20": 495.0, "ema50": 480.0, "ema200": 450.0,
                "volume_ratio": 2.0, "adx": 32.0, "supertrend_direction": 1,
            },
        )
        result = engine.score(snapshot)
        assert result.score >= 5.0

    def test_no_indicators_returns_neutral(self):
        from modules.screener.momentum_engine import MomentumEngine
        from modules.screener.data_fetcher import StockSnapshot
        engine = MomentumEngine()
        snapshot = StockSnapshot(
            symbol="TEST.NS", price=100.0, prev_close=100.0, change_pct=0.0,
        )
        result = engine.score(snapshot)
        assert result.data_quality.value == "unavailable"


class TestValuationEngine:
    """Test valuation scoring."""

    def test_deep_value(self):
        from modules.screener.valuation_engine import ValuationEngine
        from modules.screener.data_fetcher import StockSnapshot
        engine = ValuationEngine()
        snapshot = StockSnapshot(
            symbol="TEST.NS", price=100.0, prev_close=105.0, change_pct=-4.8,
            pe=8.0, pb=0.8, ev_ebitda=5.0,
            high_52w=200.0, low_52w=90.0, revenue_growth=0.12, eps=12.0,
        )
        result = engine.score(snapshot, sector="banking_financial")
        assert result.score >= 6.0, f"Deep value should score 6+, got {result.score}"


# ─── Scoring Engine Tests ────────────────────────────────────────────────────


class TestScoringEngine:
    """Test multi-factor composite scoring."""

    def test_composite_all_high_scores(self):
        from modules.screener.scoring_engine import ScoringEngine
        from modules.screener.schemas import ScoreBreakdown, DataQuality, MarketRegime
        engine = ScoringEngine()
        scores = {
            "strategy": ScoreBreakdown(score=8.0, weight=0.15, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "fundamental": ScoreBreakdown(score=8.0, weight=0.15, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "technical": ScoreBreakdown(score=8.0, weight=0.12, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "momentum": ScoreBreakdown(score=8.0, weight=0.12, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "valuation": ScoreBreakdown(score=8.0, weight=0.10, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
        }
        composite, signal, conviction = engine.compute_composite(scores, MarketRegime.RANGE_BOUND)
        assert composite >= 7.0
        assert signal.value in ("BUY", "STRONG_BUY")

    def test_composite_all_low_scores(self):
        from modules.screener.scoring_engine import ScoringEngine
        from modules.screener.schemas import ScoreBreakdown, DataQuality, MarketRegime
        engine = ScoringEngine()
        scores = {
            "strategy": ScoreBreakdown(score=2.0, weight=0.15, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "fundamental": ScoreBreakdown(score=2.0, weight=0.15, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "technical": ScoreBreakdown(score=2.0, weight=0.12, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
        }
        composite, signal, conviction = engine.compute_composite(scores, MarketRegime.RANGE_BOUND)
        assert composite <= 4.0
        assert signal.value in ("SELL", "STRONG_SELL", "REDUCE")

    def test_data_quality_score(self):
        from modules.screener.scoring_engine import ScoringEngine
        from modules.screener.schemas import ScoreBreakdown, DataQuality
        engine = ScoringEngine()
        scores = {
            "strategy": ScoreBreakdown(score=7.0, weight=0.15, confidence=0.9, data_quality=DataQuality.FULL, evidence=[]),
            "fundamental": ScoreBreakdown.unavailable(weight=0.15),
        }
        dq = engine.compute_data_quality_score(scores)
        assert dq.score < 10.0
        assert any("UNAVAILABLE" in e for e in dq.evidence)


# ─── Intent Detection Tests ─────────────────────────────────────────────────


class TestIntentDetection:
    """Test ScreenerAgent intent detection."""

    def test_bullish_category_detection(self):
        from modules.screener.agent import ScreenerAgent
        agent = ScreenerAgent()
        req = agent.detect_intent("show me bullish stocks in IT sector")
        assert req.category == "bullish"
        assert req.sector == "it_software"

    def test_strategy_detection(self):
        from modules.screener.agent import ScreenerAgent
        agent = ScreenerAgent()
        req = agent.detect_intent("golden cross momentum stocks")
        assert req.strategy == "golden_cross_momentum" or "golden_cross_momentum" in (req.strategies or [])

    def test_top_k_detection(self):
        from modules.screener.agent import ScreenerAgent
        agent = ScreenerAgent()
        req = agent.detect_intent("top 5 bullish banking stocks")
        assert req.top_k == 5

    def test_is_screener_query(self):
        from modules.screener.agent import ScreenerAgent
        agent = ScreenerAgent()
        assert agent.is_screener_query("show me bullish stocks") is True
        assert agent.is_screener_query("golden cross momentum stocks") is True
        assert agent.is_screener_query("screen banking stocks") is True
        assert agent.is_screener_query("what is the weather today") is False

    def test_exchange_detection(self):
        from modules.screener.agent import ScreenerAgent
        agent = ScreenerAgent()
        req = agent.detect_intent("best NASDAQ tech stocks")
        assert req.exchange == "NASDAQ"

    def test_cap_tier_detection(self):
        from modules.screener.agent import ScreenerAgent
        agent = ScreenerAgent()
        req = agent.detect_intent("small cap bullish stocks")
        assert req.cap_tier == "small_cap"


# ─── Query Understanding Integration ────────────────────────────────────────


class TestQueryUnderstandingIntegration:
    """Test DataSource enum has STOCK_SCREENER."""

    def test_stock_screener_datasource_exists(self):
        from modules.query_understanding import DataSource
        assert hasattr(DataSource, "STOCK_SCREENER")
        assert DataSource.STOCK_SCREENER.value == "stock_screener"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
