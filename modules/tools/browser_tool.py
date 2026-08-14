import requests
from typing import Dict, Any
from modules.tools.base import Tool

class BrowserTool(Tool):
    name = "BrowserTool"
    description = (
        "Request HTML data from documentation pages or query APIs natively using requests."
    )
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 0.99

    permissions = ["network"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 800

    def execute(self, params: Dict[str, Any]) -> str:
        url = params.get("url")
        if not url:
            return "Error: 'url' argument is required."

        try:
            resp = requests.get(url, timeout=10)
            # Truncate response context matching agent guidelines
            content = resp.text[:1200]
            return f"HTTP Status: {resp.status_code}\nContent Preview:\n{content}..."
        except Exception as e:
            return f"Headless connection lookup failure: {e}"
