import os
import shutil
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class FileTool(Tool):
    name = "FileTool"
    description = "Natively rename, copy, or delete files inside the workspace sandbox."
    risk_level = "HIGH"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["write"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 100

    def execute(self, params: Dict[str, Any]) -> str:
        operation = params.get("operation")
        src = params.get("src")
        
        if not operation or not src:
            return "Error: 'operation' ('rename', 'copy', 'delete') and 'src' paths are required."

        try:
            resolved_src = _resolve_safe_path(src)
            
            if operation == "delete":
                if resolved_src.is_dir():
                    shutil.rmtree(resolved_src)
                else:
                    os.remove(resolved_src)
                return f"Successfully deleted '{src}'."

            dest = params.get("dest")
            if not dest:
                return "Error: 'dest' path is required for copy/rename operations."
            
            resolved_dest = _resolve_safe_path(dest)
            
            if operation == "rename":
                os.rename(resolved_src, resolved_dest)
                return f"Successfully moved/renamed '{src}' to '{dest}'."
            elif operation == "copy":
                if resolved_src.is_dir():
                    shutil.copytree(resolved_src, resolved_dest)
                else:
                    shutil.copy(resolved_src, resolved_dest)
                return f"Successfully copied '{src}' to '{dest}'."
            else:
                return f"Error: Unsupported operation '{operation}'."
        except Exception as e:
            return f"File operation error: {e}"
