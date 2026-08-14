import ast
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class SymbolTool(Tool):
    name = "SymbolTool"
    description = (
        "Identify specific symbol declarations (classes, functions) across python files."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 200

    def execute(self, params: Dict[str, Any]) -> str:
        symbol = params.get("symbol")
        path = params.get("path")
        if not symbol or not path:
            return "Error: 'symbol' name and 'path' are required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == symbol:
                    return f"Symbol '{symbol}' found in file '{path}' at line {node.lineno}."
            return f"Symbol '{symbol}' not declared in '{path}'."
        except Exception as e:
            return f"Symbol search error: {e}"
