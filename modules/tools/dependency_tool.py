import ast
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class DependencyTool(Tool):
    name = "DependencyTool"
    description = (
        "Map top-level python imports and script module hierarchies in target directories."
    )
    risk_level = "SAFE"
    latency_weight = 0.6
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 250

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            deps = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        deps.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    deps.append(f"{node.module} ({', '.join([n.name for n in node.names])})")
            
            return f"Module Dependencies:\n" + "\n".join([f"- {d}" for d in set(deps)]) if deps else "No dependencies detected."
        except Exception as e:
            return f"Dependency mapping error: {e}"
