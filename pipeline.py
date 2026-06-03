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

_NEWS_KEYWORDS = [
    "current", "latest", "today", "news", "recent", "update",
    "now", "2024", "2025", "2026", "happening", "situation",
    "war", "election", "breaking", "live", "trending",
    "ताज़ा", "समाचार", "आज", "खबर",
    "noticias", "hoy", "actual",
    "nouvelles", "aujourd'hui", "actualité",
    "nachrichten", "heute", "aktuell",
    "أخبار", "اليوم",
    "ニュース", "最新", "今日",
    "新闻", "最新", "今天",
]

_FACTUAL_KEYWORDS = [
    "stock", "company", "companies", "business", "market", "explain", "list", 
    "recommend", "analysis", "trend", "latest", "current", "news", "price", 
    "difference", "how does", "why did", "information", "detail"
]

_FACTUAL_PREFIXES = [
    "who is", "who are", "who was", "who were", "who's",
    "what is", "what are", "what's", "what is the current",
    "when is", "when did", "when will", "when's",
    "where is", "where are", "where's",
    "how many", "how much",
    "tell me about", "give me information on",
]

_STRATEGY_KEYWORDS = [
    "strategy", "option", "options", "call", "put", "spread",
    "iron condor", "straddle", "strangle", "covered call",
    "bull call", "bear put", "technical", "rsi", "macd",
    "ema", "bollinger", "signal", "setup", "trade setup",
    "lot size", "stop loss", "target", "risk reward",
    "technical analysis", "chart", "indicator",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

from modules.aarkaa_engine import _LANG_NAMES
_LANGUAGE_KEYWORDS = {name.lower(): code for code, name in _LANG_NAMES.items()}



def _detect_requested_language(query: str, current_detected: str) -> str:
    q_low = query.lower()
    trigger_words = ["speak in", "speak to me in", "answer in", "respond in", "write in", "reply in", "talk in", "in "]
    if any(w in q_low for w in trigger_words):
        for lang_keyword, lang_code in _LANGUAGE_KEYWORDS.items():
            if lang_keyword in q_low:
                return lang_code
    return current_detected


def _detect_language(text: str) -> str:
    """Detect the language of the input text. Returns ISO 639-1 code."""
    try:
        import langid
        lang, _ = langid.classify(text)
        return lang
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


_FINANCE_INTENT_KEYWORDS = [
    "stock", "shares", "ticker", "market", "earnings", "price", 
    "target price", "analyst", "nasdaq", "nyse", "nse", "bse", 
    "invest", "investment", "portfolio", "dividend", "etf", "mutual fund"
]

def _is_reasoning_query(query: str) -> bool:
    """Detect math, logic word problems, and puzzles."""
    q = query.lower()
    patterns = [
        # Bat and ball, farmer sheep, trains leaving station
        r"\bbat\b.*\bball\b",
        r"\bsheep\b",
        r"\btrain\b.*\bstation\b",
        r"\bif\b.*\bmore than\b",
        r"\bhow old is\b",
        r"\briddle\b",
        r"\bpuzzle\b",
        r"\blogic question\b",
        r"\bmath problem\b",
        r"\bcost(s)?\b.*\bmore than\b",
        r"\bolder than\b",
        r"\bsister\b.*\bbrother\b",
        r"\bfarmer\b",
        # Pill / doctor / interval puzzles
        r"\bdoctor\b.*\bpill",
        r"\bpill(s)?\b.*\bevery\b.*\bminute",
        r"\btake\b.*\bpill",
        # Lily pad / doubling puzzles
        r"\blily\s*pad",
        r"\bdouble(s)?\b.*\bevery\b",
        # Classic trick / brain teaser patterns
        r"\bhow\s+(long|many|much)\b.*\b(take|need|require)\b",
        r"\bfence\s*post",
        r"\btrick\s*question",
        r"\bbrain\s*teaser",
        r"\bif\b.*\bthen\b.*\bhow\b",
    ]
    for pattern in patterns:
        if re.search(pattern, q):
            return True
    return False

def _is_finance_intent(query: str, domain: str, intent: str) -> bool:
    """Determine if finance intent is active."""
    if domain == "finance" or intent.startswith("finance"):
        return True
    q = query.lower()
    return any(kw in q for kw in _FINANCE_INTENT_KEYWORDS)


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def process_query(query: str, user_id: str = "default", session_id: str = "default", mode: str = "production") -> PromptResponse:
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
    raw_detected = _detect_language(query)
    detected_lang = _detect_requested_language(query, raw_detected)
    logger.info("Detected language: %s (raw=%s)", detected_lang, raw_detected)

    # ── 1. Semantic Filter ────────────────────────────────────────────────
    clean_q = re.sub(r"[^\w\s]", "", query.lower()).strip()
    is_greeting = clean_q in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you", "who are you", "aarka", "aarkaai"]
    is_reasoning = _is_reasoning_query(query)
    
    if is_greeting:
        filter_result = {
            "domain": "general",
            "confidence": 1.0,
            "intent": "general_query",
            "scores": {"general": 1.0}
        }
    elif is_reasoning:
        filter_result = {
            "domain": "general",
            "confidence": 1.0,
            "intent": "reasoning_puzzle",
            "scores": {"general": 1.0}
        }
    else:
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

    # RAG – check the knowledge base first (skip for simple greetings)
    if not is_greeting and mode != "benchmark":
        try:
            rag_context = rag.get_context(query)
            if rag_context:
                context_parts.append(f"[Knowledge Base]\n{rag_context}")
                sources.append("rag")
        except Exception as exc:
            logger.error("RAG module error: %s", exc)

    # Domain-specific routing
    is_fin_intent = _is_finance_intent(query, domain, intent)
    fin_tickers = []
    if is_fin_intent and not is_reasoning and mode != "benchmark":
        fin_tickers = finance.extract_tickers(query)
    if (fin_tickers or domain == "finance" or intent.startswith("finance")) and mode != "benchmark":
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

    # Technical Analysis + Options Strategy (premium feature)
    q_lower = query.lower()
    is_strategy_query = any(kw in q_lower for kw in _STRATEGY_KEYWORDS)
    if is_strategy_query and fin_tickers:
        try:
            from modules import technical, options_strategy, subscription

            # Check freemium access
            access = subscription.check_access(user_id, feature="strategy")
            if access["allowed"]:
                # Run technical analysis on first detected ticker
                target_symbol = fin_tickers[0]
                indicators = technical.compute_indicators(target_symbol)
                if indicators:
                    signal = technical.get_signal(indicators)
                    tech_summary = technical.format_technical_summary(target_symbol, indicators, signal)
                    context_parts.append(f"[Technical Analysis]\n{tech_summary}")
                    sources.append("technical")

                    # Generate options strategy
                    strategy = options_strategy.generate_strategy(
                        symbol=target_symbol,
                        indicators=indicators,
                        signal=signal,
                        risk_reward=5.0,
                    )
                    if strategy:
                        strat_text = options_strategy.format_strategy_output(strategy)
                        context_parts.append(f"[Options Strategy]\n{strat_text}")
                        sources.append("strategy")

                    subscription.record_premium_usage(user_id)
            else:
                # Paywall message
                context_parts.append(f"[Subscription]\n{access['message']}")
        except Exception as exc:
            logger.error("Strategy module error: %s", exc)

    # Detect current events / news queries that need web search
    q_lower = query.lower()
    is_factual = any(q_lower.startswith(prefix) for prefix in _FACTUAL_PREFIXES)

    # Skip web search if live finance data was already fetched — web results
    # often contain stale prices that contradict the live Yahoo Finance feed
    # and confuse the model into outputting outdated values.
    has_finance_context = "finance" in sources

    needs_web = (
        mode != "benchmark"
        and not has_finance_context
        and not is_greeting
        and (
            domain == "web_search"
            or intent in ("web_lookup", "news_search", "general_query", "science_query")
            or any(kw in q_lower for kw in _NEWS_KEYWORDS)
            or any(kw in q_lower for kw in _FACTUAL_KEYWORDS)
            or is_factual
        )
    )

    agent_triggers = ["execute", "run", "create a file", "modify file", "write to file", "bash", "test it", "test this", "test the code", "test them"]
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
        chat_ctx = memory.get_chat_context(user_id, session_id, limit=5)
        if chat_ctx:
            chat_lines = "\n".join(
                f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:1500]}"
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
    elif fused_context or (is_reasoning and mode == "benchmark"):
        final_answer = aarkaa_engine.final_response(query, fused_context, intent=intent, lang=detected_lang, mode=mode)
    else:
        # No external context (e.g. "hello", general chat) – run model directly
        final_answer, _ = aarkaa_engine.primary_check(query, lang=detected_lang)

    # Combine confidence (average of filter and primary)
    combined_confidence = (filter_confidence + primary_confidence) / 2

    # ── 7–8. Store + auto-learn ───────────────────────────────────────────
    main_source = sources[-1] if len(sources) > 1 else "aarkaa-3b"
    _post_process(
        user_id, session_id, query, final_answer,
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


async def stream_query(query: str, user_id: str = "default", session_id: str = "default", mode: str = "production"):
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
    raw_detected = _detect_language(query)
    detected_lang = _detect_requested_language(query, raw_detected)

    # ── 1. Semantic Filter ────────────────────────────────────────────────
    clean_q = re.sub(r"[^\w\s]", "", query.lower()).strip()
    is_greeting = clean_q in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you", "who are you", "aarka", "aarkaai"]
    is_reasoning = _is_reasoning_query(query)
    
    if is_greeting:
        filter_result = {
            "domain": "general",
            "confidence": 1.0,
            "intent": "general_query",
            "scores": {"general": 1.0}
        }
    elif is_reasoning:
        filter_result = {
            "domain": "general",
            "confidence": 1.0,
            "intent": "reasoning_puzzle",
            "scores": {"general": 1.0}
        }
    else:
        filter_result = semantic_filter.classify(query)
        
    domain = filter_result["domain"]
    filter_confidence = filter_result["confidence"]
    intent = filter_result["intent"]
    sources.append("aarkaa-3b")

    # ── 4. Gather Context ─────────────────────────────────────────────────
    context_parts: list[str] = []
    
    # RAG
    if not is_greeting and mode != "benchmark":
        try:
            rag_context = rag.get_context(query)
            if rag_context:
                context_parts.append(f"[Knowledge Base]\n{rag_context}")
                sources.append("rag")
        except Exception: pass

    # Domain-specific routing
    is_fin_intent = _is_finance_intent(query, domain, intent)
    fin_tickers = []
    if is_fin_intent and not is_reasoning and mode != "benchmark":
        fin_tickers = finance.extract_tickers(query)
    if (fin_tickers or domain == "finance" or intent.startswith("finance")) and mode != "benchmark":
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

    # Technical Analysis + Options Strategy (premium feature)
    q_lower = query.lower()
    is_strategy_query = any(kw in q_lower for kw in _STRATEGY_KEYWORDS)
    if is_strategy_query and fin_tickers:
        try:
            from modules import technical, options_strategy, subscription

            # Check freemium access
            access = subscription.check_access(user_id, feature="strategy")
            if access["allowed"]:
                # Run technical analysis on first detected ticker
                target_symbol = fin_tickers[0]
                indicators = technical.compute_indicators(target_symbol)
                if indicators:
                    signal = technical.get_signal(indicators)
                    tech_summary = technical.format_technical_summary(target_symbol, indicators, signal)
                    context_parts.append(f"[Technical Analysis]\n{tech_summary}")
                    sources.append("technical")

                    # Generate options strategy
                    strategy = options_strategy.generate_strategy(
                        symbol=target_symbol,
                        indicators=indicators,
                        signal=signal,
                        risk_reward=5.0,
                    )
                    if strategy:
                        strat_text = options_strategy.format_strategy_output(strategy)
                        context_parts.append(f"[Options Strategy]\n{strat_text}")
                        sources.append("strategy")

                    subscription.record_premium_usage(user_id)
            else:
                # Paywall message
                context_parts.append(f"[Subscription]\n{access['message']}")
        except Exception as exc:
            logger.error("Strategy module error: %s", exc)

    # Detect current events / news queries that need web search
    is_factual = any(q_lower.startswith(prefix) for prefix in _FACTUAL_PREFIXES)

    # Skip web search if live finance data was already fetched — web results
    # often contain stale prices that contradict the live Yahoo Finance feed
    # and confuse the model into outputting outdated values.
    has_finance_context = "finance" in sources

    needs_web = (
        mode != "benchmark"
        and not has_finance_context
        and not is_greeting
        and (
            domain == "web_search"
            or intent in ("web_lookup", "news_search", "general_query", "science_query")
            or any(kw in q_lower for kw in _NEWS_KEYWORDS)
            or any(kw in q_lower for kw in _FACTUAL_KEYWORDS)
            or is_factual
        )
    )

    agent_triggers = ["execute", "run", "create a file", "modify file", "write to file", "bash", "test it", "test this", "test the code", "test them"]
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

    # Memory
    try:
        chat_ctx = memory.get_chat_context(user_id, session_id, limit=5)
        if chat_ctx:
            chat_lines = "\n".join(f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:1500]}" for m in chat_ctx)
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
    for token in aarkaa_engine.stream_final_response(query, fused_context, intent=intent, lang=detected_lang, mode=mode):
        full_response += token
        yield {"type": "content", "token": token}

    # ── 7–8. Store + auto-learn (post-process) ───────────────────────────
    elapsed = round(time.perf_counter() - start, 3)
    combined_confidence = (filter_confidence + 0.5) / 2
    
    _post_process(
        user_id, session_id, query, full_response,
        intent, combined_confidence, sources[-1],
        memory, auto_learn,
    )

    # Yield final stats
    yield {"type": "final", "processing_time": elapsed}


def _post_process(
    user_id: str,
    session_id: str,
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
            session_id=session_id,
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
