from modules.tools.base import ToolRegistry
from modules.tools.bash import BashTool
from modules.tools.fs import FileReadTool, FileEditTool
from modules.tools.web import WebSearchTool
from modules.tools.image import ImageGenTool
from modules.tools.skill_tools import (
    ListSkillsTool, GetSkillTool, CreateSkillTool,
    UpdateSkillTool, DeleteSkillTool, ValidateSkillTool, TestSkillTool
)

registry = ToolRegistry()
registry.register(BashTool())
registry.register(FileReadTool())
registry.register(FileEditTool())
registry.register(WebSearchTool())
registry.register(ImageGenTool())
registry.register(ListSkillsTool())
registry.register(GetSkillTool())
registry.register(CreateSkillTool())
registry.register(UpdateSkillTool())
registry.register(DeleteSkillTool())
registry.register(ValidateSkillTool())
registry.register(TestSkillTool())


