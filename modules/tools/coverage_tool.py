import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class CoverageTool(Tool):
    name = "CoverageTool"
    description = (
        "Generate and analyze unit test coverage reports using Python's native "
        "coverage library API wrapper."
    )
    risk_level = "LOW"
    latency_weight = 1.5
    cost_weight = 0.3
    base_confidence = 0.98

    permissions = ["read", "execute"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 3000

    def execute(self, params: Dict[str, Any]) -> str:
        try:
            # Native execution of coverage command wrappers
            result = subprocess.run(
                ["coverage", "run", "-m", "pytest"],
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=45
            )
            report = subprocess.run(
                ["coverage", "report", "-m"],
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            return f"Coverage execution summary:\n{report.stdout}"
        except Exception as e:
            return f"Coverage calculation error: {e}"
