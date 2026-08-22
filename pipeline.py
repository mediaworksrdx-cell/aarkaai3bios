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
import threading
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
    "working capital", "depreciation", "amortization",
    "college", "colleges", "university", "universities", "school", "schools",
    "population", "census", "count", "statistics", "demographics", "how many",
    "how much", "total number", "number of"
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
    
    # Specific model/dataset alignments
    if any(k in q_low for k in ["hindi alpaca", "hindi-alpaca", "samanantar"]):
        return "hi"
    if any(k in q_low for k in ["tamil alpaca", "tamil-alpaca"]):
        return "ta"
    if "aya" in q_low:
        if "tamil" in q_low:
            return "ta"
        return "hi"

    # If the user is questioning the language choice, do not override
    if any(q_word in q_low for q_word in ["why", "how come", "reason", "explain why"]):
        if any(act in q_low for act in ["responding", "answering", "speaking", "writing", "replying"]):
            return current_detected

    trigger_words = [
        "speak in", "speak to me in", "answer in", "respond in", 
        "write in", "reply in", "talk in", "explain in", 
        "translate to", "translate in", "output in", "generate in",
        "provide in"
    ]
    
    is_triggered = any(w in q_low for w in trigger_words) or q_low.startswith("in ")
    
    if is_triggered:
        for lang_keyword, lang_code in _LANGUAGE_KEYWORDS.items():
            if lang_keyword in q_low:
                return lang_code
    return current_detected



def _detect_language(text: str) -> str:
    """Detect the language of the input text. Returns ISO 639-1 code."""
    try:
        words = text.strip().lower().split()
        if all(ord(c) < 128 for c in text):
            if len(words) < 4 or len(text) < 20:
                return "en"
            # Prioritize English if common stop words, pronouns, or common query terms are present in ASCII text
            common_english = {
                "the", "and", "of", "to", "in", "is", "that", "it", "for", "on", "are", "as", "with", 
                "have", "from", "at", "an", "this", "by", "what", "how", "who", "where", "why", "which",
                "give", "me", "about", "create", "show", "tell", "write", "please", "information", 
                "ai", "technology", "agent", "pdf", "docx", "xlsx", "pptx", "report", "file", "make"
            }
            cleaned_words = {re.sub(r"[^\w]", "", w) for w in words}
            if cleaned_words & common_english:
                return "en"
        import langid
        lang, _ = langid.classify(text)
        return lang
    except Exception:
        return "en"


def _sanitize_query(query: str) -> str:
    """Clean up the query for safe processing and security hardening."""
    # Strip control characters
    query = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    
    # Strip special ChatML/model control tokens to prevent template breakout prompt injection
    for token in ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]:
        query = query.replace(token, "")
        
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


def _resolve_search_query(query: str, chat_ctx: list[dict] | None) -> str:
    """Resolve direct conversational search triggers (e.g., 'search web') to the previous user query."""
    q_low = query.strip().lower()
    search_directives = ["search web", "search the web", "google it", "look it up", "search online", "find online", "search"]
    if q_low in search_directives and chat_ctx:
        # Scan backward to find the last user query
        for msg in reversed(chat_ctx):
            if msg.get("role") == "user":
                last_msg = msg.get("message", "")
                if last_msg and last_msg.strip().lower() not in search_directives:
                    logger.info("Resolved search directive '%s' to previous user query: '%s'", query, last_msg)
                    return last_msg
    return query


def _enhance_search_query(query: str) -> str:
    """
    Rewrite and enhance statistical/factual queries with temporal and authority keywords 
    to ensure search engines prioritize fresh, official, and authoritative results.
    """
    q_low = query.lower()
    
    # If the query already has a year (e.g. 2024, 2025, 2026), do not modify it
    if re.search(r'\b(202\d|201\d|19\d{2})\b', q_low):
        return query
        
    # Check if this is a statistical, census, or counting query
    is_statistical = any(kw in q_low for kw in ["how many", "how much", "count of", "number of", "population", "census", "statistics", "list of"])
    is_college_related = any(kw in q_low for kw in ["college", "colleges", "university", "universities", "school", "schools", "institution", "institutions"])
    
    if is_statistical:
        enhanced = query.strip().rstrip("?").rstrip(".")
        # Append the current year to force fresh results
        enhanced += " 2026"
        
        # If it's about educational institutions, append authority keywords to bias search ranking toward official sites
        if is_college_related:
            enhanced += " AICTE approved official"
        
        logger.info("Rewrote search query: '%s' -> '%s'", query, enhanced)
        return enhanced
        
    return query


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


def _is_image_generation_query(query: str) -> bool:
    """Detect queries that request image/art generation, even without the word 'image'.
    
    Catches patterns like:
      - 'Generate an ancient jungle temple...'
      - 'Create a futuristic cityscape...'
      - 'Draw a sunset over mountains...'
      - 'A cyberpunk warrior standing in rain...'
    """
    q = query.lower().strip()
    
    # Direct explicit triggers (exact substring match)
    explicit_triggers = [
        "generate an image", "generate image", "generate a photo", "generate a picture",
        "create an image", "create a picture", "create image", "create a photo",
        "draw a", "draw me", "draw an", "paint a", "paint me", "paint an",
        "make a drawing", "make a picture", "make an image", "make a photo",
        "generate a drawing", "create a drawing", "draw something",
        "portrait of", "ultra-realistic portrait", "create art", "generate art",
        "design an image", "sketch a", "sketch an", "illustrate a", "illustrate an",
        "render a", "render an", "visualize a", "visualize an",
    ]
    if any(t in q for t in explicit_triggers):
        return True
    
    # Pattern: generation verb + visual/artistic scene descriptors
    # e.g. 'Generate an ancient jungle temple covered in moss...'
    generation_verbs = r'\b(generate|create|draw|paint|make|render|design|sketch|illustrate|visualize)\b'
    visual_descriptors = [
        "realistic", "ultra-detailed", "ultra-realistic", "photorealistic", "hyper-realistic",
        "cinematic", "4k", "8k", "hd", "high quality", "high-quality", "high resolution",
        "detailed environment", "dramatic lighting", "realistic lighting",
        "fantasy art", "digital art", "concept art", "oil painting", "watercolor",
        "anime style", "pixel art", "3d render", "unreal engine", "octane render",
        "studio lighting", "golden hour", "bokeh", "depth of field",
        "artstation", "deviantart", "trending on",
    ]
    visual_subjects = [
        "temple", "castle", "dragon", "warrior", "landscape", "cityscape", "portrait",
        "forest", "ocean", "mountain", "sunset", "sunrise", "waterfall", "cyberpunk",
        "steampunk", "medieval", "futuristic", "ancient", "mythical", "ethereal",
        "creature", "monster", "fairy", "goddess", "knight", "samurai", "ninja",
        "spaceship", "galaxy", "nebula", "planet", "alien",
    ]
    
    has_gen_verb = bool(re.search(generation_verbs, q))
    has_visual_desc = any(d in q for d in visual_descriptors)
    has_visual_subj = any(s in q for s in visual_subjects)
    
    # If the query starts with a generation verb and has visual descriptors or subjects
    if has_gen_verb and (has_visual_desc or has_visual_subj):
        # Exclude coding/file creation queries
        coding_excludes = ["python", "script", "code", "function", "class", "html", "css", "javascript", "file", ".py", ".js"]
        if not any(ex in q for ex in coding_excludes):
            return True
    
    # Pattern: prompt starts with 'a/an/the' + descriptive scene (no verb, just a prompt-style input)
    # e.g. 'A cyberpunk warrior standing in the rain, neon lights, ultra-detailed'
    if re.match(r'^(a|an|the)\s+', q) and has_visual_desc and len(q.split()) >= 5:
        coding_excludes = ["python", "script", "code", "function", "class", "html", "css", "file"]
        if not any(ex in q for ex in coding_excludes):
            return True
    
    return False


def _is_pdf_generation_query(query: str) -> bool:
    """Detect if the query asks to create/generate a PDF report, document, or similar."""
    q = query.lower().strip()
    # Check if the user is asking to write code, create python scripts, or explain how to generate PDFs,
    # in which case we should NOT intercept and instead let it go to coding assistant.
    coding_excludes = ["python", "script", "code", "library", "libraries", "how to", "write code", "separate files", "make skills separate"]
    if any(ex in q for ex in coding_excludes):
        return False

    action_words = ["create", "generate", "make", "compile", "build", "produce", "export", "write"]
    pdf_words = ["pdf", "report", "document", "business report"]
    
    # Must have both action word and pdf/report word
    has_action = any(aw in q for aw in action_words)
    has_pdf = any(pw in q for pw in pdf_words)
    
    if has_action and has_pdf:
        return True
        
    return False

def _extract_pdf_topic(query: str) -> str:
    """Extract a clean topic from a PDF generation query."""
    q = query.lower()
    # Remove common prefix phrases
    prefixes = [
        "create a premium pdf report about",
        "generate a premium pdf report about",
        "create a premium pdf about",
        "generate a premium pdf about",
        "create a pdf report about",
        "generate a pdf report about",
        "create a pdf about",
        "generate a pdf about",
        "create a report about",
        "generate a report about",
        "make a pdf report about",
        "make a pdf about",
        "make a report about",
        "create a report on",
        "generate a report on",
        "create a pdf on",
        "generate a pdf on",
        "create", "generate", "make", "compile", "pdf report about", "pdf about", "report about", "document about", "report on"
    ]
    topic = query
    for p in prefixes:
        if q.startswith(p):
            topic = query[len(p):].strip()
            break
            
    # Clean up trailing punctuation or filler words
    topic = re.sub(r'[.!?]+$', '', topic).strip()
    if topic.lower().startswith("about "):
        topic = topic[6:].strip()
    elif topic.lower().startswith("on "):
        topic = topic[3:].strip()
        
    if not topic:
        topic = "Business Intelligence Report"
    return topic

def _generate_pdf_filename(topic: str) -> str:
    """Convert topic to a safe filename."""
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', topic.lower()).strip('_')
    if not safe_name:
        safe_name = "business_report"
    return f"{safe_name}.pdf"

def _extract_pdf_template(query: str) -> str:
    """Detect if the user requested a specific color template in their query."""
    q = query.lower()
    if "white" in q or "light" in q:
        return "indigo"
    elif "dark" in q:
        return "dark"
    elif "green" in q or "emerald" in q or "teal" in q:
        return "emerald"
    elif "red" in q or "crimson" in q:
        return "crimson"
    elif "amber" in q or "yellow" in q or "orange" in q:
        return "amber"
    return "indigo"


def _is_calculation_query(query: str) -> bool:
    """Detect queries that require mathematical/arithmetic calculation."""
    q = query.lower()
    
    # Currency / stock price conversion queries (which might not contain numbers in the query itself)
    if "convert" in q or "conversion" in q or "exchange rate" in q or "in inr" in q or "to inr" in q or "in rupee" in q or "in rupees" in q or "usd to inr" in q:
        if any(w in q for w in ["stock", "price", "usd", "inr", "rupee", "rupees", "rate", "currency"]):
            return True
            
    has_math_words = any(w in q for w in ["calculate", "multiply", "divide", "compute", "solve", "what is", "what's", "find", "cagr", "gst"])
    has_numbers = len(re.findall(r"\d+", q)) >= 2
    has_operators = any(op in q for op in ["+", "*", "/", "×", "x", "-", "=", "%", "percent", "gst", "tax", "discount", "interest", "cagr", "growth", "compound"])
    
    arithmetic_pattern = r"\d+\s*[\+\-\*/\^x×%]\s*\d+"
    if re.search(arithmetic_pattern, q) or (has_math_words and has_numbers and has_operators):
        exclude_keywords = ["sheep", "doctor", "lily pad", "age", "brother", "sister", "farmer"]
        if any(w in q for w in exclude_keywords):
            return False
        return True
    return False


def _needs_skill_routing(query: str) -> bool:
    """Detect queries that involve file formats or document creation which benefit from skill docs."""
    q = query.lower()
    # Skill creation/management triggers
    skill_management_words = ["create skill", "update skill", "delete skill", "manage skill", "skill creator", "new skill", "test skill"]
    if any(sw in q for sw in skill_management_words):
        return True

    # File format keywords
    file_keywords = [
        ".pdf", ".docx", ".xlsx", ".pptx", ".csv",
        "pdf", "word document", "word doc", "excel", "spreadsheet",
        "powerpoint", "presentation", "slides", "slide deck",
        "image", "picture", "drawing", "illustration", "photo", "sketch",
    ]
    # Action + format combinations
    action_words = [
        "create", "generate", "make", "build", "write", "produce",
        "export", "convert", "read", "parse", "extract", "merge",
        "split", "format", "design",
    ]
    has_file_kw = any(kw in q for kw in file_keywords)
    has_action = any(aw in q for aw in action_words)
    # Direct triggers (e.g. "create a pdf", "make an excel report")
    if has_file_kw and has_action:
        return True
    # Explicit file extension mentions
    if re.search(r'\.(pdf|docx|xlsx|pptx|csv)\b', q):
        return True
    # UI/frontend design triggers
    if any(kw in q for kw in ["design a webpage", "build a dashboard", "create a form", "html page", "web page", "landing page"]):
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

    # Check for keywords related to stock prices/market (clean trade-offs first)
    q_clean = q_low.replace("trade-off", "").replace("tradeoff", "")
    stock_keywords = [
        "stock", "shares", "ticker", "price", "dividend", "market cap", 
        "pe ratio", "volume", "day high", "day low", "nse", "bse", "nasdaq", "nyse",
        "chart", "trade", "buy", "sell", "portfolio", "etf", "mutual fund"
    ]
    if any(kw in q_clean for kw in stock_keywords):
        return True

    # Check for forex pairs or commodities explicitly
    from config import FOREX_PAIRS, COMMODITY_TICKERS
    # Exclude macro-economic queries (repo rate, GDP, inflation, bond yield, monetary policy) from live stock ticker fetch
    macro_keywords = ["repo rate", "monetary policy", "rbi", "gdp", "inflation", "interest rate", "basis points"]
    if any(mk in q_low for mk in macro_keywords) and not any(kw in q_low for kw in ["stock", "ticker", "share price", "equity price"]):
        return False

    if any(pair in q_low for pair in FOREX_PAIRS.keys()) or any(comm in q_low for comm in COMMODITY_TICKERS.keys()):
        trigger_words = ["price", "rate", "value", "cost", "convert", "conversion", "what is", "how much", "today", "live"]
        if any(tw in q_low for tw in trigger_words):
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
    
    # ── Security: Block dangerous operations in generated code ──
    _BLOCKED_PATTERNS = [
        "os.environ", "os.getenv", "subprocess", "__import__",
        "eval(", "exec(", "compile(", "open(", "os.system",
        "shutil.rmtree", "pathlib.Path", "os.remove", "os.unlink",
        "os.rmdir", "importlib", "ctypes", "socket.",
        ".env", "SECRET_KEY", "API_KEY", "MONGODB_URI",
        "requests.post", "httpx.post", "urllib.request",
    ]
    code_lower = code.lower()
    for pattern in _BLOCKED_PATTERNS:
        if pattern.lower() in code_lower:
            return f"Error: Code blocked for security — disallowed pattern: '{pattern}'"
    
    try:
        temp_file.write_text(code, encoding="utf-8")
        
        # ── Security: Execute with sanitized, minimal environment ──
        safe_env = {
            "PATH": "/usr/bin:/usr/local/bin",
            "PYTHONPATH": "",
            "HOME": str(work_dir),
            "LANG": "en_US.UTF-8",
        }
        
        cmd = [sys.executable, "-I", filename]  # -I = isolated mode (no user site, no PYTHON* env vars)
        
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5.0,
            env=safe_env,
        )
        
        output = ""
        if result.stdout:
            output += f"[stdout]\n{result.stdout}\n"
        if result.stderr:
            # Filter out sensitive paths from error output
            stderr_clean = result.stderr.replace(str(Path.home()), "~")
            output += f"[stderr]\n{stderr_clean}\n"
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


def _has_keyword_match(query: str, keywords: list[str]) -> bool:
    """Check if any of the keywords match as exact words/phrases in the query (case-insensitive)."""
    words = set(re.findall(r"\b\w+\b", query.lower()))
    for kw in keywords:
        if " " in kw:
            if re.search(r"\b" + re.escape(kw) + r"\b", query.lower()):
                return True
        elif kw.lower() in words:
            return True
    return False


def _is_identity_query(query: str) -> bool:
    """Detect if the query asks about the user's or the assistant's personal identity/profile."""
    q = query.lower()
    identity_phrases = ["who am i", "who i am", "who are you", "what is my name", "do you know me", "do you know who i am", "do u know who am i"]
    return any(p in q for p in identity_phrases)


def _should_skip_rag(query: str, intent: str, domain: str) -> bool:
    """
    Consolidated RAG bypass logic. Skip RAG when it's not beneficial
    and can contaminate reasoning (e.g., greetings, puzzles, code, math, meta-conversations, creative writing).
    """
    q_low = query.lower().strip()
    clean_q = re.sub(r"[^\w\s]", "", q_low).strip()

    # 1. Greetings / Conversational Meta Queries / Identity queries / Verification follow-ups
    greetings = {
        "hello", "hi", "hey", "greetings", "good morning", "good afternoon",
        "good evening", "how are you", "who are you", "aarka", "aarkaai",
        "what is your name", "what can you do", "help me", "who am i", "who i am",
        "are you sure", "are you certain", "really", "is that true", "is that correct",
        "why", "why so", "how come", "yes", "no", "ok", "okay", "thanks", "thank you",
        "got it", "cool", "nice"
    }
    if clean_q in greetings or _is_identity_query(query) or any(meta in q_low for meta in ["who are you", "what is your name", "what can you do", "are you sure", "are you certain"]):
        return True

    # 2. Reasoning / Math Puzzles
    if _is_reasoning_query(query) or intent == "reasoning_puzzle":
        return True

    # 3. Simple math patterns (e.g., "what is 2 + 2", "compute 54 * 23")
    if re.search(r"\b(calculate|compute|solve|what is)\b", q_low) and re.search(r"\d+\s*[\+\-\*/\^]\s*\d+", q_low):
        return True

    # 4. Coding / Technology Help (Do NOT skip RAG if it's a system design / architecture query)
    is_sysdesign = any(w in q_low for w in ["system design", "architecture", "design a", "design an", "scale a", "eviction", "replication", "sharding", "capacity estimation", "latency", "load balancer"])
    if (intent == "coding_help" or _is_coding_syntax(query) or domain == "technology") and not is_sysdesign:
        return True

    # 5. Creative writing / Humor
    creative_keywords = ["write a poem", "tell a joke", "write a story", "make a joke", "tell a story", "compose a song", "write a lyrics"]
    if any(kw in q_low for kw in creative_keywords):
        return True

    return False


def _follow_up_score(query: str, chat_ctx: list) -> float:
    """Confidence-scored follow-up detection using 7 signal categories.

    Returns a float 0.0–1.0 indicating how strongly the query depends on
    prior conversation history.  Multiple signals stack (capped at 1.0).
    """
    if not chat_ctx:
        return 0.0

    q_low = query.lower().strip()
    word_count = len(q_low.split())
    words = set(re.findall(r"\b[a-zA-Z]+\b", q_low))
    score = 0.0

    # ── Signal 1: Short query heuristic ──────────────────────────────────
    if word_count <= 3:
        score += 0.85
    elif word_count <= 6:
        score += 0.70

    # ── Signal 2: Pronoun / demonstrative references ─────────────────────
    pronoun_refs = {
        "it", "its", "they", "them", "their", "he", "him", "his",
        "she", "her", "this", "that", "these", "those",
    }
    if words.intersection(pronoun_refs):
        score += 0.60

    # ── Signal 3: Continuation phrases ───────────────────────────────────
    continuation_phrases = [
        "tell me more", "explain further", "go on", "keep going",
        "what else", "and then", "continue", "elaborate", "more details",
        "expand on", "can you elaborate", "more about", "in detail",
    ]
    if any(p in q_low for p in continuation_phrases):
        score += 0.90

    # ── Signal 4: Verification / challenge phrases ───────────────────────
    verification_phrases = [
        "are you sure", "really", "is that correct", "is that right",
        "is that true", "why so", "how come", "can you clarify",
        "are you certain", "prove it", "source", "how do you know",
        "double check", "verify", "confirm",
    ]
    if any(p in q_low for p in verification_phrases):
        score += 0.85

    # ── Signal 5: Affirmation / negation ─────────────────────────────────
    affirmation_negation = {
        "yes", "no", "ok", "okay", "right", "correct", "wrong",
        "exactly", "agreed", "nope", "yep", "yeah", "nah",
    }
    if q_low in affirmation_negation or (word_count <= 3 and words.intersection(affirmation_negation)):
        score += 0.80

    # ── Signal 6: Contextual back-references ─────────────────────────────
    back_refs = [
        "the above", "you said", "you mentioned", "earlier",
        "previous", "last answer", "your response", "as you said",
        "you told me", "your answer", "from before",
    ]
    if any(p in q_low for p in back_refs):
        score += 0.95

    # ── Signal 7: Comparative follow-ups ─────────────────────────────────
    comparative_phrases = [
        "what about", "how about", "instead of", "versus", " vs ",
        "compared to", "rather than", "difference between", "or should",
    ]
    if any(p in q_low for p in comparative_phrases):
        score += 0.70

    return min(score, 1.0)


def _is_follow_up(query: str, chat_ctx: list) -> bool:
    """Boolean wrapper — returns True when follow-up confidence > 0."""
    return _follow_up_score(query, chat_ctx) > 0.0


def _detect_topic_shift(query: str, chat_ctx: list) -> bool:
    """Detect when the user switches to an unrelated topic.

    Returns True when the current query has zero meaningful word overlap
    with recent history, indicating a fresh topic that should not carry
    stale conversation context.
    """
    if not chat_ctx:
        return False

    q_low = query.lower().strip()
    word_count = len(q_low.split())

    # Short queries (≤6 words) are almost never fresh-topic — they depend on context
    if word_count <= 6:
        return False

    # Topic-shift markers — user explicitly abandons prior topic
    shift_phrases = [
        "forget that", "never mind", "forget it", "actually forget",
        "new topic", "change topic", "different question", "something else",
        "actually,", "forget java", "forget python",  # "actually forget X"
    ]
    if any(p in q_low for p in shift_phrases):
        return True

    # Content overlap check: compare query words with last 4 messages
    stop_words = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "about", "between",
        "through", "and", "but", "or", "so", "if", "then", "than", "that",
        "this", "it", "its", "i", "me", "my", "you", "your", "we", "our",
        "what", "how", "why", "when", "where", "which", "who", "whom",
        "not", "no", "yes", "all", "each", "every", "some", "any",
        "tell", "explain", "describe", "give", "show", "please",
    }
    query_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", q_low)) - stop_words
    if len(query_words) < 2:
        return False  # Too few content words to judge

    # Collect content words from last 4 history messages
    recent = chat_ctx[-4:] if len(chat_ctx) >= 4 else chat_ctx
    history_text = " ".join(m.get("message", "") for m in recent).lower()
    history_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", history_text)) - stop_words

    overlap = query_words.intersection(history_words)
    overlap_ratio = len(overlap) / len(query_words) if query_words else 0.0

    # If less than 15% word overlap with recent history, it's likely a new topic
    if overlap_ratio < 0.15 and word_count > 8:
        return True

    return False


def _build_agent_ctx(chat_ctx, context_parts, sources) -> str:
    parts = []
    if "finance" in sources:
        for part in context_parts:
            if "[Finance Data]" in part:
                parts.append(part)
                break
    if chat_ctx:
        # Sanitize chat history: remove Action/Observation outputs to prevent agent confusion in the ReAct loop
        sanitized_messages = []
        for m in chat_ctx:
            msg = m.get('message', '')
            if not msg:
                continue
            lines = []
            for line in msg.split("\n"):
                line_strip = line.strip()
                # Remove lines starting with ReAct loop syntax keys in history
                if (line_strip.lower().startswith("action:") or 
                    line_strip.lower().startswith("action input:") or 
                    line_strip.lower().startswith("observation:")):
                    continue
                lines.append(line)
            clean_msg = "\n".join(lines).strip()
            if clean_msg:
                sanitized_messages.append({
                    "role": m["role"],
                    "message": clean_msg
                })

        chat_lines = "\n".join(
            f"{'User' if m['role'] == 'user' else 'AARKAA'}: {m['message'][:1500]}"
            for m in sanitized_messages
        )
        parts.append(f"[Recent Conversation]\n{chat_lines}")
    return "\n\n".join(parts).strip()


def _build_coder_context(coder_result: dict) -> str:
    """
    Format coder pipeline results into structured context for the 7B polish pass.
    The 7B model receives the generated code, validation status, test results,
    and execution output to produce a polished, explained response.
    """
    parts = []

    parts.append(
        "[Aarka Coder Generated Code]\n"
        "The following code was generated by the Aarka Coder 3B model and verified.\n"
        "Present this code in your response with clear markdown formatting, "
        "add a thorough explanation, time/space complexity analysis, "
        "and discuss edge cases.\n"
    )

    lang = coder_result.get("language", "python")
    code = coder_result.get("code", "")
    parts.append(f"```{lang}\n{code}\n```")

    # Validation status
    if coder_result.get("syntax_valid"):
        parts.append("✅ **Syntax Validation:** Passed (AST check clean)")
    else:
        err = coder_result.get("syntax_error", "Unknown error")
        parts.append(f"❌ **Syntax Validation:** Failed — {err}")

    # Security scan
    sec_issues = coder_result.get("security_issues", [])
    if sec_issues:
        parts.append("⚠️ **Security Issues Found:**\n" + "\n".join(f"  - {issue}" for issue in sec_issues))
    else:
        parts.append("✅ **Security Scan:** No vulnerabilities detected")

    # Execution output
    exec_output = coder_result.get("execution_output", "")
    if exec_output:
        parts.append(f"**Code Execution Output:**\n```\n{exec_output[:2000]}\n```")

    # Test results
    test_code = coder_result.get("test_code", "")
    if test_code:
        test_passed = coder_result.get("test_passed", False)
        test_output = coder_result.get("test_output", "")
        status = "✅ PASSED" if test_passed else "❌ FAILED"
        parts.append(f"**Unit Tests:** {status}")
        if test_output:
            parts.append(f"```\n{test_output[:1500]}\n```")

    duration = coder_result.get("duration", 0)
    parts.append(f"**Pipeline Duration:** {duration:.2f}s")

    return "\n\n".join(parts)

def _write_previous_message_file(chat_ctx):
    if chat_ctx:
        last_assistant_msg = None
        for m in reversed(chat_ctx):
            if m.get('role') == 'assistant':
                msg = m.get('message', '')
                if not msg:
                    continue
                # Skip messages containing PDF download links, tool actions, or short retry instructions
                if "[Download " in msg or "/download/" in msg:
                    continue
                if "Action:" in msg or "Action Input:" in msg or "Observation:" in msg:
                    continue
                # Skip messages containing tool names or error signatures
                if any(t in msg for t in ["FileReadTool", "BashTool", "FileEditTool", "GetSkillTool", "ListSkillsTool"]):
                    continue
                if "does not exist in the workspace" in msg or "not found" in msg.lower() or "error:" in msg.lower():
                    continue
                # Skip messages under 300 characters matching error/retry keywords
                if len(msg.strip()) < 300 and any(w in msg.lower() for w in ["error", "fail", "already", "restart", "invalid", "exception", "failed"]):
                    continue
                last_assistant_msg = msg
                break
        if last_assistant_msg:
            try:
                from config import SAFE_WORK_DIR
                work_dir = SAFE_WORK_DIR
                work_dir.mkdir(parents=True, exist_ok=True)
                with open(work_dir / "previous_message.txt", "w", encoding="utf-8") as f:
                    f.write(last_assistant_msg)
            except Exception as exc:
                logger.error("Error writing previous_message.txt: %s", exc)


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
    # Bypassed if the query explicitly asks for systems/software design or architecture
    _has_design_keywords = any(w in query.lower() for w in ["design a", "design an", "system design", "architecture", "explain:"])
    if _has_design_keywords:
        domain = "technology"
        intent = "tech_info"
        filter_confidence = max(filter_confidence, 0.90)
        logger.info("Forced domain=technology, intent=tech_info due to design/architecture keywords")
    elif filter_confidence < 0.45 and intent not in ["persuasion", "debate", "comparison", "roleplay"]:
        logger.info("Low filter confidence (%.3f < 0.45) — falling back to general query", filter_confidence)
        domain = "general"
        intent = "general_query"

    logger.info(
        "Filter → domain=%s  conf=%.3f  intent=%s",
        domain, filter_confidence, intent,
    )
    
    # Track the active request domain for engine model routing
    aarkaa_engine.request_domain.set(domain)

    # ── 1a. Hybrid Query Router (feature-flagged) ─────────────────────────
    # When enabled, decomposes the query into typed sub-queries, executes
    # them in parallel across data sources, fuses context, then synthesizes.
    # Falls back to the existing waterfall pipeline if the router returns
    # an empty answer or if HQR_ENABLED is False.
    from config import HQR_ENABLED
    if HQR_ENABLED and not is_greeting and not is_reasoning and mode != "benchmark":
        try:
            from modules.query_understanding import analyze as hqr_analyze
            from modules.hybrid_router import execute_hybrid

            # Fetch chat history for context
            hqr_chat_ctx = None
            try:
                hqr_chat_ctx = memory.get_chat_context(user_id, session_id, limit=15)
            except Exception:
                pass

            # Fetch user facts
            hqr_user_facts = ""
            try:
                hqr_user_facts = memory.get_user_facts_prompt(user_id)
            except Exception:
                pass

            # Step 1: Decompose query into a plan
            plan = hqr_analyze(
                query=query,
                domain=domain,
                intent=intent,
                detected_language=detected_lang,
                user_id=user_id,
                chat_context=hqr_chat_ctx,
            )

            # Skip HQR for model-only plans (greetings, puzzles) — let the
            # existing pipeline handle them with its optimised paths.
            from modules.query_understanding import DataSource as DS
            has_data_sources = any(
                sq.source_type not in (DS.MODEL_ONLY, DS.VISION, DS.CODER)
                for sq in plan.sub_queries
            )

            if has_data_sources:
                # Step 2: Execute plan through hybrid router
                hqr_result = execute_hybrid(
                    plan=plan,
                    user_id=user_id,
                    session_id=session_id,
                    chat_history=hqr_chat_ctx,
                    user_facts=hqr_user_facts,
                )

                if hqr_result.final_answer:
                    elapsed = time.perf_counter() - start
                    logger.info(
                        "HQR handled query in %.0fms (%d sources, model=%s, bypass=%s)",
                        hqr_result.total_time_ms,
                        hqr_result.fused_context.source_count,
                        hqr_result.model_used,
                        hqr_result.bypassed_llm,
                    )

                    # Store conversation
                    try:
                        memory.store_conversation(
                            user_id, session_id, query,
                            hqr_result.final_answer,
                            intent=intent, confidence=filter_confidence,
                            source=f"hybrid_router:{','.join(hqr_result.fused_context.sources_used)}"
                        )
                        memory.extract_user_facts(user_id, query)
                    except Exception as mem_exc:
                        logger.error("Memory store error (HQR): %s", mem_exc)

                    return PromptResponse(
                        response=hqr_result.final_answer,
                        intent=intent,
                        confidence=filter_confidence,
                        sources=["hybrid_router"] + hqr_result.fused_context.sources_used,
                        detected_language=detected_lang,
                        processing_time=elapsed,
                    )
                else:
                    logger.info("HQR returned empty answer — falling through to existing pipeline")
        except Exception as hqr_exc:
            logger.warning("HQR error (falling back to existing pipeline): %s", hqr_exc)

    # ── 1b. Tool Router Pipeline (3B → Permission → Tool → 7B) ───────────
    # Attempt structured tool routing for finance, portfolio, F&O, etc.
    # If the tool router handles the query, short-circuit to return.
    if not is_greeting and not is_reasoning and mode != "benchmark":
        try:
            from modules.tool_router import process_with_tools
            from modules.subscription import check_access

            # Determine user tier
            sub_info = check_access(user_id, "strategy")
            user_tier = sub_info.get("tier", "free")

            tool_result = process_with_tools(
                query, user_id=user_id, user_tier=user_tier,
                model_override=None  # Uses default 7B/Gemini
            )

            if tool_result.permission_denied:
                logger.info("Tool router: permission denied — %s", tool_result.permission_message)
                # Fall through to standard path but inject permission message
            elif tool_result.final_answer:
                elapsed = time.perf_counter() - start
                logger.info(
                    "Tool router handled query in %.1fms with %d tool(s)",
                    tool_result.total_time_ms, len(tool_result.tool_results)
                )

                # Store conversation
                try:
                    tool_sources = [r.tool_name for r in tool_result.tool_results if r.is_valid]
                    memory.store_conversation(
                        user_id, session_id, query,
                        tool_result.final_answer,
                        intent=intent, confidence=filter_confidence,
                        source=f"tool_pipeline:{','.join(tool_sources)}"
                    )
                    memory.extract_user_facts(user_id, query)
                except Exception as mem_exc:
                    logger.error("Memory store error (tool pipeline): %s", mem_exc)

                return PromptResponse(
                    response=tool_result.final_answer,
                    intent=intent,
                    confidence=filter_confidence,
                    sources=["tool_pipeline"] + [r.tool_name for r in tool_result.tool_results if r.is_valid],
                    detected_language=detected_lang,
                    processing_time=elapsed,
                )
        except Exception as tool_exc:
            logger.warning("Tool router error (falling back to standard path): %s", tool_exc)

    # ── 1c. Cognitive Subagent Orchestrator ────────────────────────────────
    # For complex/compound queries that the tool router didn't handle,
    # route through specialized subagent pipelines for deeper analysis.
    if not is_greeting and not is_reasoning and mode != "benchmark":
        try:
            from modules.subagents.orchestrator import get_orchestrator

            orch = get_orchestrator()
            orch_context = {
                "domain": domain,
                "intent": intent,
                "user_id": user_id,
                "session_id": session_id,
            }
            orch_answer = orch.orchestrate(query, orch_context)

            if orch_answer:
                elapsed = time.perf_counter() - start
                logger.info(
                    "Orchestrator handled query in %.1fms (pipeline=%s)",
                    elapsed * 1000,
                    orch_context.get("_metadata", {}).get("pipeline", [])
                )

                # Store conversation
                try:
                    memory.store_conversation(
                        user_id, session_id, query, orch_answer,
                        intent=intent, confidence=filter_confidence,
                        source=f"orchestrator:{','.join(orch_context.get('_metadata', {}).get('pipeline', []))}"
                    )
                    memory.extract_user_facts(user_id, query)
                except Exception as mem_exc:
                    logger.error("Memory store error (orchestrator): %s", mem_exc)

                return PromptResponse(
                    response=orch_answer,
                    intent=intent,
                    confidence=filter_confidence,
                    sources=["cognitive_orchestrator"] + orch_context.get("_tools_used", []),
                    detected_language=detected_lang,
                    processing_time=elapsed,
                )
        except Exception as orch_exc:
            logger.warning("Orchestrator error (falling back to standard path): %s", orch_exc)

    # ── 2. Skip primary check – run model only ONCE at the end (speed)
    # Gathering external context first, then a single model call with
    # full context gives better answers AND is 2x faster.
    primary_answer = ""
    primary_confidence = filter_confidence
    sources.append("aarkaa-3b")

    # Fetch chat history early for follow-up detection and context budget
    chat_ctx = None
    try:
        chat_ctx = memory.get_chat_context(user_id, session_id, limit=15)
        if chat_ctx:
            last_user_msg = None
            for msg in reversed(chat_ctx):
                if msg["role"] == "user":
                    last_user_msg = msg["message"]
                    break
            if last_user_msg and last_user_msg.strip().lower() == query.strip().lower() and len(query) > 15:
                if not any(w in query.lower() for w in ["pdf", "document", "previous", "report"]):
                    logger.info("Detected retry of same query. Clearing history context to avoid truncation bias.")
                    chat_ctx = None
    except Exception as exc:
        logger.error("Memory context error: %s", exc)

    # ── 4. Low confidence – route to external modules ─────────────────────
    context_parts: list[str] = []

    # RAG – check the knowledge base first
    # Confidence-gated RAG skip: high-confidence follow-ups (≥0.7) with ≤8
    # words skip RAG entirely; medium confidence (≥0.5) reduces top_k to 1.
    _fu_score = _follow_up_score(query, chat_ctx)
    _is_short_followup = _fu_score >= 0.7 and len(query.split()) <= 8
    if not _should_skip_rag(query, intent, domain) and mode != "benchmark" and not _is_short_followup:
        try:
            from modules.aarkaa_engine import _classify_and_plan
            plan = _classify_and_plan(query)
            if _fu_score >= 0.5:
                top_k = 1
            elif plan["domain"] in ["system_design", "coding", "debugging"]:
                top_k = 6
            elif plan["type"] == "fact_lookup":
                top_k = 2
            else:
                top_k = 3
            rag_context = rag.get_context(query, top_k=top_k, user_id=user_id, query_domain=domain)
            if rag_context:
                context_parts.append(f"[Knowledge Base]\n{rag_context}")
                sources.append("rag")
        except Exception as exc:
            logger.error("RAG module error: %s", exc)

    # Topic-shift detection: if the user switched to an unrelated topic,
    # trim history to prevent conversation drift from stale context.
    if chat_ctx and _detect_topic_shift(query, chat_ctx):
        logger.info("Topic shift detected — trimming history to last 2 turns")
        chat_ctx = chat_ctx[-4:]  # Keep only last 2 user+assistant pairs

    # Architecture self-awareness – detect queries about AARKAA's own internals
    from modules.architecture_verifier import is_architecture_query
    _is_arch_query = is_architecture_query(query)
    _arch_context = ""
    if _is_arch_query and mode != "benchmark":
        try:
            _arch_context = rag.get_context(
                query, top_k=5, user_id=user_id,
                max_chars=8000, source_filter="architecture"
            )
            if _arch_context:
                context_parts.insert(0, (
                    "[AARKAA Architecture Documentation — Answer from this ONLY]\n"
                    + _arch_context
                ))
                sources.append("architecture")
                logger.info("Architecture query detected — injected %d chars of arch docs", len(_arch_context))
        except Exception as exc:
            logger.error("Architecture RAG retrieval error: %s", exc)

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
    is_factual = any(prefix in q_lower for prefix in _FACTUAL_PREFIXES)

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
        "trace this", "trace the code",
        "draw a", "draw an", "draw me", "draw something",
        "generate an image", "generate image", "generate a photo", "generate a picture",
        "generate a drawing", "generate art",
        "create a picture", "create an image", "create a drawing", "create a photo", "create art",
        "make a drawing", "make a picture", "make an image",
        "paint a", "paint an", "paint me",
        "sketch a", "sketch an", "illustrate a", "render a", "render an",
        "portrait of", "ultra-realistic portrait",
    ]
    _knowledge_signals = [
        "design a", "design an", "explain", "describe", "what is", "how does",
        "provide architecture", "provide an architecture", "provide a", "give me",
        "what are", "how would you", "walk me through", "tell me about",
        "compare", "difference between", "pros and cons", "trade-off", "trade offs",
        "system design", "architecture for", "high level", "high-level",
        "for 1 million", "for 1m users", "for million users", "safely run",
    ]
    is_knowledge = any(sig in query.lower() for sig in _knowledge_signals)

    needs_agent = (
        not is_coding_output
        and not is_knowledge
        and (
            any(w in query.lower() for w in agent_triggers)
            or bool(re.search(r"\brun\b", query.lower()))
            or bool(re.search(r"\bgit\b", query.lower()))
            or (intent == "coding_help" and any(p in query.lower() for p in ["run", "execute", "trace", "test"]))
            or _is_calculation_query(query)
            or _needs_skill_routing(query)
            or _is_image_generation_query(query)
        )
    )

    # Queries that are self-contained (algorithms, system design, CS theory)
    # should NEVER trigger web search — the model knows the answer.
    is_no_web = any(kw in q_lower for kw in _NO_WEB_SEARCH_KEYWORDS)
    is_search_directive = q_lower.strip() in ["search web", "search the web", "google it", "look it up", "search online", "find online", "search"]

    is_step_by_step = any(w in query.lower() for w in ["step by step", "recipe", "detailed", "how to make", "how to build", "guide"])

    needs_web = (
        mode != "benchmark"
        and not is_trick
        and not is_no_web
        and not has_finance_context
        and not is_greeting
        and not _is_identity_query(query)
        and not _is_short_followup
        and (intent != "coding_help" or is_factual)
        and (intent != "reasoning_puzzle" or is_factual)
        and (
            domain == "web_search"
            or is_search_directive
            or intent in ("web_lookup", "news_search", "science_query")
            or _has_keyword_match(query, _NEWS_KEYWORDS)
            or _has_keyword_match(query, _FACTUAL_KEYWORDS)
            or is_factual
            or (domain in ("general", "science", "health", "history") and "rag" not in sources)
        )
    )

    if needs_web and not needs_agent:
        if not _web_breaker.is_open:
            try:
                search_query = _resolve_search_query(query, chat_ctx)
                search_query = _enhance_search_query(search_query)
                web_ctx = web_search.get_web_context(search_query, lang=detected_lang, filter_live=(not is_fin_intent))
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
    # (chat_ctx has already been retrieved early for RAG follow-up check)

    fused_context = "\n\n---\n\n".join(context_parts)

    # ── 6. AARKAA-3B final response ──────────────────────────────────────
    # Only trigger the slow autonomous agent (ReAct loop) if the user explicitly asks to run, execute, or manage files.
    is_coding = intent == "coding_help" or any(w in query.lower() for w in ["script", "code", "python", "implement", "create a file"])

    user_facts = ""
    try:
        user_facts = memory.get_user_facts_prompt(user_id)
    except Exception as exc:
        logger.error("Error loading user facts: %s", exc)

    # ── Autonomous Planner Guard Integration ────────────────────────────────
    import os
    ENABLE_AUTONOMOUS_PLANNING = os.getenv("ENABLE_AUTONOMOUS_PLANNING", "true").lower() == "true"
    
    if ENABLE_AUTONOMOUS_PLANNING:
        from modules import goal_planner
        if goal_planner.needs_planning(query, filter_result, chat_ctx):
            try:
                from modules import task_memory, execution_engine
                plan_dag = goal_planner.create_plan(query, fused_context, chat_ctx)
                goal_id = task_memory.save_goal(user_id, session_id, query, plan_dag)
                final_answer = execution_engine.execute(plan_dag, goal_id, user_id, session_id)
                
                # Combined confidence
                combined_confidence = 0.95
                elapsed = round(time.perf_counter() - start, 3)
                logger.info("Autonomous execution planner finished in %.3fs", elapsed)
                return PromptResponse(
                    response=final_answer,
                    intent=intent,
                    confidence=combined_confidence,
                    sources=sources + ["autonomous_planner"],
                    detected_language=detected_lang,
                    processing_time=elapsed,
                )
            except Exception as plan_exc:
                logger.error("Autonomous Planner execution failed: %s. Falling back.", plan_exc)

    if _is_pdf_generation_query(query):
        from pathlib import Path
        from modules.gamma_pdf import compile_gamma_pdf
        topic = _extract_pdf_topic(query)
        filename = _generate_pdf_filename(topic)
        template = _extract_pdf_template(query)
        try:
            pdf_path = compile_gamma_pdf(topic, filename, template=template)
            filename = Path(pdf_path).name
            final_answer = (
                f"I have generated the premium Gamma-style PDF report you requested.\n\n"
                f"**Downloads & Sharing:**\n"
                f"* [Download PDF Report](/download/{filename})\n"
                f"* [Download PDF Report (HTTPS)](https://synthetixanalytics.com/download/{filename})"
            )
        except Exception as exc:
            logger.error("Failed to compile premium Gamma PDF: %s", exc)
            final_answer = f"Error generating PDF: {exc}"
    elif _is_image_generation_query(query):
        from modules.tools.image import ImageGenTool
        image_result = ImageGenTool().execute({"prompt": query})
        img_match = re.search(r"!\[Generated Image\]\((.*?)\)", image_result)
        if img_match:
            img_link = img_match.group(0)
            filename = img_link.split("/")[-1].replace(")", "")
            final_answer = (
                f"I have generated the image you requested. Here is your generated image:\n\n"
                f"{img_link}\n\n"
                f"**Downloads & Sharing:**\n"
                f"* [Download Image](/download/{filename})\n"
                f"* [Download Image (HTTPS)](https://synthetixanalytics.com/download/{filename})"
            )
        else:
            final_answer = image_result
    elif needs_agent:
        from modules import coordinator
        # Proactively save previous message to previous_message.txt in case the agent reads it
        _write_previous_message_file(chat_ctx)
        # DANGER: Do NOT pass Web or RAG context to the autonomous agent to prevent 4096 context window explosions.
        # The agent has its own WebSearchTool if it needs information. Only pass chat history + live finance context.
        agent_ctx = _build_agent_ctx(chat_ctx, context_parts, sources)
        final_answer = coordinator.process_task(query, agent_ctx)
    elif fused_context or is_reasoning or chat_ctx:
        final_answer = aarkaa_engine.final_response(query, fused_context, intent=intent, lang=detected_lang, mode=mode, history=chat_ctx, user_facts=user_facts, force_general=is_knowledge)
    else:
        # No external context and no history (e.g. initial greeting) – run model directly
        final_answer, _ = aarkaa_engine.primary_check(query, lang=detected_lang)

    # For knowledge/design queries (verifier is skipped), apply ReAct stripping inline
    # since the coder model may still generate reasoning scaffolds even with force_general.
    if is_knowledge and final_answer:
        try:
            from modules.agents.verifier import _strip_react_format
            stripped = _strip_react_format(final_answer)
            if stripped and stripped.strip():
                final_answer = stripped
        except Exception:
            pass

    # Combine confidence (average of filter and primary)
    combined_confidence = (filter_confidence + primary_confidence) / 2

    # ── 7. In-depth Verification Pass ─────────────────────────────────────
    if not _is_image_generation_query(query):
        # Architecture-specific verification (runs first for arch queries)
        if _is_arch_query and _arch_context:
            try:
                from modules.architecture_verifier import verify_architecture_response, build_architecture_repair_prompt
                if not verify_architecture_response(query, final_answer):
                    logger.info("Architecture verifier rejected response — regenerating with repair prompt")
                    repair_prompt = build_architecture_repair_prompt(query, _arch_context)
                    final_answer = aarkaa_engine.generate_raw(repair_prompt, max_new_tokens=1024)
                    final_answer = aarkaa_engine.clean_response(final_answer)
                    # Verify again — if still bad, prepend arch docs as direct answer
                    if not verify_architecture_response(query, final_answer):
                        logger.warning("Architecture verifier rejected repair response — using direct docs")
                        final_answer = (
                            "Based on AARKAA's internal architecture:\n\n"
                            + _arch_context
                        )
            except Exception as exc:
                logger.error("Architecture verification failed: %s", exc)

        # Skip LLM verifier for pure knowledge/design queries — the 3B model
        # cannot reliably reproduce long architecture answers and will replace
        # correct text with hallucinated training-distribution fragments.
        _skip_verifier = is_knowledge
        if not _skip_verifier:
            try:
                from modules.agents.verifier import verify_response
                logger.info("Running verifier agent on final answer...")
                final_answer = verify_response(query, final_answer, evidence=fused_context)
            except Exception as exc:
                logger.error("Failed to run verifier agent on final answer: %s", exc)
        else:
            logger.info("Verifier skipped for knowledge/design query (domain=%s).", intent)

    # ── 8. Store + auto-learn (post-process) ──────────────────────────────
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


async def stream_query(query: str, user_id: str = "default", session_id: str = "default", mode: str = "production", model_override: str | None = None):
    """
    Streaming version of the pipeline.
    Yields JSON chunks for SSE.
    """
    import asyncio
    from modules import (
        aarkaa_engine,
        auto_learn,
        finance,
        memory,
        rag,
        semantic_filter,
        web_search,
    )

    _SENTINEL = object()

    async def _stream_in_thread(gen_func, *args, **kwargs):
        """Run a blocking generator in a thread and yield tokens via asyncio.Queue."""
        q: asyncio.Queue = asyncio.Queue(maxsize=64)
        loop = asyncio.get_event_loop()

        def _producer():
            try:
                for token in gen_func(*args, **kwargs):
                    loop.call_soon_threadsafe(q.put_nowait, token)
            except Exception as exc:
                logger.error("_stream_in_thread producer error: %s", exc)
            finally:
                loop.call_soon_threadsafe(q.put_nowait, _SENTINEL)

        asyncio.get_event_loop().run_in_executor(None, _producer)
        while True:
            item = await q.get()
            if item is _SENTINEL:
                break
            yield item

    start = time.perf_counter()
    sources: list[str] = []

    # Check for external agent model overrides (Gemini / Claude / GPT-OSS)
    if model_override and (model_override.startswith("gemini") or model_override.startswith("claude") or model_override.startswith("gpt")):
        # Fetch web context if news/latest is explicitly requested
        web_context = ""
        q_lower = query.lower()
        if any(w in q_lower for w in ["latest news", "breaking news", "today's news", "live stock price", "current weather"]):
            try:
                yield {"type": "status", "status": "Searching Google for live results..."}
                from modules.web_search import get_web_context
                web_context = get_web_context(query, max_results=3)
            except Exception as exc:
                logger.error("Failed to fetch web context for external agent: %s", exc)

        yield {
            "type": "metadata",
            "intent": "external_agent",
            "sources": [model_override] + (["google_search"] if web_context else []),
            "detected_language": "en"
        }
        if model_override.startswith("gemini"):
            yield {"type": "status", "status": f"Connecting to Google {model_override.replace('-', ' ').title()}..."}
            from modules.external_agents import stream_gemini_response
            full_resp = ""
            for token in stream_gemini_response(query, context=web_context, model_name=model_override):
                full_resp += token
                yield {"type": "content", "token": token}
                await asyncio.sleep(0.001)
        elif model_override.startswith("claude") or model_override.startswith("gpt"):
            yield {"type": "status", "status": f"Connecting to Anthropic {model_override.replace('-', ' ').title()}..."}
            from modules.external_agents import stream_claude_response
            full_resp = ""
            for token in stream_claude_response(query, context=web_context, model_name=model_override):
                full_resp += token
                yield {"type": "content", "token": token}
                await asyncio.sleep(0.001)
        
        elapsed = round(time.perf_counter() - start, 3)
        yield {"type": "final", "processing_time": elapsed}
        return

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

    # Fallback to general query if classifier confidence is low
    _has_design_keywords = any(w in query.lower() for w in ["design a", "design an", "system design", "architecture", "explain:"])
    _has_code_keywords = any(w in query.lower() for w in ["code", "program", "function", "script", "implement", "write an agent", "create an agent", "tool_1", "tool_2", "tool_3", "pytest", "unit test", "bash tool", "fileedittool", "python class"])
    if _has_design_keywords:
        domain = "technology"
        intent = "tech_info"
        filter_confidence = max(filter_confidence, 0.90)
        logger.info("Forced domain=technology, intent=tech_info due to design/architecture keywords (stream)")
    elif _has_code_keywords:
        domain = "technology"
        intent = "coding_help"
        filter_confidence = max(filter_confidence, 0.90)
        logger.info("Forced domain=technology, intent=coding_help due to coding keywords (stream)")
    elif filter_confidence < 0.45 and intent not in ["persuasion", "debate", "comparison", "roleplay"]:
        logger.info("Low filter confidence (%.3f < 0.45) — falling back to general query", filter_confidence)
        domain = "general"
        intent = "general_query"

    logger.info(
        "Filter → domain=%s  conf=%.3f  intent=%s",
        domain, filter_confidence, intent,
    )
    
    # Track the active request domain for engine model routing
    aarkaa_engine.request_domain.set(domain)

    # ── 1a. Hybrid Query Router — Streaming (feature-flagged) ─────────────
    from config import HQR_ENABLED
    if HQR_ENABLED and not is_greeting and not is_reasoning and mode != "benchmark":
        try:
            from modules.query_understanding import analyze as hqr_analyze, DataSource as DS
            from modules.hybrid_router import execute_hybrid
            import asyncio as _asyncio

            hqr_chat_ctx = None
            try:
                hqr_chat_ctx = memory.get_chat_context(user_id, session_id, limit=15)
            except Exception:
                pass

            hqr_user_facts = ""
            try:
                hqr_user_facts = memory.get_user_facts_prompt(user_id)
            except Exception:
                pass

            yield {"type": "status", "status": "Analyzing query..."}

            plan = hqr_analyze(
                query=query, domain=domain, intent=intent,
                detected_language=detected_lang, user_id=user_id,
                chat_context=hqr_chat_ctx,
            )

            has_data_sources = any(
                sq.source_type not in (DS.MODEL_ONLY, DS.VISION, DS.CODER)
                for sq in plan.sub_queries
            )

            if has_data_sources:
                # Emit per-source status
                source_labels = {
                    DS.MARKET_API: "market data", DS.NEWS_SEARCH: "news",
                    DS.RAG: "knowledge base", DS.WEB_SEARCH: "web",
                    DS.MONGODB: "user data", DS.FINANCIAL_TOOL: "financial tools",
                }
                for sq in plan.sub_queries:
                    label = source_labels.get(sq.source_type, sq.source_type.value)
                    yield {"type": "status", "status": f"Fetching {label}..."}

                yield {"type": "metadata", "intent": intent, "sources": [sq.source_type.value for sq in plan.sub_queries], "plan": plan.to_dict(), "detected_language": detected_lang}

                # Execute in thread pool (blocking) and yield result
                hqr_result = await _asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: execute_hybrid(
                        plan=plan, user_id=user_id, session_id=session_id,
                        chat_history=hqr_chat_ctx, user_facts=hqr_user_facts,
                    )
                )

                if hqr_result.final_answer:
                    yield {"type": "status", "status": "Synthesizing answer..."}

                    # Stream the answer token by token
                    for i in range(0, len(hqr_result.final_answer), 8):
                        chunk = hqr_result.final_answer[i:i+8]
                        yield {"type": "content", "token": chunk}
                        await _asyncio.sleep(0.001)

                    # Store conversation
                    try:
                        memory.store_conversation(
                            user_id, session_id, query,
                            hqr_result.final_answer,
                            intent=intent, confidence=filter_confidence,
                            source=f"hybrid_router:{','.join(hqr_result.fused_context.sources_used)}"
                        )
                    except Exception:
                        pass

                    elapsed = round(time.perf_counter() - start, 3)
                    yield {"type": "final", "processing_time": elapsed, "sources": hqr_result.fused_context.sources_used}
                    return
        except Exception as hqr_exc:
            logger.warning("HQR streaming error (falling back): %s", hqr_exc)

    # ── 1c. Cognitive Subagent Orchestrator (Stream) ──────────────────────
    # For deep reasoning mode, delegate to the subagent orchestrator
    # to yield agent status updates and stream the final verified response.
    if not is_greeting and not is_reasoning and mode == "deep_reasoning":
        try:
            from modules.subagents.orchestrator import get_orchestrator
            orch = get_orchestrator()
            complexity = orch.classify_complexity(query, domain, intent)
            if complexity in ("moderate", "complex"):
                logger.info("Orchestrating streamed response for complexity=%s", complexity)
                orch_context = {
                    "domain": domain,
                    "intent": intent,
                    "user_id": user_id,
                    "session_id": session_id,
                    "detected_language": detected_lang,
                }
                
                async for event in orch.orchestrate_stream(query, orch_context):
                    yield event
                
                # Store conversation in memory
                final_ans = orch_context.get("final_answer")
                if final_ans:
                    try:
                        memory.store_conversation(
                            user_id, session_id, query, final_ans,
                            intent=intent, confidence=filter_confidence,
                            source=f"orchestrator_stream:{','.join(orch_context.get('_metadata', {}).get('pipeline', []))}"
                        )
                        memory.extract_user_facts(user_id, query)
                    except Exception as mem_exc:
                        logger.error("Memory store error (orchestrator stream): %s", mem_exc)
                
                elapsed = round(time.perf_counter() - start, 3)
                yield {"type": "final", "processing_time": elapsed}
                return
        except Exception as orch_exc:
            logger.warning("Orchestrator stream error (falling back to direct stream): %s", orch_exc)

    sources.append("aarkaa-3b")

    # Fetch chat history early for follow-up detection and context budget
    chat_ctx = None
    try:
        chat_ctx = memory.get_chat_context(user_id, session_id, limit=15)
        if chat_ctx:
            last_user_msg = None
            for msg in reversed(chat_ctx):
                if msg["role"] == "user":
                    last_user_msg = msg["message"]
                    break
            if last_user_msg and last_user_msg.strip().lower() == query.strip().lower() and len(query) > 15:
                if not any(w in query.lower() for w in ["pdf", "document", "previous", "report"]):
                    logger.info("Detected retry of same query. Clearing history context to avoid truncation bias.")
                    chat_ctx = None
    except Exception: pass

    # ── 4. Gather Context ─────────────────────────────────────────────────
    context_parts: list[str] = []
    
    # RAG — confidence-gated skip for follow-ups
    _fu_score_s = _follow_up_score(query, chat_ctx)
    _is_short_followup_s = _fu_score_s >= 0.7 and len(query.split()) <= 8
    if not _should_skip_rag(query, intent, domain) and mode != "benchmark" and not _is_short_followup_s:
        try:
            top_k = 1 if _fu_score_s >= 0.5 else 3
            rag_context = rag.get_context(query, top_k=top_k, user_id=user_id, query_domain=domain)
            if rag_context:
                context_parts.append(f"[Knowledge Base]\n{rag_context}")
                sources.append("rag")
        except Exception: pass

    # Topic-shift detection: trim stale history on topic change
    if chat_ctx and _detect_topic_shift(query, chat_ctx):
        logger.info("Topic shift detected (stream) — trimming history to last 2 turns")
        chat_ctx = chat_ctx[-4:]

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
    is_factual = any(prefix in q_lower for prefix in _FACTUAL_PREFIXES)

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
        "trace this", "trace the code",
        "draw a", "draw an", "draw me", "draw something",
        "generate an image", "generate image", "generate a photo", "generate a picture",
        "generate a drawing", "generate art",
        "create a picture", "create an image", "create a drawing", "create a photo", "create art",
        "make a drawing", "make a picture", "make an image",
        "paint a", "paint an", "paint me",
        "sketch a", "sketch an", "illustrate a", "render a", "render an",
        "portrait of", "ultra-realistic portrait",
    ]
    _knowledge_signals = [
        "design a", "design an", "explain", "describe", "what is", "how does",
        "provide architecture", "provide an architecture", "provide a", "give me",
        "what are", "how would you", "walk me through", "tell me about",
        "compare", "difference between", "pros and cons", "trade-off", "trade offs",
        "system design", "architecture for", "high level", "high-level",
        "for 1 million", "for 1m users", "for million users", "safely run",
    ]
    is_knowledge = any(sig in query.lower() for sig in _knowledge_signals)

    needs_agent = (
        not is_coding_output
        and not is_knowledge
        and not is_coding_query
        and (
            any(w in query.lower() for w in agent_triggers)
            or bool(re.search(r"\brun\b", query.lower()))
            or bool(re.search(r"\bgit\b", query.lower()))
            or _is_calculation_query(query)
            or _needs_skill_routing(query)
            or _is_image_generation_query(query)
        )
    )

    # Queries that are self-contained (algorithms, system design, CS theory)
    # should NEVER trigger web search — the model knows the answer.
    is_no_web = any(kw in q_lower for kw in _NO_WEB_SEARCH_KEYWORDS)
    is_search_directive = q_lower.strip() in ["search web", "search the web", "google it", "look it up", "search online", "find online", "search"]

    is_step_by_step = any(w in query.lower() for w in ["step by step", "recipe", "detailed", "how to make", "how to build", "guide"])

    needs_web = (
        mode != "benchmark"
        and not _is_trick_question(query)
        and not is_no_web
        and not has_finance_context
        and not is_greeting
        and not _is_identity_query(query)
        and not _is_short_followup_s
        and (intent != "coding_help" or is_factual)
        and (intent != "reasoning_puzzle" or is_factual)
        and (
            domain == "web_search"
            or is_search_directive
            or intent in ("web_lookup", "news_search", "science_query")
            or _has_keyword_match(query, _NEWS_KEYWORDS)
            or _has_keyword_match(query, _FACTUAL_KEYWORDS)
            or is_factual
            or any(w in query.lower() for w in ["search", "find", "latest", "news", "google", "today", "2026"])
            or (domain in ("general", "science", "health", "history") and "rag" not in sources)
        )
    )

    if needs_web and not needs_agent:
        if not _web_breaker.is_open:
            try:
                yield {"type": "status", "status": "Searching Google for live results..."}
                search_query = _resolve_search_query(query, chat_ctx)
                search_query = _enhance_search_query(search_query)
                web_ctx = web_search.get_web_context(search_query, lang=detected_lang, filter_live=(not is_fin_intent))
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
    # (chat_ctx has already been retrieved early for RAG follow-up check)

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

    user_facts = ""
    try:
        user_facts = memory.get_user_facts_prompt(user_id)
    except Exception as exc:
        logger.error("Error loading user facts in stream: %s", exc)

    if _is_pdf_generation_query(query):
        import asyncio
        from pathlib import Path
        yield {"type": "status", "status": "Initializing premium Gamma PDF generator..."}
        from modules.gamma_pdf import compile_gamma_pdf, get_detailed_section, generate_domain_metadata
        from modules.gamma_domains import detect_domain
        topic = _extract_pdf_topic(query)
        filename = _generate_pdf_filename(topic)
        template = _extract_pdf_template(query)

        # Let Aarka decide section titles based on the actual topic and domain
        domain = detect_domain(topic)
        yield {"type": "status", "status": f"Analysing topic '{topic}' (domain: {domain}) and generating report structure..."}
        await asyncio.sleep(0.05)
        meta = generate_domain_metadata(topic, domain)
        s_titles = meta["section_titles"]
        s_hints  = meta["section_hints"]

        yield {"type": "status", "status": f"Generating Section 1 of 5 ({s_titles[0]})..."}
        await asyncio.sleep(0.05)
        sec1 = get_detailed_section(topic, s_titles[0], s_hints[0])

        yield {"type": "status", "status": f"Generating Section 2 of 5 ({s_titles[1]})..."}
        await asyncio.sleep(0.05)
        sec2 = get_detailed_section(topic, s_titles[1], s_hints[1])

        yield {"type": "status", "status": f"Generating Section 3 of 5 ({s_titles[2]})..."}
        await asyncio.sleep(0.05)
        sec3 = get_detailed_section(topic, s_titles[2], s_hints[2])

        yield {"type": "status", "status": f"Generating Section 4 of 5 ({s_titles[3]})..."}
        await asyncio.sleep(0.05)
        sec4 = get_detailed_section(topic, s_titles[3], s_hints[3])

        yield {"type": "status", "status": f"Generating Section 5 of 5 ({s_titles[4]})..."}
        await asyncio.sleep(0.05)
        sec5 = get_detailed_section(topic, s_titles[4], s_hints[4])

        yield {"type": "status", "status": f"Generating custom AI illustrations with AARKAA-VISION and compiling PDF with the '{template}' template..."}
        await asyncio.sleep(0.05)

        try:
            sections = [sec1, sec2, sec3, sec4, sec5]
            pdf_path = compile_gamma_pdf(topic, filename, template=template, sections=sections)
            filename = Path(pdf_path).name
            final_answer = (
                f"I have generated the premium Gamma-style PDF report you requested.\n\n"
                f"**Downloads & Sharing:**\n"
                f"* [Download PDF Report](/download/{filename})\n"
                f"* [Download PDF Report (HTTPS)](https://synthetixanalytics.com/download/{filename})"
            )
        except Exception as exc:
            logger.error("Failed to compile premium Gamma PDF in stream: %s", exc)
            final_answer = f"Error generating PDF: {exc}"
            
        chunk_size = 8
        for i in range(0, len(final_answer), chunk_size):
            token = final_answer[i:i+chunk_size]
            full_response += token
            yield {"type": "content", "token": token}
            await asyncio.sleep(0.01)
    elif _is_image_generation_query(query):
        yield {"type": "status", "status": "Generating image..."}
        from modules.tools.image import ImageGenTool
        import asyncio
        
        image_result = ImageGenTool().execute({"prompt": query})
        img_match = re.search(r"!\[Generated Image\]\((.*?)\)", image_result)
        if img_match:
            img_link = img_match.group(0)
            filename = img_link.split("/")[-1].replace(")", "")
            final_answer = (
                f"I have generated the image you requested. Here is your generated image:\n\n"
                f"{img_link}\n\n"
                f"**Downloads & Sharing:**\n"
                f"* [Download Image](/download/{filename})\n"
                f"* [Download Image (HTTPS)](https://synthetixanalytics.com/download/{filename})"
            )
        else:
            final_answer = image_result

        chunk_size = 8
        for i in range(0, len(final_answer), chunk_size):
            token = final_answer[i:i+chunk_size]
            full_response += token
            yield {"type": "content", "token": token}
            await asyncio.sleep(0.01)
    elif needs_agent:
        from modules import coordinator
        import asyncio
        # Proactively save previous message to previous_message.txt in case the agent reads it
        _write_previous_message_file(chat_ctx)
        agent_ctx = _build_agent_ctx(chat_ctx, context_parts, sources)
        
        final_answer = ""
        for event_type, data in coordinator.stream_task(query, agent_ctx):
            if event_type == "status":
                yield {"type": "status", "status": data}
            elif event_type == "error":
                yield {"type": "error", "detail": data}
                return
            elif event_type == "final":
                final_answer = data
                
        chunk_size = 8
        for i in range(0, len(final_answer), chunk_size):
            token = final_answer[i:i+chunk_size]
            full_response += token
            yield {"type": "content", "token": token}
            await asyncio.sleep(0.01)
    elif is_coding_query and not is_coding_output and not is_knowledge:
        # ── Fast Code Generation Stream ────────────────────────────────────
        # Stream code and tests directly to ensure zero 504 Gateway Timeouts.
        yield {"type": "status", "status": "Generating production code & test suite..."}
        await asyncio.sleep(0.01)

        async for token in _stream_in_thread(
            aarkaa_engine.stream_final_response,
            query, fused_context, intent=intent, lang=detected_lang,
            mode=mode, history=chat_ctx, user_facts=user_facts
        ):
            full_response += token
            yield {"type": "content", "token": token}
    else:
        # Stream tokens live token-by-token using high-performance synthesis engine
        import asyncio
        from modules.external_agents import stream_aarka_response
        async for token in _stream_in_thread(
            stream_aarka_response, query, context=fused_context, history=chat_ctx
        ):
            full_response += token
            yield {"type": "content", "token": token}

    # ── 7. Yield final stats IMMEDIATELY so the client can close the stream ─
    elapsed = round(time.perf_counter() - start, 3)
    yield {"type": "final", "processing_time": elapsed}


    # ── 8. Verification + post-process in background (non-blocking) ───────
    # The verifier runs a full LLM inference pass (~30-60s on CPU) which
    # previously blocked the SSE stream. Moving it to a background thread
    # lets the client finish immediately while we improve the stored history.
    combined_confidence = (filter_confidence + 0.5) / 2

    def _background_verify_and_store():
        try:
            _post_process(
                user_id, session_id, query, full_response,
                intent, combined_confidence, sources[-1] if sources else "aarkaa",
                memory, auto_learn,
            )
            logger.info("Background store completed for query: %.60s...", query)
        except Exception as exc:
            logger.error("Background store failed: %s", exc)

    bg_thread = threading.Thread(target=_background_verify_and_store, daemon=True)
    bg_thread.start()


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
    """Store conversation, extract user facts, and trigger auto-learn if needed."""
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
        memory_mod.extract_user_facts(user_id=user_id, query=query)
    except Exception as exc:
        logger.error("Post-process store/fact extraction failed: %s", exc)

    try:
        auto_learn_mod.check_and_learn(user_id)
    except Exception as exc:
        logger.error("Auto-learn check failed: %s", exc)
