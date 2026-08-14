"""
AARKAAI – Hybrid Query Router

Central dispatcher that executes QueryPlans across multiple data sources
in parallel, collects results, and coordinates context fusion + AI reasoning.

Architecture:
    QueryPlan (from query_understanding)
         ↓
    HybridQueryRouter.execute()
         ↓
    ┌──────────┬──────────┬──────────┬──────────┐
    │ Market   │ News/Web │ MongoDB  │ RAG      │
    │ API      │ Search   │ Query    │ ChromaDB │
    └──────────┴──────────┴──────────┴──────────┘
         ↓
    ContextFusion.fuse()
         ↓
    AI Reasoning (7B / Gemini / 3B)
         ↓
    RouterResult
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from config import (
    HQR_ENABLE_PARALLEL,
    HQR_MAX_WORKERS,
)
from modules.query_understanding import DataSource, QueryPlan, SourceResult, SubQuery
from modules.context_fusion import ContextFusion, FusedContext

logger = logging.getLogger(__name__)


# ─── Circuit Breaker (reuses the pattern from pipeline.py) ───────────────────

class _CircuitBreaker:
    """Disables a data source after N consecutive failures."""

    def __init__(self, name: str, threshold: int = 3, cooldown: float = 300.0):
        self.name = name
        self.threshold = threshold
        self.cooldown = cooldown
        self._failures = 0
        self._last_failure = 0.0

    @property
    def is_open(self) -> bool:
        if self._failures < self.threshold:
            return False
        if time.time() - self._last_failure > self.cooldown:
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure = time.time()
        if self._failures >= self.threshold:
            logger.warning(
                "HQR circuit breaker OPEN for '%s' after %d failures (cooldown=%ds)",
                self.name, self._failures, int(self.cooldown),
            )


# ─── Router Result ───────────────────────────────────────────────────────────

@dataclass
class RouterResult:
    """Complete result from the hybrid query router."""
    final_answer: str
    fused_context: FusedContext
    source_results: list[SourceResult] = field(default_factory=list)
    plan: Optional[QueryPlan] = None
    total_time_ms: float = 0.0
    model_used: str = "aarkaa-7b"
    bypassed_llm: bool = False


# ─── Source Handler Registry ─────────────────────────────────────────────────

class _SourceHandlers:
    """
    Thin wrappers around existing AARKAAI modules.
    Each handler takes a SubQuery and returns a SourceResult.
    No business logic is duplicated — these simply call the existing modules.
    """

    @staticmethod
    def fetch_market_data(sq: SubQuery, user_id: str) -> SourceResult:
        """Fetch live market data via yfinance (modules.finance)."""
        start = time.perf_counter()
        try:
            from modules.finance import get_market_data, extract_tickers

            # Use the query text or explicit symbol from params
            query = sq.params.get("query", sq.query_text)
            symbol = sq.params.get("symbol", "")

            if symbol:
                from modules.finance import _fetch_ticker_data, format_finance_context
                data = {symbol: _fetch_ticker_data(symbol)}
                summary = format_finance_context(data)
            else:
                result = get_market_data(query)
                summary = result.get("summary", "")
                symbol = ", ".join(result.get("tickers", []))

            elapsed = (time.perf_counter() - start) * 1000
            if not summary or summary == "No data available.":
                return SourceResult(
                    source=DataSource.MARKET_API,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error="No market data found",
                )

            return SourceResult(
                source=DataSource.MARKET_API,
                data=summary,
                confidence=1.0,
                latency_ms=elapsed,
                metadata={"symbol": symbol},
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR market data fetch failed: %s", exc)
            return SourceResult(
                source=DataSource.MARKET_API,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )

    @staticmethod
    def fetch_news(sq: SubQuery, user_id: str) -> SourceResult:
        """Fetch current news via Google CSE / DuckDuckGo (modules.web_search)."""
        start = time.perf_counter()
        try:
            from modules.web_search import search_google_cse, search_ddg

            query = sq.params.get("query", sq.query_text)
            lang = sq.params.get("lang", "en")
            max_results = sq.params.get("max_results", 5)

            # Google CSE first, fallback to DuckDuckGo
            results = search_google_cse(query, max_results=max_results)
            if not results:
                results = search_ddg(query, max_results=max_results)

            if not results:
                elapsed = (time.perf_counter() - start) * 1000
                return SourceResult(
                    source=DataSource.NEWS_SEARCH,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error="No news results found",
                )

            # Format news results
            lines = []
            urls = []
            for i, r in enumerate(results, 1):
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                lines.append(f"{i}. \"{title}\" — {snippet}")
                if url:
                    urls.append(url)

            elapsed = (time.perf_counter() - start) * 1000
            return SourceResult(
                source=DataSource.NEWS_SEARCH,
                data="\n".join(lines),
                confidence=0.9,
                latency_ms=elapsed,
                metadata={"urls": urls, "count": len(results)},
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR news fetch failed: %s", exc)
            return SourceResult(
                source=DataSource.NEWS_SEARCH,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )

    @staticmethod
    def fetch_rag(sq: SubQuery, user_id: str) -> SourceResult:
        """Retrieve knowledge from ChromaDB vector store (modules.rag)."""
        start = time.perf_counter()
        try:
            from modules.rag import get_context

            query = sq.params.get("query", sq.query_text)
            top_k = sq.params.get("top_k", 3)
            domain = sq.params.get("domain", None)

            context = get_context(
                query,
                top_k=top_k,
                user_id=user_id,
                query_domain=domain,
            )

            elapsed = (time.perf_counter() - start) * 1000
            if not context:
                return SourceResult(
                    source=DataSource.RAG,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error="No RAG results found",
                )

            # Estimate entry count from separators
            entry_count = context.count("---") + 1

            return SourceResult(
                source=DataSource.RAG,
                data=context,
                confidence=0.85,
                latency_ms=elapsed,
                metadata={"count": entry_count},
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR RAG fetch failed: %s", exc)
            return SourceResult(
                source=DataSource.RAG,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )

    @staticmethod
    def fetch_web(sq: SubQuery, user_id: str) -> SourceResult:
        """Fetch general web results (modules.web_search)."""
        start = time.perf_counter()
        try:
            from modules.web_search import get_web_context

            query = sq.params.get("query", sq.query_text)
            lang = sq.params.get("lang", "en")

            context = get_web_context(query, lang=lang, filter_live=False)

            elapsed = (time.perf_counter() - start) * 1000
            if not context:
                return SourceResult(
                    source=DataSource.WEB_SEARCH,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error="No web results found",
                )

            return SourceResult(
                source=DataSource.WEB_SEARCH,
                data=context,
                confidence=0.7,
                latency_ms=elapsed,
                metadata={"count": context.count("\n\n") + 1},
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR web search failed: %s", exc)
            return SourceResult(
                source=DataSource.WEB_SEARCH,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )

    @staticmethod
    def fetch_mongodb(sq: SubQuery, user_id: str) -> SourceResult:
        """Fetch user-specific data from MongoDB (modules.mongo_repository)."""
        start = time.perf_counter()
        try:
            data_type = sq.params.get("data_type", "portfolio")
            result_text = ""
            metadata: dict[str, Any] = {"data_type": data_type}

            if data_type == "portfolio":
                from modules.mongo_repository import PortfolioRepo
                holdings = PortfolioRepo.get_holdings(user_id)
                if holdings:
                    lines = [f"• {h.get('symbol', 'N/A')}: {h.get('quantity', 0)} shares @ {h.get('avg_price', 'N/A')}" for h in holdings]
                    result_text = "\n".join(lines)
                    metadata["description"] = f"{len(holdings)} holdings"

            elif data_type == "watchlist":
                from modules.mongo_repository import WatchlistRepo
                items = WatchlistRepo.get_items(user_id)
                if items:
                    lines = [f"• {w.get('symbol', 'N/A')}" for w in items]
                    result_text = "\n".join(lines)
                    metadata["description"] = f"{len(items)} watchlist items"

            elif data_type == "history":
                from modules.mongo_repository import ConversationRepo
                history = ConversationRepo.get_history(user_id, limit=10)
                if history:
                    lines = [f"• Q: {h.get('query', '')[:80]}..." for h in history]
                    result_text = "\n".join(lines)
                    metadata["description"] = f"{len(history)} recent conversations"

            elif data_type == "alerts":
                from modules.mongo_repository import MarketAlertRepo
                alerts = MarketAlertRepo.get_active(user_id)
                if alerts:
                    lines = [f"• {a.get('symbol', 'N/A')}: {a.get('condition', 'N/A')} @ {a.get('target', 'N/A')}" for a in alerts]
                    result_text = "\n".join(lines)
                    metadata["description"] = f"{len(alerts)} active alerts"

            elapsed = (time.perf_counter() - start) * 1000
            if not result_text:
                return SourceResult(
                    source=DataSource.MONGODB,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error=f"No {data_type} data found for user",
                )

            return SourceResult(
                source=DataSource.MONGODB,
                data=result_text,
                confidence=1.0,
                latency_ms=elapsed,
                metadata=metadata,
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR MongoDB fetch failed: %s", exc)
            return SourceResult(
                source=DataSource.MONGODB,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )

    @staticmethod
    def execute_financial_tool(sq: SubQuery, user_id: str) -> SourceResult:
        """Execute financial tools via the existing tool registry."""
        start = time.perf_counter()
        try:
            from modules.tool_router import ToolRouterPipeline, ToolIntent

            pipeline = ToolRouterPipeline()

            tool_name = sq.params.get("tool_name", "")
            action = sq.params.get("action", "")
            tool_params = sq.params.get("tool_params", {})

            if not tool_name:
                # Let the heuristic router determine the tool
                intents = pipeline.route(sq.query_text)
                if not intents:
                    elapsed = (time.perf_counter() - start) * 1000
                    return SourceResult(
                        source=DataSource.FINANCIAL_TOOL,
                        data="",
                        confidence=0.0,
                        latency_ms=elapsed,
                        is_valid=False,
                        error="No financial tool matched",
                    )
            else:
                intents = [ToolIntent(
                    tool_name=tool_name,
                    action=action,
                    params=tool_params,
                    confidence=0.95,
                )]

            results = pipeline.execute_tools(intents)
            validated = pipeline.validate_results(results)

            valid_results = [r for r in validated if r.is_valid]
            if not valid_results:
                elapsed = (time.perf_counter() - start) * 1000
                error_msgs = [r.error for r in validated if not r.is_valid and r.error]
                return SourceResult(
                    source=DataSource.FINANCIAL_TOOL,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error="; ".join(error_msgs) or "All financial tools returned invalid results",
                )

            # Combine valid tool outputs
            combined = "\n\n".join(
                f"[{r.tool_name}/{r.action}]\n{r.data}"
                for r in valid_results
            )

            elapsed = (time.perf_counter() - start) * 1000
            return SourceResult(
                source=DataSource.FINANCIAL_TOOL,
                data=combined,
                confidence=0.95,
                latency_ms=elapsed,
                metadata={
                    "tool_name": ", ".join(r.tool_name for r in valid_results),
                    "actions": [r.action for r in valid_results],
                },
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR financial tool execution failed: %s", exc)
            return SourceResult(
                source=DataSource.FINANCIAL_TOOL,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )

    @staticmethod
    def execute_code(sq: SubQuery, user_id: str) -> SourceResult:
        """Execute Python code in sandbox (reuses pipeline._execute_python_code)."""
        start = time.perf_counter()
        try:
            from pipeline import _extract_python_code, _execute_python_code

            code = sq.params.get("code", "")
            if not code:
                code = _extract_python_code(sq.query_text)

            if not code:
                elapsed = (time.perf_counter() - start) * 1000
                return SourceResult(
                    source=DataSource.CODE_EXECUTION,
                    data="",
                    confidence=0.0,
                    latency_ms=elapsed,
                    is_valid=False,
                    error="No executable code found in query",
                )

            output = _execute_python_code(code)
            elapsed = (time.perf_counter() - start) * 1000

            return SourceResult(
                source=DataSource.CODE_EXECUTION,
                data=output,
                confidence=1.0,
                latency_ms=elapsed,
                metadata={"code_length": len(code)},
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("HQR code execution failed: %s", exc)
            return SourceResult(
                source=DataSource.CODE_EXECUTION,
                data="",
                confidence=0.0,
                latency_ms=elapsed,
                is_valid=False,
                error=str(exc),
            )


# ─── Hybrid Query Router ────────────────────────────────────────────────────

class HybridQueryRouter:
    """
    Central query router that:
    1. Accepts a QueryPlan from QueryUnderstanding
    2. Dispatches sub-queries to data sources in parallel via ThreadPoolExecutor
    3. Collects results, respecting per-source timeouts and circuit breakers
    4. Passes results to ContextFusion for intelligent merging
    5. Feeds fused context to the AI reasoning layer for final answer generation

    Thread Safety
    -------------
    All underlying modules (finance, rag, web_search, mongo_repository) are
    either stateless or use thread-safe clients (PyMongo connection pool,
    ChromaDB PersistentClient).  The ThreadPoolExecutor is bounded to
    HQR_MAX_WORKERS threads.
    """

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=HQR_MAX_WORKERS,
            thread_name_prefix="hqr",
        )
        self._fusion = ContextFusion()
        self._handlers = _SourceHandlers()

        # Per-source circuit breakers
        self._breakers: dict[DataSource, _CircuitBreaker] = {
            DataSource.MARKET_API: _CircuitBreaker("market_api", threshold=3, cooldown=120),
            DataSource.NEWS_SEARCH: _CircuitBreaker("news_search", threshold=3, cooldown=300),
            DataSource.WEB_SEARCH: _CircuitBreaker("web_search", threshold=3, cooldown=300),
            DataSource.RAG: _CircuitBreaker("rag", threshold=5, cooldown=60),
            DataSource.MONGODB: _CircuitBreaker("mongodb", threshold=3, cooldown=120),
            DataSource.FINANCIAL_TOOL: _CircuitBreaker("financial_tool", threshold=3, cooldown=120),
            DataSource.CODE_EXECUTION: _CircuitBreaker("code_execution", threshold=3, cooldown=60),
        }

    def _get_handler(self, source: DataSource) -> Optional[Callable[[SubQuery, str], SourceResult]]:
        """Resolve handler dynamically from self._handlers to support runtime monkeypatching."""
        handler_map = {
            DataSource.MARKET_API: self._handlers.fetch_market_data,
            DataSource.NEWS_SEARCH: self._handlers.fetch_news,
            DataSource.RAG: self._handlers.fetch_rag,
            DataSource.WEB_SEARCH: self._handlers.fetch_web,
            DataSource.MONGODB: self._handlers.fetch_mongodb,
            DataSource.FINANCIAL_TOOL: self._handlers.execute_financial_tool,
            DataSource.CODE_EXECUTION: self._handlers.execute_code,
        }
        return handler_map.get(source)

    def _execute_sub_query(
        self, sq: SubQuery, user_id: str
    ) -> SourceResult:
        """Execute a single sub-query with circuit breaker and timeout protection."""
        source = sq.source_type

        # Check circuit breaker
        breaker = self._breakers.get(source)
        if breaker and breaker.is_open:
            logger.info("HQR: skipping %s (circuit breaker open)", source.value)
            return SourceResult(
                source=source,
                data="",
                confidence=0.0,
                is_valid=False,
                error=f"Circuit breaker open for {source.value}",
            )

        # Find handler
        handler = self._get_handler(source)
        if handler is None:
            logger.warning("HQR: no handler for source %s, skipping", source.value)
            return SourceResult(
                source=source,
                data="",
                confidence=0.0,
                is_valid=False,
                error=f"No handler registered for {source.value}",
            )

        # Execute
        try:
            result = handler(sq, user_id)
            if breaker:
                if result.is_valid:
                    breaker.record_success()
                else:
                    breaker.record_failure()
            return result
        except Exception as exc:
            if breaker:
                breaker.record_failure()
            logger.error("HQR: handler %s raised exception: %s", source.value, exc)
            return SourceResult(
                source=source,
                data="",
                confidence=0.0,
                is_valid=False,
                error=str(exc),
            )

    def _execute_parallel(
        self, sub_queries: list[SubQuery], user_id: str
    ) -> list[SourceResult]:
        """Execute sub-queries in parallel using ThreadPoolExecutor."""
        results: list[SourceResult] = []

        # Group by priority to ensure required sources get submitted first
        sorted_sqs = sorted(sub_queries, key=lambda sq: sq.priority)

        future_to_sq: dict[Future, SubQuery] = {}
        for sq in sorted_sqs:
            future = self._executor.submit(self._execute_sub_query, sq, user_id)
            future_to_sq[future] = sq

        # Collect results with per-source timeouts
        max_timeout = max((sq.timeout for sq in sorted_sqs), default=10.0) + 2.0

        try:
            for future in as_completed(future_to_sq, timeout=max_timeout):
                sq = future_to_sq[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(
                        "HQR: %s completed in %.0fms (valid=%s)",
                        sq.source_type.value, result.latency_ms, result.is_valid,
                    )
                except Exception as exc:
                    logger.error("HQR: %s failed: %s", sq.source_type.value, exc)
                    results.append(SourceResult(
                        source=sq.source_type,
                        data="",
                        confidence=0.0,
                        is_valid=False,
                        error=str(exc),
                    ))
        except TimeoutError:
            logger.warning("HQR: Parallel execution deadline reached")
            completed_sources = {r.source for r in results}
            for sq in sorted_sqs:
                if sq.source_type not in completed_sources:
                    results.append(SourceResult(
                        source=sq.source_type,
                        data="",
                        confidence=0.0,
                        is_valid=False,
                        error=f"Timeout after {sq.timeout}s",
                    ))

        return results

    def _execute_sequential(
        self, sub_queries: list[SubQuery], user_id: str
    ) -> list[SourceResult]:
        """Execute sub-queries sequentially (fallback when parallel is disabled)."""
        results: list[SourceResult] = []
        for sq in sorted(sub_queries, key=lambda s: s.priority):
            result = self._execute_sub_query(sq, user_id)
            results.append(result)
            logger.info(
                "HQR: %s completed in %.0fms (valid=%s)",
                sq.source_type.value, result.latency_ms, result.is_valid,
            )
        return results

    def _generate_direct_answer(
        self, plan: QueryPlan, results: list[SourceResult]
    ) -> str:
        """
        Generate a direct answer from tool/data results without LLM synthesis.
        Used when bypass_llm is True (simple lookups like "SBI price").
        """
        valid_results = [r for r in results if r.is_valid and r.data]
        if not valid_results:
            return ""

        # For single market data results, return the data directly
        if len(valid_results) == 1 and valid_results[0].source == DataSource.MARKET_API:
            return valid_results[0].data

        # For single financial tool results, return formatted output
        if len(valid_results) == 1 and valid_results[0].source == DataSource.FINANCIAL_TOOL:
            return valid_results[0].data

        # For multiple results, simple concatenation
        parts = []
        for r in valid_results:
            parts.append(r.data)
        return "\n\n".join(parts)

    def _generate_llm_answer(
        self,
        query: str,
        fused: FusedContext,
        plan: QueryPlan,
        chat_history: list[dict] | None = None,
        user_facts: str = "",
        model_override: str | None = None,
    ) -> str:
        """Generate the final answer using the AI reasoning layer."""
        from modules import aarkaa_engine

        # Use the fused context (which already includes chat history and user facts)
        return aarkaa_engine.final_response(
            query,
            fused.context,
            intent=plan.intent,
            lang=plan.detected_language,
            mode="production",
            history=chat_history,
            user_facts=user_facts,
            force_general=(plan.complexity == "simple" and plan.domain not in ("finance", "technology")),
        )

    def execute(
        self,
        plan: QueryPlan,
        user_id: str = "default",
        session_id: str = "default",
        chat_history: list[dict] | None = None,
        user_facts: str = "",
        model_override: str | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> RouterResult:
        """
        Execute the full hybrid query pipeline.

        Parameters
        ----------
        plan : QueryPlan
            The decomposed query plan from QueryUnderstanding.
        user_id : str
            Authenticated user identifier.
        session_id : str
            Current session identifier.
        chat_history : list[dict] | None
            Recent conversation history for context.
        user_facts : str
            User profile facts from memory.
        model_override : str | None
            Force a specific model (gemini, claude, etc.).
        status_callback : Callable[[str], None] | None
            Optional callback for streaming status updates.
            Called with messages like "Fetching market data for SBI..."

        Returns
        -------
        RouterResult
            Complete result including final answer, fused context, and metadata.
        """
        pipeline_start = time.perf_counter()

        # ── 1. Filter sub-queries that have handlers ──────────────────────────
        executable_sqs = [
            sq for sq in plan.sub_queries
            if self._get_handler(sq.source_type) is not None
        ]

        if not executable_sqs:
            # No data sources needed — model-only response
            elapsed = (time.perf_counter() - pipeline_start) * 1000
            logger.info("HQR: no executable sub-queries, returning empty RouterResult")
            return RouterResult(
                final_answer="",
                fused_context=FusedContext(context="", sources_used=[], total_chars=0, source_count=0),
                plan=plan,
                total_time_ms=elapsed,
            )

        # ── 2. Emit status updates ───────────────────────────────────────────
        if status_callback:
            source_labels = {
                DataSource.MARKET_API: "market data",
                DataSource.NEWS_SEARCH: "news",
                DataSource.RAG: "knowledge base",
                DataSource.WEB_SEARCH: "web",
                DataSource.MONGODB: "user data",
                DataSource.FINANCIAL_TOOL: "financial analysis",
                DataSource.CODE_EXECUTION: "code execution",
            }
            sources_text = ", ".join(
                source_labels.get(sq.source_type, sq.source_type.value)
                for sq in executable_sqs
            )
            status_callback(f"Querying {sources_text}...")

        # ── 3. Execute sub-queries ───────────────────────────────────────────
        if HQR_ENABLE_PARALLEL and len(executable_sqs) > 1:
            source_results = self._execute_parallel(executable_sqs, user_id)
        else:
            source_results = self._execute_sequential(executable_sqs, user_id)

        # ── 4. Check if we got any valid results ─────────────────────────────
        valid_count = sum(1 for r in source_results if r.is_valid)
        total_latency = sum(r.latency_ms for r in source_results)

        logger.info(
            "HQR: %d/%d sources returned valid data in %.0fms total",
            valid_count, len(source_results), total_latency,
        )

        # If no valid results and plan requires synthesis, return empty
        # so the caller can fall back to the existing pipeline
        if valid_count == 0 and plan.requires_synthesis:
            elapsed = (time.perf_counter() - pipeline_start) * 1000
            return RouterResult(
                final_answer="",
                fused_context=FusedContext(context="", sources_used=[], total_chars=0, source_count=0),
                source_results=source_results,
                plan=plan,
                total_time_ms=elapsed,
            )

        # ── 5. Context fusion ────────────────────────────────────────────────
        if status_callback:
            status_callback("Synthesizing information...")

        fused = self._fusion.fuse(
            results=source_results,
            plan=plan,
            chat_history=chat_history,
            user_facts=user_facts,
        )

        # ── 6. Generate final answer ─────────────────────────────────────────
        if plan.bypass_llm and valid_count > 0:
            # Direct data return — no LLM synthesis needed
            final_answer = self._generate_direct_answer(plan, source_results)
            elapsed = (time.perf_counter() - pipeline_start) * 1000
            logger.info(
                "HQR: bypassed LLM, returning direct data (%.0fms)", elapsed,
            )
            return RouterResult(
                final_answer=final_answer,
                fused_context=fused,
                source_results=source_results,
                plan=plan,
                total_time_ms=elapsed,
                model_used="direct_data",
                bypassed_llm=True,
            )

        # Full LLM synthesis
        if status_callback:
            status_callback("Generating answer...")

        final_answer = self._generate_llm_answer(
            plan.original_query,
            fused,
            plan,
            chat_history=chat_history,
            user_facts=user_facts,
            model_override=model_override,
        )

        elapsed = (time.perf_counter() - pipeline_start) * 1000
        logger.info(
            "HQR: pipeline complete in %.0fms (%d sources, model=%s)",
            elapsed, fused.source_count, plan.model_target,
        )

        return RouterResult(
            final_answer=final_answer,
            fused_context=fused,
            source_results=source_results,
            plan=plan,
            total_time_ms=elapsed,
            model_used=model_override or plan.model_target,
        )


# ─── Module-level singleton ─────────────────────────────────────────────────

_router: Optional[HybridQueryRouter] = None


def get_router() -> HybridQueryRouter:
    """Get or create the singleton HybridQueryRouter instance."""
    global _router
    if _router is None:
        _router = HybridQueryRouter()
        logger.info("HybridQueryRouter initialised (workers=%d, parallel=%s)", HQR_MAX_WORKERS, HQR_ENABLE_PARALLEL)
    return _router


def execute_hybrid(
    plan: QueryPlan,
    user_id: str = "default",
    session_id: str = "default",
    chat_history: list[dict] | None = None,
    user_facts: str = "",
    model_override: str | None = None,
    status_callback: Callable[[str], None] | None = None,
) -> RouterResult:
    """Convenience function to execute a query plan through the hybrid router."""
    return get_router().execute(
        plan=plan,
        user_id=user_id,
        session_id=session_id,
        chat_history=chat_history,
        user_facts=user_facts,
        model_override=model_override,
        status_callback=status_callback,
    )
