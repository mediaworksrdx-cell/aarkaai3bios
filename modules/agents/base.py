"""
AARKAAI – Base Agent Class and Context Utilities
Provides common memory, user profile, and session context synthesis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from modules import aarkaa_engine, memory

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base Agent class that every specialized agent inherits from."""

    def __init__(
        self,
        name: str,
        description: str,
        persona: str,
        rules: List[str],
        default_temp: float = 0.7,
        allowed_tools: Optional[List[str]] = None,
        use_rag: bool = False
    ):
        self.name = name
        self.description = description
        self.persona = persona
        self.rules = rules
        self.default_temp = default_temp
        self.allowed_tools = allowed_tools or []
        self.use_rag = use_rag

    def get_session_context(self, session_id: str, device: str) -> str:
        """Dynamic snapshot of session state."""
        now = datetime.now(timezone.utc)
        return (
            f"[Session Context]\n"
            f"- Session ID: {session_id}\n"
            f"- Local Time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"- Day of Week: {now.strftime('%A')}\n"
            f"- Client Device: {device}\n"
            f"- Environment: Production Backend\n"
        )

    def get_user_profile_context(self, user_id: str) -> str:
        """Dynamic snapshot of user facts and profile."""
        facts = memory.get_user_facts_prompt(user_id)
        profile = memory.get_user_profile(user_id)
        
        lines = []
        if facts:
            lines.append(facts)
        else:
            lines.append("[User Profile]\n- Dynamic Fact profile is empty/building.")

        interests = profile.get("interests", [])
        expertise = profile.get("expertise_areas", [])
        
        if interests:
            lines.append(f"- Known Interests: {', '.join(interests)}")
        if expertise:
            lines.append(f"- Expertise Areas: {', '.join(expertise)}")
            
        lines.append(f"- Platform Interaction Count: {profile.get('interaction_count', 0)}")
        return "\n".join(lines)

    def get_agent_memory_context(self, user_id: str) -> str:
        """Fetches agent-specific preferences and states from memory."""
        agent_key = self.name.lower().replace(" ", "_")
        mems = memory.get_user_memories(user_id, category=f"agent_memory:{agent_key}")
        if not mems:
            return ""
        lines = [f"[{self.name} Internal Memory]"]
        for m in mems:
            lines.append(f"- {m['key']}: {m['value']}")
        return "\n".join(lines)

    def store_agent_memory(self, user_id: str, key: str, value: str):
        """Saves a key-value pair to this specific agent's memory."""
        agent_key = self.name.lower().replace(" ", "_")
        memory.update_user_memory(user_id, key=key, value=value, category=f"agent_memory:{agent_key}")

    def get_tools_context(self) -> str:
        """Dynamically builds a list of tools owned by this agent."""
        if not self.allowed_tools:
            return ""
        from modules.tools import registry
        lines = [f"[Allowed Tools for {self.name}]"]
        for t_name in self.allowed_tools:
            tool = registry.get_tool(t_name)
            if tool:
                lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def get_rag_context(self, query: str) -> str:
        """Injects relevant RAG documents if enabled."""
        if not self.use_rag:
            return ""
        try:
            from modules import rag
            results = rag.query_knowledge(query, threshold=0.35, limit=3)
            if results:
                lines = ["[Retrieved Knowledge / Citations]"]
                for r in results:
                    lines.append(f"- Topic: {r['topic']}\n  Content: {r['content']}")
                return "\n".join(lines)
        except Exception as e:
            logger.error("RAG retrieval failed: %s", e)
        return ""

    def compile_prompt(self, user_id: str, session_id: str, device: str, query: str = "") -> str:
        """Assembles base system definitions, rules, session context, user profiles, agent memory, tools, and RAG."""
        system_part = f"{self.persona}\n\n[Core Operating Guidelines]\n"
        for rule in self.rules:
            system_part += f"- {rule}\n"

        session_part = self.get_session_context(session_id, device)
        profile_part = self.get_user_profile_context(user_id)
        agent_mem_part = self.get_agent_memory_context(user_id)
        tools_part = self.get_tools_context()
        rag_part = self.get_rag_context(query) if query else ""

        components = [system_part, session_part, profile_part]
        if agent_mem_part:
            components.append(agent_mem_part)
        if tools_part:
            components.append(tools_part)
        if rag_part:
            components.append(rag_part)

        return "\n\n".join(components) + "\n---"

    def invoke(
        self,
        user_id: str,
        session_id: str,
        query: str,
        device: str = "Web/Browser"
    ) -> str:
        """Executes a turn on the agent, loading/saving memory and user facts dynamically."""
        # 1. Update Profile Facts
        memory.extract_user_facts(user_id, query)

        # 2. Fetch Conversation Memory context
        history = memory.get_chat_context(user_id, session_id, limit=6)

        # 3. Assemble complete system prompt
        system_prompt = self.compile_prompt(user_id, session_id, device, query)

        # 4. Format into ChatML
        formatted_prompt = aarkaa_engine._build_chatml_multi(
            system=system_prompt,
            history=history,
            user=query
        )

        # 5. Generate Response
        logger.info("Invoking agent %s for user %s", self.name, user_id)
        response = aarkaa_engine._generate(
            formatted_prompt,
            max_new_tokens=1024,
            temperature=self.default_temp
        )

        # 6. Store turn to Memory
        memory.store_conversation(
            user_id=user_id,
            session_id=session_id,
            query=query,
            response=response,
            intent=self.name.lower().replace(" ", "_"),
            confidence=0.9,
            source=f"agent-{self.name.lower().replace(' ', '-')}"
        )

        return response
