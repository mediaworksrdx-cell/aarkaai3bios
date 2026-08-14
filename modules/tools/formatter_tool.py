import subprocess
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class FormatterTool(Tool):
    name = "FormatterTool"
    description = "Automatically format Python code blocks matching Black / PEP8 guidelines."
    risk_level = "HIGH"
    latency_weight = 1.2
    cost_weight = 0.2
    base_confidence = 1.0

    permissions = ["read", "write"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 1200

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            result = subprocess.run(
                ["black", str(resolved)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                return f"Successfully formatted file '{path}' using black."
            return f"Formatting failed: {result.stderr}"
        except FileNotFoundError:
            # Fallback to ruff formatting if black is not installed
            try:
                result = subprocess.run(
                    ["ruff", "format", str(resolved)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15
                )
                if result.returncode == 0:
                    return f"Successfully formatted file '{path}' using ruff."
                return f"Formatting failed: {result.stderr}"
            except Exception as e:
                return f"Formatter tool runner not found: {e}"
        except Exception as e:
            return f"Formatter execution error: {e}"
