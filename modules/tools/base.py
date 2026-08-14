"""
AARKAAI – Tool execution framework.
Defines the base class for all tools and the tool registry.
"""
from typing import Any, Dict

class SubtaskError(Exception):
    pass

class Tool:
    name: str = "BaseTool"
    description: str = "Base description"
    risk_level: str = "SAFE"        # SAFE | LOW | HIGH | CRITICAL
    latency_weight: float = 1.0     # 1.0 = normal, < 1.0 = faster, > 1.0 = slower
    cost_weight: float = 1.0        # 1.0 = normal, < 1.0 = cheaper, > 1.0 = expensive
    base_confidence: float = 1.0    # Baseline accuracy score (0.0 to 1.0)
    
    # Metadata fields for planner matching
    permissions: list[str] = []
    supported_languages: list[str] = ["*"]
    requires_workspace: bool = True
    supports_streaming: bool = False
    estimated_latency_ms: int = 1000

    def execute(self, kwargs: Dict[str, Any]) -> str:
        """Execute the tool with the given arguments."""
        raise NotImplementedError

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)

    def get_all_tool_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Return registry metadata mapping for the planning module."""
        return {
            name: {
                "name": t.name,
                "description": t.description,
                "risk_level": getattr(t, "risk_level", "SAFE"),
                "latency_weight": getattr(t, "latency_weight", 1.0),
                "cost_weight": getattr(t, "cost_weight", 1.0),
                "base_confidence": getattr(t, "base_confidence", 1.0),
            }
            for name, t in self.tools.items()
        }

    def execute_tool(self, name: str, params: Dict[str, Any]) -> str:
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool '{name}' not found. Available: {list(self.tools.keys())}"
        
        # Telemetry metrics
        if not hasattr(tool, "success_count"):
            tool.success_count = 0
            tool.failure_count = 0
            tool.last_latency_ms = 0

        import time
        start_time = time.perf_counter()
        try:
            result = tool.execute(params)
            tool.success_count += 1
            tool.last_latency_ms = int((time.perf_counter() - start_time) * 1000)
            return str(result)
        except Exception as e:
            # Re-raise GitCredentialsError to prevent capturing as generic string
            from modules.tools.git_tool import GitCredentialsError
            if isinstance(e, GitCredentialsError):
                raise e
            tool.failure_count += 1
            tool.last_latency_ms = int((time.perf_counter() - start_time) * 1000)
            return f"Error executing {name}: {str(e)}"
