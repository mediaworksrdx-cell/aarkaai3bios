from typing import Any, Dict
from modules.tools.base import Tool
from modules import market_datetime

class MarketDateTimeTool(Tool):
    name = "MarketDateTimeTool"
    description = "Market sessions, expiry dates, trading holidays, time calculations. Actions: market_status, next_expiry, holidays, time_to_expiry, is_trading_day, session_info"
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
                exchange = params.get("exchange") or "NSE"
                return str(market_datetime.is_market_open(exchange))
            elif action == "next_expiry":
                expiry_type = params.get("expiry_type") or "monthly"
                exchange = params.get("exchange") or "NSE"
                return str(market_datetime.next_expiry(expiry_type, exchange))
            elif action == "holidays":
                exchange = params.get("exchange") or "NSE"
                year = int(params["year"]) if params.get("year") else market_datetime.now(exchange).year
                status = market_datetime.holiday_calendar_status(year, exchange)
                return str({"holidays": market_datetime.get_trading_holidays(year, exchange), **status})
            elif action == "time_to_expiry":
                expiry_date_str = params.get("expiry_date_str") or ""
                if not expiry_date_str:
                    return "Error: expiry_date_str (YYYY-MM-DD) is required"
                return str(market_datetime.time_to_expiry(expiry_date_str, params.get("exchange") or "NSE"))
            elif action == "session_info":
                return str(market_datetime.market_session_info(params.get("exchange") or "NSE"))
            elif action == "is_trading_day":
                check_date = params.get("check_date")
                exchange = params.get("exchange") or "NSE"
                return str(market_datetime.is_trading_day(check_date, exchange))
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"
