import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class PkgManagerTool(Tool):
    name = "PkgManagerTool"
    description = (
        "Install and manage python workspace dependency packages natively using "
        "pip environment checks."
    )
    risk_level = "CRITICAL"
    latency_weight = 2.0
    cost_weight = 0.5
    base_confidence = 0.95

    permissions = ["write", "execute", "network"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 4000

    def execute(self, params: Dict[str, Any]) -> str:
        package = params.get("package")
        if not package:
            return "Error: 'package' target is required."

        try:
            # Native pip wrapper call
            result = subprocess.run(
                ["pip", "install", package],
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=90
            )
            return f"Package installation output:\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"Package installation failed: {e}"
