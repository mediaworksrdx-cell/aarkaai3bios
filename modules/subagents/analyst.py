"""
AARKAAI — AnalystAgent: Financial analysis with multi-tool chaining.

Chains MarketDataTool → FinancialDataTool → TechnicalAnalysisTool
for each detected ticker, then synthesizes a comprehensive analysis.
"""
from modules.subagents.base import CognitiveSubagent


class AnalystAgent(CognitiveSubagent):
    name = "AnalystAgent"
    description = "Financial analysis with multi-tool chaining."
    system_prompt = """You are AARKAAI's Expert Financial Analyst.

Your objective is to analyze financial data and provide professional, comprehensive insights.

STRICT RULES:
1. Base analysis EXCLUSIVELY on the provided verified tool data. Never fabricate numbers.
2. Present findings in structured format using markdown tables for financial metrics.
3. Maintain a professional, objective, evidence-based tone.
4. For stock comparisons, create side-by-side comparison tables.
5. Include key metrics: Price, Market Cap, P/E, P/B, RSI, MACD, Volume.
6. Always note data freshness (e.g., "as of market close on...").
7. Add brief disclaimers for investment-related conclusions.
8. If any tool returned an error, acknowledge the missing data explicitly.
9. For INR-denominated stocks, use ₹ symbol and Lakh Cr for market cap."""
    allowed_tools = [
        "MarketDataTool", "FinancialDataTool", "TechnicalAnalysisTool",
        "FnOAnalyticsTool", "FinancialCalculatorTool", "MarketDateTimeTool"
    ]
    max_tokens = 2048
    temperature = 0.2

    def _execute(self, query: str, context: dict) -> str:
        from modules.finance import extract_tickers

        try:
            tickers = extract_tickers(query)
        except Exception:
            tickers = []

        all_tool_data = ""
        tools_used = []

        if tickers:
            for symbol in tickers:
                parts = [f"--- {symbol} ---"]

                # Chain 1: Price data
                price_results = self._invoke_tools([
                    ("MarketDataTool", "price", {"symbol": symbol})
                ])
                for r in price_results:
                    if r.is_valid and r.data:
                        parts.append(f"[Price] {r.data}")
                        tools_used.append("MarketDataTool")

                # Chain 2: Financial ratios
                ratio_results = self._invoke_tools([
                    ("FinancialDataTool", "ratios", {"symbol": symbol})
                ])
                for r in ratio_results:
                    if r.is_valid and r.data:
                        parts.append(f"[Ratios] {r.data}")
                        tools_used.append("FinancialDataTool")

                # Chain 3: Technical indicators
                tech_results = self._invoke_tools([
                    ("TechnicalAnalysisTool", "indicators", {"symbol": symbol})
                ])
                for r in tech_results:
                    if r.is_valid and r.data:
                        parts.append(f"[Technicals] {r.data}")
                        tools_used.append("TechnicalAnalysisTool")

                all_tool_data += "\n".join(parts) + "\n\n"
        else:
            # No tickers found — check if context has prior tool data
            prior = context.get("prior_output", "")
            if prior:
                all_tool_data = f"Prior analysis data:\n{prior}"
            else:
                all_tool_data = "No specific tickers identified. Unable to fetch financial data."

        # Synthesize with LLM
        user_prompt = (
            f"User Query: {query}\n\n"
            f"--- VERIFIED FINANCIAL DATA ---\n{all_tool_data}\n"
            f"--- END DATA ---\n\n"
            f"Analyze this data comprehensively. Use markdown tables."
        )
        analysis = self._invoke_model(self.system_prompt, user_prompt)

        # Track tools
        context.setdefault("_tools_used", []).extend(list(set(tools_used)))
        context["_has_tool_data"] = len(tools_used) > 0

        return analysis

    def _estimate_confidence(self, output: str, context: dict) -> float:
        if context.get("_has_tool_data", False):
            return 0.9
        return 0.4
