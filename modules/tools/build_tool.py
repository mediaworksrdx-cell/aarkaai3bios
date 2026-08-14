import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class BuildTool(Tool):
    name = "BuildTool"
    description = (
        "Execute build tasks using workspace build tooling frameworks (e.g. npm, Gradle, Pip)."
    )
    risk_level = "HIGH"
    latency_weight = 2.0
    cost_weight = 0.5
    base_confidence = 0.95

    permissions = ["write", "execute"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = True
    estimated_latency_ms = 5000

    def execute(self, params: Dict[str, Any]) -> str:
        build_system = params.get("system", "pip")
        
        # Safe mapping of build commands
        if build_system == "npm":
            args = ["npm", "run", "build"]
        elif build_system == "pip":
            args = ["pip", "install", "-r", "requirements.txt"]
        else:
            return f"Unsupported build system: {build_system}"

        try:
            result = subprocess.run(
                args,
                cwd=str(SAFE_WORK_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120
            )
            return f"Build completed with exit code: {result.returncode}\n{result.stdout}\n{result.stderr}"
        except Exception as e:
            return f"Build execution failed: {e}"
