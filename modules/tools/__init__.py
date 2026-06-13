from modules.tools.base import ToolRegistry
from modules.tools.bash import BashTool
from modules.tools.fs import FileReadTool, FileEditTool
from modules.tools.web import WebSearchTool
from modules.tools.skill_tools import ListSkillsTool, GetSkillTool

registry = ToolRegistry()
registry.register(BashTool())
registry.register(FileReadTool())
registry.register(FileEditTool())
registry.register(WebSearchTool())
registry.register(ListSkillsTool())
registry.register(GetSkillTool())
