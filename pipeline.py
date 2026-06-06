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
from modules.semantic_filter import _is_coding_syntax

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
    "stock", "company", "companies", "business", "market",
    "recommend", "trend", "latest", "current", "news", "price",
    "difference", "information",
    "ebitda", "fcf", "cash flow", "capex", "ebit", "revenue", "income", "earnings",
    "working capital", "depreciation", "amortization"
]

# Queries matching these keywords are self-contained — they NEVER need web search.
# System design, algorithms, CS theory, and problem-solving questions should go
# straight to the model without a web lookup that adds noise and latency.
_NO_WEB_SEARCH_KEYWORDS = [
    # System design / architecture
    "design a", "system design", "design system", "architecture", "schema",
    "database design", "api design", "microservice", "load balancer",
    "caching", "cache", "sharding", "replication", "consistency",
    "high availability", "fault tolerant", "scalab", "distributed",
    "message queue", "event driven", "pub sub", "rate limit",
    # Algorithms / CS problems
    "algorithm", "data structure", "time complexity", "space complexity",
    "big o", "big-o", "leetcode", "dynamic programming", "recursion",
    "binary search", "hash map", "linked list", "sorting", "graph",
    "log entries", "log entry", "ip address", "frequent", "top k",
    "heap", "min-heap", "max-heap", "priority queue", "partitioning",
    "count-min sketch", "mapreduce", "map reduce",
    # CS / math theory
    "billion", "million entries", "ram available", "memory constraint",
    "constraint", "how would you solve", "how to solve", "solve this",
    "prove", "proof", "theorem", "complexity",
]

_FACTUAL_PREFIXES = [
    "who is", "who are", "who was", "who were", "who's",
    "what is", "what are", "what's", "what is the current",
    "when is", "when did", "when will", "when's",
    "where is", "where are", "where's",
    "how many", "how much",
    "tell me about", "give me information on",
    "why ", "explain ", "how does ", "how do ", "how is ", "how can ",
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
        words = text.strip().split()
        if all(ord(c) < 128 for c in text):
            if len(words) < 4 or len(text) < 20:
                return "en"
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
        r"\bsheep\b.*\b(farmer|wolf|wolves|river|boat|count|puzzle|riddle)\b",
        r"\b(farmer|count|riddle|puzzle|logic)\b.*\bsheep\b",
        r"\btrain\b.*\bstation\b",
        r"\bif\b.*\bmore than\b.*\bhow\b",
        r"\bhow\s+old\s+is\b.*\b(brother|sister|father|mother|son|daughter|years|times|age)\b",
        r"\briddle\b",
        r"\bpuzzle\b",
        r"\blogic question\b",
        r"\bmath problem\b",
        r"\bcost(s)?\b.*\bmore than\b",
        r"\bolder\s+than\b.*\b(brother|sister|father|mother|son|daughter|years|times|age)\b",
        r"\bsister\b.*\bbrother\b",
        r"\bfarmer\b.*\b(sheep|cabbage|wolf|goat|river|boat|crossing|puzzle|riddle)\b",
        # Pill / doctor / interval puzzles
        r"\bdoctor\b.*\bpill",
        r"\bpill(s)?\b.*\bevery\b.*\bminute",
        r"\btake\b.*\bpill",
        # Lily pad / doubling puzzles
        r"\blily\s*pad",
        r"\bdouble(s)?\b.*\bevery\b",
        # Classic trick / brain teaser patterns
        r"\bhow\s+(long|many|much)\b.*\b(take|need|require)\b.*\b(minute|hour|day|second|pill|interval|fence|post|task|work|job|complete|finish)\b",
        r"\bfence\s*post",
        r"\btrick\s*question",
        r"\bbrain\s*teaser",
        r"\bif\b.*\bthen\b.*\bhow\b",
        # Clock angle puzzles
        r"\bclock\b.*\bangle\b",
        r"\bangle\b.*\bhand(s)?\b",
        # Race / positional / overtaking puzzles
        r"\bovertake\b",
        r"\brunner(s)?\b.*\brace\b",
        r"\bposition\b.*\brace\b",
        # Heads/Legs and Wheels/Vehicles puzzles
        r"\bheads?\b.*\blegs?\b",
        r"\blegs?\b.*\bheads?\b",
        r"\bwheels?\b.*\b(cars?|motorcycles?|bicycles?|vehicles?|tricycles?)\b",
        r"\b(cars?|motorcycles?|bicycles?|vehicles?|tricycles?)\b.*\bwheels?\b",
        # Percentage gain/loss return puzzles (Value Recovery)
        r"\b(falls?|decreases?|rises?|increases?)\b.*\bpercentage\s+gain\b",
        r"\b(falls?|decreases?|rises?|increases?)\b.*\bpercentage\s+loss\b",
        r"\bpercentage\s+gain\b.*\breturn\b.*\boriginal\b",
        r"\bpercentage\s+loss\b.*\breturn\b.*\boriginal\b",
        # Scale weighing puzzles (e.g. finding heavier/lighter outlier items)
        r"\b(weigh\w*|scale|balance)\b.*\b(heavier|lighter|outlier|ball|balls|coin|coins|marble|marbles|item|items|bar|bars)\b",
        r"\b(heavier|lighter|outlier|ball|balls|coin|coins|marble|marbles|item|items|bar|bars)\b.*\b(weigh\w*|scale|balance)\b",
    ]
    for pattern in patterns:
        if re.search(pattern, q, re.DOTALL):
            return True
    return False


def _is_trick_question(query: str) -> bool:
    """Detect common trick questions or riddles that should bypass web search."""
    q = query.lower()
    if "moses" in q and "ark" in q:
        return True
    if "heavier" in q and "feather" in q and ("gold" in q or "brick" in q or "lead" in q or "pound" in q):
        return True
    if "surgeon" in q and "father" in q and "son" in q:
        return True
    if "trick question" in q or "riddle" in q or "brain teaser" in q:
        return True
    return False


def _has_live_finance_intent(query: str, domain: str, intent: str) -> bool:
    """
    Determine if we should query the live yfinance engine.
    We avoid queries asking about general financial concepts, history,
    corporate info, or metrics (like revenue, employees, ceo, founded) 
    unless they explicitly ask for stock/price data.
    """
    q_low = query.lower()
    
    # Exclude keywords that indicate corporate/historical research rather than stock lookup
    exclude_keywords = [
        "revenue", "sales", "income", "employee", "employees", "founded", 
        "who is the ceo", "ceo of", "history of", "corporate office", 
        "address", "phone number", "subsidiaries", "products", "services"
    ]
    if any(kw in q_low for kw in exclude_keywords):
        return False

    # Exclude queries referencing specific years (e.g. "in 2040", "in 2010") to avoid live price mismatches
    if re.search(r"\b(18\d{2}|19\d{2}|20\d{2}|2100)\b", query):
        return False

    # Exclude temporal/forecast queries
    temporal_keywords = ["forecast", "projection", "prediction", "historical", "history", "past", "future"]
    if any(kw in q_low for kw in temporal_keywords):
        return False

    # Check for explicit ticker symbols ($AAPL, AAPL.NS)
    if re.search(r"\$[A-Za-z]{1,6}\b", query):
        return True
    if re.search(r"\b[A-Za-z]{2,20}\.NS\b", query):
        return True

    # Check for keywords related to stock prices/market
    stock_keywords = [
        "stock", "shares", "ticker", "price", "dividend", "market cap", 
        "pe ratio", "volume", "day high", "day low", "nse", "bse", "nasdaq", "nyse",
        "chart", "trade", "buy", "sell", "portfolio", "etf", "mutual fund"
    ]
    if any(kw in q_low for kw in stock_keywords):
        return True

    if domain == "finance" or intent.startswith("finance") or "btc" in q_low or "eth" in q_low or "crypto" in q_low:
        from modules.finance import _US_TICKERS, _INDIA_TICKERS, _INDEX_TICKERS, _CRYPTO_TICKERS, COMMODITY_TICKERS, FOREX_PAIRS, _TICKER_BLOCKLIST
        all_known = set()
        for mapping in [_US_TICKERS, _INDIA_TICKERS, _INDEX_TICKERS, _CRYPTO_TICKERS, COMMODITY_TICKERS, FOREX_PAIRS]:
            for k, v in mapping.items():
                if k.lower() not in _TICKER_BLOCKLIST:
                    all_known.add(k.lower())
                clean_v = v.split("-")[0].split(".")[0].replace("^", "").lower()
                if clean_v not in _TICKER_BLOCKLIST:
                    all_known.add(clean_v)
        words = re.findall(r"\b[a-zA-Z]{2,15}\b", q_low)
        if any(w in all_known for w in words):
            return True
        
        # If the query is very short (e.g. 1-2 words like "Apple stock" or just "Apple")
        # we can default to fetching the price
        word_count = len(q_low.split())
        if word_count <= 2:
            return True

    return False



def _extract_python_code(query: str) -> str:
    import re
    # 1. Look for markdown code blocks
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", query, re.DOTALL | re.IGNORECASE)
    if code_blocks:
        return code_blocks[0].strip()
    
    # 2. Otherwise, look for code-like lines
    lines = query.split("\n")
    code_lines = []
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        # Start code detection on typical python statements
        if (
            stripped.startswith("def ")
            or stripped.startswith("class ")
            or stripped.startswith("import ")
            or stripped.startswith("from ")
            or stripped.startswith("print(")
            or (stripped.startswith("x ") and "=" in stripped)
            or (stripped.startswith("y ") and "=" in stripped)
        ):
            in_code = True
        
        if in_code:
            # Skip instruction/intent phrasing inside the code block
            if any(p in stripped.lower() for p in ["what is the output", "output of", "explain"]):
                continue
            code_lines.append(line)
            
    if code_lines:
        return "\n".join(code_lines).strip()
        
    return ""


def _execute_python_code(code: str) -> str:
    import subprocess
    import sys
    import uuid
    from pathlib import Path
    from config import SAFE_WORK_DIR
    
    work_dir = SAFE_WORK_DIR
    work_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"temp_eval_{uuid.uuid4().hex}.py"
    temp_file = work_dir / filename
    try:
        temp_file.write_text(code, encoding="utf-8")
        
        cmd = [sys.executable, filename]
        
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5.0
        )
        
        output = ""
        if result.stdout:
            output += f"[stdout]\n{result.stdout}\n"
        if result.stderr:
            output += f"[stderr]\n{result.stderr}\n"
        if not output:
            output = "Code executed successfully with no output."
        return output.strip()
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 5.0 seconds."
    except Exception as exc:
        return f"Error executing code: {exc}"
    finally:
        try:
            if temp_file.exists():
                temp_file.unlink()
        except Exception:
            pass


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

    # Fallback to general query if classifier confidence is low
    if filter_confidence < 0.45:
        logger.info("Low filter confidence (%.3f < 0.45) — falling back to general query", filter_confidence)
        domain = "general"
        intent = "general_query"

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

    # RAG – check the knowledge base first (skip for simple greetings and reasoning puzzles)
    if not is_greeting and not is_reasoning and mode != "benchmark":
        try:
            rag_context = rag.get_context(query, user_id=user_id)
            if rag_context:
                context_parts.append(f"[Knowledge Base]\n{rag_context}")
                sources.append("rag")
        except Exception as exc:
            logger.error("RAG module error: %s", exc)

    # Domain-specific routing
    is_fin_intent = _has_live_finance_intent(query, domain, intent)
    fin_tickers = []
    if is_fin_intent and not is_reasoning and mode != "benchmark":
        fin_tickers = finance.extract_tickers(query)
    if fin_tickers and mode != "benchmark":
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

    # ── 4a. Code Output Sandbox ───────────────────────────────────────────
    # If this query is a coding query asking for the output of code, we run the code
    # directly in our python sandbox and inject the output to the prompt context.
    # This avoids initiating the slow ReAct agent loop for simple output/tracing queries.
    is_coding_output = False
    is_coding_query = (intent == "coding_help" or _is_coding_syntax(query))
    has_output_intent = any(p in query.lower() for p in ["output", "print", "run", "trace", "execute", "result"])
    if is_coding_query and has_output_intent:
        code_snippet = _extract_python_code(query)
        if code_snippet:
            sandbox_output = _execute_python_code(code_snippet)
            context_parts.append(
                f"[Code Execution Result]\n"
                f"We executed the user's code snippet inside a secure Python sandbox. Here is the actual execution output:\n"
                f"{sandbox_output}"
            )
            sources.append("code_execution")
            is_coding_output = True

    is_trick = _is_trick_question(query)
    agent_triggers = [
        "execute", "create a file", "modify file", "write to file", "bash",
        "test it", "test this", "test the code", "test them", "run the",
        "what is the output", "what's the output", "output of the code", "what does this print",
        "what will this print", "what is printed", "what does it print", "output of this",
        "trace this", "trace the code"
    ]
    needs_agent = (
        not is_coding_output
        and (
            any(w in query.lower() for w in agent_triggers)
            or bool(re.search(r"\brun\b", query.lower()))
            or (intent == "coding_help" and any(p in query.lower() for p in ["run", "execute", "trace", "test"]))
        )
    )

    # Queries that are self-contained (algorithms, system design, CS theory)
    # should NEVER trigger web search — the model knows the answer.
    is_no_web = any(kw in q_lower for kw in _NO_WEB_SEARCH_KEYWORDS)

    needs_web = (
        mode != "benchmark"
        and not is_trick
        and not is_no_web
        and not has_finance_context
        and not is_greeting
        and intent != "coding_help"
        and intent != "reasoning_puzzle"
        and (
            domain == "web_search"
            or intent in ("web_lookup", "news_search", "science_query")
            or any(kw in q_lower for kw in _NEWS_KEYWORDS)
            or any(kw in q_lower for kw in _FACTUAL_KEYWORDS)
            or is_factual
        )
    )

    if needs_web and not needs_agent:
        if not _web_breaker.is_open:
            try:
                web_ctx = web_search.get_web_context(query, lang=detected_lang, filter_live=(not is_fin_intent))
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
    chat_ctx = None
    try:
        chat_ctx = memory.get_chat_context(user_id, session_id, limit=2)
        if chat_ctx:
            last_user_msg = None
            for msg in reversed(chat_ctx):
                if msg["role"] == "user":
                    last_user_msg = msg["message"]
                    break
            if last_user_msg and last_user_msg.strip().lower() == query.strip().lower():
                logger.info("Detected retry of same query. Clearing history context to avoid truncation bias.")
                chat_ctx = None
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
        if chat_ctx:
            chat_lines = "\n".join(
                f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:1500]}"
                for m in chat_ctx
            )
            agent_ctx = f"[Recent Conversation]\n{chat_lines}"
        final_answer = coordinator.process_task(query, agent_ctx)
    elif fused_context or is_reasoning or chat_ctx:
        final_answer = aarkaa_engine.final_response(query, fused_context, intent=intent, lang=detected_lang, mode=mode, history=chat_ctx)
    else:
        # No external context and no history (e.g. initial greeting) – run model directly
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
    if not is_greeting and not is_reasoning and mode != "benchmark":
        try:
            rag_context = rag.get_context(query, user_id=user_id)
            if rag_context:
                context_parts.append(f"[Knowledge Base]\n{rag_context}")
                sources.append("rag")
        except Exception: pass

    # Domain-specific routing
    is_fin_intent = _has_live_finance_intent(query, domain, intent)
    fin_tickers = []
    if is_fin_intent and not is_reasoning and mode != "benchmark":
        fin_tickers = finance.extract_tickers(query)
    if fin_tickers and mode != "benchmark":
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

    # ── 4a. Code Output Sandbox ───────────────────────────────────────────
    # If this query is a coding query asking for the output of code, we run the code
    # directly in our python sandbox and inject the output to the prompt context.
    # This avoids initiating the slow ReAct agent loop for simple output/tracing queries.
    is_coding_output = False
    is_coding_query = (intent == "coding_help" or _is_coding_syntax(query))
    has_output_intent = any(p in query.lower() for p in ["output", "print", "run", "trace", "execute", "result"])
    if is_coding_query and has_output_intent:
        code_snippet = _extract_python_code(query)
        if code_snippet:
            sandbox_output = _execute_python_code(code_snippet)
            context_parts.append(
                f"[Code Execution Result]\n"
                f"We executed the user's code snippet inside a secure Python sandbox. Here is the actual execution output:\n"
                f"{sandbox_output}"
            )
            sources.append("code_execution")
            is_coding_output = True

    agent_triggers = [
        "execute", "create a file", "modify file", "write to file", "bash",
        "test it", "test this", "test the code", "test them", "run the",
        "what is the output", "what's the output", "output of the code", "what does this print",
        "what will this print", "what is printed", "what does it print", "output of this",
        "trace this", "trace the code"
    ]
    needs_agent = (
        not is_coding_output
        and (
            any(w in query.lower() for w in agent_triggers)
            or bool(re.search(r"\brun\b", query.lower()))
            or (intent == "coding_help" and any(p in query.lower() for p in ["run", "execute", "trace", "test"]))
        )
    )

    # Queries that are self-contained (algorithms, system design, CS theory)
    # should NEVER trigger web search — the model knows the answer.
    is_no_web = any(kw in q_lower for kw in _NO_WEB_SEARCH_KEYWORDS)

    needs_web = (
        mode != "benchmark"
        and not _is_trick_question(query)
        and not is_no_web
        and not has_finance_context
        and not is_greeting
        and intent != "coding_help"
        and intent != "reasoning_puzzle"
        and (
            domain == "web_search"
            or intent in ("web_lookup", "news_search", "science_query")
            or any(kw in q_lower for kw in _NEWS_KEYWORDS)
            or any(kw in q_lower for kw in _FACTUAL_KEYWORDS)
            or is_factual
        )
    )

    if needs_web and not needs_agent:
        if not _web_breaker.is_open:
            try:
                web_ctx = web_search.get_web_context(query, lang=detected_lang, filter_live=(not is_fin_intent))
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
    chat_ctx = None
    try:
        chat_ctx = memory.get_chat_context(user_id, session_id, limit=2)
        if chat_ctx:
            last_user_msg = None
            for msg in reversed(chat_ctx):
                if msg["role"] == "user":
                    last_user_msg = msg["message"]
                    break
            if last_user_msg and last_user_msg.strip().lower() == query.strip().lower():
                logger.info("Detected retry of same query. Clearing history context to avoid truncation bias.")
                chat_ctx = None
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

    if needs_agent:
        from modules import coordinator
        import asyncio
        agent_ctx = ""
        if chat_ctx:
            chat_lines = "\n".join(
                f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:1500]}"
                for m in chat_ctx
            )
            agent_ctx = f"[Recent Conversation]\n{chat_lines}"
        final_answer = coordinator.process_task(query, agent_ctx)
        chunk_size = 8
        for i in range(0, len(final_answer), chunk_size):
            token = final_answer[i:i+chunk_size]
            full_response += token
            yield {"type": "content", "token": token}
            await asyncio.sleep(0.01)
    else:
        # Stream the tokens
        for token in aarkaa_engine.stream_final_response(query, fused_context, intent=intent, lang=detected_lang, mode=mode, history=chat_ctx):
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
