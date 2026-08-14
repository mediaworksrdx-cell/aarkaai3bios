import os
import re
from typing import Dict, Any
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

class XrefTool(Tool):
    name = "XrefTool"
    description = "Trace cross-references (where a specific code symbol is used) inside the workspace."
    risk_level = "SAFE"
    latency_weight = 0.8
    cost_weight = 0.2
    base_confidence = 0.98

    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 400

    def execute(self, params: Dict[str, Any]) -> str:
        symbol = params.get("symbol")
        if not symbol:
            return "Error: 'symbol' name is required."

        rx = re.compile(rf"\b{re.escape(symbol)}\b")
        references = []

        for root, _, files in os.walk(str(SAFE_WORK_DIR)):
            for file in files:
                if file.endswith((".pyc", ".db", ".png", ".jpg", ".git")):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, str(SAFE_WORK_DIR))
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if rx.search(line):
                                references.append(f"{rel_path}:{i}: {line.strip()}")
                                if len(references) >= 30:
                                    return "\n".join(references) + "\n...[truncated after 30 references]"
                except Exception:
                    continue
        return "\n".join(references) if references else f"No cross-references found for symbol: {symbol}"
