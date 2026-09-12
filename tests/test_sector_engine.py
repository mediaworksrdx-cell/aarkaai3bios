import pytest
from modules.screener.universe import UniverseManager
from modules.screener.sector_engine import SectorEngine, SectorScreenResponse, SectorMetric
from modules.screener.agent import ScreenerAgent
from modules.finance import is_stock_screener_query


def test_universe_sector_indices():
    nse_indices = UniverseManager.get_sector_indices("NSE")
    assert len(nse_indices) >= 9
    assert "banking_financial" in nse_indices
    assert nse_indices["banking_financial"]["symbol"] == "^NSEBANK"
    assert "it_software" in nse_indices
    assert nse_indices["it_software"]["symbol"] == "^CNXIT"
    assert "pharma_healthcare" in nse_indices
    assert nse_indices["pharma_healthcare"]["symbol"] == "^CNXPHARMA"
    assert "real_estate" in nse_indices
    assert nse_indices["real_estate"]["symbol"] == "^CNXREALTY"


def test_zero_cross_sector_hallucinations():
    it_constituents = UniverseManager.get_sector_constituents("it_software")
    assert "TCS.NS" in it_constituents
    assert "INFY.NS" in it_constituents
    assert "RAYMOND.NS" not in it_constituents

    fmcg_constituents = UniverseManager.get_sector_constituents("fmcg_consumer")
    assert "ITC.NS" in fmcg_constituents
    assert "TATAMOTORS.NS" not in fmcg_constituents

    auto_constituents = UniverseManager.get_sector_constituents("auto_ancillaries")
    assert "TATAMOTORS.NS" in auto_constituents
    assert "MARUTI.NS" in auto_constituents

    textile_constituents = UniverseManager.get_sector_constituents("textiles_apparel")
    assert "RAYMOND.NS" in textile_constituents


def test_sector_query_routing():
    queries = [
        "top 3 bullish sectors in NSE",
        "which sectors are performing best in NSE",
        "best bullish sectors in india",
        "top sectors on nse",
        "sector rotation ranking",
    ]
    agent = ScreenerAgent()
    for q in queries:
        assert is_stock_screener_query(q) is True, f"finance failed on: {q}"
        assert agent.is_sector_query(q) is True, f"agent is_sector_query failed on: {q}"
        assert agent.is_screener_query(q) is True, f"agent is_screener_query failed on: {q}"


def test_sector_engine_screen_sectors():
    engine = SectorEngine()
    resp = engine.screen_sectors(exchange="NSE", top_k=3)
    assert isinstance(resp, SectorScreenResponse)
    assert len(resp.results) <= 3
    assert len(resp.results) > 0
    assert resp.total_sectors >= 8

    # Verify scores are sorted descending
    scores = [r.composite_score for r in resp.results]
    assert scores == sorted(scores, reverse=True)

    for r in resp.results:
        assert 0.0 <= r.composite_score <= 10.0
        assert r.trend in ("BULLISH", "BEARISH", "NEUTRAL")
        assert r.signal in ("OVERWEIGHT", "ACCUMULATE", "NEUTRAL", "UNDERWEIGHT")
        assert r.conviction in ("HIGH", "MEDIUM", "LOW")
        assert len(r.top_drivers) <= 3


def test_authoritative_sector_report_standards():
    agent = ScreenerAgent()
    resp = agent.screen_sectors("top 3 bullish sectors in NSE")
    report = agent.generate_authoritative_sector_report(resp)

    assert "# Top" in report
    assert "Executive Master Sector Ranking Table" in report
    assert "Deep-Dive Sectoral Breakdown" in report
    assert "Production-Grade Sector Data Retrieval Implementation" in report
    assert "REGULATORY NOTICE & MANDATORY STATUTORY DISCLAIMER" in report

    # Must never contain toy stubs or cop-out apologies
    assert 'url = "https://api.nseindia.com/..."' not in report
    assert "limitations of this platform" not in report
    assert "check Moneycontrol" not in report
