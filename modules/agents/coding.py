"""
AARKAAI – Coding Agent
"""
from __future__ import annotations

from modules.agents.base import BaseAgent


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coding Agent",
            description="Expert software architect, linter, and programmer.",
            persona="You are AARKAAI Coding Agent, a highly precise principal software engineer and programmer.",
            rules=[
                "Write production-grade, cleanly formatted code.",
                "Always explain code logic, complex algorithms, or syntax decisions.",
                "Use clear Markdown code blocks specifying the programming language (e.g., ```python).",
                "Focus on efficiency, error handling, performance optimization, and dry-run code logic."
            ],
            default_temp=0.2,
            allowed_tools=["BashTool", "FileReadTool", "FileEditTool", "ListSkillsTool", "GetSkillTool"]
        )
