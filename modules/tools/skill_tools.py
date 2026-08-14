"""
AARKAAI – Skill Tools
Provides ListSkillsTool and GetSkillTool for the coordinator agent.
These allow the LLM to dynamically discover and load skill documents at runtime.
"""
import json
import logging
from typing import Any, Dict

from modules.tools.base import Tool

logger = logging.getLogger(__name__)

# Module-level reference to the shared SkillRegistry instance.
# Initialised by main.py at startup via init_skill_registry().
_registry = None


def init_skill_registry(skills_dir: str = "./skills"):
    """Initialise the shared SkillRegistry singleton.
    Called once during application startup from main._init_modules().
    """
    global _registry
    from skills.skill_registry import SkillRegistry  # noqa: delayed import
    _registry = SkillRegistry(skills_dir)
    skill_count = len(_registry.skills)
    logger.info("SkillRegistry loaded %d skills from %s", skill_count, skills_dir)
    return _registry


def get_registry():
    """Return the shared SkillRegistry instance (or None if not initialised)."""
    return _registry


class ListSkillsTool(Tool):
    name = "ListSkillsTool"
    description = (
        "List all available skills with their names and descriptions. "
        "Call this to discover what specialised skill documents are available "
        "before calling GetSkillTool. Takes no parameters: {}."
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        skills = _registry.list_skills()
        if not skills:
            return "No skills available."
        lines = []
        for s in skills:
            lines.append(f"- {s['name']}: {s['description'].strip()}")
        return "\n".join(lines)


class GetSkillTool(Tool):
    name = "GetSkillTool"
    description = (
        "Fetch the concise code templates and instructions for a specific skill. "
        "Read it to get the template code before attempting the task. "
        'Parameters: {"name": "<skill-name>"}'
    )
    risk_level = "SAFE"
    latency_weight = 0.6
    cost_weight = 0.1
    base_confidence = 1.0

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        name = kwargs.get("name", "")
        if not name:
            return "Error: 'name' parameter is required."
        content = _registry.get_skill(name)
        
        # Extract only the first ~4500 characters to keep it functional
        # This covers the installation info and all major code templates/recipes
        if len(content) > 4500:
            content = content[:4500] + "\n...[truncated for conciseness]"
        return content


class CreateSkillTool(Tool):
    name = "CreateSkillTool"
    description = (
        "Create a new custom skill. The name must be unique, and the content must start with "
        "YAML frontmatter (name and description) between '---' markers, followed by markdown content. "
        'Parameters: {"name": "<skill-name>", "content": "<markdown-content-with-frontmatter>"}'
    )
    risk_level = "LOW"
    latency_weight = 1.2
    cost_weight = 0.5
    base_confidence = 0.95

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        name = kwargs.get("name", "")
        content = kwargs.get("content", "")
        if not name:
            return "Error: 'name' parameter is required."
        if not content:
            return "Error: 'content' parameter is required."
        return _registry.create_skill(name, content, user_id="default_user")


class UpdateSkillTool(Tool):
    name = "UpdateSkillTool"
    description = (
        "Update an existing custom skill. Content must contain valid YAML frontmatter (name and description) "
        "between '---' markers. Note: Core skills cannot be updated. "
        'Parameters: {"name": "<skill-name>", "content": "<updated-markdown-content-with-frontmatter>"}'
    )
    risk_level = "LOW"
    latency_weight = 1.2
    cost_weight = 0.5
    base_confidence = 0.95

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        name = kwargs.get("name", "")
        content = kwargs.get("content", "")
        if not name:
            return "Error: 'name' parameter is required."
        if not content:
            return "Error: 'content' parameter is required."
        return _registry.update_skill(name, content, user_id="default_user")


class DeleteSkillTool(Tool):
    name = "DeleteSkillTool"
    description = (
        "Delete an existing custom skill. Note: Core skills cannot be deleted. "
        'Parameters: {"name": "<skill-name>"}'
    )
    risk_level = "HIGH"
    latency_weight = 1.0
    cost_weight = 0.3
    base_confidence = 0.99

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        name = kwargs.get("name", "")
        if not name:
            return "Error: 'name' parameter is required."
        return _registry.delete_skill(name, user_id="default_user")


class ValidateSkillTool(Tool):
    name = "ValidateSkillTool"
    description = (
        "Validate the structure and YAML frontmatter of a skill's content before creation or update. "
        'Parameters: {"content": "<skill-markdown-content>"}'
    )
    risk_level = "SAFE"
    latency_weight = 0.5
    cost_weight = 0.1
    base_confidence = 1.0

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        content = kwargs.get("content", "")
        if not content:
            return "Error: 'content' parameter is required."
        is_valid, msg = _registry.validate_skill_content(content)
        if is_valid:
            return f"Success: Content is valid. Detected skill name: '{msg}'."
        return msg


class TestSkillTool(Tool):
    name = "TestSkillTool"
    description = (
        "Test a skill by running a prompt with that skill's context injected, allowing "
        "you to verify how AARKAAI responds to user prompts using the skill. "
        'Parameters: {"skill_name": "<skill-name>", "test_prompt": "<test-prompt-for-the-skill>"}'
    )
    risk_level = "HIGH"
    latency_weight = 3.0
    cost_weight = 1.0
    base_confidence = 0.90

    def execute(self, kwargs: Dict[str, Any]) -> str:
        if _registry is None:
            return "Error: Skill registry not initialised."
        skill_name = kwargs.get("skill_name", "")
        test_prompt = kwargs.get("test_prompt", "")
        if not skill_name:
            return "Error: 'skill_name' parameter is required."
        if not test_prompt:
            return "Error: 'test_prompt' parameter is required."

        skill_content = _registry.get_skill(skill_name)
        if skill_content.startswith("Error:"):
            return skill_content

        # Execute a subtask using the stream_task from coordinator with injected skill context
        from modules.coordinator import process_task
        context = f"You are testing the skill '{skill_name}'. Below are the guidelines/code templates from the skill:\n\n{skill_content}"
        
        try:
            result = process_task(test_prompt, context=context)
            return f"--- TEST RESULTS FOR SKILL '{skill_name}' ---\nPrompt: {test_prompt}\n\nResponse:\n{result}"
        except Exception as e:
            return f"Error running test prompt: {e}"
