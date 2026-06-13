"""
AARKAAI Agents Package
Exposes all specialized agents, dynamic hybrid selection, verifier integration, and orchestration.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from modules.agents.base import BaseAgent
from modules.agents.coding import CodingAgent
from modules.agents.finance import FinanceAgent
from modules.agents.trading import TradingAgent
from modules.agents.marketing import MarketingAgent
from modules.agents.research import ResearchAgent
from modules.agents.support import CustomerSupportAgent
from modules.agents.debugging import DebuggingAgent
from modules.agents.router import select_agents
from modules.agents.verifier import verify_response

logger = logging.getLogger(__name__)

AGENTS: Dict[str, BaseAgent] = {
    "coding": CodingAgent(),
    "debugging": DebuggingAgent(),
    "finance": FinanceAgent(),
    "trading": TradingAgent(),
    "marketing": MarketingAgent(),
    "research": ResearchAgent(),
    "customer_support": CustomerSupportAgent()
}


def compile_hybrid_agent(selected: List[Tuple[str, float]]) -> BaseAgent:
    """Dynamically builds a hybrid BaseAgent from multiple selected agents."""
    names = []
    descriptions = []
    personas = []
    rules = []
    allowed_tools = []
    use_rag = False
    temps = []

    for key, score in selected:
        agent = AGENTS.get(key)
        if agent:
            names.append(agent.name)
            descriptions.append(agent.description)
            personas.append(agent.persona)
            rules.extend(agent.rules)
            allowed_tools.extend(agent.allowed_tools)
            if agent.use_rag:
                use_rag = True
            temps.append(agent.default_temp)

    # De-duplicate rules and tools while keeping order
    rules = list(dict.fromkeys(rules))
    allowed_tools = list(dict.fromkeys(allowed_tools))
    
    hybrid_name = " + ".join(names)
    hybrid_desc = "Hybrid agent combining: " + ", ".join(descriptions)
    hybrid_persona = "You are a hybrid AI agent. " + " ".join(personas)
    avg_temp = sum(temps) / len(temps) if temps else 0.7

    return BaseAgent(
        name=hybrid_name,
        description=hybrid_desc,
        persona=hybrid_persona,
        rules=rules,
        default_temp=avg_temp,
        allowed_tools=allowed_tools,
        use_rag=use_rag
    )


def invoke_agent(
    agent_key: str,
    user_id: str,
    session_id: str,
    query: str,
    device: str = "Web/Browser"
) -> str:
    """Invokes a specific agent by its key name dynamically."""
    agent = AGENTS.get(agent_key.lower())
    if not agent:
        raise ValueError(f"Agent '{agent_key}' is not registered. Choose from: {list(AGENTS.keys())}")
    
    response = agent.invoke(user_id, session_id, query, device)
    
    # Critical pass check for verification
    if agent_key.lower() in ["coding", "debugging", "finance", "trading"]:
        logger.info("Executing verification check for agent: %s", agent_key)
        response = verify_response(query, response)

    return response


def route_and_invoke(
    user_id: str,
    session_id: str,
    query: str,
    device: str = "Web/Browser",
    threshold: float = 0.5
) -> str:
    """Dynamically routes, synthesizes hybrid teams, verifies results, and returns output."""
    # 1. Identify selected agents based on confidence scores
    selected = select_agents(query, threshold=threshold)
    
    # 2. Determine agent execution path
    if not selected:
        # Fallback to customer support if no agent scores high enough
        logger.info("No agents scored above threshold. Defaulting to Customer Support Agent.")
        agent = AGENTS["customer_support"]
        is_critical = False
    elif len(selected) == 1:
        agent_key = selected[0][0]
        logger.info("Routed query to single agent: %s (score: %.2f)", agent_key, selected[0][1])
        agent = AGENTS[agent_key]
        is_critical = agent_key in ["coding", "debugging", "finance", "trading"]
    else:
        logger.info("Synthesizing hybrid agent for scores: %s", selected)
        agent = compile_hybrid_agent(selected)
        # Verify if any selected agent in the hybrid team is critical
        is_critical = any(k in ["coding", "debugging", "finance", "trading"] for k, _ in selected)

    # 3. Invoke selected / synthesized agent
    response = agent.invoke(user_id, session_id, query, device)

    # 4. Apply Verification Layer on critical output checks
    if is_critical:
        logger.info("Applying verification filter layer on query output.")
        response = verify_response(query, response)

    return response
