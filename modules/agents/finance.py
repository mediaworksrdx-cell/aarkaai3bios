"""
AARKAAI – Finance Agent (Enterprise Grade).

Elite chartered financial analyst (CFA) and strategic advisor.
Zero hardcoded values: all calculations are executed via `modules.finance_calc`,
market sessions and calendar timings via `modules.market_datetime`, and live
data via tool registries. Discrepancies and ungrounded numbers are audited and
rectified by `modules.finance_verifier`.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from modules import aarkaa_engine, memory
from modules import finance_calc, finance_parser, finance_verifier, market_datetime
from modules.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class FinanceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Finance Agent",
            description="Expert financial analyst, modeler, and corporate strategist.",
            persona=(
                "You are AARKAAI Finance Agent, an elite chartered financial analyst (CFA) "
                "and strategic corporate advisor. You have deep expertise in equity research, "
                "corporate finance, valuation modeling (DCF, DDM, multiples), financial accounting "
                "(IFRS 16 / Ind AS 116), portfolio risk metrics, and derivatives. "
                "You operate with absolute mathematical rigor: formulas are strictly defined, "
                "all numbers are verified, and assumptions are made explicit. "
                "Currency is formatted cleanly (₹ for INR, $ for USD). Always include appropriate "
                "SEBI and regulatory disclaimers."
            ),
            rules=[
                "Every financial formula must follow canonical financial economics definitions.",
                "Enterprise Value (EV) = Market Cap + Total Debt + Preferred Equity + Non-Controlling Interest - Cash & Equivalents.",
                "EV/EBITDA multiple = Enterprise Value / EBITDA. Never use Market Cap alone for EV.",
                "Debt-to-Equity (D/E) = Total Interest-Bearing Debt / Shareholders' Equity (operating liabilities like accounts payable are excluded).",
                "Economic Value Added (EVA) = NOPAT - (WACC × Invested Capital). Never subtract invested capital itself without multiplying by WACC.",
                "Weighted Average Cost of Capital (WACC) = (E/V)Ke + (D/V)Kd(1 - Tc) [incorporating the interest tax shield].",
                "Share Buybacks: Cancelling shares reduces total shares outstanding and increases proportional ownership percentage for non-participating shareholders.",
                "Currency Depreciation: Weaker domestic currency converts each foreign currency revenue unit into more domestic currency (e.g. USD revenue translates to more INR).",
                "DuPont 3-Step ROE = Net Margin (NI/Revenue) × Asset Turnover (Revenue/Avg Assets) × Equity Multiplier (Avg Assets/Avg Equity).",
                "FCFF = EBIT(1 - t) + D&A - CapEx - ΔNWC. FCFE = FCFF - Interest(1 - t) + Net Borrowing.",
                "Altman Z-Score: Always specify the model variant (Original Public Manufacturing 1968, Private Z', or Non-Manufacturing Z'').",
                "Lease Accounting (IFRS 16 effective 1 January 2019, Ind AS 116 effective 1 April 2019): Lessees recognize Right-of-Use (ROU) Asset and Lease Liability for all material leases. Low-value exemption is determined by underlying asset value when new, not an arbitrary fixed dollar limit.",
                "Never invent or hallucinate live market prices, multiples, or financial metrics. If live data is unavailable, state it clearly.",
                "Provide step-by-step mathematical derivations with clear variable definitions.",
                "Always include a disclaimer: 'This is for educational/informational purposes only. Not SEBI-registered investment advice.'",
            ],
            default_temp=0.15,
            allowed_tools=[
                "MarketDataTool",
                "FinancialCalculatorTool",
                "FinancialDataTool",
                "FinancialNewsTool",
                "FnOAnalyticsTool",
                "MarketDateTimeTool",
            ],
            use_rag=True,
        )

    def get_market_clock_context(self) -> str:
        """Dynamic exchange clock and session status for prompt injection."""
        try:
            return market_datetime.session_context_block("NSE")
        except Exception as exc:
            logger.debug("Market clock context error: %s", exc)
            return ""

    def get_formula_grounding_context(self, query: str) -> str:
        """Injects canonical mathematical definitions for detected financial concepts."""
        concepts = finance_parser.detect_concepts(query)
        if not concepts:
            return ""
        lines = ["[Authoritative Financial Formula Definitions]"]
        for c in concepts:
            formula = finance_calc.formula_reference(c)
            if formula:
                lines.append(f"- **{c.upper()}**: {formula}")
        return "\n".join(lines) if len(lines) > 1 else ""

    def compile_prompt(self, user_id: str, session_id: str, device: str, query: str = "") -> str:
        """Assembles prompt with session context, formula definitions, and market clock."""
        base_prompt = super().compile_prompt(user_id, session_id, device, query)
        extra_parts: List[str] = []

        clock_ctx = self.get_market_clock_context()
        if clock_ctx:
            extra_parts.append(clock_ctx)

        formula_ctx = self.get_formula_grounding_context(query)
        if formula_ctx:
            extra_parts.append(formula_ctx)

        if extra_parts:
            return f"{base_prompt}\n\n" + "\n\n".join(extra_parts)
        return base_prompt

    def _handle_market_datetime_query(self, query: str) -> Optional[str]:
        """Dynamically answers market hours, trading holidays, and session queries."""
        q_low = query.lower()
        is_timing_query = any(k in q_low for k in [
            "trading hours", "market hours", "market open", "market timing", "session timing",
            "pre-market", "pre market", "is the market open", "trading holiday", "holidays"
        ])
        if not is_timing_query:
            return None

        exchange = "BSE" if "bse" in q_low else ("NYSE" if "nyse" in q_low else "NSE")
        info = market_datetime.market_session_info(exchange)
        open_status = market_datetime.is_market_open(exchange)

        if "holiday" in q_low:
            year = market_datetime.now(exchange).year
            holidays = market_datetime.get_trading_holidays(year, exchange)
            status = market_datetime.holiday_calendar_status(year, exchange)
            cal_note = "Verified official exchange calendar" if status["verified"] else "Awaiting live calendar sync"
            lines = [
                f"### {exchange} Trading Holidays ({year})",
                f"- **Calendar Status:** {cal_note} ({status['source']})",
                "\n| Date | Holiday | Day |",
                "| :--- | :--- | :--- |",
            ]
            if holidays:
                for h in holidays:
                    lines.append(f"| {h['date']} | {h['name']} | {h['day_of_week']} |")
            else:
                lines.append(f"| N/A | Official {year} exchange calendar not yet published by {exchange} | N/A |")
            lines.append(finance_verifier.SEBI_DISCLAIMER)
            return "\n".join(lines)

        # Standard market session & hours query
        lines = [
            f"### {exchange} Trading Hours & Session Timings",
            f"\nAll times are stated in exchange-local time (**{info['timezone']}**):\n",
            f"- **Pre-Market Order Collection Session:** `{info['pre_market']} – {info.get('pre_open_order_end', '09:08')} IST`",
            f"- **Pre-Market Order Matching & Buffer:** `{info.get('pre_open_order_end', '09:08')} – {info['market_open']} IST`",
            f"- **Normal Equity Market Hours:** `{info['market_open']} – {info['market_close']} IST`",
            f"- **Post-Market Closing Session:** `{info['market_close']} – {info['post_market']} IST`",
            f"\n#### Current Exchange Status",
            f"- **Current Time:** `{open_status['current_time']} ({open_status['timezone']})`",
            f"- **Active Session:** `{open_status['session'].upper()}`",
            f"- **Market Is Currently Open:** `{'YES' if open_status['is_open'] else 'NO'}`",
            f"- **Next Trading Session Open:** `{open_status['next_open']}`",
            finance_verifier.SEBI_DISCLAIMER,
        ]
        return "\n".join(lines)

    def _handle_live_market_data_query(self, query: str) -> Optional[str]:
        """Detects ticker lookup queries and retrieves real data via tools."""
        try:
            from modules import finance
            tickers = finance.extract_tickers(query)
            if not tickers:
                return None

            # Only intercept if user is explicitly querying current quotes/financials
            q_low = query.lower()
            wants_quote = any(k in q_low for k in ["quote", "cmp", "current price", "share price", "trading at", "fundamentals", "financials of"])
            if not wants_quote:
                return None

            ticker = tickers[0]
            data = finance.get_market_data(ticker)
            if data and data.get("current_price"):
                context = finance.format_finance_context(data)
                return f"### Live Market Data: {ticker}\n\n{context}\n{finance_verifier.SEBI_DISCLAIMER}"
        except Exception as exc:
            logger.debug("Live market data query check failed: %s", exc)
        return None

    def invoke(
        self,
        user_id: str,
        session_id: str,
        query: str,
        device: str = "Web/Browser"
    ) -> str:
        """
        Executes a turn on the Finance Agent.
        Zero hardcoded values: pure mathematical evaluation, dynamic market
        clock verification, tool data retrieval, and numeric reconciliation.
        """
        # 1. Update Profile Facts
        memory.extract_user_facts(user_id, query)

        # 2. Check dynamic market calendar / session timings
        market_timing_resp = self._handle_market_datetime_query(query)
        if market_timing_resp:
            memory.store_conversation(
                user_id=user_id, session_id=session_id, query=query,
                response=market_timing_resp, intent="finance_market_datetime",
                confidence=0.99, source="dynamic-market-datetime"
            )
            return market_timing_resp

        # 3. Dynamic Financial Calculation Engine
        parsed_calc = None
        calc_result: Optional[finance_calc.CalcResult] = None
        try:
            parsed_calc = finance_parser.parse(query)
            if parsed_calc and parsed_calc.complete:
                calc_result = finance_calc.calculate(
                    parsed_calc.calculator,
                    **{k: v for k, v in parsed_calc.kwargs.items() if not k.startswith("_")}
                )
            elif parsed_calc and not parsed_calc.complete:
                # User requested a calculation but omitted required parameters
                missing_str = ", ".join(f"`{m}`" for m in parsed_calc.missing)
                ref = finance_calc.formula_reference(parsed_calc.calculator) or ""
                clarification = (
                    f"### {parsed_calc.calculator.upper()} Calculation — Missing Parameters\n\n"
                    f"To calculate **{parsed_calc.calculator.upper()}**, the following required parameter(s) "
                    f"must be provided: {missing_str}.\n\n"
                    f"**Formula Reference:**\n$$\\text{{{ref}}}$$\n\n"
                    f"Please provide the values so I can compute the exact step-by-step derivation."
                    f"{finance_verifier.SEBI_DISCLAIMER}"
                )
                memory.store_conversation(
                    user_id=user_id, session_id=session_id, query=query,
                    response=clarification, intent="finance_calculation_clarification",
                    confidence=0.95, source="finance-parser-validation"
                )
                return clarification
        except finance_calc.FinanceDomainError as domain_err:
            error_resp = f"Validation Error: {domain_err}\n{finance_verifier.SEBI_DISCLAIMER}"
            memory.store_conversation(
                user_id=user_id, session_id=session_id, query=query,
                response=error_resp, intent="finance_calculation_domain_error",
                confidence=0.99, source="finance-calc-domain-error"
            )
            return error_resp
        except Exception as exc:
            logger.debug("Dynamic calc evaluation note: %s", exc)

        # If a pure calculation was requested and completed, we return the verified calculation
        # If the query also asks for qualitative explanation, we use the LLM with verified grounding.
        is_pure_calc = calc_result is not None and not any(
            k in query.lower() for k in ["explain", "difference", "compare", "strategy", "why", "what is", "pros and cons"]
        )
        if is_pure_calc and calc_result:
            calc_markdown = finance_verifier.format_calc_result_markdown(calc_result)
            memory.store_conversation(
                user_id=user_id, session_id=session_id, query=query,
                response=calc_markdown, intent="finance_deterministic_calculation",
                confidence=1.0, source="deterministic-finance-engine"
            )
            return calc_markdown

        # 4. Check live market data
        live_quote_resp = self._handle_live_market_data_query(query)
        if live_quote_resp:
            memory.store_conversation(
                user_id=user_id, session_id=session_id, query=query,
                response=live_quote_resp, intent="finance_live_quote",
                confidence=0.95, source="live-market-feed"
            )
            return live_quote_resp

        # 5. Model Generation with Strict Grounding & Verification
        history = memory.get_chat_context(user_id, session_id, limit=6)
        system_prompt = self.compile_prompt(user_id, session_id, device, query)

        # If we have a verified calculation result, inject it into the prompt so LLM incorporates it
        if calc_result:
            system_prompt += (
                f"\n\n[Verified Mathematical Result for This Query]\n"
                f"- Calculator: {calc_result.name}\n"
                f"- Formula: {calc_result.formula}\n"
                f"- Inputs: {calc_result.inputs}\n"
                f"- Verified Outputs: {calc_result.outputs}\n"
                f"You MUST use these exact numbers and steps in your response."
            )

        formatted_prompt = aarkaa_engine._build_chatml_multi(
            system=system_prompt,
            history=history,
            user=query
        )

        logger.info("Invoking Finance Agent (dynamic) for user %s", user_id)
        raw_response = aarkaa_engine._generate(
            formatted_prompt,
            max_new_tokens=1200,
            temperature=self.default_temp
        )

        # 6. Audit & Reconcile Response Numbers
        verified_response = finance_verifier.verify_and_reconcile(
            query=query,
            draft_response=raw_response,
            calc_result=calc_result
        )

        # 7. Store Turn to Memory
        memory.store_conversation(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=verified_response,
            intent="finance_analytical",
            confidence=0.95,
            source="finance-agent-verified"
        )

        return verified_response
