import ast
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class CallGraphTool(Tool):
    name = "CallGraphTool"
    description = (
        "Construct caller-callee dependency relationship trees for target Python modules."
    )
    risk_level = "SAFE"
    latency_weight = 0.8
    cost_weight = 0.2
    base_confidence = 0.98

    permissions = ["read"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 350

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            calls = {}
            current_func = "global"

            class CallVisitor(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    nonlocal current_func
                    old_func = current_func
                    current_func = node.name
                    calls[current_func] = []
                    self.generic_visit(node)
                    current_func = old_func

                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        calls.setdefault(current_func, []).append(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.setdefault(current_func, []).append(node.func.attr)
                    self.generic_visit(node)

            CallVisitor().visit(tree)
            
            output = []
            for func, callee_list in calls.items():
                if callee_list:
                    output.append(f"Function {func}() calls: {', '.join(set(callee_list))}")
            return "\n".join(output) if output else "No function calls mapped in target file."
        except Exception as e:
            return f"Call graph computation error: {e}"
