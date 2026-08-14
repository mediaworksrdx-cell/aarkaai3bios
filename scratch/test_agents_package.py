"""
AARKAAI – Verification Test Script for Agent Upgrades
"""
from __future__ import annotations

import logging
import sys
import os

# Ensure modules package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestAgents")

from database import init_db
from modules.agents import AGENTS, route_and_invoke, invoke_agent, compile_hybrid_agent
from modules.agents.router import select_agents, route_query

def run_tests():
    logger.info("Initializing database...")
    init_db()

    user_id = "test_user_123"
    session_id = "test_session_abc"

    logger.info("--- TEST 1: Agent Specific Memory ---")
    trading_agent = AGENTS["trading"]
    trading_agent.store_agent_memory(user_id, "risk_tolerance", "conservative")
    trading_agent.store_agent_memory(user_id, "preferred_indicators", "RSI, MACD")

    mem_context = trading_agent.get_agent_memory_context(user_id)
    logger.info("Trading Memory:\n%s", mem_context)
    assert "risk_tolerance" in mem_context, "Failed to load risk tolerance from trading memory"
    assert "preferred_indicators" in mem_context, "Failed to load preferred indicators from trading memory"

    logger.info("--- TEST 2: Tool Ownership ---")
    coding_tools = AGENTS["coding"].get_tools_context()
    logger.info("Coding Agent Tools:\n%s", coding_tools)
    assert "BashTool" in coding_tools, "Coding agent must own BashTool"
    assert "WebSearchTool" not in coding_tools, "Coding agent must not own WebSearchTool"

    logger.info("--- TEST 3: Hybrid Compiler ---")
    hybrid = compile_hybrid_agent([("coding", 0.9), ("debugging", 0.8)])
    logger.info("Hybrid Agent Persona: %s", hybrid.persona)
    logger.info("Hybrid Agent Tools: %s", hybrid.allowed_tools)
    assert "Coding Agent" in hybrid.persona, "Hybrid persona must contain Coding Agent"
    assert "Debugging Agent" in hybrid.persona, "Hybrid persona must contain Debugging Agent"
    assert "BashTool" in hybrid.allowed_tools, "Hybrid agent tools must contain BashTool"

    logger.info("--- ALL TESTS CONCLUDED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_tests()
