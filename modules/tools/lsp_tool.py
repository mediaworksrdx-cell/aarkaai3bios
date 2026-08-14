import jedi
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class LSPTool(Tool):
    name = "LSPTool"
    description = (
        "Resolve class declarations, function signatures, definitions, and references "
        "using python-jedi static analysis parser library."
    )
    risk_level = "SAFE"
    latency_weight = 0.8
    cost_weight = 0.1
    base_confidence = 0.98

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 250

    def execute(self, params: Dict[str, Any]) -> str:
        path_str = params.get("path")
        line = params.get("line")
        column = params.get("column")
        
        if not path_str or line is None or column is None:
            return "Error: 'path', 'line', and 'column' arguments are required."

        try:
            resolved = _resolve_safe_path(path_str)
            with open(resolved, "r", encoding="utf-8") as f:
                source = f.read()

            script = jedi.Script(source, path=str(resolved))
            # Find definitions under the cursor
            defs = script.goto(line=int(line), column=int(column))
            
            result = []
            for d in defs:
                result.append(f"Definition: {d.full_name} in {d.module_path}:{d.line}:{d.column}")
            
            return "\n".join(result) if result else "No definition found at position."
        except Exception as e:
            return f"LSP Execution Error: {e}"
