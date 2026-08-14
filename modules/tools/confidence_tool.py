from typing import Dict, Any
from modules.tools.base import Tool

class ConfidenceTool(Tool):
    name = "ConfidenceTool"
    description = (
        "Calculates technical execution metrics score (0.0 to 1.0) for validation outcomes."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = []
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 80

    def execute(self, params: Dict[str, Any]) -> str:
        passed = params.get("tests_passed", True)
        syntax_ok = params.get("syntax_ok", True)
        
        score = 1.0
        reasons = []
        
        if not passed:
            score -= 0.3
            reasons.append("Unit tests are failing.")
        if not syntax_ok:
            score -= 0.4
            reasons.append("Syntax compilation errors detected.")
            
        return f"Confidence Score: {score:.2f} (Issues: {reasons if reasons else 'none'})"
