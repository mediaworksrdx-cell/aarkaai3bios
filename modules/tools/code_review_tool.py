from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path
from modules.agents.verifier import verify_response

class CodeReviewTool(Tool):
    name = "CodeReviewTool"
    description = "Validate script patches against programming guidelines and coding standards."
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 1200

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' is required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                code = f.read()

            # Perform standards review check using verify_response helper
            logs = verify_response("Verify strict enterprise coding guidelines.", code)
            
            review = (
                f"Code Review Assessment for {path}:\n"
                f"Review Output:\n{logs}"
            )
            return review
        except Exception as e:
            return f"Code review execution failure: {e}"
