from modules.tools.base import ToolRegistry
from modules.tools.bash import BashTool
from modules.tools.fs import FileReadTool, FileEditTool
from modules.tools.web import WebSearchTool

registry = ToolRegistry()
registry.register(BashTool())
registry.register(FileReadTool())
registry.register(FileEditTool())
registry.register(WebSearchTool())
