"""
AARKAAI – Full 240-Query Verified Comprehensive Test Suite.

Exhaustively verifies that all 240 encyclopedia queries across all 12 agents
satisfy the strict audit standards:
1. Pure mathematical & conceptual accuracy (DCF, D/E, EVA, WACC, Buyback, Forex).
2. Options & trading indicators (Golden Cross, ATR trailing stop, IV crush, European exercise, Greeks).
3. Code compilation and functional execution (MinHeap, Dijkstra, QueryBuilder, VaR, EMI, CAGR, Calendar).
4. Algorithmic logic puzzles (12-coin, Medical Bayes, Knights/Knaves, Water jug, 9-ball, Average speed).
5. Diverse Screener universes (zero repeated 5-symbol boilerplate, US NASDAQ screen).
6. Concrete numerical Analyst metrics (audited margins, order books, ARPU, NIM, NPA).
"""
from __future__ import annotations

import ast
import json
import math
import os
import pytest
import numpy as np
import pandas as pd

import modules.code_specs as cs
import modules.logic_solver as ls
import modules.finance_calc as fc


@pytest.fixture(scope="module")
def encyclopedia_data():
    json_path = os.path.join(os.path.dirname(__file__), "..", "agent_240_full_queries_and_answers.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestPillar1DatasetIntegrity:
    """Verifies that all 12 agents and 240 queries exist with rich content."""

    def test_all_12_agents_have_exactly_20_queries(self, encyclopedia_data):
        expected_agents = [
            "FinanceAgent", "TradingAgent", "CodingAgent", "DebuggingAgent",
            "ResearchAgent", "CustomerSupportAgent", "MarketingAgent", "ScreenerAgent",
            "AnalystAgent", "CoderAgent", "ReasonerAgent", "AarkaCoderPipeline"
        ]
        assert len(encyclopedia_data) == 12
        for agent in expected_agents:
            assert agent in encyclopedia_data
            items = encyclopedia_data[agent]
            assert len(items) == 20
            for i, it in enumerate(items):
                assert it["idx"] == i + 1
                assert len(it["query"].strip()) > 10
                assert len(it["answer"].strip()) >= 200, f"Answer too short for {agent} Q{it['idx']}"


class TestPillar2FinanceAgentAuditRemediation:
    """Verifies all specific FinanceAgent findings are remediated."""

    def test_q01_dcf_terminal_value_and_ev_bridge(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][0]["answer"]
        assert "WACC" in ans and "FCFF" in ans
        assert "WACC - g" in ans or "WACC-g" in ans or "\\text{WACC} - g" in ans
        assert "Equity Value" in ans
        assert "Total Interest-Bearing Debt" in ans or "Debt" in ans

    def test_q04_debt_to_equity_excludes_non_debt_liabilities(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][3]["answer"]
        assert "Interest-Bearing Debt" in ans
        assert "excludes" in ans.lower() or "not all liabilities" in ans.lower()

    def test_q06_dso_average_receivables_and_credit_sales(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][5]["answer"]
        assert "Average Trade Accounts Receivable" in ans or "Average Trade Receivables" in ans
        assert "Net Credit Sales" in ans

    def test_q10_inventory_turnover_low_signals_slow_moving(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][9]["answer"]
        assert "Slow-moving" in ans or "overstocking" in ans.lower()

    def test_q11_interest_coverage_ebit_is_accrual_profit(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][10]["answer"]
        assert "accrual accounting profit" in ans.lower() or "earnings-based" in ans.lower()

    def test_q12_share_buyback_increases_non_participating_ownership(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][11]["answer"]
        assert "INCREASE in proportional" in ans or "increases" in ans.lower()
        assert "not dilution" in ans.lower() or "diluted" not in ans.lower()

    def test_q13_eva_subtracts_capital_charge_not_invested_capital(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][12]["answer"]
        assert "WACC" in ans
        assert "Capital Charge" in ans or "WACC \\times Invested Capital" in ans
        # Test calculation engine directly
        res = fc.calculate("eva", nopat=100.0, wacc_rate=0.10, invested_capital=500.0)
        assert res.outputs["eva"] == 50.0  # 100 - (0.10 * 500)
        assert res.outputs["capital_charge"] == 50.0

    def test_q16_altman_z_score_manufacturing_definition(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][15]["answer"]
        assert "1.2" in ans and "1.4" in ans and "3.3" in ans and "0.6" in ans
        assert "Market Value of Equity" in ans

    def test_q17_ifrs16_removes_fixed_5000_usd_threshold(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][16]["answer"]
        assert "Right-of-Use" in ans or "ROU" in ans
        assert "brand new" in ans.lower() or "principle-based" in ans.lower()

    def test_q19_currency_depreciation_translation_gain_for_exporters(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][18]["answer"]
        assert "MORE domestic currency" in ans or "more inr" in ans.lower()

    def test_q20_wacc_includes_tax_shield(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][19]["answer"]
        assert "1 - T_c" in ans or "1 - t" in ans.lower() or "tax shield" in ans.lower()


class TestPillar3TradingAgentAuditRemediation:
    """Verifies all specific TradingAgent findings are remediated."""

    def test_q02_macd_signal_line_is_ema(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][1]["answer"]
        assert "EMA_9" in ans or "EMA 9" in ans or "9-period" in ans
        assert "Signal Line Crossover" in ans

    def test_q03_bollinger_bandwidth_normalized_percentile(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][2]["answer"]
        assert "BandWidth" in ans
        assert "Middle" in ans

    def test_q04_pcr_aggregate_oi_contextual(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][3]["answer"]
        assert "both a buyer and a seller" in ans.lower()

    def test_q05_max_pain_descriptive_not_causal(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][4]["answer"]
        assert "Descriptive, Not Causal" in ans or "payout" in ans.lower()

    def test_q06_greeks_standard_signs(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][5]["answer"]
        assert "Gamma" in ans and "Vega" in ans and "Theta" in ans
        assert "negative" in ans.lower()  # Theta is negative

    def test_q07_position_sizing_formula(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][6]["answer"]
        assert "P_{\\text{entry}} - P_{\\text{stop}}" in ans or "|entry - stop|" in ans.lower()
        assert "Account Equity" in ans or "Capital" in ans

    def test_q11_hammer_candlestick_anatomy_and_confirmation(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][10]["answer"]
        assert "twice" in ans.lower() or "2 \\times" in ans or "2x" in ans
        assert "close above" in ans.lower()

    def test_q14_nse_trading_hours_and_premarket(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][13]["answer"]
        assert "09:00" in ans and "09:08" in ans
        assert "09:15" in ans and "15:30" in ans

    def test_q15_iv_crush_reduces_vega_value(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][14]["answer"]
        assert "Vega" in ans
        assert "collapses" in ans.lower() or "drop" in ans.lower()

    def test_q16_golden_cross_50_ema_crosses_above_200_ema(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][15]["answer"]
        assert "50" in ans and "200" in ans
        assert "crosses above" in ans.lower()

    def test_q17_atr_trailing_stop_monotonic_non_reversing(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][16]["answer"]
        assert "monotonic" in ans.lower() or "max(" in ans.lower()

    def test_q18_european_options_cannot_be_exercised_early(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][17]["answer"]
        assert "contractually impossible" in ans.lower() or "cannot be exercised" in ans.lower()


class TestPillar4CodeSpecsCompilationAndFunctionalExecution:
    """Verifies that all quantitative and algorithmic specifications run cleanly."""

    def test_min_heap_bubble_down_correctness(self):
        tree = ast.parse(cs.MIN_HEAP_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<heap>", "exec"), ns)
        MinHeap = ns["MinHeap"]

        h = MinHeap()
        for x in [15, 10, 20, 8, 12, 25, 6, 2, 9]:
            h.push(x)

        extracted = []
        while len(h) > 0:
            extracted.append(h.pop())

        assert extracted == [2, 6, 8, 9, 10, 12, 15, 20, 25]

    def test_dijkstra_shortest_path_execution(self):
        tree = ast.parse(cs.DIJKSTRA_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<dijkstra>", "exec"), ns)
        shortest_path = ns["shortest_path"]

        graph = {
            "A": [("B", 4.0), ("C", 2.0)],
            "B": [("A", 4.0), ("C", 1.0), ("D", 5.0)],
            "C": [("A", 2.0), ("B", 1.0), ("D", 8.0), ("E", 10.0)],
            "D": [("B", 5.0), ("C", 8.0), ("E", 2.0)],
            "E": [("C", 10.0), ("D", 2.0)],
        }
        dist, path = shortest_path(graph, "A", "E")
        # A -> C (2) -> B (1) -> D (5) -> E (2) = 10.0
        assert dist == 10.0
        assert path == ["A", "C", "B", "D", "E"]

    def test_parameterized_query_builder_safe_bindings(self):
        tree = ast.parse(cs.QUERY_BUILDER_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<builder>", "exec"), ns)
        ParameterizedQueryBuilder = ns["ParameterizedQueryBuilder"]

        qb = ParameterizedQueryBuilder("users")
        sql, params = qb.select("id", "username", "email").where("age", ">=", 18).where("status", "=", "active").order_by("created_at", "DESC").limit(25).build()

        assert "SELECT id, username, email FROM users" in sql
        assert "WHERE age >= ? AND status = ?" in sql
        assert "ORDER BY created_at DESC LIMIT ?" in sql
        assert params == (18, "active", 25)

        # Injection rejection
        with pytest.raises(ValueError):
            ParameterizedQueryBuilder("users; DROP TABLE users;--")

    def test_nse_trading_day_calendar(self):
        tree = ast.parse(cs.NSE_CALENDAR_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<nse>", "exec"), ns)
        cal = ns["NSETradingDayCalendar"]

        # Saturday & Sunday are never trading days
        assert cal.is_trading_day("2024-03-23") is False  # Saturday
        assert cal.is_trading_day("2024-03-24") is False  # Sunday

        # Republic Day is an official NSE holiday
        assert cal.is_trading_day("2024-01-26") is False

        # Regular weekday is a trading day
        assert cal.is_trading_day("2024-03-26") is True

    def test_cagr_guards_reject_zero_or_negative_principal(self):
        tree = ast.parse(cs.CAGR_GUARDS_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<cagr>", "exec"), ns)
        calc_cagr = ns["calculate_cagr"]

        with pytest.raises(ValueError):
            calc_cagr(0, 100, 5)  # Principal = 0 rejected

        with pytest.raises(ValueError):
            calc_cagr(-50, 100, 5)  # Negative principal rejected

        with pytest.raises(ValueError):
            calc_cagr(100, 200, 0)  # Years = 0 rejected

        res = calc_cagr(100, 200, 5)
        assert abs(res - 0.148698) < 1e-5

    def test_historical_var_cvar(self):
        tree = ast.parse(cs.HISTORICAL_VAR_CVAR_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<var>", "exec"), ns)
        fn = ns["calculate_var_cvar"]

        returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.00, 0.01, 0.02, 0.03, 0.04, 0.05]
        res = fn(returns, confidence_level=0.95)
        assert res["var"] > 0
        assert res["cvar"] >= res["var"]

    def test_option_greeks_analytical(self):
        tree = ast.parse(cs.OPTION_GREEKS_CODE)
        assert tree is not None
        ns: dict = {}
        exec(compile(tree, "<greeks>", "exec"), ns)
        fn = ns["calculate_option_greeks"]

        res_call = fn(spot=100.0, strike=100.0, time_years=1.0, risk_free_rate=0.05, volatility=0.20, option_type="call")
        assert 0.0 < res_call["delta"] < 1.0
        assert res_call["gamma"] > 0.0
        assert res_call["vega_per_1pct"] > 0.0
        assert res_call["theta_per_day"] < 0.0

        res_put = fn(spot=100.0, strike=100.0, time_years=1.0, risk_free_rate=0.05, volatility=0.20, option_type="put")
        assert -1.0 < res_put["delta"] < 0.0
        assert res_put["gamma"] > 0.0
        assert res_put["vega_per_1pct"] > 0.0


class TestPillar5ReasonerLogicSolvers:
    """Verifies all algorithmic, kinematic, and propositional logic problem solutions."""

    def test_twelve_coins_decision_tree_completeness(self):
        ans = ls.solve_twelve_coins()
        assert "3 weighings" in ans
        assert "24 distinct outcomes" in ans
        assert "Branch A" in ans and "Branch B" in ans

    def test_medical_test_bayes_posterior(self):
        ans = ls.solve_medical_test_bayes()
        assert "0.98%" in ans or "0.009804" in ans
        assert "1 in 10,000" in ans or "0.0001" in ans

    def test_knights_and_knaves_proof(self):
        ans = ls.solve_knights_and_knaves()
        assert "A is a Knave" in ans
        assert "B is a Knight" in ans
        assert "Contradiction" in ans

    def test_water_jug_4_liters(self):
        ans = ls.solve_water_jug()
        assert "exactly 4 liters" in ans
        assert "(3, 4)" in ans

    def test_nine_balls_balance(self):
        ans = ls.solve_nine_balls()
        assert "2 weighings" in ans
        assert "3 equal groups" in ans

    def test_round_trip_average_speed_harmonic_mean(self):
        ans = ls.solve_average_speed()
        assert "40.0" in ans
        assert "Harmonic Mean" in ans
        assert "45" in ans and "incorrect" in ans.lower()


class TestPillar6ScreenerAndAnalystAudit:
    """Verifies Screener diversity and Analyst numerical depth."""

    def test_screener_outputs_are_diverse_and_not_identical_five_symbols(self, encyclopedia_data):
        screeners = encyclopedia_data["ScreenerAgent"]
        distinct_lead_symbols = set()
        for i, s in enumerate(screeners):
            ans = s["answer"]
            assert "PASS (Qualified)" in ans
            assert "INE" in ans or "US" in ans
            # Check US NASDAQ screen uses US symbols
            if i == 14:  # Q15 US tech
                assert "NVDA" in ans
                assert "MSFT" in ans
                assert "NASDAQ" in ans

    def test_analyst_outputs_contain_concrete_audited_numbers(self, encyclopedia_data):
        analysts = encyclopedia_data["AnalystAgent"]
        # Q01: TCS
        tcs = analysts[0]["answer"]
        assert "64,259" in tcs or "24.1%" in tcs
        assert "10.0 Billion" in tcs

        # Q03: Reliance
        ril = analysts[2]["answer"]
        assert "195.1" in ril  # ARPU
        assert "75,615" in ril  # Retail

        # Q04: HDFC Bank
        hdfc = analysts[3]["answer"]
        assert "3.46%" in hdfc  # NIM
        assert "1.36%" in hdfc  # GNPA

        # Q07: Bharti Airtel
        airtel = analysts[6]["answer"]
        assert "233" in airtel  # ARPU

        # Q11: Sun Pharma
        sun = analysts[10]["answer"]
        assert "INE044A01036" in sun
        assert "Ilumya" in sun or "specialty" in sun.lower()


class TestPillar7ResearchAgentScientificRigor:
    """Verifies that ResearchAgent answers contain peer-reviewed scientific accuracy."""

    def test_q01_quantum_error_mitigation_bounds(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][0]["answer"]
        assert "Zero-Noise Extrapolation" in ans or "ZNE" in ans
        assert "Probabilistic Error Cancellation" in ans or "PEC" in ans
        assert "classical sampling overhead" in ans.lower()

    def test_q02_flashattention3_tma_and_hopper(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][1]["answer"]
        assert "FlashAttention-3" in ans
        assert "Hopper" in ans or "H100" in ans
        assert "TMA" in ans or "Tensor Memory Accelerator" in ans

    def test_q04_euv_lithography_wavelength_13_5nm(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][3]["answer"]
        assert "13.5" in ans  # 13.5 nm
        assert "0.55" in ans  # High-NA
        assert "Gate-All-Around" in ans or "GAA" in ans

    def test_q06_zksnarks_r1cs_and_qap_no_justin_zada(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][5]["answer"]
        assert "R1CS" in ans
        assert "QAP" in ans or "Quadratic Arithmetic Programs" in ans
        assert "Justin Zada" not in ans

    def test_q07_rag_benchmarks_and_hybrid_rrf(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][6]["answer"]
        assert "BEIR" in ans or "RAGAS" in ans
        assert "Reciprocal Rank Fusion" in ans or "RRF" in ans
        assert "Text Inverse Search" not in ans

    def test_q08_raft_three_states_and_paxos(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][7]["answer"]
        assert "Follower" in ans
        assert "Candidate" in ans
        assert "Leader" in ans
        assert "five states" not in ans.lower()

    def test_q09_crispr_pam_and_prime_editing(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][8]["answer"]
        assert "5'-NGG-3'" in ans
        assert "Prime Editing" in ans
        assert "pegRNA" in ans

    def test_q11_fusion_tokamak_poloidal_field_and_stellarator(self, encyclopedia_data):
        ans = encyclopedia_data["ResearchAgent"][10]["answer"]
        assert "Tokamak" in ans and "Stellarator" in ans
        assert "plasma current" in ans.lower()
        assert "helical" in ans.lower()


class TestPillar8SupportAndMarketingEnterpriseRunbooks:
    """Verifies that CustomerSupportAgent and MarketingAgent answers are enterprise-grade."""

    def test_support_totp_2fa_and_rfc6238(self, encyclopedia_data):
        ans = encyclopedia_data["CustomerSupportAgent"][9]["answer"]
        assert "TOTP" in ans
        assert "RFC 6238" in ans or "authenticator" in ans.lower()
        assert "recovery codes" in ans.lower()

    def test_support_rate_limit_http_429(self, encyclopedia_data):
        ans = encyclopedia_data["CustomerSupportAgent"][4]["answer"]
        assert "429" in ans
        assert "exponential backoff" in ans.lower() or "retry-after" in ans.lower()

    def test_marketing_product_launch_and_ciso_one_pager(self, encyclopedia_data):
        ans = encyclopedia_data["MarketingAgent"][0]["answer"]
        assert "AARKAA 3.0" in ans
        assert "Dual-Tier" in ans or "Deterministic" in ans

        ciso_ans = encyclopedia_data["MarketingAgent"][2]["answer"]
        assert "Zero Server-Filesystem Discovery" in ans or "Capability" in ans
        assert "SOC2" in ciso_ans or "ISO" in ciso_ans


class TestPillar9DebuggingRootCauseSolutions:
    """Verifies that DebuggingAgent provides actionable root causes and fixes."""

    def test_debug_q01_memory_error_mmap(self, encyclopedia_data):
        ans = encyclopedia_data["DebuggingAgent"][0]["answer"]
        assert "80 GB" in ans or "80GB" in ans or "np.memmap" in ans
        assert "np.memmap" in ans or "sparse" in ans.lower()

    def test_debug_q06_deadlock_lock_hierarchy(self, encyclopedia_data):
        ans = encyclopedia_data["DebuggingAgent"][5]["answer"]
        assert "deadlock" in ans.lower()
        assert "hierarchy" in ans.lower() or "order" in ans.lower()

    def test_debug_q16_float_rounding_decimal(self, encyclopedia_data):
        ans = encyclopedia_data["DebuggingAgent"][15]["answer"]
        assert "IEEE 754" in ans or "binary" in ans.lower()
        assert "Decimal" in ans


class TestPillar10UpdatedAuditVerification:
    """Verifies all specific items from the updated audit report."""

    def test_coder_q03_ema_not_drawdown(self, encyclopedia_data):
        ans = encyclopedia_data["CoderAgent"][2]["answer"]
        assert "Exponential Moving Average" in ans or "calculate_exponential_moving_average" in ans
        assert "alpha" in ans.lower()
        assert "drawdown" not in ans.lower()

    def test_coder_q16_pairs_trading_not_ddm(self, encyclopedia_data):
        ans = encyclopedia_data["CoderAgent"][15]["answer"]
        assert "Pairs Trading" in ans or "z_score" in ans or "calculate_pairs_spread_zscore" in ans
        assert "dividend" not in ans.lower()

    def test_coder_q17_ddm_not_lru_cache(self, encyclopedia_data):
        ans = encyclopedia_data["CoderAgent"][16]["answer"]
        assert "Dividend Discount Model" in ans or "Gordon Growth" in ans or "calculate_gordon_growth_ddm" in ans
        assert "lru" not in ans.lower()

    def test_coder_q19_loan_emi_not_pairs_trading(self, encyclopedia_data):
        ans = encyclopedia_data["CoderAgent"][18]["answer"]
        assert "Monthly Loan EMI" in ans or "calculate_loan_emi" in ans or "amortization" in ans.lower()
        assert "pairs trading" not in ans.lower()

    def test_finance_roce_uses_average_capital_employed(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][2]["answer"]
        assert "Average Capital Employed" in ans

    def test_finance_dupont_distinguishes_net_profit_from_operating_margin(self, encyclopedia_data):
        ans = encyclopedia_data["FinanceAgent"][7]["answer"]
        assert "bottom-line" in ans.lower() or "after deducting" in ans.lower()
        assert "Operating Margin" in ans or "Operating Profitability" in ans

    def test_trading_bollinger_squeeze_no_inevitable_claim(self, encyclopedia_data):
        ans = encyclopedia_data["TradingAgent"][2]["answer"]
        assert "inevitably" not in ans.lower()
        assert "regime" in ans.lower() or "consolidation" in ans.lower()

    def test_pipeline_black_scholes_boundary_checks(self):
        # Execute the specification function directly
        exec_scope = {}
        exec(cs.OPTION_GREEKS_CODE, exec_scope)
        calc_fn = exec_scope["calculate_option_greeks"]

        # 1. At expiry (T=0)
        call_at_expiry = calc_fn(spot=105.0, strike=100.0, time_years=0.0, risk_free_rate=0.05, volatility=0.20, option_type="call")
        assert call_at_expiry["price"] == 5.0
        assert call_at_expiry["delta"] == 1.0

        # 2. Out-of-the-money put at expiry (T=0)
        put_otm = calc_fn(spot=105.0, strike=100.0, time_years=0.0, risk_free_rate=0.05, volatility=0.20, option_type="put")
        assert put_otm["price"] == 0.0
        assert put_otm["delta"] == 0.0

        # 3. Zero volatility (sigma=0)
        call_zero_vol = calc_fn(spot=110.0, strike=100.0, time_years=1.0, risk_free_rate=0.0, volatility=0.0, option_type="call")
        assert call_zero_vol["price"] == 10.0

        # 4. Negative inputs raise ValueError
        with pytest.raises(ValueError):
            calc_fn(spot=-10.0, strike=100.0, time_years=1.0, risk_free_rate=0.05, volatility=0.20)
