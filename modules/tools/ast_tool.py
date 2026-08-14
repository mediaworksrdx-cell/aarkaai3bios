import ast
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class ASTTool(Tool):
    name = "ASTTool"
    description = (
        "Inspects Python source file structure. Identifies classes, "
        "functions, imports, and variables using Python's native AST parser."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 150

    def execute(self, params: Dict[str, Any]) -> str:
        path_str = params.get("path")
        if not path_str:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path_str)
            if not resolved.is_file():
                return f"Error: File '{path_str}' not found."
            
            with open(resolved, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(resolved))
            
            summary = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    summary.append(f"Class: {node.name} (Line {node.lineno})")
                elif isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    summary.append(f"Function: {node.name}({', '.join(args)}) (Line {node.lineno})")
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    summary.append(f"Import: {ast.unparse(node).strip()} (Line {node.lineno})")

            return "\n".join(summary) if summary else "No classes or functions defined."
        except Exception as e:
            return f"Error analyzing AST: {e}"
