import time
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class BenchmarkTool(Tool):
    name = "BenchmarkTool"
    description = "Trace speed performance statistics and execution bottlenecks on target code blocks."
    risk_level = "LOW"
    latency_weight = 1.6
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read", "execute"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 3000

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()

            start_t = time.perf_counter()
            exec_vars = {}
            exec(content, {"__name__": "__main__"}, exec_vars)
            elapsed = time.perf_counter() - start_t
            
            return f"Benchmark completed.\nTotal Execution Time: {elapsed:.4f} seconds"
        except Exception as e:
            return f"Performance benchmark run error: {e}"
