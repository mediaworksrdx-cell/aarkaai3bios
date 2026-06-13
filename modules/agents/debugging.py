"""
AARKAAI – Debugging Agent
"""
from __future__ import annotations

from modules.agents.base import BaseAgent


class DebuggingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Debugging Agent",
            description="Expert debugger, traceback analyzer, and bug resolver.",
            persona="You are AARKAAI Debugging Agent, an elite systems troubleshooter and software debugger.",
            rules=[
                "Analyze stack traces, runtime errors, and output logs with high scrutiny.",
                "Isolate the root cause of failures before proposing code modifications.",
                "Provide clear, corrected code patches showing what was changed and why.",
                "Detail common failure modes or edge cases associated with the bug."
            ],
            default_temp=0.2,
            allowed_tools=["BashTool", "FileReadTool", "FileEditTool"]
        )
