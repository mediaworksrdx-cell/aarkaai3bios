"""
AARKAAI — Cognitive Orchestrator

Classifies query complexity and routes to the optimal subagent pipeline.
Simple queries bypass subagents entirely (zero overhead).
Complex queries are decomposed, processed by specialized agents, and
verified by the Critic before delivery.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from modules.subagents.base import CognitiveSubagent, SubagentResult

logger = logging.getLogger(__name__)

# ── Complexity Signals ────────────────────────────────────────────────────────

_COMPARISON_WORDS = {
    "compare", "versus", "vs", "vs.", "difference between",
    "better", "which is", "pros and cons", "similarities"
}
_ANALYSIS_WORDS = {
    "analyze", "analyse", "evaluate", "assess", "review",
    "deep dive", "breakdown", "in-depth", "comprehensive",
    "explain", "overvalued", "undervalued", "whether",
    "recommend", "should i", "worth buying", "outlook"
}
_MULTI_STEP_WORDS = {
    "and then", "after that", "step by step", "first",
    "also", "additionally", "furthermore", "moreover"
}
_COMPOUND_PATTERNS = [
    r"\b(compare|vs\.?|versus)\b.*\b(and|with|to)\b",
    r"\b(what|how|why|explain).*\b(and|also|plus)\b.*\b(what|how|why)\b",
    r"\d+\s*(stocks?|companies|tickers?|symbols?)",
]


class CognitiveOrchestrator:
    """Routes queries to optimal subagent pipelines based on complexity."""

    def __init__(self):
        self._logger = logging.getLogger(f"{__name__}.CognitiveOrchestrator")

    # ── Complexity Classification ─────────────────────────────────────────

    def classify_complexity(self, query: str, domain: str = "general",
                            intent: str = "general_query") -> str:
        """Classify query as 'simple', 'moderate', or 'complex'.

        Uses a weighted heuristic scoring system. No LLM call needed.

        Returns:
            One of: 'simple', 'moderate', 'complex'
        """
        q_lower = query.lower().strip()
        score = 0.0

        # 1. Length signal
        word_count = len(query.split())
        if word_count > 30:
            score += 2.0
        elif word_count > 15:
            score += 1.0

        # 2. Question complexity
        question_marks = query.count("?")
        if question_marks >= 2:
            score += 2.0
        elif question_marks == 1:
            score += 0.5

        # 3. Comparison queries
        if any(w in q_lower for w in _COMPARISON_WORDS):
            score += 2.5

        # 4. Analysis depth
        if any(w in q_lower for w in _ANALYSIS_WORDS):
            score += 2.0

        # 5. Multi-step indicators
        if any(w in q_lower for w in _MULTI_STEP_WORDS):
            score += 1.5

        # 6. Compound patterns (regex)
        for pattern in _COMPOUND_PATTERNS:
            if re.search(pattern, q_lower):
                score += 2.0
                break

        # 7. Multiple tickers/entities
        try:
            from modules.finance import extract_tickers
            tickers = extract_tickers(query)
            if len(tickers) >= 3:
                score += 3.0
            elif len(tickers) == 2:
                score += 1.5
        except Exception:
            pass

        # 8. Domain crossover — only for substantive queries (>8 words)
        #    to avoid false-positives on "What is TCS price?"
        if word_count > 8:
            domain_keywords = {
                "finance": ["stock", "market", "invest", "portfolio", "trading",
                            "pe ratio", "balance sheet", "fundamentals"],
                "code": ["code", "function", "script", "debug", "implement",
                         "algorithm", "api"],
                "research": ["explain in detail", "how does", "history of",
                             "deep dive", "comprehensive overview"],
            }
            domains_hit = sum(
                1 for kws in domain_keywords.values()
                if any(k in q_lower for k in kws)
            )
            if domains_hit >= 2:
                score += 2.0

        # 9. Intent boost
        if intent in ("comparison", "deep_analysis", "strategy"):
            score += 1.5

        # Classify
        if score >= 5.0:
            classification = "complex"
        elif score >= 2.0:
            classification = "moderate"
        else:
            classification = "simple"

        self._logger.info(
            "Complexity: %s (score=%.1f, words=%d, domain=%s)",
            classification, score, word_count, domain
        )
        return classification

    # ── Pipeline Selection ────────────────────────────────────────────────

    def select_pipeline(self, complexity: str, domain: str,
                        intent: str) -> List[str]:
        """Select which subagents to invoke and in what order.

        Args:
            complexity: 'simple', 'moderate', or 'complex'
            domain: Detected domain (finance, technology, general, etc.)
            intent: Detected intent (general_query, comparison, etc.)

        Returns:
            Ordered list of subagent names to invoke.
        """
        if complexity == "simple":
            return []  # Fast-path, no subagents needed

        if complexity == "moderate":
            if domain == "finance":
                return ["analyst", "writer"]
            elif domain == "technology":
                return ["coder", "writer"]
            else:
                return ["researcher", "writer"]

        # Complex
        pipeline = ["planner"]

        if domain == "finance":
            pipeline.append("analyst")
        elif domain == "technology":
            pipeline.extend(["researcher", "coder"])
        else:
            pipeline.append("researcher")

        pipeline.append("reasoner")
        pipeline.append("writer")
        pipeline.append("critic")

        return pipeline

    # ── Orchestration Engine ──────────────────────────────────────────────

    def orchestrate(self, query: str,
                    context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Execute the selected subagent pipeline.

        Args:
            query: The user's query.
            context: Dict with domain, intent, user_id, history, rag_context, etc.

        Returns:
            Final verified answer string, or None if orchestration should
            be skipped (simple queries).
        """
        ctx = context or {}
        domain = ctx.get("domain", "general")
        intent = ctx.get("intent", "general_query")

        # Step 1: Classify complexity
        complexity = self.classify_complexity(query, domain, intent)
        if complexity == "simple":
            return None  # Let existing fast-path handle it

        # Step 2: Select pipeline
        pipeline = self.select_pipeline(complexity, domain, intent)
        if not pipeline:
            return None

        self._logger.info(
            "Orchestrating %s pipeline: %s",
            complexity, " → ".join(pipeline)
        )

        # Step 3: Execute subagent pipeline
        start = time.perf_counter()
        accumulated_context = dict(ctx)
        accumulated_context["_tools_used"] = []
        accumulated_context["_metadata"] = {"complexity": complexity, "pipeline": pipeline}
        accumulated_results: List[SubagentResult] = []

        from modules.subagents import get_subagent

        for agent_name in pipeline:
            agent = get_subagent(agent_name)
            if not agent:
                self._logger.warning("Subagent '%s' not found, skipping", agent_name)
                continue

            # Inject prior results into context
            if accumulated_results:
                last = accumulated_results[-1]
                accumulated_context["prior_output"] = last.output
                accumulated_context["prior_agent"] = last.agent_name

                # For critic, pass the answer to verify
                if agent_name == "critic":
                    accumulated_context["answer_to_verify"] = last.output
                    # Collect all tool data for verification
                    tool_data_parts = []
                    for r in accumulated_results:
                        if r.tools_used:
                            tool_data_parts.append(
                                f"[{r.agent_name}] tools={r.tools_used}"
                            )
                    accumulated_context["tool_data"] = "\n".join(tool_data_parts)

                # For writer, pass raw content
                if agent_name == "writer":
                    accumulated_context["raw_content"] = last.output

            # Execute subagent
            result = agent.think(query, accumulated_context)
            accumulated_results.append(result)

            self._logger.info(
                "  %s completed in %.0fms (conf=%.2f, valid=%s)",
                agent_name, result.execution_time_ms,
                result.confidence, result.is_valid
            )

            # Track tools used across pipeline
            if result.tools_used:
                accumulated_context["_tools_used"].extend(result.tools_used)

            # If agent failed and it's critical, abort pipeline
            if not result.is_valid and agent_name in ("analyst", "researcher"):
                self._logger.warning(
                    "Critical agent %s failed, aborting pipeline", agent_name
                )
                return None

        total_ms = (time.perf_counter() - start) * 1000
        self._logger.info("Orchestration completed in %.0fms", total_ms)

        # Return the last valid result
        for result in reversed(accumulated_results):
            if result.is_valid and result.output:
                return result.output

        return None

    async def orchestrate_stream(self, query: str,
                                 context: Optional[Dict[str, Any]] = None):
        """Execute the subagent pipeline and yield SSE status and content chunks.

        Allows the web and app client to see the intermediate thought process
        (agent-by-agent progress) and stream the final answer.
        """
        import asyncio
        ctx = context or {}
        domain = ctx.get("domain", "general")
        intent = ctx.get("intent", "general_query")

        # Step 1: Classify complexity
        complexity = self.classify_complexity(query, domain, intent)
        if complexity == "simple":
            return

        # Step 2: Select pipeline
        pipeline = self.select_pipeline(complexity, domain, intent)
        if not pipeline:
            return

        self._logger.info(
            "Streaming Orchestrator %s pipeline: %s",
            complexity, " → ".join(pipeline)
        )

        # Yield initial metadata
        yield {
            "type": "metadata",
            "intent": intent,
            "sources": ["cognitive_orchestrator"],
            "detected_language": ctx.get("detected_language", "en")
        }

        # Step 3: Execute subagent pipeline yielding status
        accumulated_context = dict(ctx)
        accumulated_context["_tools_used"] = []
        accumulated_context["_metadata"] = {"complexity": complexity, "pipeline": pipeline}
        accumulated_results: List[SubagentResult] = []

        from modules.subagents import get_subagent

        # Mapping from subagent name to user-friendly status message
        status_messages = {
            "planner": "Decomposing query and planning subtasks...",
            "analyst": "Analyst Agent: Fetching and parsing market/financial data...",
            "researcher": "Researcher Agent: Searching knowledge base and web resources...",
            "reasoner": "Reasoner Agent: Conducting logical analysis and multi-step reasoning...",
            "writer": "Writer Agent: Structuring and formatting final response...",
            "critic": "Critic Agent: Verifying facts and validating accuracy...",
            "coder": "Coder Agent: Implementing and reviewing code solution...",
            "memory": "Memory Agent: Accessing context and prior conversation facts...",
        }

        for agent_name in pipeline:
            agent = get_subagent(agent_name)
            if not agent:
                continue

            # Yield status update to user
            status_msg = status_messages.get(agent_name, f"Executing {agent_name} agent...")
            yield {"type": "status", "status": status_msg}
            await asyncio.sleep(0.01)

            # Inject prior results into context
            if accumulated_results:
                last = accumulated_results[-1]
                accumulated_context["prior_output"] = last.output
                accumulated_context["prior_agent"] = last.agent_name

                if agent_name == "critic":
                    accumulated_context["answer_to_verify"] = last.output
                    tool_data_parts = []
                    for r in accumulated_results:
                        if r.tools_used:
                            tool_data_parts.append(
                                f"[{r.agent_name}] tools={r.tools_used}"
                            )
                    accumulated_context["tool_data"] = "\n".join(tool_data_parts)

                if agent_name == "writer":
                    accumulated_context["raw_content"] = last.output

            # Execute subagent blocking call (run in executor to keep async loop free if needed, or simple sync call)
            # Since local llama-cpp runs in background threads, simple sync invocation is fine.
            result = agent.think(query, accumulated_context)
            accumulated_results.append(result)

            if result.tools_used:
                accumulated_context["_tools_used"].extend(result.tools_used)

            # Abort on critical agent failures
            if not result.is_valid and agent_name in ("analyst", "researcher"):
                yield {"type": "status", "status": f"Critical error in {agent_name} agent. Aborting pipeline."}
                return

        # Find final answer
        final_answer = None
        for result in reversed(accumulated_results):
            if result.is_valid and result.output:
                final_answer = result.output
                break

        if not final_answer:
            yield {"type": "status", "status": "Failed to generate answer from subagent pipeline."}
            return

        # Update metadata sources
        ctx["final_answer"] = final_answer
        ctx["_tools_used"] = accumulated_context["_tools_used"]
        ctx["_metadata"] = accumulated_context["_metadata"]

        # Stream final response token-by-token (simulating Claude slow-and-steady style)
        yield {"type": "status", "status": "Streaming verified response..."}
        chunk_size = 8
        for i in range(0, len(final_answer), chunk_size):
            token = final_answer[i:i+chunk_size]
            yield {"type": "content", "token": token}
            await asyncio.sleep(0.005)



# ── Module-level singleton ────────────────────────────────────────────────────

_orchestrator: Optional[CognitiveOrchestrator] = None


def get_orchestrator() -> CognitiveOrchestrator:
    """Get or create the singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CognitiveOrchestrator()
    return _orchestrator
