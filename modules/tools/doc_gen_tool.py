import ast
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class DocGenTool(Tool):
    name = "DocGenTool"
    description = "Inspect classes and functions in python scripts to compile markdown API document sheets."
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 400

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            doc_lines = [f"# API Reference: {path}\n"]
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    doc_string = ast.get_docstring(node) or "No docstring provided."
                    doc_lines.append(f"## Class: `{node.name}`\n{doc_string}\n")
                elif isinstance(node, ast.FunctionDef):
                    doc_string = ast.get_docstring(node) or "No docstring provided."
                    args = [arg.arg for arg in node.args.args]
                    doc_lines.append(f"### Function: `{node.name}({', '.join(args)})`\n{doc_string}\n")

            return "\n".join(doc_lines)
        except Exception as e:
            return f"Documentation compiler failure: {e}"
