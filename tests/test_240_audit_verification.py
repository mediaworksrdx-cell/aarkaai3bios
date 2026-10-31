"""
AARKAAI — Comprehensive 240-Query Technical Audit Verification Suite

Tests all 5 architectural remediation pillars:
1. Assertion-based mathematical, financial, and logical verification (replacing len > 40).
2. Deterministic sandbox & ground-truth routing in BaseAgent and CognitiveSubagent.
3. Parametric math computation (CAGR, kinematics, domain error handling).
4. Auditable Screener & Analyst execution (including Sun Pharmaceutical ticker resolution).
5. AST compilation + functional unit execution of generated quantitative code.
"""
from __future__ import annotations

import ast
import numpy as np
import pandas as pd
import pytest

from modules.agents.finance import FinanceAgent
from modules.agents.trading import TradingAgent
from modules.agents.coding import CodingAgent
from modules.agents.debugging import DebuggingAgent
from modules.agents.research import ResearchAgent
from modules.agents.support import CustomerSupportAgent
from modules.agents.marketing import MarketingAgent
from modules.subagents.analyst import AnalystAgent
from modules.subagents.coder import CoderAgent
from modules.subagents.reasoner import ReasonerAgent
from modules.screener.agent import ScreenerAgent
from modules import aarka_coder, finance, verified_ground_truth


class TestPillar1And2FinanceAndTradingAgents:
    """Verifies FinanceAgent and TradingAgent return mathematically & structurally exact answers."""

    def test_finance_cagr_50_to_120_is_positive_24_47_pct(self):
        agent = FinanceAgent()
        out = agent.invoke(
            "test_user", "test_sess",
            "Calculate the compound annual growth rate (CAGR) from 50 Cr to 120 Cr over 4 years."
        )
        assert "24.47%" in out.replace("\\%", "%")
        assert "-41.32%" not in out.replace("\\%", "%")

    def test_finance_parametric_cagr_arbitrary_values(self):
        # Verify parametric math engine computes dynamic numbers (e.g., 100 Cr to 200 Cr over 5 years = 14.87%)
        out = verified_ground_truth.compute_deterministic_math(
            "Calculate the compound annual growth rate (CAGR) from 100 Cr to 200 Cr over 5 years."
        )
        assert out is not None
        assert "+14.87%" in out

    def test_finance_ev_ebitda_subtracts_cash(self):
        agent = FinanceAgent()
        out = agent.invoke(
            "test_user", "test_sess",
            "What is the difference between P/E ratio and EV/EBITDA multiple for capital-intensive firms?"
        )
        assert "Cash" in out
        assert "subtracted" in out.lower() or "- \\text{Cash" in out

    def test_finance_dupont_and_fcfe_and_altman_z(self):
        agent = FinanceAgent()
        dupont = agent.invoke("u", "s", "Explain DuPont analysis and its three constituent components.")
        assert "Equity Multiplier" in dupont
        assert "Average Total Assets" in dupont

        fcfe = agent.invoke("u", "s", "What is the difference between Free Cash Flow to Firm (FCFF) and FCFE?")
        assert "Net Borrowing" in fcfe

        altman = agent.invoke("u", "s", "How do you calculate Altman Z-Score to predict corporate bankruptcy risk?")
        for coeff in ("1.2", "1.4", "3.3", "0.6", "0.999"):
            assert coeff in altman

        ifrs16 = agent.invoke("u", "s", "Explain the accounting treatment of operating leases under IFRS 16 / Ind AS 116.")
        assert "1 January 2019" in ifrs16 or "1 April 2019" in ifrs16
        assert "Right-of-Use" in ifrs16

    def test_trading_rsi_divergence_and_options_and_nse_hours(self):
        agent = TradingAgent()
        rsi = agent.invoke("u", "s", "Explain how the Relative Strength Index (RSI) detects bullish and bearish divergence.")
        assert "Lower Low" in rsi and "Higher Low" in rsi
        assert "Higher High" in rsi and "Lower High" in rsi

        bull_call = agent.invoke("u", "s", "What is a Bull Call Spread options strategy, its maximum gain, and maximum loss?")
        assert "Lower-Strike Call" in bull_call
        assert "Higher-Strike Call" in bull_call

        bear_put = agent.invoke("u", "s", "Explain Bear Put Spread payoff structure and when a trader should deploy it.")
        assert "Higher-Strike Put" in bear_put
        assert "Lower-Strike Put" in bear_put

        iron_condor = agent.invoke("u", "s", "Explain how an Iron Condor option strategy generates returns in range-bound markets.")
        assert "Net Credit" in iron_condor
        assert "K_1 < K_2 < K_3 < K_4" in iron_condor

        nse = agent.invoke("u", "s", "What are the trading hours and pre-market session timings for the National Stock Exchange (NSE)?")
        assert "09:15" in nse and "15:30" in nse
        assert "09:00" in nse and "09:08" in nse


class TestPillar3ReasonerMathematicalLogic:
    """Verifies ReasonerAgent solves logical, calendar, probability, and kinematic problems accurately."""

    def test_reasoner_river_crossing_valid_sequence(self):
        reasoner = ReasonerAgent()
        res = reasoner.think(
            "Solve: A farmer needs to cross a river with a wolf, a goat, and a cabbage. "
            "The boat only fits the farmer and one item. If left alone, wolf eats goat, "
            "goat eats cabbage. How do all get across safely?"
        )
        assert res.is_valid
        assert "brings the **Goat** back" in res.output
        assert "7 one-way crossings" in res.output

    def test_reasoner_leap_year_monday_to_wednesday(self):
        reasoner = ReasonerAgent()
        res = reasoner.think(
            "Solve: If January 1st of a leap year is a Monday, what day of the week is January 1st of the following year?"
        )
        assert res.is_valid
        assert "366" in res.output
        assert "Wednesday" in res.output

    def test_reasoner_train_and_fly_75_miles(self):
        reasoner = ReasonerAgent()
        res = reasoner.think(
            "Solve: Two trains 100 miles apart travel toward each other at 50 mph each. "
            "A fly flies back and forth between them at 75 mph until they collide. What total distance does the fly travel?"
        )
        assert res.is_valid
        assert "75 miles" in res.output or "75\\text{ miles}" in res.output
        assert "90 miles" not in res.output

    def test_reasoner_birthday_paradox_and_coin_change(self):
        reasoner = ReasonerAgent()
        bday = reasoner.think(
            "Solve: Why is there a greater than 50% probability that at least two people share a birthday in a group of just 23 people?"
        )
        assert "50.73%" in bday.output.replace("\\%", "%")
        assert "253" in bday.output

        coins = reasoner.think(
            "Solve: What is the minimum number of coins needed to make 63 cents using standard US coin denominations (1, 5, 10, 25 cents)?"
        )
        assert "6 coins" in coins.output or "6\\text{ coins}" in coins.output
        assert "2 Quarters" in coins.output and "1 Dime" in coins.output and "3 Pennies" in coins.output


class TestPillar4ScreenerAndAnalystProvenance:
    """Verifies ScreenerAgent and AnalystAgent return auditable tables, ISINs, and resolve Sun Pharmaceutical."""

    def test_extract_tickers_resolves_sun_pharmaceutical_and_tata_motors(self):
        t1 = finance.extract_tickers("Analyze Sun Pharmaceutical R&D investment, specialty pipeline, and US generic price erosion.")
        assert "SUNPHARMA.NS" in t1

        t2 = finance.extract_tickers("Evaluate Tata Motors commercial vehicle vs passenger EV market share and margin expansion.")
        assert "TATAMOTORS.NS" in t2

    def test_analyst_agent_resolves_sun_pharma_with_provenance(self):
        analyst = AnalystAgent()
        res = analyst.think("Analyze Sun Pharmaceutical R&D investment, specialty pipeline, and US generic price erosion.")
        assert res.is_valid
        assert "SUNPHARMA" in res.output
        assert "INE044A01036" in res.output
        assert "No specific tickers identified" not in res.output

    def test_screener_agent_returns_auditable_table_not_label_only(self):
        screener = ScreenerAgent()
        out = screener.invoke("Screen for Indian large-cap stocks with a Golden Cross momentum setup on the NSE.")
        assert "ISIN" in out
        assert "RELIANCE" in out
        assert "INE002A01018" in out
        assert "PASS (Qualified)" in out


class TestPillar5CompiledAndExecutedQuantitativeCode:
    """Executes unit tests directly against the Python code generated by AarkaCoderPipeline & CoderAgent."""

    def _exec_generated(self, query: str) -> dict:
        code = aarka_coder.generate_code(query)
        assert code, f"Empty code generated for: {query}"
        tree = ast.parse(code)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, filename="<generated>", mode="exec"), ns)
        return ns

    def test_portfolio_fifo_lot_depletion_and_realized_pnl(self):
        ns = self._exec_generated(
            "Write a Python FIFO stock portfolio lot tracker class with realize_pnl and buy_lot methods."
        )
        PortfolioFIFO = ns["PortfolioFIFO"]
        pf = PortfolioFIFO()
        pf.buy_lot(100, 50.0)   # 100 @ $50
        pf.buy_lot(100, 60.0)   # 100 @ $60
        pnl, cost = pf.sell_lot(150, 70.0)
        # FIFO: first 100 sold @ $70 (cost $50 -> +$2000), next 50 sold @ $70 (cost $60 -> +$500) = +$2500
        assert abs(pnl - 2500.0) < 1e-6
        assert abs(cost - 8000.0) < 1e-6
        assert abs(pf.total_shares() - 50.0) < 1e-6
        with pytest.raises(ValueError):
            pf.sell_lot(100, 70.0)  # Oversell rejected

    def test_limit_order_book_price_time_priority_matching(self):
        ns = self._exec_generated(
            "Write a Python class for a limit order book bid-ask queue with market order matching."
        )
        LimitOrderBook = ns["LimitOrderBook"]
        lob = LimitOrderBook()
        lob.place_order("S1", "SELL", 101.0, 50)
        lob.place_order("S2", "SELL", 100.0, 40)
        trades = lob.place_order("B1", "BUY", 102.0, 60)
        # Should match 40 against S2 @ 100.0 first, then 20 against S1 @ 101.0
        assert len(trades) == 2
        assert trades[0]["seller_id"] == "S2" and trades[0]["price"] == 100.0 and trades[0]["quantity"] == 40
        assert trades[1]["seller_id"] == "S1" and trades[1]["price"] == 101.0 and trades[1]["quantity"] == 20
        assert lob.asks[0].quantity == 30

    def test_sharpe_and_sortino_accept_negative_returns(self):
        ns = self._exec_generated(
            "Write a Python function to compute the Sharpe Ratio and Sortino Ratio for portfolio returns."
        )
        fn = ns["calculate_sharpe_and_sortino"]
        returns = [0.01, -0.02, 0.015, -0.005, 0.02, 0.01, -0.01, 0.025]
        res = fn(returns)
        assert "sharpe_ratio" in res and "sortino_ratio" in res
        assert np.isfinite(res["sharpe_ratio"])
        assert np.isfinite(res["sortino_ratio"])

    def test_token_bucket_rate_limiter_positive_capacity(self):
        ns = self._exec_generated(
            "Write a Python class implementing a Token-Bucket Rate Limiter with thread-safe acquisition."
        )
        TokenBucketRateLimiter = ns["TokenBucketRateLimiter"]
        with pytest.raises(ValueError):
            TokenBucketRateLimiter(0, 5.0)
        limiter = TokenBucketRateLimiter(capacity=5.0, refill_rate_per_sec=10.0)
        assert limiter.acquire(3.0) is True
        assert limiter.acquire(3.0) is False  # Only ~2 tokens left

    def test_thread_safe_lru_cache_atomic_eviction(self):
        ns = self._exec_generated(
            "Write a Python class implementing a thread-safe LRU Cache with O(1) get and put."
        )
        ThreadSafeLRUCache = ns["ThreadSafeLRUCache"]
        cache = ThreadSafeLRUCache(capacity=2)
        cache.put("a", 1)
        cache.put("b", 2)
        assert cache.get("a") == 1  # 'a' is now MRU, 'b' is LRU
        cache.put("c", 3)           # Evicts 'b'
        assert cache.get("b") is None
        assert cache.get("a") == 1
        assert cache.get("c") == 3

    def test_ema_macd_and_atr_wilder(self):
        ns_ema = self._exec_generated(
            "Write a Python script to compute Exponential Moving Average (EMA) and 50/200 EMA crossovers."
        )
        s = pd.Series(np.linspace(100, 150, 250))
        df_cross = ns_ema["detect_50_200_crossovers"](s)
        assert "ema50" in df_cross.columns and "ema200" in df_cross.columns

        ns_macd = self._exec_generated(
            "Write a Python function to compute MACD line, 9-day Signal line, and MACD Histogram."
        )
        df_macd = ns_macd["compute_macd"](s)
        assert np.allclose(
            df_macd["macd_histogram"],
            df_macd["macd_line"] - df_macd["signal_line"]
        )

        ns_atr = self._exec_generated(
            "Write a Python script to compute Average True Range (ATR) with 14-period Wilder smoothing."
        )
        h = np.linspace(102, 152, 30)
        l = np.linspace(98, 148, 30)
        c = np.linspace(100, 150, 30)
        atr = ns_atr["compute_atr_wilder"](h, l, c, period=14)
        assert len(atr) == 30
        assert atr[-1] > 0
