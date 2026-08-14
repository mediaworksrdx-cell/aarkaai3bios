import requests
from typing import Dict, Any
from modules.tools.base import Tool

class HealthTool(Tool):
    name = "HealthTool"
    description = "Validate health, modules, and database status of AARKAAI services."
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["network"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 200

    def execute(self, params: Dict[str, Any]) -> str:
        url = params.get("url", "http://127.0.0.1:8000/health")
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return f"Health check passed (200 OK):\n{resp.text}"
            return f"Health check failed. Status code: {resp.status_code}\nResponse: {resp.text}"
        except Exception as e:
            return f"Service health connection error: {e}"
