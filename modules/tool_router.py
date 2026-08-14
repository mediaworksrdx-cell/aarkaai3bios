"""
AARKAAI – Tool Router Pipeline

Implements: User → 3B Router → Permission Layer → Tool → Validated Result → 7B → Final Answer

The 3B small model acts as a fast classifier/router that:
1. Determines which tool(s) to invoke
2. Extracts structured parameters for tool invocation
3. The permission layer validates access
4. Tools execute and return validated data
5. The 7B large model receives user query + tool results to generate the final answer
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Tool name constants matching the 14 core tools
TOOL_NAMES = [
    "MarketDataTool",
    "FinancialDataTool",
    "FinancialNewsTool",
    "FinancialCalculatorTool",
    "PortfolioTool",
    "TechnicalAnalysisTool",
    "FnOAnalyticsTool",
    "KnowledgeSearchTool",
    "FinanceCodeTool",
    "MarketDateTimeTool",
    "DocumentParserTool",
    "DatabaseQueryTool",
    "NotificationTool",
    "AuthPermissionTool",
]


@dataclass
class ToolIntent:
    """Classified intent from the 3B router."""
    tool_name: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class ToolResult:
    """Validated result from tool execution."""
    tool_name: str
    action: str
    data: str  # String output from tool
    is_valid: bool = True
    error: str = ""
    execution_time_ms: float = 0.0
    source: str = "tool"
    timestamp: str = ""


@dataclass
class PipelineResult:
    """Complete pipeline result."""
    final_answer: str
    tool_results: List[ToolResult] = field(default_factory=list)
    intents: List[ToolIntent] = field(default_factory=list)
    total_time_ms: float = 0.0
    model_used: str = "aarkaa-7b"
    permission_denied: bool = False
    permission_message: str = ""


# 3B Router System Prompt
ROUTER_SYSTEM_PROMPT = """You are the AARKAAI Tool Router. Your job is to analyze the user's query and determine which tool(s) to invoke.

Available tools:
1. MarketDataTool - Live stock/index prices, OHLCV history, options chain, OI, IV, PCR. Actions: price, ohlcv, options_chain, oi, iv, pcr
2. FinancialDataTool - Financial statements, ratios, earnings, fundamentals. Actions: financials, ratios, earnings, company_info
3. FinancialNewsTool - Current news, company announcements, RBI/SEBI updates. Actions: market_news, company_news, regulatory_updates
4. FinancialCalculatorTool - CAGR, returns, valuation, financial formulas. Actions: cagr, returns, sip, dcf, pe_value, position_size, margin, emi, compound_interest
5. PortfolioTool - Holdings, P&L, allocation, risk, watchlist. Actions: holdings, add, remove, summary, risk, watchlist_add, watchlist_remove, watchlist_view
6. TechnicalAnalysisTool - RSI, MACD, Bollinger Bands, moving averages, ATR, patterns. Actions: indicators, signal, patterns, extended
7. FnOAnalyticsTool - Option Greeks, Max Pain, PCR, IV, OI analysis. Actions: greeks, max_pain, pcr, iv_analysis, oi_analysis
8. KnowledgeSearchTool - Internal knowledge base, financial documents. Actions: search, store
9. FinanceCodeTool - Python code execution for financial calculations. Actions: execute
10. MarketDateTimeTool - Market sessions, expiry dates, holidays. Actions: market_status, next_expiry, holidays, time_to_expiry, is_trading_day
11. DocumentParserTool - Parse PDFs, annual reports. Actions: parse, extract_tables, extract_figures
12. DatabaseQueryTool - User portfolio, watchlists, history. Actions: portfolio, watchlist, history, alerts
13. NotificationTool - Alerts and scheduled events. Actions: create_alert, check_alerts, list_alerts, cancel_alert, market_events
14. AuthPermissionTool - User access and permissions. Actions: check_access, user_info

Analyze the user query and output ONLY a JSON object:
{
  "tools": [
    {
      "tool_name": "ToolName",
      "action": "action_name",
      "params": {"key": "value"},
      "confidence": 0.95,
      "reasoning": "brief reason"
    }
  ],
  "needs_tool": true,
  "fallback_to_llm": false
}

If the query is a general conversation, greeting, or doesn't need any tool, set needs_tool=false and fallback_to_llm=true with empty tools array.
If multiple tools are needed (e.g., "Compare TCS fundamentals with its technical signals"), include multiple tool entries.
Extract specific parameters from the query (symbol names, dates, amounts, etc.)."""


def _heuristic_route(query: str) -> List[ToolIntent]:
    """Fast, deterministic heuristic router for standard financial queries.

    ORDERING MATTERS: More specific categories (technical indicators,
    fundamentals, calculator, F&O) are checked BEFORE the broad
    MarketData ticker-regex catch-all to prevent mis-routing queries
    like 'RSI of TCS' or 'TCS balance sheet'.
    """
    import re
    from modules.finance import extract_tickers

    q_lower = query.lower().strip()
    intents: List[ToolIntent] = []

    # ── 1. Technical Indicators (BEFORE MarketData to avoid ticker-regex stealing) ──
    tech_keywords = [
        "rsi", "macd", "bollinger", "moving average", "supertrend",
        "vwap", "adx", "candlestick pattern", "candlestick", "technical indicators",
        "technical analysis", "sma", "ema", "stochastic", "atr",
        "obv", "williams", "ichimoku", "parabolic sar"
    ]
    if any(kw in q_lower for kw in tech_keywords):
        tickers = extract_tickers(query)
        if tickers:
            symbol = tickers[0]
            if "pattern" in q_lower or "candlestick" in q_lower:
                action = "patterns"
            elif any(kw in q_lower for kw in ["supertrend", "vwap", "adx", "atr", "obv", "ichimoku", "parabolic"]):
                action = "extended"
            else:
                action = "indicators"

            intents.append(ToolIntent(
                tool_name="TechnicalAnalysisTool",
                action=action,
                params={"symbol": symbol},
                confidence=0.95,
                reasoning=f"Heuristic matched technical analysis query for {symbol}"
            ))
            return intents

    # ── 2. Fundamentals / Financial Data (BEFORE MarketData) ──
    financial_keywords = [
        "balance sheet", "income statement", "cash flow", "financials",
        "key ratios", "pe ratio", "pb ratio", "roe", "roa", "eps",
        "earnings", "company info", "company profile", "dividend",
        "debt to equity", "revenue", "profit margin", "annual report"
    ]
    if any(kw in q_lower for kw in financial_keywords):
        tickers = extract_tickers(query)
        if tickers:
            symbol = tickers[0]
            if any(kw in q_lower for kw in ["balance sheet", "income statement", "cash flow"]):
                action = "financials"
            elif any(kw in q_lower for kw in ["earnings", "eps", "revenue"]):
                action = "earnings"
            elif any(kw in q_lower for kw in ["profile", "company info"]):
                action = "company_info"
            else:
                action = "ratios"

            intents.append(ToolIntent(
                tool_name="FinancialDataTool",
                action=action,
                params={"symbol": symbol},
                confidence=0.95,
                reasoning=f"Heuristic matched fundamentals query for {symbol}"
            ))
            return intents

    # ── 3. Financial Calculator ──
    calc_keywords = [
        "cagr", "sip", "lumpsum", "dcf", "pe valuation", "margin",
        "position size", "risk reward", "emi", "compound interest"
    ]
    for kw in calc_keywords:
        if kw in q_lower:
            nums = [float(n) for n in re.findall(r"\b\d+(?:\.\d+)?\b", query)]
            params = {}
            if kw == "cagr" and len(nums) >= 3:
                params = {"initial_value": nums[0], "final_value": nums[1], "years": nums[2]}
            elif kw == "sip" and len(nums) >= 3:
                params = {"monthly_investment": nums[0], "annual_rate_pct": nums[1], "years": int(nums[2])}
            elif kw == "lumpsum" and len(nums) >= 3:
                params = {"principal": nums[0], "annual_rate_pct": nums[1], "years": int(nums[2])}
            elif kw == "emi" and len(nums) >= 3:
                params = {"principal": nums[0], "annual_rate_pct": nums[1], "tenure_months": int(nums[2])}
            elif kw == "margin" and len(nums) >= 3:
                params = {"price": nums[0], "lot_size": int(nums[1]), "margin_pct": nums[2]}
            elif kw == "position size" and len(nums) >= 4:
                params = {"total_capital": nums[0], "risk_per_trade_pct": nums[1], "entry_price": nums[2], "stoploss_price": nums[3]}
            elif kw == "risk reward" and len(nums) >= 3:
                params = {"entry_price": nums[0], "target_price": nums[1], "stoploss_price": nums[2]}

            action = kw.replace(" ", "_")
            intents.append(ToolIntent(
                tool_name="FinancialCalculatorTool",
                action=action,
                params=params,
                confidence=0.98,
                reasoning=f"Heuristic matched calculator query for {kw}"
            ))
            return intents

    # ── 4. F&O Analytics ──
    fno_keywords = ["greeks", "black scholes", "max pain", "option greeks", "implied volatility"]
    if any(kw in q_lower for kw in fno_keywords):
        nums = [float(n) for n in re.findall(r"\b\d+(?:\.\d+)?\b", query)]
        if "greeks" in q_lower or "black scholes" in q_lower:
            params = {}
            if len(nums) >= 4:
                params = {
                    "spot": nums[0], "strike": nums[1],
                    "time_to_expiry": nums[2], "volatility": nums[3],
                    "risk_free_rate": 0.065, "option_type": "put" if "put" in q_lower else "call"
                }
            intents.append(ToolIntent(
                tool_name="FnOAnalyticsTool", action="greeks", params=params, confidence=0.95
            ))
            return intents
        elif "max pain" in q_lower:
            intents.append(ToolIntent(tool_name="FnOAnalyticsTool", action="max_pain", params={}, confidence=0.95))
            return intents

    # ── 5. Market DateTime ──
    dt_keywords = ["is market open", "market status", "market open", "next expiry", "trading holidays", "expiry date"]
    if any(kw in q_lower for kw in dt_keywords):
        if any(kw in q_lower for kw in ["is market open", "market status", "market open"]):
            action = "market_status"
        elif "expiry" in q_lower:
            action = "next_expiry"
        elif "holidays" in q_lower:
            action = "holidays"
        else:
            action = "market_status"

        intents.append(ToolIntent(
            tool_name="MarketDateTimeTool",
            action=action,
            params={"exchange": "BSE" if "bse" in q_lower else "NSE"},
            confidence=0.98
        ))
        return intents

    # ── 6. Portfolio / Watchlist ──
    port_keywords = ["my portfolio", "my holdings", "portfolio summary", "my watchlist", "add to portfolio", "watchlist"]
    if any(kw in q_lower for kw in port_keywords):
        if "watchlist" in q_lower:
            action = "watchlist_view"
        elif "summary" in q_lower:
            action = "summary"
        elif "risk" in q_lower:
            action = "risk"
        else:
            action = "holdings"

        intents.append(ToolIntent(
            tool_name="PortfolioTool",
            action=action,
            params={},
            confidence=0.95
        ))
        return intents

    # ── 7. Market Data / Stock Price (BROAD CATCH-ALL — must be LAST) ──
    price_keywords = [
        "price", "quote", "cost", "share price", "stock price",
        "market cap", "ohlcv", "options chain", "open interest",
        "how much is", "current value", "live price", "stock"
    ]
    ticker_regex = r"\b(tcs|ril|infosys|infy|reliance|aapl|tsla|nvda|msft|googl|btc|eth|wipro|hcl|sbi|icici|hdfc|kotak|bharti|airtel|lt|itc|bajaj)\b"
    if any(kw in q_lower for kw in price_keywords) or re.search(ticker_regex, q_lower):
        tickers = extract_tickers(query)
        if tickers:
            symbol = tickers[0]
            if "ohlcv" in q_lower or "history" in q_lower or "chart" in q_lower or "candle" in q_lower:
                action = "ohlcv"
            elif "options chain" in q_lower or "option chain" in q_lower:
                action = "options_chain"
            elif "open interest" in q_lower or " oi " in q_lower or q_lower.endswith(" oi"):
                action = "oi"
            elif "pcr" in q_lower or "put call ratio" in q_lower:
                action = "pcr"
            elif "iv" in q_lower or "implied volatility" in q_lower:
                action = "iv"
            else:
                action = "price"

            intents.append(ToolIntent(
                tool_name="MarketDataTool",
                action=action,
                params={"symbol": symbol},
                confidence=0.98,
                reasoning=f"Heuristic matched market data query for {symbol}"
            ))
            return intents

    # ── 8. Document Parser ──
    if ".pdf" in q_lower or "parse pdf" in q_lower:
        match = re.search(r"[\w\-\./]+\.pdf", query, re.IGNORECASE)
        file_path = match.group(0) if match else ""
        intents.append(ToolIntent(
            tool_name="DocumentParserTool",
            action="parse",
            params={"file_path": file_path},
            confidence=0.95
        ))
        return intents

    return []


class ToolRouterPipeline:
    """Central orchestrator for the 3B → Tool → 7B pipeline."""

    def __init__(self):
        from modules.tools import registry
        self._registry = registry
        self._logger = logging.getLogger(f"{__name__}.ToolRouterPipeline")

    def route(self, query: str) -> List[ToolIntent]:
        """Step 1: Use fast heuristic router first, fall back to 3B LLM model."""
        # 1. Fast deterministic heuristic match
        h_intents = _heuristic_route(query)
        if h_intents:
            self._logger.info("Heuristic router matched tool: %s/%s", h_intents[0].tool_name, h_intents[0].action)
            return h_intents

        # 2. Fallback to 3B LLM classifier
        from modules import aarkaa_engine

        prompt = aarkaa_engine._build_chatml(ROUTER_SYSTEM_PROMPT, query)
        try:
            response = aarkaa_engine._generate(
                prompt,
                max_new_tokens=512,
                temperature=0.0
            )

            # Parse JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                self._logger.warning("3B router returned no JSON. Falling back to LLM.")
                return []

            parsed = json.loads(response[start:end])

            if not parsed.get("needs_tool", False):
                return []

            intents = []
            for tool_spec in parsed.get("tools", []):
                tool_name = tool_spec.get("tool_name", "")
                if tool_name not in TOOL_NAMES:
                    self._logger.warning("Unknown tool: %s, skipping", tool_name)
                    continue

                intents.append(ToolIntent(
                    tool_name=tool_name,
                    action=tool_spec.get("action", ""),
                    params=tool_spec.get("params", {}),
                    confidence=float(tool_spec.get("confidence", 0.0)),
                    reasoning=tool_spec.get("reasoning", "")
                ))

            # Filter low confidence intents
            intents = [i for i in intents if i.confidence >= 0.3]
            return intents

        except json.JSONDecodeError as e:
            self._logger.error("JSON parse error from 3B router: %s", e)
            return []
        except Exception as e:
            self._logger.error("3B router failed: %s", e)
            return []

    def check_permissions(self, user_id: str, intents: List[ToolIntent], user_tier: str = "free") -> Tuple[List[ToolIntent], List[str]]:
        """Step 2: Validate permissions for each tool intent."""
        from modules.permissions import verify_permission, check_tool_access

        allowed = []
        denied_messages = []

        for intent in intents:
            # Check tool-level ACL
            access = check_tool_access(user_id, intent.tool_name, user_tier)
            if not access["allowed"]:
                denied_messages.append(f"{intent.tool_name}: {access['reason']}")
                continue

            # Check operation-level permission
            perm_level, reason = verify_permission(
                intent.tool_name,
                {"action": intent.action, **intent.params}
            )

            if perm_level == "STRICT_BLOCK":
                denied_messages.append(f"{intent.tool_name}/{intent.action}: {reason}")
                continue

            allowed.append(intent)

        return allowed, denied_messages

    def execute_tools(self, intents: List[ToolIntent]) -> List[ToolResult]:
        """Step 3: Execute each tool and collect results."""
        from datetime import datetime, timezone

        results = []
        for intent in intents:
            start_time = time.perf_counter()
            try:
                # Build params with action
                params = {"action": intent.action, **intent.params}
                output = self._registry.execute_tool(intent.tool_name, params)

                elapsed_ms = (time.perf_counter() - start_time) * 1000
                results.append(ToolResult(
                    tool_name=intent.tool_name,
                    action=intent.action,
                    data=output,
                    is_valid=True,
                    execution_time_ms=elapsed_ms,
                    source="tool",
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))
                self._logger.info(
                    "Tool %s/%s executed in %.1fms",
                    intent.tool_name, intent.action, elapsed_ms
                )

            except Exception as e:
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                self._logger.error("Tool %s/%s failed: %s", intent.tool_name, intent.action, e)
                results.append(ToolResult(
                    tool_name=intent.tool_name,
                    action=intent.action,
                    data="",
                    is_valid=False,
                    error=str(e),
                    execution_time_ms=elapsed_ms,
                    timestamp=datetime.now(timezone.utc).isoformat()
                ))

        return results

    def execute_tool_chain(self, chain: List[ToolIntent]) -> List[ToolResult]:
        """Execute a chain of tools where each tool's output feeds the next.

        Unlike execute_tools() which runs tools independently, this method
        injects accumulated context from prior tool results into each
        subsequent tool's params as '_prior_context'.

        Args:
            chain: Ordered list of ToolIntent objects to execute sequentially.

        Returns:
            List of ToolResult objects, one per tool in the chain.
        """
        results = []
        accumulated_context = ""

        for intent in chain:
            if accumulated_context:
                intent.params["_prior_context"] = accumulated_context

            step_results = self.execute_tools([intent])
            results.extend(step_results)

            for r in step_results:
                if r.is_valid and r.data:
                    accumulated_context += f"\n[{r.tool_name}/{r.action}]\n{r.data}\n"

        return results

    def validate_results(self, results: List[ToolResult]) -> List[ToolResult]:
        """Step 4: Validate tool results for data integrity."""
        validated = []
        for result in results:
            if not result.is_valid:
                self._logger.warning(
                    "Skipping invalid result from %s/%s: %s",
                    result.tool_name, result.action, result.error
                )
                validated.append(result)
                continue

            # Check for empty/error responses
            if not result.data or result.data.strip() == "":
                result.is_valid = False
                result.error = "Tool returned empty result"
            elif result.data.startswith("Error:"):
                result.is_valid = False
                result.error = result.data

            validated.append(result)

        return validated

    def generate_final_answer(self, query: str, results: List[ToolResult], user_id: str = "default", model_override: str = None) -> str:
        """Step 5: Use 7B model to generate final answer from tool results."""
        # Build context from tool results
        tool_context_parts = []
        for r in results:
            if r.is_valid and r.data:
                tool_context_parts.append(
                    f"[{r.tool_name}/{r.action}] (executed in {r.execution_time_ms:.0f}ms):\n{r.data}"
                )
            elif not r.is_valid:
                tool_context_parts.append(
                    f"[{r.tool_name}/{r.action}] ERROR: {r.error}"
                )

        tool_context = "\n\n".join(tool_context_parts)

        system_prompt = """You are AARKAAI, a professional financial AI assistant. You have been provided with verified tool results below. Use ONLY this verified data to answer the user's question. Do not fabricate numbers or data. If tool results contain errors or missing data, acknowledge that clearly.

Present financial data in a clean, structured format. Use tables for comparative data. Include relevant disclaimers for investment advice."""

        user_prompt = f"""User Question: {query}

--- VERIFIED TOOL RESULTS ---
{tool_context}
--- END TOOL RESULTS ---

Using the verified data above, provide a comprehensive answer to the user's question."""

        # Use external 7B model or Gemini/Claude for final answer
        if model_override == "gemini":
            from modules.external_agents import call_gemini_streaming
            # Collect streaming response
            chunks = []
            for chunk in call_gemini_streaming(f"{system_prompt}\n\n{user_prompt}"):
                chunks.append(chunk)
            return "".join(chunks)

        elif model_override == "claude":
            from modules.external_agents import call_claude
            return call_claude(f"{system_prompt}\n\n{user_prompt}")

        else:
            # Default: use local 7B or Gemini as configured
            from modules import aarkaa_engine
            prompt = aarkaa_engine._build_chatml(system_prompt, user_prompt)
            return aarkaa_engine._generate(
                prompt,
                max_new_tokens=2048,
                temperature=0.3
            )

    def process(self, query: str, user_id: str = "default", user_tier: str = "free", model_override: str = None) -> PipelineResult:
        """Execute the full pipeline: 3B Route → Permission → Tool → Validate → 7B Answer."""
        pipeline_start = time.perf_counter()

        # Step 1: Route via 3B
        intents = self.route(query)
        if not intents:
            return PipelineResult(
                final_answer="",  # Caller should fall back to standard LLM path
                intents=[],
                total_time_ms=(time.perf_counter() - pipeline_start) * 1000
            )

        # Step 2: Permission check
        allowed_intents, denied = self.check_permissions(user_id, intents, user_tier)
        if not allowed_intents and denied:
            return PipelineResult(
                final_answer="",
                intents=intents,
                permission_denied=True,
                permission_message="\n".join(denied),
                total_time_ms=(time.perf_counter() - pipeline_start) * 1000
            )

        # Step 3: Execute tools
        results = self.execute_tools(allowed_intents)

        # Step 4: Validate results
        validated = self.validate_results(results)

        # Check if we have any valid results
        valid_results = [r for r in validated if r.is_valid]
        if not valid_results:
            self._logger.warning("All tool results invalid. Falling back.")
            return PipelineResult(
                final_answer="",
                tool_results=validated,
                intents=intents,
                total_time_ms=(time.perf_counter() - pipeline_start) * 1000
            )

        # Step 5: Generate final answer via 7B
        final_answer = self.generate_final_answer(
            query, validated, user_id, model_override
        )

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        self._logger.info("Pipeline completed in %.1fms", total_ms)

        return PipelineResult(
            final_answer=final_answer,
            tool_results=validated,
            intents=allowed_intents,
            total_time_ms=total_ms,
            model_used=model_override or "aarkaa-7b"
        )


# Module-level singleton
_pipeline: Optional[ToolRouterPipeline] = None

def get_pipeline() -> ToolRouterPipeline:
    """Get or create the singleton pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = ToolRouterPipeline()
    return _pipeline


def process_with_tools(query: str, user_id: str = "default", user_tier: str = "free", model_override: str = None) -> PipelineResult:
    """Convenience function to process a query through the tool pipeline."""
    return get_pipeline().process(query, user_id, user_tier, model_override)
