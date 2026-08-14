import subprocess
from typing import Dict, Any
from modules.tools.base import Tool

class DockerTool(Tool):
    name = "DockerTool"
    description = (
        "Inspect container definitions, environment specs, or docker daemon presence natively."
    )
    risk_level = "CRITICAL"
    latency_weight = 2.0
    cost_weight = 0.5
    base_confidence = 0.95

    permissions = ["write", "execute"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 4000

    def execute(self, params: Dict[str, Any]) -> str:
        operation = params.get("operation", "ps")
        if operation not in ["ps", "images", "version"]:
            return f"Error: Docker operation '{operation}' is blocked for workspace security."

        try:
            result = subprocess.run(
                ["docker", operation],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            return f"Docker {operation} output:\n{result.stdout}\n{result.stderr}"
        except FileNotFoundError:
            return "Docker daemon / command-line wrapper is not installed in host ecosystem."
        except Exception as e:
            return f"Docker tool execution failure: {e}"
