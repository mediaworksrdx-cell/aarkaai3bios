import os
import re
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class SearchTool(Tool):
    name = "SearchTool"
    description = "Perform regex-based text search over files in the workspace."
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 1.0

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 300

    def execute(self, params: Dict[str, Any]) -> str:
        pattern = params.get("pattern")
        if not pattern:
            return "Error: 'pattern' argument is required."

        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except Exception as e:
            return f"Error: Invalid regex pattern '{pattern}': {e}"

        matches = []
        for root, _, files in os.walk(str(SAFE_WORK_DIR)):
            for file in files:
                # Skip binary, log, cache or database files
                if file.endswith((".pyc", ".db", ".png", ".jpg", ".zip", ".git")):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, str(SAFE_WORK_DIR))
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if rx.search(line):
                                matches.append(f"{rel_path}:{i}: {line.strip()}")
                                if len(matches) >= 50:
                                    return "\n".join(matches) + "\n...[truncated after 50 matches]"
                except Exception:
                    continue
        return "\n".join(matches) if matches else "No matches found."
