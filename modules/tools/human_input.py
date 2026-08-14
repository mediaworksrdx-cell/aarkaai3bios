from modules.tools.base import Tool
from typing import Dict, Any

class HumanInput(Tool):
    name: str = "HumanInput"
    description: str = "Ask the user for clarification, paths, passwords, or decision approvals."
    risk_level: str = "SAFE"
    latency_weight: float = 2.0
    cost_weight: float = 0.5
    base_confidence: float = 1.0

    def execute(self, kwargs: Dict[str, Any]) -> str:
        prompt_text = kwargs.get("prompt", "Please provide input:")
        # Return structured instruction so the client platform knows to intercept this.
        # If running inside a background console pipeline without interaction, it requests default fallback.
        return f"INTERACTIVE_INPUT_REQUEST: {prompt_text}"
