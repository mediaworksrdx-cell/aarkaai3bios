import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class TestTool(Tool):
    name = "TestTool"
    description = "Execute unit test suites (pytest, jest) on the target workspace."
    risk_level = "HIGH"
    latency_weight = 1.8
    cost_weight = 0.5
    base_confidence = 0.98

    permissions = ["read", "execute"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = True
    estimated_latency_ms = 4000

    def execute(self, params: Dict[str, Any]) -> str:
        framework = params.get("framework", "pytest")
        test_path = params.get("path", "")

        if framework == "pytest":
            args = ["pytest"]
            if test_path:
                args.append(test_path)
        elif framework == "npm":
            args = ["npm", "test"]
        else:
            return f"Unsupported testing framework: {framework}"

        try:
            result = subprocess.run(
                args,
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )
            return f"Tests finished with exit code {result.returncode}\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"Error executing tests: {e}"
