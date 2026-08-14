import cProfile
import pstats
import io
from typing import Dict, Any
from modules.tools.base import Tool
from modules.tools.fs import _resolve_safe_path

class ProfilerTool(Tool):
    name = "ProfilerTool"
    description = (
        "Natively run python target files inside cProfile to trace execution hotspots, "
        "function call counts, and execution bottlenecks."
    )
    risk_level = "LOW"
    latency_weight = 1.6
    cost_weight = 0.3
    base_confidence = 0.99

    permissions = ["read", "execute"]
    supported_languages = ["python"]
    requires_workspace = True
    supports_streaming = False
    estimated_latency_ms = 2500

    def execute(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        if not path:
            return "Error: 'path' argument is required."

        try:
            resolved = _resolve_safe_path(path)
            
            # Setup cProfile execution sandbox
            pr = cProfile.Profile()
            pr.enable()
            
            with open(resolved, "r", encoding="utf-8") as f:
                code_content = f.read()
            
            local_vars = {}
            exec(code_content, {"__name__": "__main__"}, local_vars)
            
            pr.disable()
            s = io.StringIO()
            ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
            ps.print_stats(30)
            
            return f"Profile trace (top 30 hotspots):\n{s.getvalue()}"
        except Exception as e:
            return f"Execution profiling error: {e}"
