"""
AARKAAI Pipeline – Helper Functions & Constants

Extracted from pipeline.py lines 86-1154.
All pure helper functions and keyword constants live here.

Fixes applied during extraction:
  - P-3: Regex patterns in _is_reasoning_query pre-compiled at module level
  - CQ-4: Magic thresholds replaced with named constants
  - CQ-1: Bare `except: pass` replaced with `except Exception as exc: logger.debug(...)`
"""
from __future__ import annotations

import logging
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional

import config
from config import MAX_QUERY_LENGTH

logger = logging.getLogger(__name__)

# ─── Named Constants (CQ-4: replaces inline magic numbers) ───────────────────
FILTER_CONFIDENCE_FLOOR = 0.45       # Below this → fall back to general_query
FOLLOWUP_SCORE_THRESHOLD = 0.4       # Above this → is_followup_query
FOLLOWUP_RAG_THRESHOLD = 0.5         # Above this → top_k=1 for RAG
TOPIC_SHIFT_OVERLAP_MIN = 0.10       # Below this → topic shift detected
TOPIC_SHIFT_WORD_MIN = 10            # Min words to trigger topic shift check
BUDGET_MIN_CHUNK = 400               # Min chars to keep in context budget

# ─── Keyword Constants ───────────────────────────────────────────────────────

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

_NO_WEB_SEARCH_KEYWORDS = [
    "design a", "system design", "design system", "architecture", "schema",
    "database design", "api design", "microservice", "load balancer",
    "caching", "cache", "sharding", "replication", "consistency",
    "high availability", "fault tolerant", "scalab", "distributed",
    "message queue", "event driven", "pub sub", "rate limit",
    "algorithm", "data structure", "time complexity", "space complexity",
    "big o", "big-o", "leetcode", "dynamic programming", "recursion",
    "binary search", "hash map", "linked list", "sorting", "graph",
    "log entries", "log entry", "ip address", "frequent", "top k",
    "heap", "min-heap", "max-heap", "priority queue", "partitioning",
    "count-min sketch", "mapreduce", "map reduce",
    "billion", "million entries", "ram available", "memory constraint",
    "constraint", "how would you solve", "how to solve", "solve this",
    "prove", "proof", "theorem", "complexity",
]

_KNOWLEDGE_FIRST_BYPASS_DOMAINS = frozenset({"finance", "web_search", "news"})
_KNOWLEDGE_FIRST_BYPASS_INTENTS = frozenset({
    "stock_query", "market_data", "news_search", "web_lookup",
    "price_query", "portfolio_query",
})
_FRESHNESS_KEYWORDS = frozenset({
    "today", "now", "latest", "current", "live", "price", "quote",
    "market", "news", "2026", "yesterday", "this week", "this month",
})

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
    "strategy", "strategies", "option", "options", "call", "put", "spread",
    "iron condor", "straddle", "strangle", "covered call",
    "bull call", "bear put", "technical", "rsi", "macd",
    "ema", "bollinger", "signal", "setup", "trade setup",
    "lot size", "stop loss", "target", "risk reward",
    "technical analysis", "chart", "indicator",
    "bullish", "bearish", "neutral", "reversal",
    "screener", "scanner", "screen",
    "what strategy", "choose strategy", "which strategy", "trade plan",
]

_FINANCE_INTENT_KEYWORDS = [
    "stock", "shares", "ticker", "market", "earnings", "price",
    "target price", "analyst", "nasdaq", "nyse", "nse", "bse",
    "invest", "investment", "portfolio", "dividend", "etf", "mutual fund"
]

# Language keywords (lazy-loaded to avoid import-time dependency on aarkaa_engine)
_LANGUAGE_KEYWORDS: dict[str, str] = {}

def _ensure_language_keywords():
    """Populate _LANGUAGE_KEYWORDS on first use."""
    global _LANGUAGE_KEYWORDS
    if not _LANGUAGE_KEYWORDS:
        try:
            from modules.aarkaa_engine import _LANG_NAMES
            _LANGUAGE_KEYWORDS = {name.lower(): code for code, name in _LANG_NAMES.items()}
        except Exception as exc:
            logger.debug("Could not load _LANG_NAMES: %s", exc)


# ─── Pre-compiled Regex Patterns (P-3 fix) ───────────────────────────────────

_REASONING_PATTERNS = [
    re.compile(r'\bbat\b.*\bball\b', re.DOTALL),
    re.compile(r'\bsheep\b.*\b(farmer|wolf|wolves|river|boat|count|puzzle|riddle)\b', re.DOTALL),
    re.compile(r'\b(farmer|count|riddle|puzzle|logic)\b.*\bsheep\b', re.DOTALL),
    re.compile(r'\btrain\b.*\bstation\b', re.DOTALL),
    re.compile(r'\bif\b.*\bmore than\b.*\bhow\b', re.DOTALL),
    re.compile(r'\bhow\s+old\s+is\b.*\b(brother|sister|father|mother|son|daughter|years|times|age)\b', re.DOTALL),
    re.compile(r'\briddle\b', re.DOTALL),
    re.compile(r'\bpuzzle\b', re.DOTALL),
    re.compile(r'\blogic question\b', re.DOTALL),
    re.compile(r'\bmath problem\b', re.DOTALL),
    re.compile(r'\bcost(s)?\b.*\bmore than\b', re.DOTALL),
    re.compile(r'\bolder\s+than\b.*\b(brother|sister|father|mother|son|daughter|years|times|age)\b', re.DOTALL),
    re.compile(r'\bsister\b.*\bbrother\b', re.DOTALL),
    re.compile(r'\bfarmer\b.*\b(sheep|cabbage|wolf|goat|river|boat|crossing|puzzle|riddle)\b', re.DOTALL),
    re.compile(r'\bdoctor\b.*\bpill', re.DOTALL),
    re.compile(r'\bpill(s)?\b.*\bevery\b.*\bminute', re.DOTALL),
    re.compile(r'\btake\b.*\bpill', re.DOTALL),
    re.compile(r'\blily\s*pad', re.DOTALL),
    re.compile(r'\bdouble(s)?\b.*\bevery\b', re.DOTALL),
    re.compile(r'\bhow\s+(long|many|much)\b.*\b(take|need|require)\b.*\b(minute|hour|day|second|pill|interval|fence|post|task|work|job|complete|finish)\b', re.DOTALL),
    re.compile(r'\bfence\s*post', re.DOTALL),
    re.compile(r'\btrick\s*question', re.DOTALL),
    re.compile(r'\bbrain\s*teaser', re.DOTALL),
    re.compile(r'\bif\b.*\bthen\b.*\bhow\b', re.DOTALL),
    re.compile(r'\bclock\b.*\bangle\b', re.DOTALL),
    re.compile(r'\bangle\b.*\bhand(s)?\b', re.DOTALL),
    re.compile(r'\bovertake\b', re.DOTALL),
    re.compile(r'\brunner(s)?\b.*\brace\b', re.DOTALL),
    re.compile(r'\bposition\b.*\brace\b', re.DOTALL),
    re.compile(r'\bheads?\b.*\blegs?\b', re.DOTALL),
    re.compile(r'\blegs?\b.*\bheads?\b', re.DOTALL),
    re.compile(r'\bwheels?\b.*\b(cars?|motorcycles?|bicycles?|vehicles?|tricycles?)\b', re.DOTALL),
    re.compile(r'\b(cars?|motorcycles?|bicycles?|vehicles?|tricycles?)\b.*\bwheels?\b', re.DOTALL),
    re.compile(r'\b(falls?|decreases?|rises?|increases?)\b.*\bpercentage\s+gain\b', re.DOTALL),
    re.compile(r'\b(falls?|decreases?|rises?|increases?)\b.*\bpercentage\s+loss\b', re.DOTALL),
    re.compile(r'\bpercentage\s+gain\b.*\breturn\b.*\boriginal\b', re.DOTALL),
    re.compile(r'\bpercentage\s+loss\b.*\breturn\b.*\boriginal\b', re.DOTALL),
    re.compile(r'\b(weigh\w*|scale|balance)\b.*\b(heavier|lighter|outlier|ball|balls|coin|coins|marble|marbles|item|items|bar|bars)\b', re.DOTALL),
    re.compile(r'\b(heavier|lighter|outlier|ball|balls|coin|coins|marble|marbles|item|items|bar|bars)\b.*\b(weigh\w*|scale|balance)\b', re.DOTALL),
]


# ─── Helper Functions ────────────────────────────────────────────────────────

def _detect_requested_language(query: str, current_detected: str = "en") -> str:
    """Always enforce English as the system language."""
    return "en"


def _detect_language(text: str) -> str:
    """Always enforce English as the system language."""
    return "en"


def _sanitize_query(query: str) -> str:
    """Clean up the query for safe processing and security hardening."""
    query = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", query)
    for token in ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]:
        query = query.replace(token, "")
    if len(query) > MAX_QUERY_LENGTH:
        query = query[:MAX_QUERY_LENGTH]
    return query.strip()


def _is_reasoning_query(query: str) -> bool:
    """Detect math, logic word problems, and puzzles.

    Uses pre-compiled regex patterns (P-3 fix) for ~10× faster matching
    vs. compiling patterns on every call.
    """
    q = query.lower()
    return any(p.search(q) for p in _REASONING_PATTERNS)


def _resolve_search_query(query: str, chat_ctx: list[dict] | None) -> str:
    """Resolve direct conversational search triggers to the previous user query."""
    q_low = query.strip().lower()
    search_directives = ["search web", "search the web", "google it", "look it up", "search online", "find online", "search"]
    if q_low in search_directives and chat_ctx:
        for msg in reversed(chat_ctx):
            if msg.get("role") == "user":
                last_msg = msg.get("message", "")
                if last_msg and last_msg.strip().lower() not in search_directives:
                    logger.info("Resolved search directive '%s' to previous user query: '%s'", query, last_msg)
                    return last_msg
    return query


def _enhance_search_query(query: str) -> str:
    """Rewrite statistical/factual queries with temporal and authority keywords."""
    q_low = query.lower()
    if re.search(r'\b(202\d|201\d|19\d{2})\b', q_low):
        return query
    is_statistical = any(kw in q_low for kw in ["how many", "how much", "count of", "number of", "population", "census", "statistics", "list of"])
    is_college_related = any(kw in q_low for kw in ["college", "colleges", "university", "universities", "school", "schools", "institution", "institutions"])
    if is_statistical:
        enhanced = query.strip().rstrip("?").rstrip(".")
        enhanced += " 2026"
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
    """Detect queries that request image/art generation."""
    q = query.lower().strip()
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
    if has_gen_verb and (has_visual_desc or has_visual_subj):
        coding_excludes = ["python", "script", "code", "function", "class", "html", "css", "javascript", "file", ".py", ".js"]
        if not any(ex in q for ex in coding_excludes):
            return True
    if re.match(r'^(a|an|the)\s+', q) and has_visual_desc and len(q.split()) >= 5:
        coding_excludes = ["python", "script", "code", "function", "class", "html", "css", "file"]
        if not any(ex in q for ex in coding_excludes):
            return True
    return False


def _is_pdf_generation_query(query: str) -> bool:
    """Detect if the query explicitly asks to create/generate a downloadable PDF report."""
    q = query.lower().strip()
    coding_excludes = [
        "python", "script", "code", "library", "libraries", "how to", "write code",
        "separate files", "make skills separate"
    ]
    if any(ex in q for ex in coding_excludes):
        return False
    if bool(re.search(r'(?:^|\s)[@/](?:pdf|gamma-pdf|premium-report)\b', q)):
        return True
    pdf_action_patterns = [
        r"\b(create|generate|make|compile|produce|export|write|prepare|build)\s+(a\s+|an\s+|the\s+)?(premium\s+|detailed\s+|executive\s+)?pdf(\s+report|\s+document)?\b",
        r"\b(as\s+a\s+pdf|in\s+pdf(\s+format)?|export\s+to\s+pdf|download\s+pdf|download\s+as\s+pdf)\b",
        r"\bpdf\s+(report|dossier|document)\s+(on|about|for)\b",
    ]
    if any(re.search(pat, q) for pat in pdf_action_patterns):
        return True
    report_action_patterns = [
        r"\b(create|generate|make|compile|produce|write|prepare)\s+(a\s+|an\s+|the\s+)?(premium\s+|detailed\s+|executive\s+|comprehensive\s+)?(report|whitepaper|dossier)\s+(on|about|for|regarding)\b",
        r"^(please\s+)?(create|generate|make|compile|write|prepare)\s+(a\s+|an\s+|the\s+)?(premium\s+|detailed\s+|executive\s+|comprehensive\s+)?(report|whitepaper)\b",
    ]
    if any(re.search(pat, q) for pat in report_action_patterns):
        if not re.search(r"\b(according\s+to|what\s+does|explain|show\s+me|read|analyze|analyse|audit)\s+the\s+(annual|financial|earnings)?\s*report\b", q):
            return True
    return False


def _extract_pdf_topic(query: str) -> str:
    """Extract a clean topic from a PDF generation query."""
    topic = re.sub(r'^\s*[@/](?:pdf|gamma-pdf|premium-report)\s*', '', query, flags=re.IGNORECASE).strip()
    q = topic.lower()
    prefixes = [
        "create a premium pdf report about", "generate a premium pdf report about",
        "create a premium pdf about", "generate a premium pdf about",
        "create a pdf report about", "generate a pdf report about",
        "create a pdf about", "generate a pdf about",
        "create a report about", "generate a report about",
        "make a pdf report about", "make a pdf about", "make a report about",
        "create a report on", "generate a report on",
        "create a pdf on", "generate a pdf on",
        "create", "generate", "make", "compile",
        "pdf report about", "pdf about", "report about", "document about", "report on"
    ]
    topic = query
    for p in prefixes:
        if q.startswith(p):
            topic = query[len(p):].strip()
            break
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
    """Detect if the user requested a specific color template."""
    q = query.lower()
    if "gold" in q or "audit" in q or "executive" in q:
        return "gold"
    elif "cyber" in q or "neon" in q:
        return "cyber"
    elif "minimal" in q or "editorial" in q or "black and white" in q:
        return "minimal"
    elif "white" in q or "light" in q:
        return "indigo"
    elif "dark" in q:
        return "dark"
    elif "green" in q or "emerald" in q or "teal" in q or "startup" in q or "vc" in q:
        return "emerald"
    elif "red" in q or "crimson" in q or "risk" in q:
        return "crimson"
    elif "amber" in q or "yellow" in q or "orange" in q or "corporate" in q:
        return "amber"
    return "indigo"


def _is_calculation_query(query: str) -> bool:
    """Detect queries that require mathematical/arithmetic calculation."""
    q = query.lower()
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


def _extract_and_load_skill(query: str) -> tuple[Optional[str], Optional[str], str]:
    """Detect explicit skill invocation via @<skill-name> or /<skill-name> tags."""
    match = re.search(r'(?:^|\s)[@/]([a-zA-Z0-9_-]+)', query)
    if not match:
        return None, None, query
    raw_name = match.group(1).lower().replace("_", "-")
    aliases = {
        "strategy": "options-strategy", "option": "options-strategy",
        "options": "options-strategy", "report": "premium-report",
        "reports": "premium-report", "docs": "docx", "word": "docx",
        "excel": "xlsx", "powerpoint": "pptx", "presentation": "pptx",
    }
    target_name = aliases.get(raw_name, raw_name)
    candidate_paths = [
        Path("./skills") / target_name / "SKILL.md",
        Path(".agents/skills") / target_name / "SKILL.md",
        Path("./skills") / raw_name / "SKILL.md",
        Path(".agents/skills") / raw_name / "SKILL.md",
    ]
    skill_content = None
    resolved_name = target_name
    for p in candidate_paths:
        if p.exists() and p.is_file():
            try:
                skill_content = p.read_text(encoding="utf-8")
                break
            except Exception as exc:
                logger.warning("Failed to read %s: %s", p, exc)
    if not skill_content:
        try:
            from modules.tools.skill_tools import get_registry, init_skill_registry
            reg = get_registry()
            if reg is None:
                reg = init_skill_registry()
            if reg and target_name in reg.skills:
                skill_content = reg.get_skill(target_name)
        except Exception as exc:
            logger.debug("Skill registry lookup failed: %s", exc)
    if not skill_content:
        return None, None, query
    clean_q = re.sub(r'(?:^|\s)[@/]' + re.escape(match.group(1)) + r'\b', ' ', query).strip()
    if not clean_q:
        clean_q = f"Execute autonomous analysis and execution adhering to the @{resolved_name} skill guidelines."
    return resolved_name, skill_content, clean_q


def _needs_skill_routing(query: str) -> bool:
    """Detect queries that involve file formats or document creation."""
    q = query.lower()
    if re.search(r'(?:^|\s)[@/][a-zA-Z0-9_-]+', query):
        return True
    skill_management_words = ["create skill", "update skill", "delete skill", "manage skill", "skill creator", "new skill", "test skill"]
    if any(sw in q for sw in skill_management_words):
        return True
    file_keywords = [
        ".pdf", ".docx", ".xlsx", ".pptx", ".csv",
        "pdf", "word document", "word doc", "excel", "spreadsheet",
        "powerpoint", "presentation", "slides", "slide deck",
        "image", "picture", "drawing", "illustration", "photo", "sketch",
    ]
    action_words = [
        "create", "generate", "make", "build", "write", "produce",
        "export", "convert", "read", "parse", "extract", "merge",
        "split", "format", "design",
    ]
    has_file_kw = any(kw in q for kw in file_keywords)
    has_action = any(aw in q for aw in action_words)
    if has_file_kw and has_action:
        return True
    if re.search(r'\.(pdf|docx|xlsx|pptx|csv)\b', q):
        return True
    if any(kw in q for kw in ["design a webpage", "build a dashboard", "create a form", "html page", "web page", "landing page"]):
        return True
    return False


def _has_live_finance_intent(query: str, domain: str, intent: str) -> bool:
    """Determine if we should query the live yfinance engine."""
    q_low = query.lower()
    exclude_keywords = [
        "revenue", "sales", "income", "employee", "employees", "founded",
        "who is the ceo", "ceo of", "history of", "corporate office",
        "address", "phone number", "subsidiaries", "products", "services"
    ]
    if any(kw in q_low for kw in exclude_keywords):
        return False
    if re.search(r"\b(?:what(?:['']s|\s+is)?|which|identify|detect|name)\s+(?:the\s+)?language\b|\bwhat\s*is\s*the\s*language\b|\bwhat\s*language\b|\btranslate\b", q_low):
        return False
    if re.search(r"\b(18\d{2}|19\d{2}|20\d{2}|2100)\b", query):
        return False
    temporal_keywords = ["forecast", "projection", "prediction", "historical", "history", "past", "future"]
    if any(kw in q_low for kw in temporal_keywords):
        return False
    if re.search(r"\$[A-Za-z]{1,6}\b", query):
        return True
    if re.search(r"\b[A-Za-z]{2,20}\.NS\b", query):
        return True
    q_clean = q_low.replace("trade-off", "").replace("tradeoff", "")
    stock_keywords = [
        "stock", "shares", "ticker", "price", "dividend", "market cap",
        "pe ratio", "volume", "day high", "day low", "nse", "bse", "nasdaq", "nyse",
        "chart", "trade", "buy", "sell", "portfolio", "etf", "mutual fund"
    ]
    if any(kw in q_clean for kw in stock_keywords):
        return True
    strategy_keywords = [
        "strategy", "strategies", "bullish", "bearish", "neutral", "reversal",
        "options", "option", "call", "put", "strike", "spread", "straddle", "condor",
        "screener", "scanner", "setup", "setups", "trade plan", "nifty", "banknifty", "sensex"
    ]
    if any(kw in q_clean for kw in strategy_keywords):
        return True
    from config import FOREX_PAIRS, COMMODITY_TICKERS
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
        word_count = len(q_low.split())
        if word_count <= 2:
            return True
    return False


def _extract_python_code(query: str) -> str:
    """Extract Python code from a query containing code blocks or code-like lines."""
    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", query, re.DOTALL | re.IGNORECASE)
    if code_blocks:
        return code_blocks[0].strip()
    lines = query.split("\n")
    code_lines = []
    in_code = False
    for line in lines:
        stripped = line.strip()
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
            if any(p in stripped.lower() for p in ["what is the output", "output of", "explain"]):
                continue
            code_lines.append(line)
    if code_lines:
        return "\n".join(code_lines).strip()
    return ""


def _execute_python_code(code: str) -> str:
    """Execute Python code in a sandboxed subprocess."""
    from config import SAFE_WORK_DIR
    work_dir = SAFE_WORK_DIR
    work_dir.mkdir(parents=True, exist_ok=True)
    filename = f"temp_eval_{uuid.uuid4().hex}.py"
    temp_file = work_dir / filename
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
        safe_env = {
            "PATH": "/usr/bin:/usr/local/bin",
            "PYTHONPATH": "",
            "HOME": str(work_dir),
            "LANG": "en_US.UTF-8",
        }
        cmd = [sys.executable, "-I", filename]
        result = subprocess.run(
            cmd, cwd=str(work_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=5.0, env=safe_env,
        )
        output = ""
        if result.stdout:
            stdout_text = result.stdout[:3000] + ("\n... [stdout truncated]" if len(result.stdout) > 3000 else "")
            output += f"[stdout]\n{stdout_text}\n"
        if result.stderr:
            stderr_clean = result.stderr.replace(str(Path.home()), "~")
            stderr_text = stderr_clean[:1000] + ("\n... [stderr truncated]" if len(stderr_clean) > 1000 else "")
            output += f"[stderr]\n{stderr_text}\n"
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
        except Exception as exc:
            logger.debug("Temp file cleanup failed: %s", exc)


def _fuse_context_budget(context_parts: list[str], max_budget: int = 8000) -> str:
    """Join context parts and enforce a cumulative character budget."""
    if not context_parts:
        return ""
    total = sum(len(p) for p in context_parts)
    if total <= max_budget:
        return "\n\n---\n\n".join(context_parts)
    logger.info("Context parts total %d chars exceeds budget %d chars — enforcing cumulative budget", total, max_budget)
    budget_remaining = max_budget
    budgeted_parts = []
    for part in context_parts:
        if not part.strip():
            continue
        part_len = len(part)
        if part_len <= budget_remaining:
            budgeted_parts.append(part)
            budget_remaining -= part_len
        elif budget_remaining >= BUDGET_MIN_CHUNK:
            truncated = part[:budget_remaining - 50] + "\n... [context truncated to fit budget]"
            budgeted_parts.append(truncated)
            budget_remaining = 0
            break
        else:
            break
    fused = "\n\n---\n\n".join(budgeted_parts)
    logger.info("Fused context constrained to %d chars (from %d chars)", len(fused), total)
    return fused


def _has_keyword_match(query: str, keywords: list[str]) -> bool:
    """Check if any keywords match as exact words/phrases in the query."""
    words = set(re.findall(r"\b\w+\b", query.lower()))
    for kw in keywords:
        if " " in kw:
            if re.search(r"\b" + re.escape(kw) + r"\b", query.lower()):
                return True
        elif kw.lower() in words:
            return True
    return False


def _is_identity_query(query: str) -> bool:
    """Detect if the query asks about the user's or assistant's identity."""
    q = query.lower()
    identity_phrases = ["who am i", "who i am", "who are you", "what is my name", "do you know me", "do you know who i am", "do u know who am i"]
    return any(p in q for p in identity_phrases)


def _should_skip_rag(query: str, intent: str, domain: str) -> bool:
    """Consolidated RAG bypass logic."""
    try:
        from modules.semantic_filter import _is_coding_syntax
    except ImportError:
        _is_coding_syntax = lambda q: False  # noqa: E731

    q_low = query.lower().strip()
    clean_q = re.sub(r"[^\w\s]", "", q_low).strip()
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
    if _is_reasoning_query(query) or intent == "reasoning_puzzle":
        return True
    if re.search(r"\b(calculate|compute|solve|what is)\b", q_low) and re.search(r"\d+\s*[\+\-\*/\^]\s*\d+", q_low):
        return True
    is_sysdesign = any(w in q_low for w in ["system design", "architecture", "design a", "design an", "scale a", "eviction", "replication", "sharding", "capacity estimation", "latency", "load balancer"])
    if (intent == "coding_help" or _is_coding_syntax(query) or domain == "technology") and not is_sysdesign:
        return True
    creative_keywords = ["write a poem", "tell a joke", "write a story", "make a joke", "tell a story", "compose a song", "write a lyrics"]
    if any(kw in q_low for kw in creative_keywords):
        return True
    is_live_fin = domain == "finance" or intent.startswith("finance") or any(sig in q_low for sig in ["btc", "bitcoin", "crypto", "forex", "stock", "nifty", "gold", "silver", "crude", "trading plan", "channel oscillation"])
    if is_live_fin and not is_sysdesign:
        return True
    return False


def _follow_up_score(query: str, chat_ctx: list) -> float:
    """Confidence-scored follow-up detection using 7 signal categories."""
    if not chat_ctx:
        return 0.0
    try:
        from modules.query_understanding import calculate_follow_up_score
        return calculate_follow_up_score(query, chat_ctx)
    except Exception:
        return 0.0


def _is_follow_up(query: str, chat_ctx: list) -> bool:
    """Boolean wrapper — returns True when follow-up confidence > 0."""
    return _follow_up_score(query, chat_ctx) > 0.0


def _detect_topic_shift(query: str, chat_ctx: list) -> bool:
    """Detect when the user switches to an unrelated topic."""
    if not chat_ctx:
        return False
    if _follow_up_score(query, chat_ctx) >= FOLLOWUP_SCORE_THRESHOLD:
        return False
    q_low = query.lower().strip()
    word_count = len(q_low.split())
    if word_count <= 6:
        return False
    shift_phrases = [
        "forget that", "never mind", "forget it", "actually forget",
        "new topic", "change topic", "different question", "something else",
        "actually,", "forget java", "forget python",
    ]
    if any(p in q_low for p in shift_phrases):
        return True
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
        return False
    history_text = " ".join(m.get("message", "") for m in chat_ctx[-20:]).lower()
    history_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", history_text)) - stop_words
    overlap = query_words.intersection(history_words)
    overlap_ratio = len(overlap) / len(query_words) if query_words else 0.0
    if overlap_ratio < TOPIC_SHIFT_OVERLAP_MIN and word_count > TOPIC_SHIFT_WORD_MIN:
        return True
    return False


def _build_agent_ctx(chat_ctx, context_parts, sources) -> str:
    """Build a context string for the coordinator agent."""
    parts = []
    if "finance" in sources:
        for part in context_parts:
            if "[Finance Data]" in part:
                parts.append(part)
                break
    for part in context_parts:
        if "[Active Autonomous Skill Directives" in part:
            parts.append(part)
            break
    if chat_ctx:
        sanitized_messages = []
        for m in chat_ctx:
            msg = m.get('message', '')
            if not msg:
                continue
            lines = []
            for line in msg.split("\n"):
                line_strip = line.strip()
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
    """Format coder pipeline results into structured context for the 7B polish pass."""
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
    if coder_result.get("syntax_valid"):
        parts.append("✅ **Syntax Validation:** Passed (AST check clean)")
    else:
        err = coder_result.get("syntax_error", "Unknown error")
        parts.append(f"❌ **Syntax Validation:** Failed — {err}")
    sec_issues = coder_result.get("security_issues", [])
    if sec_issues:
        parts.append("⚠️ **Security Issues Found:**\n" + "\n".join(f"  - {issue}" for issue in sec_issues))
    else:
        parts.append("✅ **Security Scan:** No vulnerabilities detected")
    exec_output = coder_result.get("execution_output", "")
    if exec_output:
        parts.append(f"**Code Execution Output:**\n```\n{exec_output[:2000]}\n```")
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
    """Write the last meaningful assistant response to previous_message.txt."""
    if chat_ctx:
        last_assistant_msg = None
        for m in reversed(chat_ctx):
            if m.get('role') == 'assistant':
                msg = m.get('message', '')
                if not msg:
                    continue
                if "[Download " in msg or "/download/" in msg:
                    continue
                if "Action:" in msg or "Action Input:" in msg or "Observation:" in msg:
                    continue
                if any(t in msg for t in ["FileReadTool", "BashTool", "FileEditTool", "GetSkillTool", "ListSkillsTool"]):
                    continue
                if "does not exist in the workspace" in msg or "not found" in msg.lower() or "error:" in msg.lower():
                    continue
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
