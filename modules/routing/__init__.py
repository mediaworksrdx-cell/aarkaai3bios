"""
AARKAAI Backend – Unified Query Routing Package

Consolidates the three routing strategies (heuristic, semantic, LLM-based)
into a single composable AgentRouter.
"""
from modules.routing.router import AgentRouter, RoutingDecision

__all__ = ["AgentRouter", "RoutingDecision"]
