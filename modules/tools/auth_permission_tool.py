from typing import Any, Dict
from modules.tools.base import Tool
from modules import permissions, memory

class AuthPermissionTool(Tool):
    name = "AuthPermissionTool"
    description = "Check user access levels and tool permissions. Actions: check_access, user_info, tool_list"
    risk_level = "SAFE"
    latency_weight = 0.2
    cost_weight = 0.1
    base_confidence = 0.99
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 50

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        try:
            if action == "check_access":
                user_id = params.get("user_id")
                tool_name = params.get("tool_name")
                user_tier = params.get("user_tier")
                return str(permissions.check_tool_access(user_id, tool_name, user_tier))
            elif action == "user_info":
                user_id = params.get("user_id")
                profile = memory.get_user_profile(user_id)
                facts = memory.get_user_facts_prompt(user_id)
                return f"Profile:\n{profile}\n\nFacts:\n{facts}"
            elif action == "tool_list":
                user_tier = params.get("user_tier")
                return str(permissions.get_tool_permissions_summary(user_tier))
            return f"Unknown action: {action}"
        except Exception as e:
            return f"Error: {e}"
