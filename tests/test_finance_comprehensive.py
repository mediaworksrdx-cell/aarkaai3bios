"""
Comprehensive Unit & Integration Test Suite for AARKAAI Finance Engine.
Tests all pure mathematical calculations, natural-language query parsing,
market session dynamics, and FinanceAgent zero-hardcoded execution.
"""
from __future__ import annotations

import math
from datetime import date
import pytest

from modules import finance_calc, finance_parser, finance_verifier, market_datetime
from modules.agents.finance import FinanceAgent


# ───────────────────────────── 1. finance_calc Tests ──────────────────────────

class TestFinanceCalc:
    def test_cagr_growth_and_decline(self):
        # 50 Cr to 120 Cr in 4 years = 24.47%
        res = finance_calc.cagr(50e7, 120e7, 4.0)
        assert round(res.outputs["cagr_pct"], 2) == 24.47
        assert res.outputs["total_multiple"] == 2.4

        # 100 to 50 in 2 years = -29.29%
        res_down = finance_calc.cagr(100, 50, 2.0)
        assert round(res_down.outputs["cagr_pct"], 2) == -29.29

    def test_cagr_domain_errors(self):
        with pytest.raises(finance_calc.FinanceDomainError):
            finance_calc.cagr(0, 100, 5)  # Initial value must be > 0
        with pytest.raises(finance_calc.FinanceDomainError):
            finance_calc.cagr(100, -10, 5)  # Final value must be >= 0
        with pytest.raises(finance_calc.FinanceDomainError):
            finance_calc.cagr(100, 200, 0)  # Years must be > 0

    def test_emi_calculation(self):
        # 25 lakh at 8.5% for 20 years (240 months)
        res = finance_calc.emi(2500000, 0.085, 240)
        assert round(res.outputs["emi"], 2) == 21695.58
        assert round(res.outputs["total_payment"], 2) == 5206939.40

    def test_sip_future_value(self):
        # 10,000/mo at 12% for 15 years (annuity due)
        res = finance_calc.sip_future_value(10000, 0.12, 15, timing="begin")
        assert round(res.outputs["future_value"], 0) == 5045760.0
        assert res.outputs["total_invested"] == 1800000.0

    def test_npv_and_irr(self):
        # Cash flows: -1000, 300, 400, 500 at 10%
        cfs = [-1000.0, 300.0, 400.0, 500.0]
        npv_res = finance_calc.npv(0.10, cfs)
        assert round(npv_res.outputs["npv"], 2) == -21.04

        # IRR of -500, 150, 200, 250 = 8.896%
        irr_res = finance_calc.irr([-500.0, 150.0, 200.0, 250.0])
        assert round(irr_res.outputs["irr_pct"], 2) == 8.90

    def test_wacc_and_capm(self):
        capm_res = finance_calc.capm(0.065, 1.2, 0.13)
        assert round(capm_res.outputs["cost_of_equity_pct"], 2) == 14.30

        # WACC: Equity 600, Debt 400, Ke 14%, Kd 9%, Tax 25%
        wacc_res = finance_calc.wacc(600, 400, 0.14, 0.09, 0.25)
        # (0.6 * 0.14) + (0.4 * 0.09 * 0.75) = 0.084 + 0.027 = 0.111 (11.1%)
        assert round(wacc_res.outputs["wacc_pct"], 2) == 11.10

    def test_dupont_3_step(self):
        # NI=150, Rev=1000, Assets=2000, Equity=500
        # Net Margin = 15%, Asset Turnover = 0.5, Equity Multiplier = 4.0
        # ROE = 15% * 0.5 * 4.0 = 30%
        res = finance_calc.dupont(150, 1000, 2000, 500)
        assert round(res.outputs["net_margin"], 4) == 0.1500
        assert round(res.outputs["asset_turnover"], 4) == 0.5000
        assert round(res.outputs["equity_multiplier"], 4) == 4.0000
        assert round(res.outputs["roe_pct"], 2) == 30.00

    def test_enterprise_value_and_ev_ebitda(self):
        # MCap=1000, Debt=300, Cash=100, Preferred=50, NCI=20
        # EV = 1000 + 300 + 50 + 20 - 100 = 1270
        ev_res = finance_calc.enterprise_value(1000, 300, 100, preferred_equity=50, minority_interest=20)
        assert ev_res.outputs["enterprise_value"] == 1270.0

        # EV/EBITDA with EBITDA=200 -> 6.35x
        mult_res = finance_calc.ev_to_ebitda(1270, 200)
        assert round(mult_res.outputs["ev_ebitda"], 2) == 6.35

    def test_fcff_and_fcfe(self):
        # EBIT=500, Tax=25%, D&A=80, CapEx=120, ΔNWC=40
        # NOPAT = 500 * 0.75 = 375
        # FCFF = 375 + 80 - 120 - 40 = 295
        fcff_res = finance_calc.fcff(500, 0.25, 80, 120, 40)
        assert fcff_res.outputs["fcff"] == 295.0

        # FCFE = FCFF - Interest(1-t) + Net Borrowing
        # Interest=60, Net Borrowing=50
        # FCFE = 295 - 60*(0.75) + 50 = 295 - 45 + 50 = 300
        fcfe_res = finance_calc.fcfe_from_fcff(295, 60, 0.25, 50)
        assert fcfe_res.outputs["fcfe"] == 300.0

    def test_altman_z_public_manufacturing(self):
        res = finance_calc.altman_z(
            "original",
            working_capital_to_assets=0.2,
            retained_earnings_to_assets=0.3,
            ebit_to_assets=0.15,
            market_equity_to_liabilities=1.5,
            sales_to_assets=1.2
        )
        # Z = 1.2*0.2 + 1.4*0.3 + 3.3*0.15 + 0.6*1.5 + 1.0*1.2
        # Z = 0.24 + 0.42 + 0.495 + 0.90 + 1.2 = 3.255 (Safe zone > 2.99)
        assert round(res.outputs["z_score"], 3) == 3.255
        assert "safe" in res.assumptions[0].lower()

    def test_black_scholes_and_greeks(self):
        # Spot 100, Strike 100, T=1 year, r=5%, vol=20%, Call
        res = finance_calc.black_scholes(100, 100, 1.0, 0.05, 0.20, "call")
        assert round(res.outputs["price"], 2) == 10.45
        assert 0.50 < res.outputs["delta"] < 0.70
        assert res.outputs["gamma"] > 0
        assert res.outputs["vega_per_1pct"] > 0

    def test_option_strategy_bull_call_spread(self):
        # Buy 100 call at 5, sell 110 call at 2
        legs = [
            {"type": "call", "strike": 100.0, "premium": 5.0, "quantity": 1.0},
            {"type": "call", "strike": 110.0, "premium": 2.0, "quantity": -1.0},
        ]
        res = finance_calc.option_strategy_payoff(legs)
        assert res.outputs["net_premium"] == -3.0  # net debit of 3
        assert res.outputs["max_loss"] == -3.0
        assert res.outputs["max_profit"] == 7.0   # 10 strike width - 3 debit
        assert res.outputs["breakeven_1"] == 103.0


# ───────────────────────────── 2. finance_parser Tests ────────────────────────

class TestFinanceParser:
    def test_parse_cagr_various_syntaxes(self):
        p1 = finance_parser.parse("Calculate CAGR from 50 Cr to 120 Cr over 4 years")
        assert p1 is not None and p1.complete
        assert p1.kwargs["initial_value"] == 50e7
        assert p1.kwargs["final_value"] == 120e7
        assert p1.kwargs["years"] == 4.0

        p2 = finance_parser.parse("CAGR from ₹75 lakh to ₹2.1 crore in 6 yrs")
        assert p2 is not None and p2.complete
        assert p2.kwargs["initial_value"] == 75e5
        assert p2.kwargs["final_value"] == 21e6
        assert p2.kwargs["years"] == 6.0

    def test_parse_loan_emi(self):
        p = finance_parser.parse("EMI for a loan of ₹25 lakh at 8.5% for 20 years")
        assert p is not None and p.complete
        assert p.calculator == "emi"
        assert p.kwargs["principal"] == 2500000.0
        assert p.kwargs["annual_rate"] == 0.085
        assert p.kwargs["months"] == 240.0

    def test_parse_options_strategy(self):
        p = finance_parser.parse("Bull call spread: buy 100 call at 5, sell 110 call at 2")
        assert p is not None and p.complete
        assert p.calculator == "option_strategy"
        assert len(p.kwargs["legs"]) == 2


# ───────────────────────────── 3. market_datetime Tests ───────────────────────

class TestMarketDatetime:
    def test_session_info_nse(self):
        info = market_datetime.market_session_info("NSE")
        assert info["market_open"] == "09:15"
        assert info["market_close"] == "15:30"
        assert info["timezone"] == "Asia/Kolkata"

    def test_next_expiry_rule(self):
        res = market_datetime.next_expiry("monthly", "NSE")
        assert "expiry_date" in res
        assert res["days_remaining"] >= 0


# ───────────────────────────── 4. FinanceAgent Integration ─────────────────────

class TestFinanceAgentIntegration:
    def test_finance_agent_cagr_dynamic(self):
        agent = FinanceAgent()
        out = agent.invoke("u", "s", "Calculate CAGR from ₹75 lakh to ₹2.1 crore in 6 yrs")
        assert "18.72%" in out or "18.72\\%" in out
        assert "Disclaimer" in out

    def test_finance_agent_missing_param_clarification(self):
        agent = FinanceAgent()
        # Incomplete query without loan rate
        out = agent.invoke("u", "s", "Calculate the EMI for a loan of ₹50 lakh")
        assert "Missing Parameters" in out or "annual_rate" in out
