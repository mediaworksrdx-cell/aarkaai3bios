from typing import Any, Dict
from modules.tools.base import Tool
from modules import portfolio, memory, notifications

class DatabaseQueryTool(Tool):
    name = "DatabaseQueryTool"
    description = "Query user data: portfolio, watchlists, conversation history, alerts. Actions: portfolio, watchlist, history, alerts"
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 0.95
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 200

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        user_id = params.get("user_id")
        if not user_id:
            return "Error: 'user_id' parameter is required for all actions."
            
        try:
            if action == "portfolio":
                holdings = portfolio.get_holdings(user_id)
                summary = portfolio.get_portfolio_summary(user_id)
                return f"Holdings:\n{holdings}\n\nSummary:\n{summary}"
            elif action == "watchlist":
                return str(portfolio.get_watchlist(user_id))
            elif action == "history":
                limit = params.get("limit", 10)
                return str(memory.get_recent_conversations(user_id, limit))
            elif action == "alerts":
                return str(notifications.get_active_alerts(user_id))
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"
