import subprocess
import sys
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path
from config import BASH_TIMEOUT, SAFE_WORK_DIR


class DebuggerTool(Tool):
    name = "DebuggerTool"
    description = (
        "Inspect execution flow and evaluate stack traces matching target "
        "Python modules by running them in an isolated subprocess."
    )
    risk_level = "LOW"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 0.98

    permissions = ["read", "execute"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 1500

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)

            # SEC-C1 FIX: Execute in an isolated subprocess instead of exec()
            # This prevents arbitrary code from accessing the parent process's
            # memory, globals, imports, or environment.
            result = subprocess.run(
                [sys.executable, str(resolved)],
                capture_output=True,
                text=True,
                timeout=BASH_TIMEOUT,
                cwd=str(SAFE_WORK_DIR),
            )

            if result.returncode == 0:
                output = "Execution completed successfully. No traceback exceptions captured."
                if result.stdout:
                    output += f"\n\n[stdout]\n{result.stdout[:2000]}"
                return output
            else:
                output = f"Runtime error captured (exit code {result.returncode}):\n"
                if result.stderr:
                    output += f"\nStack Trace:\n{result.stderr[:3000]}"
                if result.stdout:
                    output += f"\n\n[stdout]\n{result.stdout[:1000]}"
                return output

        except subprocess.TimeoutExpired:
            return f"Error: Debugger execution timed out after {BASH_TIMEOUT} seconds."
        except Exception as e:
            return f"Debugger setup error: {e}"
