import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class DeployTool(Tool):
    name = "DeployTool"
    description = "Pushes build products to configured remote targets via SCP/SSH wrappers."
    risk_level = "CRITICAL"
    latency_weight = 2.5
    cost_weight = 0.8
    base_confidence = 0.95

    permissions = ["write", "execute", "network"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 8000

    def execute(self, params: Dict[str, Any]) -> str:
        script = params.get("script", "deploy.py")
        
        # Deploy operations strictly invoke deployment automation scripts
        if not script.endswith(".py"):
            return "Error: Execution is restricted to deployment python scripts only."

        try:
            result = subprocess.run(
                ["python", script],
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120
            )
            return f"Deployment execution result:\nStdout: {result.stdout}\nStderr: {result.stderr}"
        except Exception as e:
            return f"Deployment failed: {e}"
