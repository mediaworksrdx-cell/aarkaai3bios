from typing import Dict, Any
from modules.tools.base import Tool
import ast

class RepairTool(Tool):
    name = "RepairTool"
    description = (
        "Natively runs AST NodeTransformer rewrites to fix unsafe shell executions."
    )
    risk_level = "HIGH"
    latency_weight = 1.0
    cost_weight = 0.3
    base_confidence = 0.98

    permissions = ["read", "write"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 800

    def execute(self, params: Dict[str, Any]) -> str:
        code_block = params.get("code")
        if not code_block:
            return "Error: 'code' argument containing the python script is required."

        try:
            from modules.repair_agents import ChainedRepairController
            
            # Use ChainedRepairController internal security repair logic directly
            repaired_code = ChainedRepairController._apply_security_fix(code_block, ["subprocess_shell"])
            return f"Repaired Code:\n{repaired_code}"
        except Exception as e:
            return f"Repair Tool transformation error: {e}"
