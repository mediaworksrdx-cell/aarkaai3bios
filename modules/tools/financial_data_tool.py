import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.fundamentals

logger = logging.getLogger(__name__)

class FinancialDataTool(Tool):
    """
    Financial data tool for statements, ratios, and fundamentals.
    """
    name = "FinancialDataTool"
    description = "Financial statements, ratios, earnings, company fundamentals. Actions: financials, ratios, earnings, company_info"
    risk_level = "SAFE"
    latency_weight = 1.5
    cost_weight = 0.5
    base_confidence = 0.93
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 2000

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        symbol = params.get("symbol", "")
        if not symbol and action != "default":
            return "Error: 'symbol' is required for financial data."

        try:
            if action == "financials":
                statement_type = params.get("statement_type", "income_statement")
                data = modules.fundamentals.get_financial_statements(symbol, statement_type)
                return modules.fundamentals.format_fundamentals_context(data, "statement")
                
            elif action == "ratios":
                data = modules.fundamentals.get_key_ratios(symbol)
                return f"Key Ratios for {symbol}:\n{str(data)}"
                
            elif action == "earnings":
                data = modules.fundamentals.get_earnings(symbol)
                return f"Earnings Data for {symbol}:\n{str(data)}"
                
            elif action == "company_info":
                data = modules.fundamentals.get_company_info(symbol)
                return f"Company Info for {symbol}:\n{str(data)}"
                
            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in FinancialDataTool: {str(e)}")
            return f"Error: {e}"
