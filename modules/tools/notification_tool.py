from typing import Any, Dict
from modules.tools.base import Tool
from modules import notifications

class NotificationTool(Tool):
    name = "NotificationTool"
    description = "Manage price alerts and market events. Actions: create_alert, check_alerts, list_alerts, cancel_alert, market_events"
    risk_level = "LOW"
    latency_weight = 1.0
    cost_weight = 0.3
    base_confidence = 0.93
    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 1000

    VALID_CONDITIONS = ['above', 'below', 'crosses_above', 'crosses_below', 'pct_change']

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        try:
            if action == "create_alert":
                user_id = params.get("user_id")
                symbol = params.get("symbol")
                condition = params.get("condition")
                threshold = params.get("threshold")
                notes = params.get("notes")
                if condition not in self.VALID_CONDITIONS:
                    return f"Error: Invalid condition. Must be one of {self.VALID_CONDITIONS}"
                return str(notifications.create_alert(user_id, symbol, condition, threshold, notes))
            elif action == "check_alerts":
                user_id = params.get("user_id")
                return str(notifications.check_alerts(user_id))
            elif action == "list_alerts":
                user_id = params.get("user_id")
                return str(notifications.get_active_alerts(user_id))
            elif action == "cancel_alert":
                user_id = params.get("user_id")
                alert_id = params.get("alert_id")
                return str(notifications.cancel_alert(user_id, alert_id))
            elif action == "market_events":
                return str(notifications.get_upcoming_market_events())
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"
