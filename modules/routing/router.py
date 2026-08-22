"""
AARKAAI Backend – Unified Agent Router

Replaces the previous triple-router architecture (hybrid_router.py,
ai_router.py, semantic_filter.py) with a single composable router
that tries strategies in priority order.

Existing routers are preserved as strategy implementations;
this module provides a unified entry point.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of agent routing."""
    agent: str
    confidence: float = 0.0
    strategy_used: str = "unknown"
    scores: dict[str, float] = field(default_factory=dict)
    is_hybrid: bool = False
    hybrid_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentRouter:
    """
    Unified agent router that composes multiple routing strategies.
    
    Tries strategies in priority order:
    1. Heuristic (fast keyword + embedding scoring via HybridQueryRouter)
    2. Semantic (cosine similarity pre-filter)
    3. LLM-based (fallback classification via AI router)
    
    Usage:
        router = AgentRouter()
        decision = router.route("What is the P/E ratio of AAPL?")
        print(decision.agent, decision.confidence, decision.strategy_used)
    """
    
    def __init__(self):
        self._heuristic = None
        self._semantic = None
        self._llm = None
        self._initialized = False
    
    def _lazy_init(self):
        """Lazy-load routing strategies to avoid circular imports."""
        if self._initialized:
            return
        self._initialized = True
        
        try:
            from modules.hybrid_router import HybridQueryRouter
            self._heuristic = HybridQueryRouter()
            logger.info("AgentRouter: Heuristic strategy loaded (hybrid_router)")
        except Exception as e:
            logger.warning("AgentRouter: Heuristic strategy unavailable: %s", e)
        
        try:
            from modules.semantic_filter import SemanticFilter
            self._semantic = SemanticFilter()
            logger.info("AgentRouter: Semantic strategy loaded (semantic_filter)")
        except Exception as e:
            logger.warning("AgentRouter: Semantic strategy unavailable: %s", e)
        
        try:
            from modules.ai_router import AIRouter
            self._llm = AIRouter()
            logger.info("AgentRouter: LLM strategy loaded (ai_router)")
        except Exception as e:
            logger.warning("AgentRouter: LLM strategy unavailable: %s", e)
    
    def route(
        self,
        query: str,
        context: Optional[dict] = None,
        confidence_threshold: float = 0.50,
    ) -> RoutingDecision:
        """
        Route a query to the best agent(s), trying strategies in priority order.
        
        Args:
            query: The user's input query.
            context: Optional context dict (user_id, session_id, history, etc.).
            confidence_threshold: Minimum confidence to accept a routing decision.
        
        Returns:
            RoutingDecision with the selected agent(s) and metadata.
        """
        self._lazy_init()
        context = context or {}
        
        # Strategy 1: Heuristic (fast path)
        if self._heuristic is not None:
            try:
                result = self._heuristic.route(query)
                if isinstance(result, dict):
                    top_agent = result.get("agent", "general")
                    confidence = result.get("confidence", 0.0)
                    scores = result.get("scores", {})
                    is_hybrid = result.get("is_hybrid", False)
                    hybrid_agents = result.get("agents", [])
                    
                    if confidence >= confidence_threshold:
                        logger.info(
                            "AgentRouter: Heuristic routed to '%s' (%.2f confidence)",
                            top_agent, confidence,
                        )
                        return RoutingDecision(
                            agent=top_agent,
                            confidence=confidence,
                            strategy_used="heuristic",
                            scores=scores,
                            is_hybrid=is_hybrid,
                            hybrid_agents=hybrid_agents,
                        )
            except Exception as e:
                logger.warning("AgentRouter: Heuristic strategy failed: %s", e)
        
        # Strategy 2: Semantic filter
        if self._semantic is not None:
            try:
                result = self._semantic.classify(query)
                if isinstance(result, dict):
                    top_agent = result.get("agent", "general")
                    confidence = result.get("confidence", 0.0)
                    
                    if confidence >= confidence_threshold:
                        logger.info(
                            "AgentRouter: Semantic routed to '%s' (%.2f confidence)",
                            top_agent, confidence,
                        )
                        return RoutingDecision(
                            agent=top_agent,
                            confidence=confidence,
                            strategy_used="semantic",
                        )
            except Exception as e:
                logger.warning("AgentRouter: Semantic strategy failed: %s", e)
        
        # Strategy 3: LLM-based (slowest, most accurate fallback)
        if self._llm is not None:
            try:
                result = self._llm.classify(query)
                if isinstance(result, dict):
                    top_agent = result.get("agent", "general")
                    confidence = result.get("confidence", 0.0)
                    
                    logger.info(
                        "AgentRouter: LLM routed to '%s' (%.2f confidence)",
                        top_agent, confidence,
                    )
                    return RoutingDecision(
                        agent=top_agent,
                        confidence=confidence,
                        strategy_used="llm",
                    )
            except Exception as e:
                logger.warning("AgentRouter: LLM strategy failed: %s", e)
        
        # Fallback: general agent
        logger.info("AgentRouter: All strategies failed, falling back to 'general'")
        return RoutingDecision(
            agent="general",
            confidence=0.0,
            strategy_used="fallback",
        )


# Module-level singleton for convenience
_default_router: Optional[AgentRouter] = None


def get_router() -> AgentRouter:
    """Get the default AgentRouter singleton."""
    global _default_router
    if _default_router is None:
        _default_router = AgentRouter()
    return _default_router
