import difflib
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class PatchTool(Tool):
    name = "PatchTool"
    description = (
        "Applies atomic patch replacements (hunks) on files to support minimal code diff edits."
    )
    risk_level = "HIGH"
    latency_weight = 0.8
    cost_weight = 0.1
    base_confidence = 1.0

    permissions = ["read", "write"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 300

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        target_lines = params.get("target")
        replacement_lines = params.get("replacement")

        if not path or target_lines is None or replacement_lines is None:
            return "Error: 'path', 'target', and 'replacement' text arguments are required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()

            if target_lines not in content:
                return "Error: Target content to replace was not found in the file."

            updated = content.replace(target_lines, replacement_lines, 1)
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(updated)

            # Generate and return unified diff of the patch change
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}"
            )
            return "Patch applied successfully.\n" + "".join(diff)
        except Exception as e:
            return f"Patch operation error: {e}"
