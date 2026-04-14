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

    def execute_tool(self, name: str, params: Dict[str, Any]) -> str:
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool '{name}' not found. Available: {list(self.tools.keys())}"
        try:
            result = tool.execute(params)
            return str(result)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"
