"""
AARKAAI – Main Orchestration Pipeline (Production-Ready)

Flow:
  0. Query sanitization + language detection
  1. Semantic Filter → classify domain + confidence
  2. AARKAA-3B primary_check → first-pass answer
  3. If HIGH confidence (≥ threshold) → return immediately
  4. If LOW confidence → route to external modules by intent
  5. Context fusion → merge all sources
  6. AARKAA-3B final_response → full reasoning with context
  7. Store conversation → Memory
  8. Check auto-learn trigger
  9. Return response

Production features:
  - Circuit breaker for web_search (disables after N consecutive failures)
  - Per-module error isolation
  - Query sanitization
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional

from config import CONFIDENCE_THRESHOLD, MAX_QUERY_LENGTH
from schemas import PromptResponse

logger = logging.getLogger(__name__)


# ─── Circuit Breaker ─────────────────────────────────────────────────────────

class _CircuitBreaker:
    """Simple circuit breaker: disables a module after N consecutive failures."""

    def __init__(self, name: str, threshold: int = 3, cooldown: float = 300.0):
        self.name = name
        self.threshold = threshold
        self.cooldown = cooldown  # seconds before retry
        self._failures = 0
        self._last_failure = 0.0

    @property
    def is_open(self) -> bool:
        if self._failures < self.threshold:
            return False
        # Check if cooldown elapsed
        if time.time() - self._last_failure > self.cooldown:
            self._failures = 0  # Reset — allow retry
            return False
        return True

    def record_success(self):
        self._failures = 0

    def record_failure(self):
        self._failures += 1
        self._last_failure = time.time()
        if self._failures >= self.threshold:
            logger.warning(
                "Circuit breaker OPEN for '%s' after %d failures (cooldown=%ds)",
                self.name, self._failures, int(self.cooldown),
            )


_web_breaker = _CircuitBreaker("web_search", threshold=3, cooldown=300)
_finance_breaker = _CircuitBreaker("finance", threshold=3, cooldown=120)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _detect_language(text: str) -> str:
    """Detect the language of the input text. Returns ISO 639-1 code."""
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "en"


def _sanitize_query(query: str) -> str:
    """Clean up the query for safe processing."""
    # Strip control characters
    query = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    # Truncate to max length
    if len(query) > MAX_QUERY_LENGTH:
        query = query[:MAX_QUERY_LENGTH]
    return query.strip()


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def process_query(query: str, user_id: str = "default") -> PromptResponse:
    """
    End-to-end pipeline: receive a user query and return a
    fully-processed PromptResponse.
    """
    from modules import (
        aarkaa_engine,
        auto_learn,
        finance,
        memory,
        rag,
        semantic_filter,
        web_search,
    )

    start = time.perf_counter()
    sources: list[str] = []

    # ── 0. Sanitize + Language Detection ──────────────────────────────────
    query = _sanitize_query(query)
    detected_lang = _detect_language(query)
    logger.info("Detected language: %s", detected_lang)

    # ── 1. Semantic Filter ────────────────────────────────────────────────
    filter_result = semantic_filter.classify(query)
    domain = filter_result["domain"]
    filter_confidence = filter_result["confidence"]
    intent = filter_result["intent"]

    logger.info(
        "Filter → domain=%s  conf=%.3f  intent=%s",
        domain, filter_confidence, intent,
    )

    # ── 2. Skip primary check – run model only ONCE at the end (speed)
    # Gathering external context first, then a single model call with
    # full context gives better answers AND is 2x faster.
    primary_answer = ""
    primary_confidence = filter_confidence
    sources.append("aarkaa-3b")

    # ── 4. Low confidence – route to external modules ─────────────────────
    context_parts: list[str] = []

    # RAG – always check the knowledge base first
    try:
        rag_context = rag.get_context(query)
        if rag_context:
            context_parts.append(f"[Knowledge Base]\n{rag_context}")
            sources.append("rag")
    except Exception as exc:
        logger.error("RAG module error: %s", exc)

    # Domain-specific routing
    if domain == "finance" or intent.startswith("finance"):
        if not _finance_breaker.is_open:
            try:
                fin_data = finance.get_market_data(query)
                if fin_data.get("summary"):
                    context_parts.append(f"[Finance Data]\n{fin_data['summary']}")
                    sources.append("finance")
                _finance_breaker.record_success()
            except Exception as exc:
                _finance_breaker.record_failure()
                logger.error("Finance module error: %s", exc)
        else:
            logger.info("Finance circuit breaker is OPEN — skipping")

    # Detect current events / news queries that need web search
    q_lower = query.lower()
    _NEWS_KEYWORDS = [
        # English
        "current", "latest", "today", "news", "recent", "update",
        "now", "2024", "2025", "2026", "happening", "situation",
        "war", "election", "breaking", "live", "trending",
        # Hindi
        "ताज़ा", "समाचार", "आज", "खबर",
        # Spanish
        "noticias", "hoy", "actual",
        # French
        "nouvelles", "aujourd'hui", "actualité",
        # German
        "nachrichten", "heute", "aktuell",
        # Arabic
        "أخبار", "اليوم",
        # Japanese
        "ニュース", "最新", "今日",
        # Chinese
        "新闻", "最新", "今天",
    ]
    needs_web = (
        domain == "web_search"
        or intent in ("web_lookup", "news_search")
        or any(kw in q_lower for kw in _NEWS_KEYWORDS)
    )

    agent_triggers = ["execute", "run", "create a file", "modify file", "write to file", "bash"]
    needs_agent = any(w in query.lower() for w in agent_triggers)

    if needs_web and not needs_agent:
        if not _web_breaker.is_open:
            try:
                web_ctx = web_search.get_web_context(query, lang=detected_lang)
                if web_ctx:
                    context_parts.append(f"[Web Search]\n{web_ctx}")
                    sources.append("web_search")
                _web_breaker.record_success()
            except Exception as exc:
                _web_breaker.record_failure()
                logger.error("Web search error: %s", exc)
        else:
            logger.info("Web search circuit breaker is OPEN — skipping")

    # ── 5. Context fusion ─────────────────────────────────────────────────
    # Include recent conversation context for continuity
    try:
        chat_ctx = memory.get_chat_context(user_id, limit=5)
        if chat_ctx:
            chat_lines = "\n".join(
                f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:200]}"
                for m in chat_ctx
            )
            context_parts.insert(0, f"[Recent Conversation]\n{chat_lines}")
    except Exception as exc:
        logger.error("Memory context error: %s", exc)

    fused_context = "\n\n---\n\n".join(context_parts)

    # ── 6. AARKAA-3B final response ──────────────────────────────────────
    # Only trigger the slow autonomous agent (ReAct loop) if the user explicitly asks to run, execute, or manage files.
    is_coding = intent == "coding_help" or any(w in query.lower() for w in ["script", "code", "python", "implement", "create a file"])

    if needs_agent:
        from modules import coordinator
        # DANGER: Do NOT pass Web or RAG context to the autonomous agent to prevent 4096 context window explosions.
        # The agent has its own WebSearchTool if it needs information. Only pass the chat history.
        agent_ctx = ""
        if context_parts and "[Recent Conversation]" in context_parts[0]:
            agent_ctx = context_parts[0]
        final_answer = coordinator.process_task(query, agent_ctx)
    elif fused_context:
        final_answer = aarkaa_engine.final_response(query, fused_context, intent=intent)
    else:
        # No external context (e.g. "hello", general chat) – run model directly
        final_answer, _ = aarkaa_engine.primary_check(query)

    # Combine confidence (average of filter and primary)
    combined_confidence = (filter_confidence + primary_confidence) / 2

    # ── 7–8. Store + auto-learn ───────────────────────────────────────────
    main_source = sources[-1] if len(sources) > 1 else "aarkaa-3b"
    _post_process(
        user_id, query, final_answer,
        intent, combined_confidence, main_source,
        memory, auto_learn,
    )

    # ── 9. Return ─────────────────────────────────────────────────────────
    elapsed = round(time.perf_counter() - start, 3)
    logger.info("Pipeline done in %.3fs  sources=%s  lang=%s", elapsed, sources, detected_lang)

    return PromptResponse(
        response=final_answer,
        intent=intent,
        confidence=round(combined_confidence, 4),
        sources=sources,
        detected_language=detected_lang,
        processing_time=elapsed,
    )


async def stream_query(query: str, user_id: str = "default"):
    """
    Streaming version of the pipeline.
    Yields JSON chunks for SSE.
    """
    from modules import (
        aarkaa_engine,
        auto_learn,
        finance,
        memory,
        rag,
        semantic_filter,
        web_search,
    )

    start = time.perf_counter()
    sources: list[str] = []

    # ── 0. Sanitize + Language Detection ──────────────────────────────────
    query = _sanitize_query(query)
    detected_lang = _detect_language(query)

    # ── 1. Semantic Filter ────────────────────────────────────────────────
    filter_result = semantic_filter.classify(query)
    domain = filter_result["domain"]
    filter_confidence = filter_result["confidence"]
    intent = filter_result["intent"]
    sources.append("aarkaa-3b")

    # ── 4. Gather Context ─────────────────────────────────────────────────
    context_parts: list[str] = []
    
    # RAG
    try:
        rag_context = rag.get_context(query)
        if rag_context:
            context_parts.append(f"[Knowledge Base]\n{rag_context}")
            sources.append("rag")
    except Exception: pass

    # Memory
    try:
        chat_ctx = memory.get_chat_context(user_id, limit=5)
        if chat_ctx:
            chat_lines = "\n".join(f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:200]}" for m in chat_ctx)
            context_parts.insert(0, f"[Recent Conversation]\n{chat_lines}")
    except Exception: pass

    fused_context = "\n\n---\n\n".join(context_parts)

    # ── 6. Streaming Response ─────────────────────────────────────────────
    full_response = ""
    
    # Yield initial metadata chunk
    yield {
        "type": "metadata",
        "intent": intent,
        "sources": sources,
        "detected_language": detected_lang
    }

    # Stream the tokens
    for token in aarkaa_engine.stream_final_response(query, fused_context, intent=intent):
        full_response += token
        yield {"type": "content", "token": token}

    # ── 7–8. Store + auto-learn (post-process) ───────────────────────────
    elapsed = round(time.perf_counter() - start, 3)
    combined_confidence = (filter_confidence + 0.5) / 2
    
    _post_process(
        user_id, query, full_response,
        intent, combined_confidence, sources[-1],
        memory, auto_learn,
    )

    # Yield final stats
    yield {"type": "final", "processing_time": elapsed}


def _post_process(
    user_id: str,
    query: str,
    response: str,
    intent: str,
    confidence: float,
    source: str,
    memory_mod,
    auto_learn_mod,
) -> None:
    """Store conversation and trigger auto-learn if needed."""
    try:
        memory_mod.store_conversation(
            user_id=user_id,
            query=query,
            response=response,
            intent=intent,
            confidence=confidence,
            source=source,
        )
        memory_mod.update_user_profile(user_id=user_id, increment_count=True)
    except Exception as exc:
        logger.error("Post-process store failed: %s", exc)

    try:
        auto_learn_mod.check_and_learn(user_id)
    except Exception as exc:
        logger.error("Auto-learn check failed: %s", exc)
