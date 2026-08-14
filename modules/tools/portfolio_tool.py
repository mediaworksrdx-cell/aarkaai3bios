import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.portfolio

logger = logging.getLogger(__name__)

class PortfolioTool(Tool):
    """
    Portfolio management tool for holdings, allocation, and risk.
    """
    name = "PortfolioTool"
    description = "Portfolio management: holdings, P&L, allocation, risk, watchlist. Actions: holdings, add, remove, summary, risk, watchlist_add, watchlist_remove, watchlist_view"
    risk_level = "LOW"
    latency_weight = 1.2
    cost_weight = 0.3
    base_confidence = 0.95
    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 1000

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        user_id = params.get("user_id", "")
        if not user_id:
            return "Error: 'user_id' is required for portfolio actions."

        try:
            if action == "holdings":
                data = modules.portfolio.get_holdings(user_id)
                return f"Portfolio Holdings for {user_id}:\n{str(data)}"
                
            elif action == "add":
                symbol = params.get("symbol", "")
                qty = float(params.get("quantity", 0))
                price = float(params.get("price", 0))
                data = modules.portfolio.add_holding(user_id, symbol, qty, price)
                return f"Added Holding for {user_id}:\n{str(data)}"
                
            elif action == "remove":
                symbol = params.get("symbol", "")
                qty = float(params.get("quantity", 0))
                data = modules.portfolio.remove_holding(user_id, symbol, qty)
                return f"Removed Holding for {user_id}:\n{str(data)}"
                
            elif action == "summary":
                data = modules.portfolio.get_summary(user_id)
                return f"Portfolio Summary for {user_id}:\n{str(data)}"
                
            elif action == "risk":
                data = modules.portfolio.get_portfolio_risk(user_id)
                return f"Portfolio Risk Metrics for {user_id}:\n{str(data)}"
                
            elif action == "watchlist_add":
                symbol = params.get("symbol", "")
                data = modules.portfolio.add_to_watchlist(user_id, symbol)
                return f"Added {symbol} to Watchlist for {user_id}:\n{str(data)}"
                
            elif action == "watchlist_remove":
                symbol = params.get("symbol", "")
                data = modules.portfolio.remove_from_watchlist(user_id, symbol)
                return f"Removed {symbol} from Watchlist for {user_id}:\n{str(data)}"
                
            elif action == "watchlist_view":
                data = modules.portfolio.view_watchlist(user_id)
                return f"Watchlist for {user_id}:\n{str(data)}"
                
            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in PortfolioTool: {str(e)}")
            return f"Error: {e}"
