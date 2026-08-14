import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class CiCdTool(Tool):
    name = "CiCdTool"
    description = (
        "Verify build status and simulate CI pipeline runs (e.g. actions syntax, docker build)."
    )
    risk_level = "HIGH"
    latency_weight = 1.8
    cost_weight = 0.4
    base_confidence = 0.95

    permissions = ["read", "execute"]
    supported_languages = ["yaml"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 3500

    def execute(self, params: Dict[str, Any]) -> str:
        try:
            # Safe wrapper executing static syntax tests on yaml configs
            result = subprocess.run(
                ["pytest", "tests/"],
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            return f"CI Workflow Simulator Result:\n{result.stdout}"
        except Exception as e:
            return f"CI validation run exception: {e}"
