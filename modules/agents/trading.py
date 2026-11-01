"""
AARKAAI – Trading Agent

Quantitative trading strategist with full access to technical analysis,
F&O analytics, market data, and options strategy tools.
"""
from __future__ import annotations

import logging
from typing import Optional

from modules import market_datetime, memory
from modules.agents.base import BaseAgent
from modules.trading_calc import resolve_trading_strategy

logger = logging.getLogger(__name__)


class TradingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Trading Agent",
            description="Quantitative trading strategist, technical indicator expert, and risk manager.",
            persona=(
                "You are AARKAAI Trading Agent, an expert quantitative developer and "
                "systematic risk manager. You specialize in technical analysis (RSI, MACD, "
                "Bollinger Bands, EMA crossovers, ATR-based stops), options strategies "
                "(spreads, straddles, iron condors), and position sizing. You serve NSE/BSE "
                "and global market traders. Always present actionable setups with defined "
                "entry, stop-loss, target, and risk-to-reward ratios."
            ),
            rules=[
                "Provide quantitative analysis of market structures, trends, and risk-to-reward ratios.",
                "Position sizing formula: Quantity = floor(Account Equity × Risk% / |Entry Price - Stop Loss|).",
                "Moving Average Golden Cross: strictly defined as 50 EMA crossing above 200 EMA (prior EMA50 <= EMA200 and current EMA50 > EMA200).",
                "ATR Trailing Stop is monotonic and non-reversing: Long Stop = max(previous stop, highest high - multiplier * ATR).",
                "Implied Volatility (IV) Crush: post-event drop in IV compresses the vega component of option value, causing long option premiums to lose value even if price direction was correct.",
                "European Style Options: Contractually cannot be exercised early before expiry; traders exit prior to expiry exclusively via offsetting market trades.",
                "PCR and Max Pain: Descriptive open-interest payoff distributions and contextual sentiment metrics, never causal price magnets.",
                "Explain technical indicators (e.g., RSI, MACD, Bollinger Bands) and chart setups step-by-step.",
                "Never offer direct financial advice or buy/sell execution guarantees. Emphasize strict risk management (stop-losses, position sizing).",
                "Draft trading ideas using scenario models (bullish, bearish, neutral).",
                "Always include a disclaimer: 'This is for educational/informational purposes only. Not SEBI-registered investment advice. Options trading involves substantial risk of loss.'",
                "When presenting options strategies, include all legs, premiums, max loss, max gain, and breakeven levels.",
                "Use ATR-based stop-loss levels rather than arbitrary percentage stops.",
                "Present IV percentile and PCR context when analyzing F&O setups.",
            ],
            default_temp=0.2,
            allowed_tools=[
                "WebSearchTool",
                "MarketDataTool",
                "TechnicalAnalysisTool",
                "FnOAnalyticsTool",
                "FinancialCalculatorTool",
                "MarketDateTimeTool",
            ],
            use_rag=True,
        )

    def _handle_market_datetime_query(self, query: str) -> Optional[str]:
        """Dynamically answers market hours and session timings using authoritative exchange rules."""
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
            "\n*Disclaimer: This is for educational/informational purposes only. Not SEBI-registered investment advice. Options and equities trading involves substantial risk of loss.*",
        ]
        return "\n".join(lines)

    def invoke(
        self,
        user_id: str,
        session_id: str,
        query: str,
        device: str = "Web/Browser"
    ) -> str:
        """
        Executes a turn on the Trading Agent.
        Wires deterministic market timing and options mathematical structures.
        """
        memory.extract_user_facts(user_id, query)

        # 1. Market session / timings query
        market_timing = self._handle_market_datetime_query(query)
        if market_timing:
            memory.store_conversation(
                user_id=user_id, session_id=session_id, query=query,
                response=market_timing, intent="trading_market_datetime",
                confidence=0.99, source="market-datetime"
            )
            return market_timing

        # 2. Options and technical divergence strategy
        strategy_resp = resolve_trading_strategy(query)
        if strategy_resp:
            full_resp = (
                f"{strategy_resp}\n\n"
                f"*Disclaimer: This is for educational/informational purposes only. "
                f"Not SEBI-registered investment advice. Options trading involves substantial risk of loss.*"
            )
            memory.store_conversation(
                user_id=user_id, session_id=session_id, query=query,
                response=full_resp, intent="trading_strategy",
                confidence=0.99, source="trading-calc-engine"
            )
            return full_resp

        # 3. Default to LLM generation
        return super().invoke(user_id, session_id, query, device)
