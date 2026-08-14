"""
AARKAAI – Web Search Module (DuckDuckGo + Wikipedia)

Used when latest information is required or RAG is insufficient.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Google Custom Search ───────────────────────────────────────────────────


def search_google_cse(query: str, max_results: int = 5) -> list[dict]:
    """
    Search using Google Custom Search JSON API when GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID are set.
    Returns list of dicts with keys: title, url, snippet
    """
    import urllib.request
    import urllib.parse
    import json
    import config

    api_key = config.GOOGLE_CSE_API_KEY or config.GEMINI_API_KEY
    cse_id = config.GOOGLE_CSE_ID

    if not api_key or not cse_id:
        logger.debug("Google CSE not configured (missing key or cse_id). Falling back to DuckDuckGo.")
        return []

    try:
        params = urllib.parse.urlencode({
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(max_results, 10),
        })
        url = f"https://www.googleapis.com/customsearch/v1?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "AARKAAI/2.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        
        results = []
        items = data.get("items", [])
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        logger.info("Google CSE returned %d results for query: %s", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("Google Custom Search failed: %s", exc)
        return []


# ─── DuckDuckGo ───────────────────────────────────────────────────────────────


def search_ddg(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo for web results.

    Returns list of dicts with keys: title, url, snippet
    """
    try:
        from ddgs import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
        logger.info("DDG returned %d results for: %s", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("DDG search failed: %s", exc)
        return []


# ─── Wikipedia ────────────────────────────────────────────────────────────────


def search_wikipedia(query: str, sentences: int = 5, lang: str = "en") -> Optional[str]:
    """
    Fetch a Wikipedia summary for the query.

    Parameters
    ----------
    lang : str
        ISO 639-1 language code (e.g., 'en', 'hi', 'es', 'fr').

    Returns the summary text, or None if not found.
    """
    try:
        import wikipediaapi

        wiki = wikipediaapi.Wikipedia(
            user_agent="AARKAAI/1.0 (https://aarkaai.local)",
            language=lang,
        )
        page = wiki.page(query)

        if not page.exists() and lang != "en":
            wiki_en = wikipediaapi.Wikipedia(
                user_agent="AARKAAI/1.0 (https://aarkaai.local)",
                language="en",
            )
            page = wiki_en.page(query)

        if page.exists():
            summary = page.summary
            # Truncate to requested sentence count
            sents = summary.split(". ")
            truncated = ". ".join(sents[:sentences])
            if not truncated.endswith("."):
                truncated += "."
            logger.info("Wikipedia match: %s (%d chars, lang=%s)", page.title, len(truncated), lang)
            return f"[Wikipedia: {page.title}]\n{truncated}"

        return None
    except Exception as exc:
        logger.error("Wikipedia search failed: %s", exc)
        return None


import re

def _is_live_tracker_snippet(text: str) -> bool:
    """Detect if a snippet or title looks like a live stock/crypto ticker or widget."""
    s_low = text.lower()
    live_patterns = [
        "price today is", "live price", "current price", "price as of",
        "trading volume", "market cap of", "market capitalization",
        "24-hour volume", "circulating supply", "max supply"
    ]
    if any(p in s_low for p in live_patterns):
        return True
    # Match percentage changes commonly found in live tickers, e.g. -1.09%, +2.5%
    if re.search(r"[-+]\d+(\.\d+)?%", s_low):
        return True
    return False


def _get_source_authority(url: str) -> tuple[int, str]:
    """
    Calculate the domain authority score and tier of a URL.
    Returns (score, tier_label)
    - 10: Official Education/Government Authority
    - 8: General Gov/Edu/Org Domain
    - 5: Reputable Reference/News
    - 1: General Web Source
    - 0: Low-Quality Directory/SEO Aggregator (Penalized/Filtered)
    """
    url_low = url.lower()
    
    # Low-quality business directories, SEO aggregators, and course hubs (Score 0)
    directories = [
        "justdial.com", "collegedunia.com", "sulekha.com", "shiksha.com", 
        "yellowpages.com", "indiamart.com", "asklaila.com", "collegedekho.com",
        "getmyuni.com", "targetstudy.com", "unacademy.com", "glassdoor.com",
        "ambitionbox.com", "indiatoday.in", "collegedekho.com"
    ]
    if any(d in url_low for d in directories):
        return 0, "SEO Directory / Unverified Aggregator"
        
    # High-authority official education and government portals (Score 10)
    official_auths = [
        "ugc.ac.in", "aicte-india.org", "mhrd.gov", "tneaonline.org", 
        "annauniv.edu", "education.gov"
    ]
    if any(auth in url_low for auth in official_auths):
        return 10, "Official Education/Government Authority"
        
    # General Gov, Edu, or Org domains (Score 8)
    if any(domain in url_low for domain in [".gov", ".edu", "ac.in", ".org"]):
        return 8, "Government / Educational Domain"
        
    # Reputable Reference and global news channels (Score 5)
    news_and_reference = [
        "wikipedia.org", "britannica.com", "reuters.com", "bloomberg.com", 
        "nytimes.com", "bbc.co.uk", "bbc.com", "thehindu.com", "indianexpress.com",
        "moneycontrol.com", "livemint.com"
    ]
    if any(n in url_low for n in news_and_reference):
        return 5, "Reputable Reference / News"
        
    return 1, "General Web Source"


def _calculate_freshness(text: str, current_year: int = 2026) -> float:
    """
    Calculate a freshness multiplier based on temporal clues in the text.
    Returns a float between 0.01 and 1.15.
    """
    text_low = text.lower()
    
    # Extract all 4-digit years between 1990 and 2030
    years = [int(y) for y in re.findall(r'\b(19\d{2}|20[0-2]\d|2030)\b', text)]
    
    if not years:
        # If no year is mentioned, default to neutral freshness (1.0)
        if any(w in text_low for w in ["latest", "current", "update", "today", "live"]):
            return 1.1
        return 1.0
        
    # Find the most recent year mentioned in the snippet
    max_year = max(years)
    
    # If the snippet contains historical markers
    if max_year < current_year:
        age = current_year - max_year
        # Stronger exponential decay penalty (18% drop per year)
        freshness = 0.82 ** age
        # Severe penalty for extremely old data (> 5 years old) to prevent outdating high authority
        if age > 5:
            freshness *= 0.4
        # Further penalize if it has explicit historical qualifiers
        if any(q in text_low for q in ["as of", "historical", "archived", "back in"]):
            freshness *= 0.7
        return max(0.01, freshness)
    elif max_year == current_year:
        return 1.15  # Freshness boost for the current year
    elif max_year == current_year - 1:
        return 1.05  # Slight boost for last year's data
    else:
        return 1.0


def get_web_context(query: str, max_results: int = 5, lang: str = "en", filter_live: bool = False) -> str:
    """
    Combined search: DDG + Wikipedia with unified freshness/authority ranking.
    Returns a single unified list of reference contexts sorted by composite quality score.
    """
    candidates = []

    # 1. Search Google Custom Search first; fallback to DuckDuckGo if CSE is not configured or fails
    search_results = search_google_cse(query, max_results=max_results)
    if not search_results:
        search_results = search_ddg(query, max_results=max_results)

    # 2. Extract Wikipedia page title if present in search results
    wiki_title = None
    wiki_lang = lang
    if search_results:
        from urllib.parse import urlparse, unquote
        for r in search_results:
            url = r.get("url", "")
            parsed = urlparse(url)
            if "wikipedia.org" in parsed.netloc:
                path_parts = parsed.path.split("/wiki/")
                if len(path_parts) > 1:
                    wiki_title = unquote(path_parts[1]).split("#")[0].replace("_", " ")
                    netloc_parts = parsed.netloc.split(".")
                    if netloc_parts and len(netloc_parts[0]) == 2:
                        wiki_lang = netloc_parts[0]
                    break

    # 3. Fetch Wikipedia summary
    wiki_context = None
    if wiki_title:
        logger.info("Found Wikipedia link in search results: %s (lang=%s)", wiki_title, wiki_lang)
        wiki_context = search_wikipedia(wiki_title, lang=wiki_lang)

    if not wiki_context:
        wiki_context = search_wikipedia(query, lang=lang)

    if wiki_context:
        # Extract title and summary text from Wikipedia context block
        # Format: "[Wikipedia: Page Title]\nSummary Text"
        lines = wiki_context.split("\n", 1)
        title = lines[0].replace("[", "").replace("]", "") if lines else "Wikipedia"
        summary = lines[1] if len(lines) > 1 else wiki_context
        wiki_url = f"https://{wiki_lang}.wikipedia.org/wiki/{title.replace('Wikipedia: ', '').replace(' ', '_')}"
        
        # Wikipedia starts with very high authority (10)
        authority_score = 10
        tier = "Official Education/Government Authority"
        freshness = _calculate_freshness(summary)
        composite_score = authority_score * freshness
        
        candidates.append({
            "title": title,
            "url": wiki_url,
            "snippet": summary,
            "tier": tier,
            "composite_score": composite_score,
            "authority": authority_score,
            "freshness": freshness
        })

    # 4. Filter and Score search results (Google CSE / DDG)
    if search_results:
        for r in search_results:
            # Skip live stock tickers if requested
            if filter_live and (_is_live_tracker_snippet(r["snippet"]) or _is_live_tracker_snippet(r["title"])):
                logger.info("Filtered out live tracker snippet from web search: %s", r["title"])
                continue
            # Skip Wikipedia duplicate
            if "wikipedia.org" in r.get("url", ""):
                continue
                
            authority_score, tier = _get_source_authority(r["url"])
            
            # Skip low-quality directories entirely
            if authority_score == 0:
                continue
                
            freshness = _calculate_freshness(r["snippet"] + " " + r["title"])
            composite_score = authority_score * freshness
            
            candidates.append({
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"],
                "tier": tier,
                "composite_score": composite_score,
                "authority": authority_score,
                "freshness": freshness
            })

    if not candidates:
        return ""

    # Sort all candidates (Wikipedia + DDG) together by composite score descending
    candidates.sort(key=lambda x: x["composite_score"], reverse=True)

    # Format the unified context string
    formatted_parts = []
    for c in candidates:
        formatted_parts.append(
            f"- [{c['title']}]({c['url']}) [Source Tier: {c['tier']}] [Freshness Weight: {c['freshness']:.2f}]: {c['snippet']}"
        )

    return "[Web Search Results (Ranked by Combined Authority & Freshness)]\n" + "\n".join(formatted_parts)

# Financial news source domains for targeted search
_FINANCIAL_NEWS_DOMAINS = [
    "moneycontrol.com", "economictimes.indiatimes.com", "livemint.com",
    "reuters.com", "bloomberg.com", "cnbcawaaz.com", "ndtvprofit.com",
    "business-standard.com", "financialexpress.com", "thehindubusinessline.com",
    "marketwatch.com", "seekingalpha.com", "investopedia.com"
]

_REGULATORY_DOMAINS = [
    "rbi.org.in", "sebi.gov.in", "mca.gov.in", "nseindia.com", "bseindia.com",
    "pib.gov.in", "incometaxindia.gov.in"
]

def search_financial_news(query: str, max_results: int = 5) -> str:
    """Search financial news from trusted sources.
    Appends financial source domain filters to the search query.
    Returns formatted context with source attribution."""
    domains_query = " OR ".join([f"site:{d}" for d in _FINANCIAL_NEWS_DOMAINS])
    full_query = f"{query} ({domains_query})"
    return get_web_context(full_query, max_results)

def search_regulatory_updates(query: str, max_results: int = 5) -> str:
    """Search RBI/SEBI/MCA regulatory updates.
    Targets government and regulatory domains.
    Returns formatted context with official source links."""
    domains_query = " OR ".join([f"site:{d}" for d in _REGULATORY_DOMAINS])
    full_query = f"{query} ({domains_query})"
    return get_web_context(full_query, max_results)

def search_company_announcements(symbol: str, max_results: int = 5) -> str:
    """Search for recent company announcements, results, board meetings.
    Constructs query from symbol name + 'announcement OR results OR board meeting'.
    Returns formatted results."""
    full_query = f"{symbol} announcement OR results OR board meeting"
    return get_web_context(full_query, max_results)

