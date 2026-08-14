import sys
import traceback
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class DebuggerTool(Tool):
    name = "DebuggerTool"
    description = (
        "Inspect execution flow and evaluate stack traces matching target "
        "Python modules natively."
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
            with open(resolved, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            # Execute in isolated space capturing tracebacks
            local_scope = {}
            try:
                exec(code_content, {"__name__": "__main__"}, local_scope)
                return "Execution completed successfully. No traceback exceptions captured."
            except Exception as runtime_err:
                tb = traceback.format_exc()
                return f"Runtime error captured:\n{runtime_err}\n\nStack Trace:\n{tb}"
        except Exception as e:
            return f"Debugger setup error: {e}"
