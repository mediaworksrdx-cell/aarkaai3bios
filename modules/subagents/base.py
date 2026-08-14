"""
AARKAAI — Cognitive Subagent Framework: Base Classes

Provides the foundational abstractions for all cognitive subagents.
Each subagent wraps a specialized system prompt + optional tool access
to produce high-quality, verified outputs from the local 7B model.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SubagentResult:
    """Output container for a single subagent invocation."""
    agent_name: str
    output: str
    confidence: float = 0.0
    reasoning_trace: str = ""
    execution_time_ms: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return bool(self.output) and self.error is None


class CognitiveSubagent:
    """Base class for all cognitive subagents.

    Each subagent encapsulates:
    - A specialized system prompt that constrains the 7B model's behavior
    - An optional set of tools it can invoke via the ToolRouterPipeline
    - Temperature and token budget tuned for its cognitive task
    - A structured think() method that produces SubagentResult
    """

    name: str = "BaseSubagent"
    description: str = "Base cognitive subagent"
    system_prompt: str = "You are a helpful AI assistant."
    allowed_tools: List[str] = []
    max_tokens: int = 1024
    temperature: float = 0.3

    def think(self, query: str, context: Optional[Dict[str, Any]] = None) -> SubagentResult:
        """Execute this subagent's cognitive task.

        Args:
            query: The user query or subtask description.
            context: Dictionary containing prior subagent results,
                     tool data, conversation history, and other state.

        Returns:
            SubagentResult with the agent's output and metadata.
        """
        ctx = context or {}
        start = time.perf_counter()

        try:
            output = self._execute(query, ctx)
            elapsed = (time.perf_counter() - start) * 1000

            return SubagentResult(
                agent_name=self.name,
                output=output,
                confidence=self._estimate_confidence(output, ctx),
                reasoning_trace=ctx.get("_reasoning_trace", ""),
                execution_time_ms=elapsed,
                tools_used=ctx.get("_tools_used", []),
                metadata=ctx.get("_metadata", {})
            )
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("Subagent %s failed: %s", self.name, e)
            return SubagentResult(
                agent_name=self.name,
                output="",
                execution_time_ms=elapsed,
                error=str(e)
            )

    def _execute(self, query: str, context: Dict[str, Any]) -> str:
        """Core execution logic. Override in subclasses."""
        raise NotImplementedError(f"{self.name}._execute() not implemented")

    def _estimate_confidence(self, output: str, context: Dict[str, Any]) -> float:
        """Estimate confidence in the output. Override for custom logic."""
        if not output:
            return 0.0
        if len(output) < 20:
            return 0.3
        return 0.7

    def _invoke_model(self, system: str, user: str,
                      max_tokens: Optional[int] = None,
                      temperature: Optional[float] = None,
                      model_override: Optional[str] = None) -> str:
        """Invoke the LLM with a system+user prompt pair.

        Uses the local 7B model by default. Can route to external
        models (Gemini/Claude) via model_override.
        """
        from modules import aarkaa_engine

        tokens = max_tokens or self.max_tokens
        temp = temperature if temperature is not None else self.temperature

        if model_override == "gemini":
            from modules.external_agents import call_gemini_streaming
            chunks = list(call_gemini_streaming(f"{system}\n\n{user}"))
            return "".join(chunks)
        elif model_override == "claude":
            from modules.external_agents import call_claude
            return call_claude(f"{system}\n\n{user}")
        else:
            prompt = aarkaa_engine._build_chatml(system, user)
            return aarkaa_engine._generate(
                prompt, max_new_tokens=tokens,
                temperature=temp, force_general=True
            )

    def _invoke_tools(self, tool_intents: list) -> list:
        """Execute tools via the ToolRouterPipeline.

        Args:
            tool_intents: List of (tool_name, action, params) tuples.

        Returns:
            List of ToolResult objects.
        """
        from modules.tool_router import get_pipeline, ToolIntent

        pipeline = get_pipeline()
        intents = []
        for tool_name, action, params in tool_intents:
            if tool_name not in self.allowed_tools and "*" not in self.allowed_tools:
                logger.warning(
                    "%s: tool %s not in allowed_tools, skipping",
                    self.name, tool_name
                )
                continue
            intents.append(ToolIntent(
                tool_name=tool_name,
                action=action,
                params=params,
                confidence=0.98,
                reasoning=f"Invoked by {self.name}"
            ))

        if not intents:
            return []

        results = pipeline.execute_tools(intents)
        return pipeline.validate_results(results)

    def __repr__(self) -> str:
        return f"<{self.name} tools={self.allowed_tools} temp={self.temperature}>"
