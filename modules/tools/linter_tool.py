import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class LinterTool(Tool):
    name = "LinterTool"
    description = "Run static analysis checks (flake8, ruff) on Python files to find issues."
    risk_level = "LOW"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 0.99

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 800

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            result = subprocess.run(
                ["ruff", "check", str(resolved)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            return result.stdout if result.stdout else "Lint check passed successfully. No issues found."
        except FileNotFoundError:
            # Fallback to standard flake8 if ruff is missing
            try:
                result = subprocess.run(
                    ["flake8", str(resolved)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                return result.stdout if result.stdout else "Lint check passed successfully."
            except Exception as e:
                return f"Linter runner exception: {e}"
        except Exception as e:
            return f"Linter error: {e}"
