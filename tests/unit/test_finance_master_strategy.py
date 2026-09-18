import pytest
from modules.options_strategy import generate_candidate_strategies, generate_strategy


def test_generate_candidate_strategies_bullish():
    indicators = {
        "current_price": 815.0,
        "atr": 12.0,
        "rsi": 58.0,
    }
    res = generate_candidate_strategies("SBIN.NS", indicators, "BULLISH", risk_reward=5.0)
    assert res is not None
    assert res["symbol"] == "SBIN.NS"
    assert res["signal"] == "BULLISH"
    assert res["master_recommended"] == "candidate_defined_risk"
    assert len(res["candidates"]) == 2

    # Verify candidates
    cand_ids = [c["candidate_id"] for c in res["candidates"]]
    assert "candidate_defined_risk" in cand_ids
    assert "candidate_alpha_momentum" in cand_ids

    spread_cand = next(c for c in res["candidates"] if c["candidate_id"] == "candidate_defined_risk")
    assert spread_cand["strategy_type"] == "bull_call_spread"
    assert len(spread_cand["legs"]) == 2

    alpha_cand = next(c for c in res["candidates"] if c["candidate_id"] == "candidate_alpha_momentum")
    assert alpha_cand["strategy_type"] == "long_call"
    assert len(alpha_cand["legs"]) == 1


def test_generate_candidate_strategies_neutral():
    indicators = {
        "current_price": 2500.0,
        "atr": 35.0,
        "rsi": 50.0,
        "bb_upper": 2550.0,
        "bb_lower": 2450.0,
    }
    res = generate_candidate_strategies("RELIANCE.NS", indicators, "NEUTRAL", risk_reward=5.0)
    assert res is not None
    assert res["signal"] == "NEUTRAL"
    assert res["master_recommended"] == "candidate_delta_neutral"
    assert len(res["candidates"]) == 2


def test_generate_candidate_strategies_commodity_non_options():
    # Verify GC=F (Gold Commodity) produces institutional spot/futures setups, NOT options
    indicators = {
        "current_price": 2580.0,
        "atr": 22.0,
        "rsi": 48.0,
    }
    res = generate_candidate_strategies("GC=F", indicators, "NEUTRAL", risk_reward=5.0, is_options_intent=False)
    assert res is not None
    assert res["is_options"] is False
    assert res["symbol"] == "GC=F"
    assert res["master_recommended"] == "candidate_range_mean_reversion"
    assert len(res["candidates"]) == 2

    cands = res["candidates"]
    assert cands[0]["strategy_name"] == "Range-Bound Channel Oscillation"
    assert cands[0]["technology_tag"] == "Range-Bound Mean Reversion"
    assert cands[0]["legs"] == []  # No option legs!
    assert "strike" not in cands[0]

    assert cands[1]["strategy_name"] == "Volatility Squeeze Channel Trading"
    assert cands[1]["technology_tag"] == "Consolidation Squeeze"
    assert cands[1]["legs"] == []


def test_mutating_action_signals_detection():
    query_action = "Write a python script named healthcheck.py that checks disk space and save it to the workspace directory."
    
    mutating_action_signals = [
        "save it to", "save to", "save this to", "write to file", "save file",
        "create a file", "create file", "modify file", "edit file", "delete file",
        "save it in", "save in", "write a script and save", "write script and save",
        "in the workspace", "to workspace", "to the workspace", "in workspace",
        "execute script", "run script", "run the script", "run command"
    ]
    
    has_mutating_action = any(sig in query_action.lower() for sig in mutating_action_signals)
    assert has_mutating_action is True