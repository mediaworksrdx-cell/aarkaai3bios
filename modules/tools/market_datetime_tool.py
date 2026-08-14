from typing import Any, Dict
from modules.tools.base import Tool
from modules import market_datetime

class MarketDateTimeTool(Tool):
    name = "MarketDateTimeTool"
    description = "Market sessions, expiry dates, trading holidays, time calculations. Actions: market_status, next_expiry, holidays, time_to_expiry, is_trading_day"
    risk_level = "SAFE"
    latency_weight = 0.2
    cost_weight = 0.1
    base_confidence = 0.98
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 50

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        try:
            if action == "market_status":
                exchange = params.get("exchange")
                return str(market_datetime.is_market_open(exchange))
            elif action == "next_expiry":
                expiry_type = params.get("expiry_type")
                exchange = params.get("exchange")
                return str(market_datetime.next_expiry(expiry_type, exchange))
            elif action == "holidays":
                year = params.get("year")
                exchange = params.get("exchange")
                return str(market_datetime.get_trading_holidays(year, exchange))
            elif action == "time_to_expiry":
                expiry_date_str = params.get("expiry_date_str")
                return str(market_datetime.time_to_expiry(expiry_date_str))
            elif action == "is_trading_day":
                check_date = params.get("check_date")
                exchange = params.get("exchange")
                return str(market_datetime.is_trading_day(check_date, exchange))
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"
