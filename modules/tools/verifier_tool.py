from typing import Dict, Any
from modules.tools.base import Tool
from modules.agents.verifier import verify_response

class VerifierTool(Tool):
    name = "VerifierTool"
    description = (
        "Natively run the verification check on code modifications to "
        "enforce coding rules."
    )
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 1000

    def execute(self, params: Dict[str, Any]) -> str:
        prompt = params.get("prompt", "")
        code_block = params.get("code", "")

        if not code_block:
            return "Error: 'code' argument containing the block to verify is required."

        try:
            # Perform verification check on the proposed code block
            verified_output = verify_response(prompt, code_block)
            return f"Verification Outcome:\n{verified_output}"
        except Exception as e:
            return f"Verifier execution error: {e}"
