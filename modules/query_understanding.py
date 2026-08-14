from __future__ import annotations

import logging
import re
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any

# Import config values, with fallbacks in case config is not present during testing
try:
    from config import (
        HQR_MARKET_TIMEOUT,
        HQR_WEB_TIMEOUT,
        HQR_NEWS_TIMEOUT,
        HQR_DB_TIMEOUT,
        HQR_RAG_TIMEOUT,
        HQR_TOOL_TIMEOUT,
        HQR_BYPASS_LLM_THRESHOLD
    )
except ImportError:
    HQR_MARKET_TIMEOUT = 5.0
    HQR_WEB_TIMEOUT = 5.0
    HQR_NEWS_TIMEOUT = 5.0
    HQR_DB_TIMEOUT = 5.0
    HQR_RAG_TIMEOUT = 5.0
    HQR_TOOL_TIMEOUT = 5.0
    HQR_BYPASS_LLM_THRESHOLD = 0.9

logger = logging.getLogger(__name__)

class DataSource(Enum):
    MARKET_API = "market_api"         # Live price/OHLC/OI/IV via yfinance
    NEWS_SEARCH = "news_search"       # Google CSE / DuckDuckGo for current events  
    MONGODB = "mongodb"               # User data, conversation history, portfolio
    RAG = "rag"                       # ChromaDB vector knowledge base
    FINANCIAL_TOOL = "financial_tool" # Calculator, fundamentals, technical analysis
    WEB_SEARCH = "web_search"         # General web lookup
    CODE_EXECUTION = "code_execution" # Python sandbox
    VISION = "vision"                 # Image/chart analysis
    CODER = "coder"                   # Code generation service
    MODEL_ONLY = "model_only"         # Pure LLM reasoning, no retrieval needed

@dataclass
class SubQuery:
    query_text: str
    source_type: DataSource
    priority: int             # Lower = execute first
    params: dict = field(default_factory=dict)
    required: bool = True     # Is this sub-query mandatory?
    timeout: float = 5.0      # Per-source timeout in seconds

@dataclass
class SourceResult:
    source: DataSource
    data: str                 # The retrieved text/data
    confidence: float = 1.0
    latency_ms: float = 0.0
    error: str = ""
    is_valid: bool = True
    metadata: dict = field(default_factory=dict)

@dataclass 
class QueryPlan:
    original_query: str = ""
    detected_language: str = "en"
    domain: str = "general"
    intent: str = "general_query"
    sub_queries: list[SubQuery] = field(default_factory=list)
    requires_synthesis: bool = True    # Does the final answer need multi-source fusion?
    complexity: str = "simple"         # "simple" | "compound" | "complex"
    bypass_llm: bool = False           # Can return data directly without LLM synthesis?
    model_target: str = "general_3b"   # Which model to use: general_3b, coder, vision

    def to_dict(self) -> dict[str, Any]:
        """Convert QueryPlan to dictionary for serialization."""
        result = asdict(self)
        for sq in result.get("sub_queries", []):
            if isinstance(sq.get("source_type"), Enum):
                sq["source_type"] = sq["source_type"].value
        return result

# --- Constants for Keyword Matching ---
_MARKET_KEYWORDS = ["stock", "price", "shares", "market cap", "volume", "ohlc", "live", "nse", "bse", "nasdaq", "nyse", "crypto", "forex", "commodity"]
_MARKET_EXCLUDE_CORPORATE = ["revenue", "ceo", "founded", "employees", "history"]
_MARKET_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")

_NEWS_KEYWORDS = ["current", "latest", "today", "news", "recent", "update", "now", "2024", "2025", "2026", "happening", "trending", "breaking", "live", "war", "election", "ताज़ा", "समाचार", "आज", "खबर"]

_DB_KEYWORDS = ["my portfolio", "my holdings", "my watchlist", "my account", "my history", "my settings", "my alerts"]

_FINTOOL_CALC = ["cagr", "sip", "lumpsum", "dcf", "pe valuation", "margin", "position size", "emi", "compound interest"]
_FINTOOL_FUNDA = ["balance sheet", "income statement", "cash flow", "pe ratio", "eps", "earnings"]
_FINTOOL_TECH = ["rsi", "macd", "bollinger", "moving average", "technical analysis"]
_FINTOOL_FNO = ["greeks", "black scholes", "max pain", "implied volatility", "pcr"]
_FINTOOL_ALL = _FINTOOL_CALC + _FINTOOL_FUNDA + _FINTOOL_TECH + _FINTOOL_FNO

_WEB_FACTUAL = ["who is", "what is", "when did", "where is", "how many"]

_CODE_EXEC = ["output", "print", "run", "trace", "execute", "result"]
_CODER_KEYWORDS = ["def", "class", "import", "function", "code", "script", "implement", "debug", "refactor"]


def analyze(
    query: str,
    domain: str = "general",
    intent: str = "general_query",
    detected_language: str = "en",
    user_id: str = "default",
    chat_context: list[dict] | None = None,
) -> QueryPlan:
    """
    Decomposes user queries into typed sub-queries with data source requirements 
    for the AARKAAI hybrid query router.
    """
    plan = QueryPlan(
        original_query=query,
        detected_language=detected_language,
        domain=domain,
        intent=intent
    )

    if not query or not query.strip():
        plan.sub_queries.append(
            SubQuery(query_text=query, source_type=DataSource.MODEL_ONLY, priority=1)
        )
        plan.complexity = "simple"
        logger.info(f"QueryPlan: complexity={plan.complexity}, sources={['model_only']}, bypass_llm={plan.bypass_llm}")
        return plan

    query_lower = query.lower()
    
    tickers = []
    try:
        # Lazy import to avoid circular dependencies
        from modules.finance import extract_tickers
        tickers = extract_tickers(query)
    except ImportError:
        logger.debug("Could not import extract_tickers from modules.finance; proceeding without it.")

    sub_queries = []

    # Helper flags
    is_coding_help = (intent == "coding_help")
    is_greeting_or_id = intent in ("greeting", "identity", "chit_chat")
    is_reasoning_algo = intent in ("reasoning", "system_design", "algorithm", "puzzle")
    has_python_block = "```python" in query_lower
    
    # 1. Market API
    has_market_kw = any(kw in query_lower for kw in _MARKET_KEYWORDS)
    has_corp_kw = any(kw in query_lower for kw in _MARKET_EXCLUDE_CORPORATE)
    has_year = bool(_MARKET_YEAR_PATTERN.search(query_lower))
    
    if (tickers or has_market_kw) and not has_corp_kw and not has_year:
        params = {"symbols": tickers} if tickers else {}
        sub_queries.append(SubQuery(
            query_text=f"Market data lookup for: {query}",
            source_type=DataSource.MARKET_API,
            priority=1,
            params=params,
            required=True,
            timeout=HQR_MARKET_TIMEOUT
        ))

    # 2. News Search
    has_news_kw = any(kw in query_lower for kw in _NEWS_KEYWORDS)
    if has_news_kw or domain == "web_search" or intent in ("news_search", "web_lookup"):
        sub_queries.append(SubQuery(
            query_text=f"News search: {query}",
            source_type=DataSource.NEWS_SEARCH,
            priority=1,
            params={"query": query},
            required=True,
            timeout=HQR_NEWS_TIMEOUT
        ))

    # 3. MongoDB
    has_db_kw = any(kw in query_lower for kw in _DB_KEYWORDS)
    if has_db_kw:
        sub_queries.append(SubQuery(
            query_text="Fetch user data",
            source_type=DataSource.MONGODB,
            priority=1,
            params={"user_id": user_id},
            required=True,
            timeout=HQR_DB_TIMEOUT
        ))

    # 4. Financial Tool
    has_fintool_calc = any(kw in query_lower for kw in _FINTOOL_CALC)
    has_fintool_kw = any(kw in query_lower for kw in _FINTOOL_ALL)
    if has_fintool_kw:
        sub_queries.append(SubQuery(
            query_text="Financial calculation / data tools",
            source_type=DataSource.FINANCIAL_TOOL,
            priority=2,
            required=True,
            timeout=HQR_TOOL_TIMEOUT
        ))

    # 5. Code Execution
    has_code_exec = any(kw in query_lower for kw in _CODE_EXEC)
    if (is_coding_help and has_code_exec) or has_python_block:
        sub_queries.append(SubQuery(
            query_text="Execute Python code",
            source_type=DataSource.CODE_EXECUTION,
            priority=1,
            required=True,
            timeout=5.0
        ))

    # 6. Coder
    has_coder_kw = any(kw in query_lower for kw in _CODER_KEYWORDS)
    if is_coding_help and not has_code_exec and has_coder_kw:
        sub_queries.append(SubQuery(
            query_text="Generate / Analyze code",
            source_type=DataSource.CODER,
            priority=1,
            required=True,
            timeout=10.0
        ))

    # 7. Web Search
    has_web_factual = any(kw in query_lower for kw in _WEB_FACTUAL)
    if (has_web_factual or domain == "general") and not is_coding_help and not is_reasoning_algo and not is_greeting_or_id:
        if not any(sq.source_type == DataSource.NEWS_SEARCH for sq in sub_queries):
            sub_queries.append(SubQuery(
                query_text=f"Web search: {query}",
                source_type=DataSource.WEB_SEARCH,
                priority=2,
                required=False,
                timeout=HQR_WEB_TIMEOUT
            ))

    # 8. RAG
    is_pure_calc = has_fintool_calc and len(query_lower.split()) < 5
    is_code_output = has_code_exec and is_coding_help
    has_market = any(sq.source_type == DataSource.MARKET_API for sq in sub_queries)
    is_simple_price = has_market and (
        len(query.split()) <= 4
        or not any(w in query_lower for w in ["why", "explain", "what is", "how", "analyze", "analysis", "news", "today", "report", "difference", "compare"])
    )
    
    if not is_greeting_or_id and not is_pure_calc and not is_code_output and not is_reasoning_algo and not is_simple_price:
        if domain in ("finance", "technology", "science", "health", "history", "general"):
            sub_queries.append(SubQuery(
                query_text="Knowledge base search",
                source_type=DataSource.RAG,
                priority=3,
                required=False,
                timeout=HQR_RAG_TIMEOUT
            ))

    # 9. Vision
    has_image = False
    if chat_context:
        has_image = any(msg.get("has_image", False) for msg in chat_context)
    if has_image or intent == "vision":
        sub_queries.append(SubQuery(
            query_text="Analyze image",
            source_type=DataSource.VISION,
            priority=1,
            params={"has_image": True},
            required=True,
            timeout=10.0
        ))

    # 10. Model Only (Fallback)
    if not sub_queries or is_greeting_or_id or is_reasoning_algo:
        if not any(sq.source_type in (DataSource.VISION, DataSource.CODER, DataSource.CODE_EXECUTION) for sq in sub_queries):
            sub_queries.append(SubQuery(
                query_text="LLM reasoning",
                source_type=DataSource.MODEL_ONLY,
                priority=1,
                required=True,
                timeout=5.0
            ))

    plan.sub_queries = sub_queries

    # --- Complexity Classification ---
    num_sources = len(plan.sub_queries)
    if num_sources >= 4:
        plan.complexity = "complex"
    elif num_sources >= 2:
        plan.complexity = "compound"
    else:
        plan.complexity = "simple"

    plan.requires_synthesis = num_sources > 1

    # --- Determine bypass_llm ---
    plan.bypass_llm = False
    if num_sources == 1:
        sq = plan.sub_queries[0]
        if sq.source_type == DataSource.MARKET_API:
            plan.bypass_llm = True
            plan.requires_synthesis = False
        elif sq.source_type == DataSource.FINANCIAL_TOOL and has_fintool_calc:
            plan.bypass_llm = True
            plan.requires_synthesis = False

    # --- Determine model_target ---
    if any(sq.source_type == DataSource.VISION for sq in plan.sub_queries) or intent == "vision" or has_image:
        plan.model_target = "vision"
    elif any(sq.source_type == DataSource.CODER for sq in plan.sub_queries) or (is_coding_help and not has_code_exec):
        plan.model_target = "coder"
    else:
        plan.model_target = "general_3b"

    source_names = [sq.source_type.value for sq in plan.sub_queries]
    logger.info(f"QueryPlan: complexity={plan.complexity}, sources={source_names}, bypass_llm={plan.bypass_llm}")

    return plan
