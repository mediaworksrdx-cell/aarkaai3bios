from typing import Dict, Any
from modules.tools.base import Tool
from modules.cvr_pipeline import SecurityScanner

class SecurityTool(Tool):
    name = "SecurityTool"
    description = (
        "Analyze workspace files for credentials leaks, vulnerable command injections, "
        "and security policy compliance using the static AST scanner."
    )
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 0.99

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
            scanner = SecurityScanner()
            issues = scanner.scan_file(path)
            
            if not issues:
                return "Security scan passed. No critical vulnerabilities found."
            
            res = []
            for issue in issues:
                res.append(f"[{issue['type']}] line {issue.get('line', 'unknown')}: {issue['details']}")
            return "\n".join(res)
        except Exception as e:
            return f"Security audit execution error: {e}"
