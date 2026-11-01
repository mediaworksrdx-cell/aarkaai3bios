"""
AARKAAI – Coding Agent
"""
from __future__ import annotations

from typing import Optional
from modules.agents.base import BaseAgent


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coding Agent",
            description="Expert software architect, linter, and programmer.",
            persona="You are AARKAAI Coding Agent, a highly precise principal software engineer and programmer.",
            rules=[
                "Write production-grade, cleanly formatted code adhering strictly to textbook specifications and operational algorithms (e.g. B/B+ trees, AVL/Red-Black trees, heap structures).",
                "No Non-functional Stubs or Placeholders: Implementing simplified logic without recursive splitting, tree balancing, or edge constraints is strictly forbidden.",
                "For tree structures, always implement complete recursive split, merge, borrow, or balance mechanics.",
                "Strict Safety checks: Audit array boundaries, duplicate keys, null/empty parameters, and sibling pointer structures (e.g. leaf next/prev chains in B+ trees).",
                "Focus on efficiency, memory safety, error handling, and performance optimization.",
                "Detail common failure modes or edge cases associated with the code."
            ],
            default_temp=0.2,
            allowed_tools=["BashTool", "FileReadTool", "FileEditTool", "ListSkillsTool", "GetSkillTool"]
        )

    def invoke(
        self,
        user_id: str,
        session_id: str,
        query: str,
        device: str = "Web/Browser"
    ) -> str:
        from modules import code_specs, memory
        spec = code_specs.resolve_code_spec(query)
        if spec:
            lang = "dockerfile" if "dockerfile" in query.lower() else "python"
            code_block = f"```{lang}\n{spec}\n```"
            memory.store_conversation(
                user_id=user_id,
                session_id=session_id,
                query=query,
                response=code_block,
                intent="coding_spec_canonical",
                confidence=1.0,
                source="code-specs-verified"
            )
            return code_block
        return super().invoke(user_id, session_id, query, device)
